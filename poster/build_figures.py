"""
Build the poster's figures and numbers from the Holdings Workbench repository.

Every number on the poster and the /poster/ page comes from here, so that the
recount before the print freeze is one command rather than a re-reading:

    python poster/build_figures.py --workbench ../holdings-workbench

It writes, and the site reads:

    static/poster/figures/statement.svg      the 866 and the 853/863 it becomes
    static/poster/figures/releases-wide.svg  the releases, as a strip (poster, desktop)
    static/poster/figures/releases-tall.svg  the same, top to bottom (phones)
    static/poster/figures/silent-loss.svg    corpus outcomes, then and now
    poster/numbers.json                      every number, with where it came from

The Workbench repository is only read. Run this with a Python that has the
Workbench installed (``pip install -e <workbench>``), because figure 1 is drawn
from what its converter actually writes, not from a copy of it.

Nothing is drawn from a value the script cannot check: if the converter's
output, the corpus report or the release list stops matching what a figure
says, the script stops with the reason instead of drawing it.

The figures are themed by CSS custom properties (``--fig-*``). The fallbacks
written into each file are the poster's light theme; the page sets its own.
"""

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from collections import Counter
from html import escape
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = SITE_ROOT / "static" / "poster" / "figures"
NUMBERS = SITE_ROOT / "poster" / "numbers.json"

# The statement figure 1 converts. It is from the Workbench's synthetic sample
# (scripts/create_example_mrc.py: "All titles, identifiers, and location codes
# below are invented"), never from real holdings.
STATEMENT = "v. 27 no. 4-v. 31 no. 4 (April 1992-April 1996)"
EXPECTED_853 = "853 31 $8 1 $a v. $b no. $i (year) $j (month)"
EXPECTED_863 = "863 40 $8 1.1 $a 27-31 $b 4-4 $i 1992-1996 $j 04-04"

# Each token of the statement, and the subfield it ends up in. A caption goes
# to the 853 (what a level is called); a value goes to the 863 (what is held).
TOKENS = [
    ("v.", "a"), ("27", "a"), ("no.", "b"), ("4", "b"), ("-", None),
    ("v.", "a"), ("31", "a"), ("no.", "b"), ("4", "b"),
    ("(", None), ("April", "j"), ("1992", "i"), ("-", None),
    ("April", "j"), ("1996", "i"), (")", None),
]

# Milestones on the release strip: (version, short label).
MILESTONES = [
    ("0.1.0", "First working version"),
    ("0.11.0", "Workbench replaces the other two"),
    ("0.28.0", "Simulated Alma round trip"),
]

# Corpus outcomes before the working rules, from the headline table of
# CORPUS-FINDINGS.md ("at 0.6.0"). These are history and cannot be re-run here,
# so they are copied with their source. The corpus then held 112 statements
# ("held on 112 real statements"); it holds 117 now.
BASELINE = {
    "label": "1 September 2026",
    "version": "0.6.0",
    "statements": 112,
    "clean": 67, "warned": 3, "lost": 36, "none": 6,
    "source": "holdings-workbench CORPUS-FINDINGS.md, headline table, 'at 0.6.0' column",
}

