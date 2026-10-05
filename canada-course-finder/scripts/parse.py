import csv, io, re, json, collections

import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Usage: python scripts/parse.py [path-to-sheet-export] [usd-to-cad-rate]
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "source-sheet.txt")
raw = open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n").replace("\r", " ")

sections = {}
cur = None
for line in raw.split("\n"):
    m = re.match(r"^## Sheet name: (.*)$", line)
    if m:
        cur = m.group(1).strip(); sections[cur] = []
    elif cur:
        sections[cur].append(line)

FACULTY = {
    "Faculty of Business & Economics": "Business & Economics",
    "Faculty of Engineering & Technology": "Engineering & Technology",
    "Faculty of Law & Social Sciences": "Law & Social Sciences",
    "Faculty of Health & Life Sciences": "Health & Life Sciences",
    "Extra": None,  # classified by keyword below
}

PROVINCE = {
    "Ontario": ["Lakehead", "Brock", "Windsor", "Laurentian", "Trent", "Toronto Metropol", "York University",
                "Ontario Tech", "University of Ottawa", "Wilfrid Laurier", "International Business University",
                "Niagara Falls", "Seneca", "Centennial", "George Brown"],
    "British Columbia": ["British Columbia", "UNBC", "Fairleigh", "Thompson Rivers", "Vancouver Island", "Royal Roads",
                         "Capilano", "Trinity Western", "University Canada West", "New York Institute"],
    "Manitoba": ["University of Manitoba", "Providence"],
    "Saskatchewan": ["Regina", "Saskatchewan"],
    "Alberta": ["Concordia University of Edmonton", "Lethbridge"],
    "Nova Scotia": ["Cape Breton", "Dalhousie", "Mount Saint Vincent"],
    "Quebec": ["Bishop", "Concordia University"],
    "Newfoundland & Labrador": ["Memorial"],
    "New Brunswick": ["Crandall", "University of New Brunswick"],
}
def province_of(u):
    for p, keys in PROVINCE.items():
        for k in keys:
            if k in u:
                # Concordia University (Montreal) vs Concordia University of Edmonton
                if k == "Concordia University" and "Edmonton" in u: continue
                return p
    return "Unknown"

NAME_FIX = {"Toronto Metropoliton University": "Toronto Metropolitan University", "Royal Roads": "Royal Roads University", "The University of Northern British Columbia (UNBC)": "University of Northern British Columbia (UNBC)"}

def clean(s): return re.sub(r"[ \t]+", " ", (s or "").replace('""', '"')).strip().strip('"').strip()

def parse_uni(cell):
    lines = [l.strip().strip('"') for l in cell.split("\n") if l.strip().strip('"')]
    name_lines = []
    for l in lines:
        if l.upper().startswith("QS"): break
        name_lines.append(l)
    name = " ".join(name_lines)
    name = re.sub(r"\s*QS.*$", "", name).strip()
    m2 = re.match(r"^(.*?University)\s+(\d[\d\-]+)$", name)
    if m2: name, qs_inline = m2.group(1), m2.group(2)
    else: qs_inline = ""
    name = NAME_FIX.get(name, name)
    qs = ""
    m = re.search(r"QS[^:\-]*[:\-]\s*(.*)", cell)
    if m:
        qs = m.group(1).strip().strip('"').strip()
    qs = qs.lstrip("#").strip() or qs_inline
    if qs in ("0", "", '"'): qs = ""
    return name, qs

def level_of(p):
    s = p.lower()
    if re.search(r"foundation", s): return "Pathway / Foundation"
    if re.search(r"post[- ]?bacc|graduate certificate|post graduate|graduate diploma", s): return "Postgraduate Diploma / Certificate"
    if re.search(r"\b(master|mba|msc|m\.sc|meng|masc|mas\b|ma\b|med\b|m\.ed|m\.ica|mmb|mhrm)", s) or "goodman mba" in s: return "Master's"
    if re.search(r"\b(bachelor|bba|bcom|bsc|beng|b\.tech|bcs|ba\b|ba \(|honours bachelor)", s): return "Bachelor's"
    if "diploma" in s or "dip." in s or "management –" in s: return "Diploma"
    return "Other"

def faculty_guess(p):
    s = p.lower()
    if re.search(r"engineer|computer|software|cyber|data|information|it\b|technology|programming|analytics|ai\b|energy|automation", s): return "Engineering & Technology"
    if re.search(r"biomed|health|nutrition|biolog", s): return "Health & Life Sciences"
    if re.search(r"media|communication|education", s): return "Law & Social Sciences"
    return "Business & Economics"

