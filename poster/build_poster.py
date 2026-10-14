"""
Build the printed poster as a PDF, ready to send to FedEx Office.

    python poster/build_poster.py

It writes:

    static/poster/figures/qr.svg   the QR code, pointing to the companion page
    static/poster/poster.pdf       36 x 48 in. plus 0.125 in. bleed: 36.25 x 48.25 in.

The poster is the page at /poster/print/ (templates/poster_print.html and
static/css/poster-print.css), drawn from the same figures and numbers as
/poster/. Run poster/build_figures.py first if the Workbench has changed.

Needs: pip install segno playwright, then playwright install chromium. The PDF
is only written if everything fits on the sheet; otherwise the script says
which part overflows.

    --preview FILE   also save a small PNG of the whole poster, to look at
"""

import argparse
import os
import sys
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent.parent
QR_SVG = SITE_ROOT / "static" / "poster" / "figures" / "qr.svg"
PDF = SITE_ROOT / "static" / "poster" / "poster.pdf"

# Scans are counted in the nginx log by the ?src=qr on the request.
QR_TARGET = "https://matthewcodey.com/poster?src=qr"
INK = "#1f1c29"
WIDTH_IN, HEIGHT_IN = 36.25, 48.25


def build_qr():
    import segno
    qr = segno.make(QR_TARGET, error="m", micro=False)
    path = qr.svg_inline(scale=1, border=0, dark=INK)
    path = path[path.index("<path"):path.rindex("</svg>")]
    size, quiet = qr.symbol_size(scale=1, border=0)[0], 4
    QR_SVG.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-quiet} {-quiet} {size + 2 * quiet} {size + 2 * quiet}" '
        f'role="img" aria-label="QR code for {QR_TARGET}" shape-rendering="crispEdges">'
        f'<rect x="{-quiet}" y="{-quiet}" width="{size + 2 * quiet}" height="{size + 2 * quiet}" fill="#ffffff"/>'
        f"{path}</svg>\n",
        encoding="utf-8",
    )


def build_pdf(preview=None):
    sys.path.insert(0, str(SITE_ROOT))
    from app import app
    from playwright.sync_api import sync_playwright

    client = app.test_client()
    origin = "http://poster.local"

    def serve(route):
        """Answer the poster's own requests from the Flask app; let fonts through."""
        url = route.request.url
        if not url.startswith(origin):
            return route.continue_()
        resp = client.get(url[len(origin):])
        route.fulfill(status=resp.status_code, body=resp.data,
                      headers={"Content-Type": resp.headers.get("Content-Type", "text/plain")})

    with sync_playwright() as p:
        # POSTER_CHROMIUM names a browser to use when Playwright's own is missing.
        browser = p.chromium.launch(executable_path=os.environ.get("POSTER_CHROMIUM") or None)
        page = browser.new_page(viewport={"width": int(WIDTH_IN * 96), "height": int(HEIGHT_IN * 96)})
        page.route("**/*", serve)
        page.goto(f"{origin}/poster/print/", wait_until="networkidle")
        page.evaluate("document.fonts.ready")

        # Everything must fit inside the safe area: nothing may spill past it.
        overflow = page.evaluate("""() => {
            const safe = document.querySelector('.safe').getBoundingClientRect();
            const out = [];
            for (const el of document.querySelectorAll('.safe *')) {
                const r = el.getBoundingClientRect();
                if (r.width && (r.bottom > safe.bottom + 1 || r.right > safe.right + 1))
                    out.push((el.querySelector('h3,h2')?.textContent || el.tagName).trim().slice(0, 60)
                             + ` (${Math.round(r.bottom - safe.bottom)}px past the bottom)`);
            }
            return [...new Set(out)].slice(0, 8);
        }""")
        fonts = page.evaluate("[...document.fonts].filter(f => f.status === 'loaded').map(f => f.family)")
        if not {"Fraunces", "Inter", "IBM Plex Mono"} <= {f.strip('"') for f in fonts}:
            browser.close()
            sys.exit("Stopped: the Fraunces, Inter and IBM Plex Mono fonts did not load (is the network available?)")
        if preview:   # saved even when it overflows, so the problem can be seen
            page.screenshot(path=preview, full_page=True, scale="css")
        if overflow:
            browser.close()
            sys.exit("Stopped: the poster overflows its safe area:\n  " + "\n  ".join(overflow))

        page.pdf(path=str(PDF), width=f"{WIDTH_IN}in", height=f"{HEIGHT_IN}in",
                 print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                 prefer_css_page_size=True)
        browser.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--preview", help="also save a PNG of the whole poster here")
    args = ap.parse_args()
    build_qr()
    build_pdf(args.preview)
    print(f"Wrote {QR_SVG.relative_to(SITE_ROOT)} and {PDF.relative_to(SITE_ROOT)} "
          f"({WIDTH_IN} x {HEIGHT_IN} in.).")


if __name__ == "__main__":
    main()
