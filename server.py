from flask import Flask, session, url_for, redirect, request, abort
from flask import render_template_string, render_template
import sys
import os
import string, random
import requests
import json

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
        git_url = git_authorize_url 
        git_url += '?client_id='+GITHUB_CLIENT_ID 
        git_url += '&state=' + session['state']
        git_url += '&scope=read:org' 
        return redirect(git_url)

@app.route('/logout')
def logout():
    keys = list(session.keys())
    for key in keys:
        session.pop(key)
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
        print('json data: %s'%json.dumps(data))
        print('url: %s'%git_access_token_url)
        r = requests.post(git_access_token_url, data = data, headers={'Accept': 'application/json'})
        print('Here is the text: %s'%r.text)
        session['access_token'] = r.json()['access_token']
        return redirect(url_for('home'))

@app.route('/control_room')
def home():
    data = {}
    data['orgs'] = [{'login':'foo'}, {'login': 'bar'}]
    data['url_logout'] = url_for('logout')
    return render_template('home.html', data = data)   

@app.route('/user')
def user():
    r = requests.get(r'https://api.github.com/user', headers={
        'Content-Type': 'application/json', 
        'Authorization': 'token %s'%session['access_token']
        })
    return r.json()['login']

@app.route('/orgs')
def orgs():
    r = requests.get(r'https://api.github.com/user/orgs', headers={
        'Content-Type': 'application/json', 
        'Authorization': 'token %s'%session['access_token']
        })
    return str([org['login'] for org in r.json()])

    
if __name__ == '__main__':
    app.run(debug=True)