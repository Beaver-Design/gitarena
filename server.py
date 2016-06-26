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

def gen_header(access_token):
    return {
    'Content-Type': 'application/json', 
    'Authorization': 'token %s'%access_token
    }
def logged_in(session = session):
    if session.get('logged_in', False) and session['logged_in']:
        return True
    else:
        return False

def form_git_authorize_url(base = git_authorize_url, id = GITHUB_CLIENT_ID, session = session, scope = 'admin:org'):
    url = '%s?client_id=%s&state=%s&scope=%s'%(base, id, session['state'], scope)
    return url
###############################################################################
@app.before_first_request
def set_github_access_token():
    dev_access_token = os.environ.get('GITHUB_ACCESS_TOKEN')
    dev_logged_in_status = os.environ.get('LOGGED_IN')
    print(dev_access_token)
    session['access_token'] = dev_access_token
    session['std_header'] = gen_header(session['access_token'])
    if dev_logged_in_status == "False":
        session['logged_in'] = False
    else: 
        session['logged_in'] = True

@app.route('/')
def index():
    if logged_in():
        t = '<p>Hello, you are logged in, but we have not asked GitHub who you are.</p>'\
            '<a href="{{ url_for("logout") }}">Logout</a>'\
            '<p>Below are the session variables.'
        for key in session:
            t = t + '<p>%s: %s</p>'%(key, session[key])
    else:
        t = 'Hello! <a href="{{ url_for("login") }}">Login</a>'
        for key in session:
            t = t + '<p>%s: %s</p>'%(key, session[key])

    return render_template_string(t)

@app.route('/login')
def login():
    if logged_in():
        redirect('/')
    else:
        session['state'] = random_string()
        url = form_git_authorize_url()
        return redirect(url)

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
        session['std_header'] = gen_header(session['access_token'])
        session['logged_in'] = True
        return redirect(url_for('home'))

@app.route('/control_room')
def home():
    if not logged_in():
        return redirect('/')
    data = {}
    data['orgs'] = [{'login':'foo'}, {'login': 'bar'}]
    data['url_logout'] = url_for('logout')
    return render_template('home.html', data = data)   

@app.route('/user')
def user():
    if not logged_in():
        return redirect('/')
    r = requests.get(r'https://api.github.com/user', headers=session['std_header'])
    return r.text

@app.route('/orgs')
def orgs():
    if not logged_in():
        return redirect('/')    
    r = requests.get(r'https://api.github.com/user/orgs', headers=session['std_header'])
    return r.text

@app.route('/orgs/<org>/teams')
def org_teams(org):
    if not logged_in():
        return redirect('/')
    r = requests.get(r'https://api.github.com/orgs/%s/teams'%org, headers=session['std_header'])
    return r.text

@app.route('/orgs/<org>/repos')
def org_repos(org):
    if not logged_in():
        return redirect('/')
    r = requests.get(r'https://api.github.com/orgs/%s/repos'%org, headers=session['std_header'])
    return r.text

@app.route('/repos/<org>/<repo>/issues')
def org_repo_issues(org, repo):
    if not logged_in():
        return redirect('/')
    r = requests.get(r'https://api.github.com/repos/%s/%s/issues'%(org, repo), headers=session['std_header'])
    return r.text

@app.route('/teams/<team>/repos')
def team_repos(team):
    if not logged_in():
        return redirect('/')
    r = requests.get(r'https://api.github.com/teams/%s/repos'%(team), headers=session['std_header'])
    return r.text + str(r.headers)

if __name__ == '__main__':
    app.run(debug=True)