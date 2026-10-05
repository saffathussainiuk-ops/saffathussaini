"""Build dist/index.html from src/template.html and data/courses.json.

Usage: python scripts/build.py [usd-to-cad-rate] ["Month Year" for the last-updated line]
Run scripts/parse.py first whenever the sheet changes.

Only university programs go on the page. Colleges, polytechnics and institutes
are left out (see NOT_UNIVERSITY). Rows listed in data/issues.txt get a
"check" note so applicants know to confirm them with a counsellor.
"""
import json, os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rate = sys.argv[1] if len(sys.argv) > 1 else "1.42"
updated = sys.argv[2] if len(sys.argv) > 2 else datetime.date.today().strftime("%B %Y")

# A name must contain "University" and must not be an institute, polytechnic or
# plain college. "Providence University College" is a degree-granting university.
NOT_UNIVERSITY = re.compile(r"\b(institute|polytechnic)\b", re.I)


def is_university(name):
    if NOT_UNIVERSITY.search(name) or "University" not in name:
        return False
    return not re.search(r"\bCollege\b", name) or "University College" in name


courses = json.load(open(os.path.join(ROOT, "data", "courses.json"), encoding="utf-8"))
for i, c in enumerate(courses):
    c["id"] = i  # stable across builds while the sheet order holds; used for shortlists

# Issues file lines look like "University | Program title: problem" or "University: problem".
checks = {}
issues_path = os.path.join(ROOT, "data", "issues.txt")
if os.path.exists(issues_path):
    for line in open(issues_path, encoding="utf-8"):
        if " | " in line:
            uni, rest = line.strip().split(" | ", 1)
            for c in courses:
                if c["uni"] == uni and rest.startswith(c["title"] + ":"):
                    checks[c["id"]] = True

kept = []
for c in courses:
    if not is_university(c["uni"]):
        continue
    if c["id"] in checks:
        c["check"] = True
    kept.append(c)

dropped = sorted({c["uni"] for c in courses} - {c["uni"] for c in kept})

template = open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8").read()
data = json.dumps(kept, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = template.replace("__DATA__", data).replace("__RATE__", rate).replace("__UPDATED__", updated)

# The template is a fragment (the artifact host adds <html>/<head>/<body>).
# For standalone hosting (GitHub Pages, Netlify, your own site) wrap it in a full document.
page = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    + html.split("<style>")[0]
    + "<style>" + html.split("<style>", 1)[1].split("</style>", 1)[0] + "</style>\n</head>\n<body>\n"
    + html.split("</style>", 1)[1]
    + "\n</body>\n</html>\n"
)
os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
open(os.path.join(ROOT, "dist", "index.html"), "w", encoding="utf-8").write(page)
if "--fragment" in sys.argv:
    out = sys.argv[sys.argv.index("--fragment") + 1]
    open(out, "w", encoding="utf-8").write(html)

print(f"Built dist/index.html with {len(kept)} university programs "
      f"at {len({c['uni'] for c in kept})} universities (USD to CAD {rate}, updated {updated})")
print("Left out (not universities): " + ", ".join(dropped))
