# Canada Course Finder

A single-page course finder that helps Bangladeshi applicants find Canadian university programs that match their IELTS score, budget, study level, subject, province and intake. Applicants star programs into a shortlist and copy it to a counsellor.

Owner: Saffat Hussaini. The course data comes from the counsellor Google Sheet "Updated Canada Counselor Couress Sheet-Saffat".

Long-term goal: a white-label version that other education agencies can license, with their own brand name and WhatsApp number on the same course data.

## How it fits together

```
data/source-sheet.txt   Text export of the whole Google Sheet (all tabs, "## Sheet name:" headers, CSV rows)
scripts/parse.py        Sheet export -> data/courses.json (+ data/issues.txt with data problems found)
src/template.html       The page: HTML, CSS and JS, with __DATA__, __RATE__ and __UPDATED__ placeholders
scripts/build.py        template + courses.json -> dist/index.html (a standalone page)
dist/index.html         The built page. Open it in a browser or host it anywhere static
```

build.py keeps university programs only (`is_university`): colleges, polytechnics and
institutes are dropped at build time, so courses.json still holds every row. Rows named in
data/issues.txt get `check: true` and show a "check with counsellor" tag.

## Commands

```bash
python3 scripts/parse.py                         # uses data/source-sheet.txt, USD->CAD 1.42
python3 scripts/parse.py path/to/export.txt 1.40 # different source file or exchange rate
python3 scripts/build.py 1.42 "October 2026"     # rate shown in footer, "last updated" text
python3 scripts/build.py 1.42 "October 2026" --fragment out.html  # also write the artifact fragment
```

No dependencies beyond Python 3 standard library. Open `dist/index.html` in a browser to test.

## Parser rules worth knowing

- Only these tabs are applicant-facing courses: the four "Faculty of ..." tabs and "Extra". Programs in "Extra" get a subject area from keywords (`faculty_guess`).
- Read the file with `newline=""`. Some cells contain stray carriage returns, and universal-newline mode splits rows in the wrong place.
- University and province carry down from the row above when the cell is blank. Province comes from the `PROVINCE` keyword map, not the sheet's province column, because that column is unreliable (e.g. "10. Edmonton" for Lethbridge, Royal Roads under Manitoba).
- `NAME_FIX` corrects display names (e.g. "Toronto Metropoliton" to "Toronto Metropolitan").
- One QS value per university (most common in the sheet). Conflicts go to `data/issues.txt`.
- `annual` = tuition per year in CAD, used for the budget filter and sorting. Totals are divided by the duration in years; USD is converted with the rate argument. The page labels both cases "approx."
- Duplicate programs (same university and title) are dropped.

## Content rules

- Never put the "Special Note" tab on the page. It holds internal negotiation tips (e.g. lower IELTS if a student pays a full year's tuition).
- Never show commission, partner terms or internal report tabs (CB Report, AS A Report, Updated Report, Info Report).
- Keep the disclaimer telling applicants to confirm fees and requirements on the official university page.
- Do not use university logos without permission.
- Writing style for all page copy: plain, natural, human tone. Never use the em dash character. Use commas, periods, colons, or "to" for ranges.

## Design

Theme: "anti-gravity". Program pills drift upward on the hero canvas, cards and university orbs float, a starred program rises into the shortlist. The "Gravity" switch drops the pills into a pile and settles the cards. All motion stops under prefers-reduced-motion.

Tokens are in the `:root` block at the top of `src/template.html`, with matching dark-mode values. Fonts: Schibsted Grotesk (text) and IBM Plex Mono (numbers) from Google Fonts. Maple red is reserved for prices and the main action. Must work at 400px phone width with no horizontal scroll.

`CONFIG` at the top of the script sets the brand name, the counsellor WhatsApp number (empty hides the WhatsApp button), the last-updated text and the exchange rate. Change `CONFIG` to white-label the page.

## Known data problems in the sheet (fix at the source)

See `data/issues.txt` after each parse. As of October 2026:
- UCW Bachelor of Commerce, Accounting: tuition CAD 84,760/year, probably a typo
- Royal Roads MA Global Leadership: Duration cell holds a fee
- Dalhousie MHA: website URL cell holds "CAD 1000-3,000.00"
- Royal Roads MA Environmental Education: no IELTS score listed
- QS ranks disagree for UBC (40/45) and Dalhousie (283/293); Concordia University of Edmonton shows 465, likely copied from Concordia Montreal

## Ideas not built yet

- Live data: read the Google Sheet directly (published CSV per tab, or the Sheets API) so edits show without re-running the parser
- WhatsApp number in `CONFIG`
- Per-agency white-label builds (one config file per client, one build each)
- Hosting on GitHub Pages or Netlify with a custom domain
- Simple analytics on which programs get shortlisted most
