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

def form_git_authorize_url(base = git_authorize_url, id = GITHUB_CLIENT_ID, session = session, scope = 'read:org%20repo'):
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

###############################################################################
def get_helper(url, parameters={'per_page': '10'}, return_all=False):
    if not logged_in():
        return redirect('/')    
    r = requests.get(url, params=parameters, headers=session['std_header'])
    print(url)
    print(r.url)
    if return_all:
        return r
    else:
        return r.text

def form_url(endpoint, prefix=r'https://api.github.com'):
    return prefix + endpoint

@app.route('/user')
def user():
    url = form_url('/user')
    return get_helper(url)

@app.route('/orgs')
def orgs(return_all = False):
    url = form_url('/user/orgs')
    return get_helper(url, return_all=return_all)

@app.route('/orgs/<org>/teams')
def org_teams(org):
    url = form_url('/orgs/%s/teams'%org)
    return get_helper(url)

@app.route('/orgs/<org>/repos')
def org_repos(org, return_all=False):
    url = form_url('/orgs/%s/repos'%org)
    return get_helper(url, return_all=return_all)

@app.route('/repos/<org>/<repo>/issues')
def org_repo_issues(org, repo, return_all=False):
    url = form_url('/repos/%s/%s/issues'%(org, repo))
    return get_helper(url, return_all=return_all)

@app.route('/teams/<team>/repos')
def team_repos(team):
    url = form_url('/teams/%s/repos'%(team))
    return get_helper(url)

@app.route('/rate_limit')
def get_rate_limit():
    url = form_url('/rate_limit')
    return get_helper(url)

@app.route('/repos/<owner>/<repo>/milestones')
def get_milestones(owner, repo):
    if not logged_in():
        return redirect('/')
    r = requests.get(r'https://api.github.com/repos/%s/%s/milestones'%(owner, repo), headers=session['std_header'])
    return r.text

@app.route('/search/issues')
def search_issues(payload, return_all=False):
    if not logged_in():
        return redirect('/')
    r = requests.get(r'https://api.github.com/search/issues', headers=session['std_header'], params=payload)
    if return_all:
        return r
    else:
        return r.text

def form_search_string(search_params):
    search_string = 'q='
    for key in search_params:
        search_string += key + ':' + search_params[key] + '+'
    return search_string.rstrip('+')

###############################################################################
@app.route('/milestones')
def get_milestones_by_orgs():
    data = {}
    organizations = json.loads(orgs())
    for org in organizations:
        login = org['login']
        print(login)
        repos = json.loads(org_repos(login))
        for repo in repos:
            name = repo['name']
            print(' %s'%name)
            milestones = json.loads(get_milestones(login, name))
            for milestone in milestones:
                title = milestone['title']
                if title in data:
                    data[title]['org'].append(login)
                    data[title]['repo'].append(name)
                else:
                    data[title] = {'org': [login], 'repo': [name]}
                print('  %s'%title)
    return json.dumps(data)

def check_pagination(response):
    try:
        #print(response.links)
        #print(response.headers)
        return {'last_url': response.links['last']['url']}
    except KeyError:
        return False

def get_extra_data(url, last_url):
    r =  requests.get(url, headers=session['std_header'])
    print('Items returned: %i'%len(r.json()))
    if url == last_url:
        return r.json()
    else:
        return r.json() + get_extra_data(r.links['next']['url'], last_url)

def get_all_data(response):
    response_data = response.json()
    extra_pages = check_pagination(response)
    if extra_pages:
        next_url = response.links['next']['url']
        last_url = extra_pages['last_url']
        print('Next url: %s'%next_url)
        print('Last url: %s'%last_url)
        response_data += get_extra_data(next_url, last_url)
    return response_data

@app.route('/all_issues')
def get_all_issues():
    all_issues = []
    org_response = orgs(True)
    org_data = get_all_data(org_response)
    for org in org_data:
        org_login = org['login']
        #print('Organization: %s'%org_login)
        repo_response = org_repos(org_login, True)
        repo_data = get_all_data(repo_response)
        for repo in repo_data:
            repo_name = repo['name']
            print('   Repository: %s'%repo_name)
            issue_response = org_repo_issues(org_login, repo_name, True)
            issue_data = get_all_data(issue_response)
            print('Number of issues found: %i'%len(issue_data))
            for issue in issue_data:
                #print('      Issue: %s'%issue['title'])
                issue['org_login'] = org_login
                issue['repo_name'] = repo_name
                all_issues.append(issue)

    return render_template('all_issues.html', all_issues = all_issues)

if __name__ == '__main__':
    app.run(debug=True)