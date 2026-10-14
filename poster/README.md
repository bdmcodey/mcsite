# Poster figures and numbers

The ALA Core Forum poster and its companion page (`/poster/`) share three
figures and one set of numbers, all made by `build_figures.py` from the
[Holdings Workbench](https://github.com/bdmcodey/holdings-workbench) repository.
Re-run it whenever the Workbench has a new release, and once more before the
print freeze.

| Figure | File | Made from |
|---|---|---|
| One statement, and the 853/863 it becomes | `static/poster/figures/statement.svg` | the Workbench's converter, run on a statement from its synthetic sample |
| The releases, by day | `releases-wide.svg` (poster, desktop), `releases-tall.svg` (phones) | `marc_serials/shared/about.json` |
| Silent losses, then and now | `silent-loss.svg` | "then": CORPUS-FINDINGS.md; "now": the Workbench's own `scripts/corpus_report.py` |

`numbers.json` holds every number the page shows, each with its source. The
page reads it, so a re-run updates the page's text too. The real-export numbers
(372 records, 1,057 statements, the simulated round trip) come from an export
that is not in the repository, so they are copied in the script with their
source rather than recounted.

## Running it

You need a local copy of the Workbench and a Python with it installed. On
Windows, from the folder that holds both repositories:

```bat
git clone https://github.com/bdmcodey/holdings-workbench
cd mcsite
python -m venv .venv-poster
.venv-poster\Scripts\activate
pip install -e ..\holdings-workbench
python poster\build_figures.py --workbench ..\holdings-workbench
```

On macOS or Linux, activate with `source .venv-poster/bin/activate` and use `/`
for `\`.

If the Workbench's output no longer matches what a figure says (the converter
writes something different for the sample statement, or the corpus report
changes its wording), the script stops and says why instead of drawing it.

## The printed poster

`build_poster.py` turns the page at `/poster/print/` (`templates/poster_print.html`,
`static/css/poster-print.css`) into `static/poster/poster.pdf`, the file sent to
FedEx Office. It also writes the QR code, `static/poster/figures/qr.svg`, which
points to `https://matthewcodey.com/poster?src=qr` so scans can be counted.

- Size: 36 x 48 in. portrait, plus FedEx Office's 0.125 in. bleed on every side,
  so the PDF page is 36.25 x 48.25 in. Text stays at least 0.6 in. inside the trim.
- It uses the same figures and numbers as the page; run `build_figures.py` first
  if the Workbench has changed.
- It writes the PDF only if everything fits on the sheet, and otherwise says which
  section overflows.

```bat
pip install segno playwright
playwright install chromium
python poster\build_poster.py --preview poster-preview.png
```

To see it while editing, run the site locally and open
http://127.0.0.1:5000/poster/print/ (it is 3,480 px wide; zoom out).

## Theme

The figures are themed with CSS custom properties (`--fig-*`). The values
written into each SVG are the poster's light theme; `static/css/poster.css`
sets the page's dark one. The four subfield colours in figure 1 were checked
for colour-blind separation and contrast in both themes; every mark that uses
one also carries its subfield letter.
