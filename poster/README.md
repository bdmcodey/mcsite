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

## Theme

The figures are themed with CSS custom properties (`--fig-*`). The values
written into each SVG are the poster's light theme; `static/css/poster.css`
sets the page's dark one. The four subfield colours in figure 1 were checked
for colour-blind separation and contrast in both themes; every mark that uses
one also carries its subfield letter.