# Measured on a real 372-record Alma export that is not in the repository, so
# these cannot be re-run either. Copied with their source.
REAL_EXPORT = {
    "records": 372,
    "statements": 1057,
    "unaccounted": 0,
    "alma_866s_reproduced": 48,
    "alma_866s_checked": 48,
    "round_trip": {"same": 938, "caption_only": 106, "not_converted": 11, "drift": 0},
    "round_trip_note": (
        "A simulated round trip: Alma cannot be run from the Workbench, so "
        "marc_serials/display.py imitates the 866 Alma regenerates from 853/863. "
        "The imitation reproduces all 48 866s in the export that Alma itself "
        "built from hand-entered 863s."
    ),
    "source": "holdings-workbench CORPUS-FINDINGS.md: 'Round the loop with the ILS · 0.28.0', "
              "and the 0.29.0 and 0.30.0 sections (938 / 106 / 11 / 0 drift)",
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Light theme (the poster) as fallbacks; the page overrides every --fig-* var.
# The four subfield hues were checked for colour-blind separation and contrast
# on both themes; every mark that wears one also carries its subfield letter.
STYLE = """
.fig text{font-family:var(--fig-sans,"Inter",system-ui,sans-serif);fill:var(--fig-ink,#1f1c29)}
.fig .mono{font-family:var(--fig-mono,ui-monospace,"SFMono-Regular",Menlo,Consolas,monospace)}
.fig .muted{fill:var(--fig-muted,#5d5a69)}
.fig .strong{font-weight:600}
.fig .rule{stroke:var(--fig-line,#d9d5e0);stroke-width:1;fill:none}
.fig .leader{stroke:var(--fig-muted,#5d5a69);stroke-width:1;fill:none}
.fig .band{fill:var(--fig-band,#efeaf7)}
.fig .chip{fill:none;stroke:var(--fig-line,#d9d5e0);stroke-width:1}
.fig .sf-a-stroke{stroke:var(--fig-sf-a,#6f55c0);stroke-width:2.5}
.fig .sf-b-stroke{stroke:var(--fig-sf-b,#d9592a);stroke-width:2.5}
.fig .sf-i-stroke{stroke:var(--fig-sf-i,#138a60);stroke-width:2.5}
.fig .sf-j-stroke{stroke:var(--fig-sf-j,#b07a00);stroke-width:2.5}
.fig .dot{fill:var(--fig-dot,#a08fd0)}
.fig .dot-key{fill:var(--fig-accent,#6f55c0);stroke:var(--fig-surface,#faf8f5);stroke-width:2}
.fig .hit{fill:transparent}
.fig .hit:hover{fill:var(--fig-line,#d9d5e0);fill-opacity:.5}
.fig .seg-clean{fill:var(--fig-grey-1,#8e8a99)}
.fig .seg-warned{fill:var(--fig-accent-soft,#c4b6ea)}
.fig .seg-lost{fill:var(--fig-accent,#6f55c0)}
.fig .seg-none{fill:var(--fig-grey-2,#d3d0db)}
.fig .on-accent{fill:var(--fig-on-accent,#fff)}
.fig .sf-a{fill:var(--fig-sf-a,#6f55c0)}
.fig .sf-b{fill:var(--fig-sf-b,#d9592a)}
.fig .sf-i{fill:var(--fig-sf-i,#138a60)}
.fig .sf-j{fill:var(--fig-sf-j,#b07a00)}
.fig .arrow{stroke:var(--fig-muted,#5d5a69);stroke-width:1.5;fill:none}
""".strip()


class Stop(Exception):
    """A number or an output no longer matches what a figure would say."""


# --------------------------------------------------------------------------
# Reading the Workbench
# --------------------------------------------------------------------------

def read_releases(wb: Path):
    about = json.loads((wb / "marc_serials" / "shared" / "about.json").read_text(encoding="utf-8"))
    releases = [(e["version"], dt.date.fromisoformat(e["date"])) for e in about["changelog"]]
    releases.sort(key=lambda r: (r[1], [int(p) for p in r[0].split(".")]))
    versions = [v for v, _ in releases]
    if len(set(versions)) != len(versions):
        raise Stop("about.json lists a version twice")
    for v, _ in MILESTONES:
        if v not in versions:
            raise Stop(f"milestone {v} is not in about.json")
    return about["version"], releases


def read_corpus(wb: Path, python: str):
    """Run the Workbench's own corpus report and read its summary."""
    out = subprocess.run(
        [python, "scripts/corpus_report.py"], cwd=wb,
        capture_output=True, text=True, check=True,
    ).stdout
    want = {
        "statements": r"statements\s+(\d+) unique",
        "clean": r"converted cleanly\s+(\d+)",
        "lost": r"converted with values lost\s+(\d+)",
        "warned": r"converted with a warning\s+(\d+)",
        "none": r"produced no fields at all\s+(\d+)",
    }
    got = {}
    for key, rx in want.items():
        m = re.search(rx, out)
        if not m:
            raise Stop(f"corpus_report.py no longer prints '{key}'; read it before trusting figure 3")
        got[key] = int(m.group(1))
    parts = got["clean"] + got["lost"] + got["warned"] + got["none"]
    if parts != got["statements"]:
        raise Stop(f"corpus outcomes sum to {parts}, not {got['statements']}")
    return got


def convert_statement():
    try:
        from marc_serials.parser import parse_866
        from marc_serials.converter import convert_holdings
    except ImportError as e:
        raise Stop(f"the Workbench is not importable ({e}); run with a Python that has it installed")
    result = convert_holdings(parse_866(STATEMENT))
    f853 = result.field_853.display() if result.field_853 else None
    f863 = [f.display() for f in result.fields_863]
    if result.warnings or f853 != EXPECTED_853 or f863 != [EXPECTED_863]:
        raise Stop(
            "the converter no longer writes what figure 1 shows:\n"
            f"  853: {f853}\n  863: {f863}\n  warnings: {result.warnings}"
        )
    return f853, f863[0]


# --------------------------------------------------------------------------
# SVG helpers
# --------------------------------------------------------------------------

def svg(width, height, fig_id, title, desc, body):
    return (
        f'<svg class="fig" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="{fig_id}-t {fig_id}-d">\n'
        f'<title id="{fig_id}-t">{escape(title)}</title>\n'
        f'<desc id="{fig_id}-d">{escape(desc)}</desc>\n'
        f"<style>{STYLE}</style>\n{body}\n</svg>\n"
    )


def text(x, y, s, cls="", size=12, anchor="start", extra=""):
    c = f' class="{cls}"' if cls else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}"{a}{c}{extra}>{escape(s)}</text>'


