# Canada Course Finder

A filterable finder for 269 Canadian programs at 38 institutions, built from the counsellor course sheet. Applicants filter by IELTS, budget, level, subject, province and intake, then shortlist programs and copy the list to a counsellor.

## Quick start

1. Open `dist/index.html` in any browser to see the page.
2. When the sheet changes, export it again into `data/source-sheet.txt`, then run:

```bash
python3 scripts/parse.py
python3 scripts/build.py 1.42 "October 2026"
```

3. Check `data/issues.txt` for rows the parser flagged.

## Working on it in Claude Code

Open this folder in Claude Code (terminal: `cd canada-course-finder` then `claude`, or open the folder in the desktop app's Code tab). Claude reads `CLAUDE.md` automatically, which explains the structure, the parser rules and the content rules.

Good first requests:
- "Add our counsellor WhatsApp number 8801XXXXXXXXX to CONFIG and rebuild"
- "Make the page read the Google Sheet live instead of the exported text file"
- "Set this up as a GitHub repo and publish it on GitHub Pages"
- "Create a white-label build for another agency called X"
