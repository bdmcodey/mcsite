# matthewcodey.com

My personal website — a small Flask application I built, version-control here, and
self-host on my own Linux server. It doubles as an honest demonstration of the
web-development and systems side of my work as an academic librarian.

**Live:** https://matthewcodey.com

## About

A multi-page portfolio: a landing page, selected projects and systems work, a
résumé, and a contact page. It's deliberately lightweight — no build step and no
JavaScript framework, just server-rendered templates and a single hand-written
stylesheet.

## Built with

- **Python · Flask 3** — routing and server-rendered templates (Jinja2)
- **Gunicorn** — WSGI server in production
- **nginx** — reverse proxy and TLS termination
- **Vanilla HTML/CSS** — no framework; Fraunces + Inter typefaces, dark theme, a
  single `main.css` themed with CSS custom properties
- **Git + a Linux VPS** — deployment by pull

## Structure

```
app.py              # Flask app — one route per page
requirements.txt    # pinned dependencies
templates/          # Jinja2 templates
  base.html         #   shared layout (nav, footer, meta / Open Graph tags)
  index.html        #   landing
  projects.html     #   projects & systems work
  resume.html       #   résumé
  contact.html      #   contact
static/
  css/main.css      # single stylesheet (theme driven by CSS variables)
  cv/               # downloadable CV (PDF)
  *.png             # favicon, apple-touch-icon, Open Graph image
```

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app run --debug
```

Then visit http://127.0.0.1:5000.

## Deployment

The production site runs on a Linux VPS: Gunicorn serves the Flask app behind
nginx, which handles TLS (Let's Encrypt) and routing, with systemd keeping the
service alive across reboots. Deploying an update is a `git pull` on the server
followed by a service restart.

## License

Code is released under the MIT License (see [LICENSE](LICENSE)). Site content, the
résumé, and images are © Matthew Codey and are not covered by that license.