def bar(x, y, w, h, cls, tip, r=4, round_end=True):
    """A horizontal bar, square at its start, 4px rounded at its data end."""
    if w <= 0:
        return ""
    r = min(r, w / 2, h / 2) if round_end else 0
    d = (f"M{x:.1f},{y:.1f} H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
         f"V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} H{x:.1f} Z")
    return f'<path class="{cls}" d="{d}"><title>{escape(tip)}</title></path>'


def fmt_date(d: dt.date, year=False):
    s = f"{d.day} {MONTHS[d.month - 1]}"
    return f"{s} {d.year}" if year else s


# --------------------------------------------------------------------------
# Figure 1: one statement, and the 853/863 it becomes
# --------------------------------------------------------------------------

SUBFIELDS = [
    # code, what it holds, 853 caption, 863 value
    ("a", "volume", "v.", "27-31"),
    ("b", "issue", "no.", "4-4"),
    ("i", "year", "(year)", "1992-1996"),
    ("j", "month", "(month)", "04-04"),
]


def figure_statement(f853, f863):
    # 340 wide so that, scaled into a phone's column, the text stays readable.
    # The statement wraps where a person would break it, before the dates.
    W, CW = 340, 9.0          # width; one monospace character, forced by textLength
    brk = STATEMENT.index(" (") + 1
    lines = [STATEMENT[:brk].rstrip(), STATEMENT[brk:]]
    body = [text(16, 20, "866 · as a person typed it", "muted", 13)]

    # The statement, token by token, each underlined in its subfield's colour.
    y0, lh, pos = 54, 50, 0
    for tok, sf in TOKENS:
        start = STATEMENT.index(tok, pos)
        pos = start + len(tok)
        line, col = (0, start) if start < brk else (1, start - brk)
        x = (W - len(lines[line]) * CW) / 2 + col * CW
        y = y0 + line * lh
        w = len(tok) * CW
        body.append(text(x, y, tok, "mono", 15,
                         extra=f' textLength="{w:.1f}" lengthAdjust="spacingAndGlyphs"'))
        if sf:
            body.append(f'<rect x="{x:.1f}" y="{y + 6}" width="{w:.1f}" height="3.5" rx="1.75" class="sf-{sf}"/>')
            body.append(text(x + w / 2, y + 22, sf, "muted", 11.5, "middle"))
    y = y0 + lh

    # Arrow down to the fields.
    body.append(f'<path class="arrow" d="M{W / 2},{y + 32} V{y + 54} M{W / 2 - 5},{y + 48} L{W / 2},{y + 54} L{W / 2 + 5},{y + 48}"/>')

    # The table: one row per subfield. The 853 says what a level is called,
    # the 863 says what is held at it.
    ty = y + 84
    cols = [16, 132, 222]
    for cx, h in zip(cols, ["subfield", "853 caption", "863 held"]):
        body.append(text(cx, ty, h, "muted", 12.5))
    body.append(f'<line class="rule" x1="16" x2="{W - 16}" y1="{ty + 9}" y2="{ty + 9}"/>')
    for n, (code, meaning, cap, val) in enumerate(SUBFIELDS):
        ry = ty + 34 + n * 28
        body.append(f'<rect x="16" y="{ry - 12}" width="13" height="13" rx="3" class="sf-{code}"/>')
        body.append(text(36, ry, f"${code}", "mono strong", 14))
        body.append(text(62, ry, meaning, "muted", 13))
        body.append(text(cols[1], ry, cap, "mono", 14))
        body.append(text(cols[2], ry, val, "mono", 14))
    H = ty + 34 + (len(SUBFIELDS) - 1) * 28 + 14

    return svg(W, H, "fig-statement",
               "One 866 statement and the 853/863 it becomes",
               f"The free-text statement \u201c{STATEMENT}\u201d converts to two fields. "
               f"The 853 names the levels: $a v., $b no., $i year, $j month. "
               f"The 863 records the holdings: $a 27-31, $b 4-4, $i 1992-1996, $j 04-04. "
               f"In full: {f853}; {f863}.",
               "\n".join(body))


# --------------------------------------------------------------------------
# Figure 2: the releases
# --------------------------------------------------------------------------

