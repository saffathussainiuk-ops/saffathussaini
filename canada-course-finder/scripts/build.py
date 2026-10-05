"""Build dist/index.html from src/template.html and data/courses.json.

Usage: python scripts/build.py [usd-to-cad-rate] ["Month Year" for the last-updated line]
Run scripts/parse.py first whenever the sheet changes.
"""
import json, os, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rate = sys.argv[1] if len(sys.argv) > 1 else "1.42"
updated = sys.argv[2] if len(sys.argv) > 2 else datetime.date.today().strftime("%B %Y")

courses = json.load(open(os.path.join(ROOT, "data", "courses.json"), encoding="utf-8"))
template = open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8").read()

data = json.dumps(courses, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = template.replace("__DATA__", data).replace("__RATE__", rate).replace("__UPDATED__", updated)

# The published page is a fragment (the artifact host adds <html>/<head>/<body>).
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
print(f"Built dist/index.html with {len(courses)} programs (USD to CAD {rate}, updated {updated})")
