"""
Build the downloadable CV, static/cv/Matthew_Codey_CV.pdf.

    pip install reportlab
    python cv/build_cv.py

Edit the CONTENT below and re-run. The layout reproduces the original CV
(letter size, Helvetica, the magenta accent) from measurements of that file,
and every paragraph is re-wrapped, so wording can change freely. The
resume page (templates/resume.html) carries the same text; keep them in step.
"""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

OUT = Path(__file__).resolve().parent.parent / "static" / "cv" / "Matthew_Codey_CV.pdf"

# ── Content ──────────────────────────────────────────────────────────────────
# A paragraph is a list of runs: (text, style), style being "r" regular,
# "b" bold or "i" italic.

NAME = "Matthew Codey"
SUBTITLE = "MLIS  ·  Academic Libraries Paraprofessional"
CONTACT = ("matthew.codey@gmail.com  ·  github.com/bdmcodey  ·  "
           "matthewcodey.com  ·  Los Angeles, CA")

SUMMARY = [("Academic libraries paraprofessional, with an MLIS and nearly twenty years in academic libraries, "
            "pairing hands-on library-systems expertise with a user-centered, "
            "equity-minded approach to reference and instruction. Ex Libris Alma "
            "Certified Administrator experienced in large-scale metadata management, "
            "discovery-service enhancement, and staff supervision, with a record of "
            "collaborative service and governance leadership.", "r")]

JOBS = [
    {
        "title": "Senior Library Assistant, Wilson Dental Library, USC",
        "dates": "Oct 2014 – Present",
        "place": "Los Angeles, CA",
        "bullets": [
            "Coordinate the full serials lifecycle: ordering, receiving, processing, "
            "claims, and vendor and subscription-agent correspondence.",
            "Provide in-person and virtual reference (LibChat, LibAnswers), guiding "
            "students and faculty through research strategies, database navigation, "
            "and access to physical and electronic resources.",
            "Oversee quality control of the ILS (Alma): maintain the bibliographic "
            "database and correct records; audit e-resources for link integrity and access.",
            "Recruit, train, supervise, and schedule student workers; manage timecards "
            "and performance.",
            "Designed and delivered an accessibility workshop as part of the ABC "
            "Committee; compile circulation and collection statistics and reports.",
            "Service & leadership: Staff Professional Development Committee, Staff "
            "Council, ABC Committee, and Chair of the Culture Committee.",
        ],
    },
    {
        "title": "Library Assistant III, Geisel Library, UC San Diego",
        "dates": "Aug 2007 – Sep 2014",
        "place": "La Jolla, CA",
        "bullets": [
            "Staffed the main circulation desk and managed processing of returned "
            "materials within Access Services.",
            "Hired, trained, and supervised 30–40 student assistants.",
            "Led the searching unit: resolved lost and missing items and claims "
            "returns, coordinating with billing on fines and fees.",
            "Partnered with the Metadata Department on records-maintenance projects.",
        ],
    },
]

EDUCATION = [
    ([("Master of Library & Information Science", "b"),
      (", San José State University, 2018", "r")],
     "Concentration: Web Programming & Information Architecture"),
    ([("B.S., Cognitive Science", "b"),
      (", University of California San Diego, 2007", "r")],
     "Specialization: Human-Computer Interaction"),
]

SKILLS = [
    [("Library systems:", "b"),
     (" Ex Libris Alma (Certified Administrator) & Primo: normalization jobs, batch "
      "processing, Analytics dashboards & reporting; EZproxy administration.", "r")],
    [("Metadata & cataloging:", "b"),
     (" MARC, BIBFRAME, RDA, and current cataloging standards.", "r")],
    [("Programming & web:", "b"),
     (" Python, PHP, JavaScript, SQL, HTML, CSS, Git, Visual Basic.", "r")],
    [("Reference & instruction:", "b"),
     (" Point-of-need instruction and reference (in-person, LibChat, LibAnswers); "
      "research strategies, database navigation, information literacy.", "r")],
]

PRESENTATIONS = [
    [("Thompson, A. M., Codey, M., Lyle, C., & Davis, R. O. (2017). ", "r"),
     ("Do We Dare Discard? Retention of Print Serials in a Digital Age.", "i"),
     (" Poster session, MLA '17 Annual Meeting, Seattle, WA.", "r")],
    [("Medical Library Association (2014–Present) · Beta Phi Mu Honor Society, "
      "Omega Chapter (2019–Present) · ELUNA 2019 & 2020.", "r")],
]

# ── Layout, measured from the original file ──────────────────────────────────
# Distances are between baselines, in points from the top of the page.

PAGE_W, PAGE_H = 612, 792
LEFT, RIGHT = 60, 552
INK, MUTED, ACCENT, RULE = HexColor("#1c1d22"), HexColor("#4b4d55"), HexColor("#b0356f"), HexColor("#d9d9de")
FONT = {"r": "Helvetica", "b": "Helvetica-Bold", "i": "Helvetica-Oblique"}