def _release_layout(releases):
    by_day = {}
    for v, d in releases:
        by_day.setdefault(d, []).append(v)
    start = releases[0][1] - dt.timedelta(days=4)
    end = releases[-1][1] + dt.timedelta(days=4)
    return by_day, start, end


def _month_starts(start, end):
    m = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    while m <= end:
        yield m
        m = (m.replace(day=28) + dt.timedelta(days=4)).replace(day=1)


def _hit_title(d, versions):
    n = len(versions)
    span = versions[0] if n == 1 else f"{versions[0]} to {versions[-1]}"
    return f"{fmt_date(d, True)}: {n} release{'s' if n > 1 else ''} ({span})"


def figure_releases_wide(releases, sept):
    by_day, start, end = _release_layout(releases)
    days = (end - start).days + 1
    L, R, W = 24, 24, 960
    step = (W - L - R) / days
    base, dy, r = 250, 10.5, 4
    x = lambda d: L + ((d - start).days + 0.5) * step
    body = []

    # September, where most of the work happened.
    s0 = dt.date(start.year, 9, 1)
    bx = L + (s0 - start).days * step
    body.append(f'<rect class="band" x="{bx:.1f}" y="40" width="{30 * step:.1f}" height="{base - 40 + 6}" rx="4"/>')
    body.append(text(bx + 10, 58, f"{sept} releases in September", "strong", 13))

    body.append(f'<line class="rule" x1="{L}" x2="{W - R}" y1="{base + 6}" y2="{base + 6}"/>')
    body.append(text(L, base + 26, MONTHS[start.month - 1], "muted", 12))
    for m in _month_starts(start, end):
        mx = L + (m - start).days * step
        body.append(f'<line class="rule" x1="{mx:.1f}" x2="{mx:.1f}" y1="{base + 6}" y2="{base + 12}"/>')
        body.append(text(mx + 4, base + 26, MONTHS[m.month - 1], "muted", 12))

    key = {v for v, _ in MILESTONES} | {releases[-1][0]}
    for d, versions in sorted(by_day.items()):
        cx = x(d)
        for k, v in enumerate(versions):
            cls = "dot-key" if v in key else "dot"
            body.append(f'<circle class="{cls}" cx="{cx:.1f}" cy="{base - k * dy:.1f}" r="{r + (1 if v in key else 0)}"/>')
        top = base - (len(versions) - 1) * dy - r - 3
        body.append(f'<rect class="hit" x="{cx - step / 2:.1f}" y="{top:.1f}" width="{step:.1f}" height="{base + r + 3 - top:.1f}">'
                    f"<title>{escape(_hit_title(d, versions))}</title></rect>")

    # Milestone labels, staggered so they never collide.
    dates = dict(releases)
    tops = {v: base - (len(vs) - 1) * dy for vs in by_day.values() for v in vs}
    notes = [(v, lbl) for v, lbl in MILESTONES] + [(releases[-1][0], f"{releases[-1][0]}, release {len(releases)}")]
    place = {  # version -> (label y, anchor)
        notes[0][0]: (150, "start"),
        notes[1][0]: (96, "end"),
        notes[2][0]: (24, "start"),
        notes[3][0]: (128, "end"),
    }
    for v, lbl in notes:
        d = dates[v]
        ly, anchor = place[v]
        cx, cy = x(d), tops[v]
        body.append(f'<line class="leader" x1="{cx:.1f}" x2="{cx:.1f}" y1="{ly - 12}" y2="{cy - r - 4:.1f}"/>')
        tx = cx + (5 if anchor == "start" else -5)
        body.append(text(tx, ly, fmt_date(d), "strong", 12, anchor))
        body.append(text(tx, ly + 15, lbl, "muted", 12, anchor))
    return svg(W, base + 34, "fig-releases-wide", *_releases_text(releases, sept), "\n".join(body))


