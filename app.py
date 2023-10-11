from flask import Flask

app = Flask(__name__)


@app.route('/')
def index():
    return '<img style="position: absolute; top: 50%; left: 50%; \
        margin-top: -349px; margin-left: -453px;" src="static/img.jpg">'


if __name__ == '__main__':
    app.run()