BODY, BODY_LEAD, PARA_GAP = 9.2, 12.42, 13.4
BULLET, BULLET_LEAD, BULLET_GAP = 9.1, 12.5, 13.5
BULLET_WIDTH = 482          # the original lets a bullet line run to about 481.5pt
SMALL = 8.8
HEAD = 10.5
JOB_INDENT = 8.4            # the job title and dates sit in a padded table cell


def words(runs):
    """Split runs into (word, style, space_before) for wrapping. A space counts
    wherever it falls, including at the edge of a run, so "(2017). " followed
    by an italic title keeps its space."""
    out, pending = [], False
    for text, style in runs:
        for i, w in enumerate(text.split(" ")):
            if i > 0:
                pending = True
            if w:
                out.append((w, style, pending and bool(out)))
                pending = False
    return out


def wrap(runs, size, width):
    """Greedy wrap, as ReportLab's Paragraph does: a list of lines of (word, style, space)."""
    lines, line, used = [], [], 0.0
    for w, style, space in words(runs):
        gap = stringWidth(" ", FONT[style], size) if (line and space) else 0.0
        ww = stringWidth(w, FONT[style], size)
        if line and used + gap + ww > width:
            lines.append(line)
            line, used, gap = [], 0.0, 0.0
        line.append((w, style, bool(line) and space))
        used += gap + ww
    if line:
        lines.append(line)
    return lines


class Page:
    def __init__(self, path):
        self.c = Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
        self.c.setAuthor("Matthew Codey")
        self.c.setTitle("Matthew Codey · CV")
        self.y = 0.0

    def text(self, x, y, s, style, size, colour):
        self.c.setFont(FONT[style], size)
        self.c.setFillColor(colour)
        self.c.drawString(x, PAGE_H - y, s)

    def line_of_words(self, x, y, line, size, colour):
        for w, style, space in line:
            if space:
                x += stringWidth(" ", FONT[style], size)
            self.text(x, y, w, style, size, colour)
            x += stringWidth(w, FONT[style], size)

    def paragraph(self, x, y, runs, size, lead, width, colour=INK):
        lines = wrap(runs, size, width)
        for i, line in enumerate(lines):
            self.line_of_words(x, y + i * lead, line, size, colour)
        return y + (len(lines) - 1) * lead          # baseline of the last line

    def heading(self, y, title):
        self.text(LEFT, y, title, "b", HEAD, ACCENT)
        self.c.setStrokeColor(RULE)
        self.c.setLineWidth(0.6)
        self.c.line(LEFT, PAGE_H - (y + 5.0), RIGHT, PAGE_H - (y + 5.0))


def build(path=OUT):
    p = Page(path)
    y = 67.75
    p.text(LEFT, y, NAME, "b", 22, INK)
    y += 14.34
    p.text(LEFT, y, SUBTITLE, "r", HEAD, ACCENT)
    y += 12.27
    p.text(LEFT, y, CONTACT, "r", SMALL, MUTED)

    y += 26.83
    p.heading(y, "PROFESSIONAL SUMMARY")
    y = p.paragraph(LEFT, y + 19.2, SUMMARY, BODY, BODY_LEAD, RIGHT - LEFT)

    y += 21.8
    p.heading(y, "EXPERIENCE")
    y += 20.06
    for n, job in enumerate(JOBS):
        if n:
            y += 16.47
        p.text(LEFT + JOB_INDENT, y, job["title"], "b", 10, INK)
        dw = stringWidth(job["dates"], FONT["r"], SMALL)
        p.text(RIGHT - JOB_INDENT - dw, y - 1.29, job["dates"], "r", SMALL, MUTED)
        y += 11.81
        p.text(LEFT, y, job["place"], "i", SMALL, MUTED)
        y += 14.22 - BULLET_GAP
        for b in job["bullets"]:
            y += BULLET_GAP
            p.text(LEFT, y + 2.92, "•", "r", 12, ACCENT)
            y = p.paragraph(LEFT + 12, y, [(b, "r")], BULLET, BULLET_LEAD, BULLET_WIDTH)

    y += 22.0
    p.heading(y, "EDUCATION")
    y += 19.3
    for n, (line, sub) in enumerate(EDUCATION):
        if n:
            y += 17.43
        y = p.paragraph(LEFT, y, line, BODY, BODY_LEAD, RIGHT - LEFT)
        y += 12.97
        p.text(LEFT, y, sub, "i", SMALL, MUTED)

    for title, paras in (("TECHNICAL SKILLS", SKILLS), ("PRESENTATIONS & AFFILIATIONS", PRESENTATIONS)):
        y += 21.75
        p.heading(y, title)
        y += 19.25 - PARA_GAP
        for para in paras:
            y = p.paragraph(LEFT, y + PARA_GAP, para, BODY, BODY_LEAD, RIGHT - LEFT)

    p.c.showPage()
    p.c.save()


if __name__ == "__main__":
    build()
    print(f"Wrote {OUT}")