def figure_releases_tall(releases, sept):
    by_day, start, end = _release_layout(releases)
    days = (end - start).days + 1
    W, T, step, dx, r = 372, 16, 9, 9, 3.6
    X0 = 64
    y = lambda d: T + ((d - start).days + 0.5) * step
    body = []

    s0 = dt.date(start.year, 9, 1)
    by0 = T + (s0 - start).days * step
    body.append(f'<rect class="band" x="{X0 - 10}" y="{by0:.1f}" width="{W - X0 + 4}" height="{30 * step:.1f}" rx="4"/>')
    body.append(text(W - 10, by0 + 18, f"{sept} in September", "strong", 12, "end"))

    body.append(f'<line class="rule" x1="{X0 - 10}" x2="{X0 - 10}" y1="{T}" y2="{T + days * step}"/>')
    body.append(text(X0 - 20, T + 12, MONTHS[start.month - 1], "muted", 12, "end"))
    for m in _month_starts(start, end):
        my = T + (m - start).days * step
        body.append(f'<line class="rule" x1="{X0 - 16}" x2="{X0 - 10}" y1="{my:.1f}" y2="{my:.1f}"/>')
        body.append(text(X0 - 20, my + 12, MONTHS[m.month - 1], "muted", 12, "end"))

    key = {v for v, _ in MILESTONES} | {releases[-1][0]}
    row_end = {}
    for d, versions in sorted(by_day.items()):
        cy = y(d)
        for k, v in enumerate(versions):
            row_end[v] = len(versions) - 1
            cls = "dot-key" if v in key else "dot"
            body.append(f'<circle class="{cls}" cx="{X0 + k * dx:.1f}" cy="{cy:.1f}" r="{r + (1 if v in key else 0)}"/>')
        right = X0 + (len(versions) - 1) * dx + r + 3
        body.append(f'<rect class="hit" x="{X0 - r - 3:.1f}" y="{cy - step / 2:.1f}" width="{right - X0 + r + 3:.1f}" height="{step}">'
                    f"<title>{escape(_hit_title(d, versions))}</title></rect>")

    dates = dict(releases)
    notes = [(v, lbl) for v, lbl in MILESTONES] + [(releases[-1][0], f"{releases[-1][0]}, release {len(releases)}")]
    LX = X0 + 10 * dx + 10
    for v, lbl in notes:
        d = dates[v]
        cy = y(d)
        cx = X0 + row_end[v] * dx + r + 5
        body.append(f'<line class="leader" x1="{cx:.1f}" x2="{LX - 4}" y1="{cy:.1f}" y2="{cy:.1f}"/>')
        body.append(text(LX, cy - 2, fmt_date(d), "strong", 12))
        body.append(text(LX, cy + 13, lbl, "muted", 11.5))
    H = T + days * step + 12
    return svg(W, H, "fig-releases-tall", *_releases_text(releases, sept), "\n".join(body))


def _releases_text(releases, sept):
    first, last = releases[0], releases[-1]
    dates = dict(releases)
    title = f"{len(releases)} releases, {fmt_date(first[1])} to {fmt_date(last[1], True)}"
    desc = (f"Each dot is one released version of the Workbench, stacked by day. "
            f"{sept} of the {len(releases)} came in September. "
            + " ".join(f"{fmt_date(dates[v])}: {lbl} ({v})." for v, lbl in MILESTONES)
            + f" The latest is {last[0]}, on {fmt_date(last[1])}.")
    return title, desc


# --------------------------------------------------------------------------
# Figure 3: silent losses, then and now
# --------------------------------------------------------------------------

OUTCOMES = [
    ("clean", "seg-clean", "converted cleanly"),
    ("warned", "seg-warned", "converted, said what it left out"),
    ("lost", "seg-lost", "converted, losing values silently"),
    ("none", "seg-none", "converted nothing (866 kept)"),
]


def figure_silent_loss(before, now):
    W, L, R = 340, 16, 16
    BW, BH, gap = W - L - R, 28, 2
    names = {k: label for k, _, label in OUTCOMES}
    body = []

    # Legend first, one outcome to a line.
    for n, (_, cls, label) in enumerate(OUTCOMES):
        ly = 18 + n * 22
        body.append(f'<rect x="{L}" y="{ly - 11}" width="13" height="13" rx="3" class="{cls}"/>')
        body.append(text(L + 21, ly, label, "", 13))

    y = 18 + len(OUTCOMES) * 22 + 26
    for data in (before, now):
        n = data["statements"]
        body.append(text(L, y, f"{data['label']} · {data['version']}", "strong", 13.5))
        body.append(text(W - R, y, f"{n} statements", "muted", 12.5, "end"))
        by = y + 10
        segs = [(k, cls, data[k]) for k, cls, _ in OUTCOMES if data[k] > 0]
        usable = BW - gap * (len(segs) - 1)
        x = L
        for i, (k, cls, v) in enumerate(segs):
            w = usable * v / n
            body.append(bar(x, by, w, BH, cls, f"{names[k]}: {v} of {n}",
                            round_end=(i == len(segs) - 1)))
            label_txt = str(v)
            if w > len(label_txt) * 8.5 + 12:
                ink = "on-accent" if k == "lost" else ""
                body.append(text(x + w / 2, by + 19, label_txt, f"strong {ink}".strip(), 13, "middle"))
            if k == "lost":
                lost_x, lost_w = x, w
            x += w + gap
        # The callout: the one number this figure is about.
        lost = data["lost"]
        if lost:
            pct = round(100 * lost / n)
            cx = lost_x + lost_w / 2
            body.append(f'<line class="leader" x1="{cx:.1f}" x2="{cx:.1f}" y1="{by + BH + 2}" y2="{by + BH + 10}"/>')
            body.append(text(W - R, by + BH + 26, f"{lost} of {n} ({pct}%) lost values silently", "strong", 13.5, "end"))
        else:
            body.append(text(L, by + BH + 26, f"0 of {n} lose values silently", "strong", 13.5))
        y = by + BH + 70
    H = y - 34
    desc = (f"Outcomes for the Workbench's corpus of real 866 statements. "
            f"On {before['label']} (version {before['version']}), {before['statements']} statements: "
            f"{before['clean']} converted cleanly, {before['warned']} converted and said what they left out, "
            f"{before['lost']} lost values silently, {before['none']} converted nothing. "
            f"On {now['label']} (version {now['version']}), {now['statements']} statements: "
            f"{now['clean']} clean, {now['warned']} said what they left out, "
            f"{now['lost']} lost values silently, {now['none']} converted nothing.")
    return svg(W, H, "fig-silent-loss",
               f"Silent losses, {before['lost']} to {now['lost']}", desc, "\n".join(body))


