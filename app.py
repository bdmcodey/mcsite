from flask import Flask, render_template, send_from_directory
 
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
@app.route('/lastfm')
def lastfm():
    return send_from_directory(app.static_folder, 'lastfm.html')
 
 
if __name__ == '__main__':
    app.run(debug=True)