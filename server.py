import flask
import json
import os
import sys

app = flask.Flask(__name__)

@app.route('/')
def home():
    return flask.render_template('home.html')

if __name__ == '__main__':
    app.run(debug='--debug' in sys.argv)