# --------------------------------------------------------------------------
# How a statement becomes a pattern: the detector's tokens, the shape, the
# named slots and the meanings it offers, as the Workbench produces them.
# --------------------------------------------------------------------------

# The same statement as figure 1, and a second from the same synthetic sample
# whose first number carries no caption: the case a cataloguer decides.
UNCAPTIONED = "39 no 1 (Spring 1995)"
EXPECTED_SHAPE = "VOL ISS — VOL ISS(CHRON YEAR-CHRON YEAR)"
EXPECTED_UNCAPTIONED = {
    "shape": "# ISS(CHRON YEAR)",
    "853_parser": "853 31 $8 1 $a (*) $b no. $i (year) $j (season)",
    "853_confirmed": "853 31 $8 1 $a v. $b no. $i (year) $j (season)",
}

# Short labels for the detector's token kinds, as the Patterns screen writes
# them in a group's heading.
TOKEN_LABEL = {"VOL_CAP": "VOL", "ISS_CAP": "ISS", "PT_CAP": "PT", "NUMBER": "#",
               "YEAR": "YEAR", "CHRON": "CHRON", "SEP_HYPHEN": "-",
               "PAREN_OPEN": "", "PAREN_CLOSE": ""}
SUBFIELD = "abcdef"
CHRON_SUBFIELD = {"year": "i", "month": "j"}
VALUE_KINDS = {"NUMBER", "YEAR", "CHRON"}
CAPTION_KINDS = {"VOL_CAP", "ISS_CAP", "PT_CAP"}
COLOURED = set("abij")


def marc_segments(field):
    """A field as display text, cut so each coloured subfield can be marked."""
    head, _, rest = field.partition(" $")
    segments = [{"text": head + " ", "sf": None}]
    for part in ("$" + rest).split(" $"):
        part = part if part.startswith("$") else "$" + part
        code = part[1]
        segments.append({"text": part, "sf": code if code in COLOURED else None})
        segments.append({"text": " ", "sf": None})
    segments.pop()
    if "".join(seg["text"] for seg in segments) != field:
        raise Stop(f"could not mark the subfields of {field!r}")
    return segments