MONTHS = ["Jan", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
def intakes_of(s):
    t = s.lower()
    if "suspend" in t: return [], True
    found = []
    for m in MONTHS:
        key = m.lower()
        if re.search(r"\b" + key, t) or (m == "Sep" and "fall" in t) or (m == "Jan" and "winter" in t):
            found.append(m)
    return found, False

def ielts_of(s):
    m = re.search(r"I?ELTS[^0-9]{0,60}?(\d(?:\.\d)?)", s, re.I) or re.search(r"overall band score of (\d(?:\.\d)?)", s, re.I) or re.search(r"^Minimum (\d\.\d) overall", s, re.I)
    if m:
        v = float(m.group(1))
        if 5 <= v <= 9: return v
    return None

def money(s):
    s2 = s.replace(",", "")
    m = re.search(r"(\d{3,6}(?:\.\d+)?)", s2)
    return float(m.group(1)) if m else None

def tuition_of(s, duration):
    amt = money(s)
    cur = "USD" if re.search(r"\bUS|USD", s) else "CAD"
    total = bool(re.search(r"total", s, re.I))
    return amt, cur, total

def years_of(d):
    t = d.lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*month", t)
    if m: return round(float(m.group(2) or m.group(1)) / 12, 2)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to|/)?\s*(\d+(?:\.\d+)?)?\s*year", t)
    if m: return float(m.group(2) or m.group(1))
    return None

USD_TO_CAD = None  # set from args
USD_TO_CAD = float(sys.argv[2]) if len(sys.argv) > 2 else 1.42

courses, issues = [], []
seen = set()
for sheet, fac in FACULTY.items():
    rows = list(csv.reader(io.StringIO("\n".join(sections[sheet]))))
    header = rows[0]
    has_deadline = any("deadline" in h.lower() for h in header)
    uni, qs = "", ""
    for r in rows[1:]:
        r = r + [""] * (16 - len(r))
        if clean(r[1]):
            uni, qs = parse_uni(r[1])
        program = clean(r[2])
        if not program or not uni: continue
        lines = [l.strip(" •").strip() for l in program.split("\n") if l.strip(" •").strip()]
        title = lines[0]
        specs = lines[1:]
        url = clean(r[3]) if clean(r[3]).startswith("http") else ""
        if clean(r[3]) and not url: issues.append(f"{uni} | {title}: website URL column holds '{clean(r[3])}'")
        intakes, suspended = intakes_of(r[4])
        duration = clean(r[5])
        if "$" in duration or "CAD" in duration:
            issues.append(f"{uni} | {title}: duration column holds a fee ('{duration}')"); duration = ""
        english = clean(r[6])
        entry = clean(r[7])
        tuition_raw = clean(r[8])
        amt, cur, total = tuition_of(tuition_raw, duration)
        yrs = years_of(duration)
        annual = None
        if amt:
            annual = amt / yrs if (total and yrs and yrs >= 1) else amt
            if cur == "USD": annual *= USD_TO_CAD
            annual = round(annual)
        sch = clean(r[9]); dep = clean(r[10]); fee = clean(r[11])
        if has_deadline:
            deadline = clean(r[12]); note = clean(r[13])
        else:
            deadline = ""; note = clean(r[12])
            # Dalhousie rows put deadlines in the Note column
            if "start:" in note.lower(): deadline, note = note, ""
        key = (uni.lower(), re.sub(r"\W+", "", title.lower()))
        if key in seen: continue
        seen.add(key)
        f = fac or faculty_guess(title + " " + " ".join(specs))
        ielts = ielts_of(english)
        if annual and annual > 70000 and not total:
            issues.append(f"{uni} | {title}: tuition '{tuition_raw}' looks unusually high, please check")
        if ielts is None: issues.append(f"{uni} | {title}: no IELTS overall score found")
        courses.append(dict(
            uni=uni, qs=qs, prov=province_of(uni), fac=f, level=level_of(title),
            title=title, specs=specs, url=url, intakes=intakes, suspended=suspended,
            intakeRaw=clean(r[4]), duration=duration, english=english, ielts=ielts,
            entry=entry, tuition=tuition_raw, annual=annual, cur=cur, isTotal=total,
            sch=sch, dep=dep, fee=fee, deadline=deadline, note=note))

# one QS value per university (most common non-empty), flag conflicts
byu = collections.defaultdict(collections.Counter)
for c in courses:
    if c["qs"]: byu[c["uni"]][c["qs"]] += 1
for u, cnt in byu.items():
    if len(cnt) > 1: issues.append(f"{u}: QS ranking differs between rows ({', '.join(cnt)})")
for c in courses:
    c["qs"] = byu[c["uni"]].most_common(1)[0][0] if byu[c["uni"]] else ""
unknown = sorted({c["uni"] for c in courses if c["prov"] == "Unknown"})
json.dump(courses, open(os.path.join(ROOT, "data", "courses.json"), "w"), ensure_ascii=False, indent=1)
open(os.path.join(ROOT, "data", "issues.txt"), "w").write("\n".join(issues) + "\n")
print("courses:", len(courses), "unis:", len({c['uni'] for c in courses}))
print("unknown province:", unknown)
print(collections.Counter(c["level"] for c in courses))
print(collections.Counter(c["fac"] for c in courses))
print(collections.Counter(c["prov"] for c in courses))
print("no annual:", [(c["uni"], c["title"], c["tuition"]) for c in courses if not c["annual"]])
print("Other level:", [c["title"] for c in courses if c["level"] == "Other"])
print(sorted({(c["uni"],c["qs"],c["prov"]) for c in courses}))
print("\nISSUES"); print("\n".join(issues))
