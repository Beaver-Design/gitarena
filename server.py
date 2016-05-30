from flask import Flask, session, url_for, redirect, flash, request, abort
from flask import render_template_string
import sys
import os
import string, random
import requests

GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG')

git_authorize_url = r'https://github.com/login/oauth/authorize'
git_access_token_url = r'https://github.com/login/oauth/access_token'

app = Flask(__name__)
app.config.from_object(__name__)

def random_string(size=10, chars=string.ascii_letters):
    return ''.join(random.choice(chars) for _ in range(size))

###############################################################################
@app.route('/')
def index():
    if session.get('state', False):
        t = '<p>Hello, you are logged in, but we have not asked GitHub who you are.</p>'\
            '<a href="{{ url_for("logout") }}">Logout</a>'\
            '<p>Below are the session variables.'
        for key in session:
            t = t + '<p>%s: %s</p>'%(key, session[key])
    else:
        t = 'Hello! <a href="{{ url_for("login") }}">Login</a>'

    return render_template_string(t)

@app.route('/login')
def login():
    if session.get('state', False):
        redirect('/')
    else:
        session['state'] = random_string()
        git_url = git_authorize_url + '?client_id='+GITHUB_CLIENT_ID + '&state=' + session['state']
        return redirect(git_url)

@app.route('/logout')
def logout():
    session.pop('state')
    return redirect('/')

@app.route('/github-callback')
def authorized():
    if request.args['state'] != session['state']:
        print('There is evidence a third party has intercepted your request. Restart Session!!!')
        abort(500)
    else:
        session['code'] = request.args['code']
        data = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': session['code'],
        'state': session['state']
        }
        r = requests.post(git_access_token_url, data = data)
        session['access_token'] = r.json()['access_token']
        redirect('/')

if __name__ == '__main__':
    app.run(debug=True)