def read_pattern():
    """Run the Workbench's detector on the statements, and check what it says."""
    import re as _re
    from dataclasses import replace
    from marc_serials.detector import (detect_patterns, tokenize, _strip_spaces,
                                       _find_range_sep)
    from marc_serials.bridge import infer_roles, apply_patterns
    from marc_serials.library import ConfirmedPattern
    from marc_serials.parser import parse_866
    from marc_serials.converter import convert_holdings
    from marc_serials.webapp import _what_confirming_decides

    toks = _strip_spaces(tokenize(STATEMENT))
    sep = _find_range_sep(toks)
    tokens = []
    for i, t in enumerate(toks):
        if t.kind not in TOKEN_LABEL:
            raise Stop(f"the detector now reads {t.raw!r} as {t.kind}; update TOKEN_LABEL")
        tokens.append({"raw": t.raw, "label": "\u2014" if i == sep else TOKEN_LABEL[t.kind]})

    group = detect_patterns([STATEMENT])[0]
    if group.human_label != EXPECTED_SHAPE:
        raise Stop(f"the detector now heads this group {group.human_label!r}")
    match = _re.fullmatch(group.regex, STATEMENT, _re.IGNORECASE)
    if not match:
        raise Stop("the generated expression no longer matches its own statement")
    slots = []
    for r in infer_roles(group.named_groups):
        d = r.to_dict()
        if r.kind == "enum":
            meaning = f"Enumeration, level {r.level + 1} (${SUBFIELD[r.level]}), caption {r.caption}"
        else:
            meaning = d["kind_label"]
        sf = SUBFIELD[r.level] if r.kind == "enum" else CHRON_SUBFIELD.get(r.kind)
        if sf is None:
            raise Stop(f"no subfield colour for the slot {r.group} ({r.kind})")
        slots.append({"slot": r.group, "value": match.group(r.group),
                      "meaning": meaning, "boundary": r.boundary,
                      "suggested": r.suggested, "sf": sf})

    # Each piece of the statement takes its subfield's colour: a value from
    # the slot that captures it, a caption from the value it names. These must
    # agree with figure 1's TOKENS, so the colours mean the same everywhere.
    values = iter(slots)
    for t, tok in zip(toks, tokens):
        if t.kind in VALUE_KINDS:
            slot = next(values)
            if slot["value"] != t.raw:
                raise Stop(f"piece {t.raw!r} does not line up with slot {slot['slot']}")
            tok["sf"] = slot["sf"]
    for i, (t, tok) in enumerate(zip(toks, tokens)):
        if t.kind in CAPTION_KINDS:
            tok["sf"] = next(tokens[j]["sf"] for j in range(i + 1, len(toks))
                             if toks[j].kind in VALUE_KINDS)
    if [(tok["raw"], tok.get("sf")) for tok in tokens] != list(TOKENS):
        raise Stop("the detector's pieces and figure 1's colours disagree")

    # The rule, simplified for reading: the statement with each value replaced
    # by the name of the slot that captures it.
    segments, pos, values = [], 0, iter(slots)
    for t, tok in zip(toks, tokens):
        start = STATEMENT.index(t.raw, pos)
        segments.append({"text": STATEMENT[pos:start], "sf": None})
        text_ = "<" + next(values)["slot"] + ">" if t.kind in VALUE_KINDS else t.raw
        segments.append({"text": text_, "sf": tok.get("sf")})
        pos = start + len(t.raw)
    segments.append({"text": STATEMENT[pos:], "sf": None})
    segments = [seg for seg in segments if seg["text"]]
    template = "".join(seg["text"] for seg in segments)
    if _re.sub(r"<[a-z_]+>", "", template) != _re.sub(
            r"\d+|April", "", STATEMENT):
        raise Stop(f"the simplified rule does not line up with the statement: {template}")

    # The uncaptioned statement: what the parser writes alone, and with the
    # caption the card suggests confirmed.
    ug = detect_patterns([UNCAPTIONED])[0]
    alone = convert_holdings(parse_866(UNCAPTIONED)).field_853.display()
    roles = [replace(r, suggested=False) for r in infer_roles(ug.named_groups)]
    suggested = [r for r in infer_roles(ug.named_groups) if r.suggested]
    confirmed_pattern = ConfirmedPattern(id="p", label=ug.human_label, regex=ug.regex, roles=roles)
    confirmed = convert_holdings(apply_patterns(UNCAPTIONED, [confirmed_pattern])[0]).field_853.display()
    got = {"shape": ug.human_label, "853_parser": alone, "853_confirmed": confirmed}
    if got != EXPECTED_UNCAPTIONED or len(suggested) != 1 or suggested[0].caption != "v.":
        raise Stop(f"the uncaptioned example no longer behaves as the page says: {got}")

    return {
        "statement": STATEMENT,
        "tokens": tokens,
        "shape": group.human_label,
        "regex_length": len(group.regex),
        "template": template,
        "template_segments": segments,
        "slots": slots,
        "decides": _what_confirming_decides([STATEMENT]),
        "uncaptioned": dict(got, statement=UNCAPTIONED,
                            segments_853_parser=marc_segments(alone),
                            segments_853_confirmed=marc_segments(confirmed),
                            decides=_what_confirming_decides([UNCAPTIONED]),
                            suggested_slot=suggested[0].group,
                            suggested_value=_re.fullmatch(ug.regex, UNCAPTIONED, _re.IGNORECASE)
                            .group(suggested[0].group)),
        "source": "holdings-workbench marc_serials.detector and marc_serials.bridge, run by this script",
    }


