from flask import Flask, render_template, send_from_directory, Response
 
app = Flask(__name__)
 
 
@app.route('/')
def index():
    return render_template('index.html')
 
 
@app.route('/projects/')
def projects():
    return render_template('projects.html')
 
 
@app.route('/resume/')
def resume():
    return render_template('resume.html')
 
 
@app.route('/contact/')
def contact():
    return render_template('contact.html')
 
 
# Unlisted: not linked from anywhere on the site. Served as a raw static file
# (not render_template) so Jinja never tries to parse the dashboard's JS braces.
# Kept out of search via a response header rather than robots.txt, which would
# advertise the URL.
@app.route('/lastfm')
def lastfm():
    resp = send_from_directory(app.static_folder, 'lastfm.html')
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return resp
 
 
@app.route('/robots.txt')
def robots():
    return Response(
        "User-agent: *\nAllow: /\nSitemap: https://matthewcodey.com/sitemap.xml\n",
        mimetype="text/plain",
    )
 
 
@app.route('/sitemap.xml')
def sitemap():
    pages = ['/', '/projects/', '/resume/', '/contact/']  # /lastfm deliberately omitted
    urls = "".join(f"<url><loc>https://matthewcodey.com{p}</loc></url>" for p in pages)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           f'{urls}</urlset>')
    return Response(xml, mimetype="application/xml")
 
 
if __name__ == '__main__':
    app.run(debug=True)