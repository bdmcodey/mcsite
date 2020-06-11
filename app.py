from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '<img src="static/img.jpg">'

if __name__ == '__main__':
    app.run()