def figure_tokens(pattern):
    """The statement cut into labelled pieces, and the shape those labels make."""
    W, CW, LW = 340, 9.0, 6.4          # width; a token character; a label character
    PAD, GAP, CH = 5, 6, 26            # chip padding, gap between chips, chip height
    brk = STATEMENT.index(" (") + 1
    toks = pattern["tokens"]
    # Which line each piece goes on: the numbering, then the dates.
    rows, pos = [[], []], 0
    for tok in toks:
        start = STATEMENT.index(tok["raw"], pos)
        pos = start + len(tok["raw"])
        rows[0 if start < brk else 1].append(tok)
    body = [text(16, 20, "1 · Cut into labelled pieces", "muted", 13)]
    y = 40
    for row in rows:
        widths = [max(len(t["raw"]) * CW, len(t["label"]) * LW) + 2 * PAD for t in row]
        x = (W - sum(widths) - GAP * (len(row) - 1)) / 2
        for t, w in zip(row, widths):
            chip = f"chip sf-{t['sf']}-stroke" if t.get("sf") else "chip"
            body.append(f'<rect class="{chip}" x="{x:.1f}" y="{y}" width="{w:.1f}" height="{CH}" rx="5"/>')
            body.append(text(x + w / 2, y + 18, t["raw"], "mono", 15, "middle"))
            if t["label"]:
                strong = t["label"] == "\u2014"
                body.append(text(x + w / 2, y + CH + 15, t["label"],
                                 "mono strong" if strong else "mono muted", 10.5, "middle"))
            x += w + GAP
        y += CH + 34
    y += 18
    body.append(text(16, y, "2 · Its shape", "muted", 13))
    body.append(text(W / 2, y + 28, pattern["shape"], "mono strong", 12, "middle"))
    H = y + 42
    desc = ("The statement " + STATEMENT + " is cut into pieces, each labelled: "
            + ", ".join(f"{t['raw']} {t['label'] or '(punctuation)'}" for t in toks)
            + f". In order, the labels make its shape: {pattern['shape']}.")
    return svg(W, H, "fig-tokens", "How the detector reads a statement", desc, "\n".join(body))


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--workbench", required=True, type=Path,
                    help="path to a local clone of bdmcodey/holdings-workbench")
    args = ap.parse_args()
    wb = args.workbench.resolve()
    if not (wb / "marc_serials" / "shared" / "about.json").exists():
        sys.exit(f"{wb} does not look like the holdings-workbench repository")
    sys.path.insert(0, str(wb))

    try:
        version, releases = read_releases(wb)
        corpus = read_corpus(wb, sys.executable)
        f853, f863 = convert_statement()
        pattern = read_pattern()
    except (Stop, subprocess.CalledProcessError) as e:
        sys.exit(f"Stopped: {e}")

    latest_v, latest_d = releases[-1]
    if latest_v != version:
        sys.exit(f"Stopped: about.json says version {version}, but its newest changelog entry is {latest_v}")
    months = Counter(d.strftime("%Y-%m") for _, d in releases)
    sept = months.get(f"{latest_d.year}-09", 0)
    now = dict(corpus, label=f"{latest_d.day} {latest_d.strftime('%B')} {latest_d.year}", version=latest_v)
    dates = dict(releases)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    (FIG_DIR / "statement.svg").write_text(figure_statement(f853, f863), encoding="utf-8")
    (FIG_DIR / "releases-wide.svg").write_text(figure_releases_wide(releases, sept), encoding="utf-8")
    (FIG_DIR / "releases-tall.svg").write_text(figure_releases_tall(releases, sept), encoding="utf-8")
    (FIG_DIR / "silent-loss.svg").write_text(figure_silent_loss(BASELINE, now), encoding="utf-8")
    (FIG_DIR / "tokens.svg").write_text(figure_tokens(pattern), encoding="utf-8")

    numbers = {
        "_comment": "Written by poster/build_figures.py. Do not edit by hand; re-run the script.",
        "as_of_version": latest_v,
        "releases": {
            "count": len(releases),
            "first": {"version": releases[0][0], "date": releases[0][1].isoformat()},
            "latest": {"version": latest_v, "date": latest_d.isoformat()},
            "by_month": dict(sorted(months.items())),
            "milestones": [{"version": v, "date": dates[v].isoformat(), "label": lbl} for v, lbl in MILESTONES],
            "source": "holdings-workbench marc_serials/shared/about.json, changelog",
        },
        "corpus": {
            "before": BASELINE,
            "now": dict(now, source="holdings-workbench scripts/corpus_report.py, run by this script"),
        },
        "statement": {
            "866": STATEMENT, "853": f853, "863": f863,
            "segments_853": marc_segments(f853), "segments_863": marc_segments(f863),
            "source": "holdings-workbench data/example_holdings.mrc (synthetic), converted by marc_serials.converter",
        },
        "pattern": pattern,
        "real_export": REAL_EXPORT,
    }
    NUMBERS.write_text(json.dumps(numbers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Workbench {latest_v} ({latest_d}): {len(releases)} releases, {sept} in September; "
          f"corpus {corpus['statements']} statements, {corpus['lost']} silent losses.")
    print(f"Wrote 5 figures to {FIG_DIR.relative_to(SITE_ROOT)} and {NUMBERS.relative_to(SITE_ROOT)}.")


if __name__ == "__main__":
    main()
