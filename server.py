import config
import flask
import json
import os
import sys
import requests

app = flask.Flask(__name__)

def getRequest(url, username, password, parameters = {}, debug = False): 
    r = requests.get(url, params=parameters, auth=(username, password))
    if debug:
        print('Status Code: %i'%r.status_code)
    return r

def getRequestJson(url, username, password, parameters = {}, debug = False, drill = False): 
    print(url)
    r = requests.get(url, params=parameters, auth=(username, password))
    if debug:
        print('Status Code: %i'%r.status_code)
    if not drill:
        return r.json()
    else:
        page_count = findPageCount(r.links)
        if page_count == 1:
            return r.json()
        current_page = findCurrentPage(url)
        if debug:
            print('page: %i of %i'%(current_page, page_count))
        if page_count == current_page:
            return r.json()
        else:
            return r.json() + getRequestJson(r.links['next']['url'], username, password, parameters, debug, drill)
        
def headRequest(url, username, password, parameters = {}, debug = False): 
    r = requests.head(url, params=parameters, auth=(username, password))
    if degug:
        print('Status Code: %i'%r.status_code)
    return r

def findPageCount(links, search = 'page=([^,]+)'):
    if not links:
        return 1
    try:
        match = re.search(search, links['last']['url'])
        if match:
            count = int(match.group(1))
            return count
        else:
            return False
    except KeyError:
        print('should be the last one' + json.dumps(links))
        match = re.search(search, links['prev']['url'])
        if match:
            count = int(match.group(1)) + 1
            return count
        else:
            return False

def findCurrentPage(url, search = 'page=([^,]+)'):
    if 'page=' in url:
        match = re.search(search, url)
        if match:
            count = int(match.group(1))
            return count
        else:
            return False
    else:
        return 1
    
def formURLMilestoneByRepo(base, owner, repo):
    return '%s/repos/%s/%s/milestones'%(base, owner, repo)
def formURLUserOrgs(base, username):
    return "%s/users/%s/orgs"%(base, username)
def formURLRepos(base, org):
    return '%s/orgs/%s/repos'%(base, org)
def formURLRepos(base, org):
    return '%s/orgs/%s/teams'%(base, org)
def formURLRepos(base, org):
    return '%s/orgs/%s/issues'%(base, org)

@app.route('/')
def home():
    url_orgs = formURLUserOrgs(config.URL_BASE, config.USER)
    orgs = getRequestJson(url_orgs, config.USER, config.TOKEN, parameters = {'filter':'all'}, drill = True)
    return flask.render_template('home.html', orgs = orgs)

if __name__ == '__main__':
    url_orgs = formURLUserOrgs(config.URL_BASE, config.USER)
    orgs = getRequestJson(url_orgs, config.USER, config.TOKEN, parameters = {'filter':'all'}, drill = True)
    print('this is a test')
    for org in orgs:
        print(org['url'])
    r_orgs = getRequest(url_orgs, config.USER, config.TOKEN, debug = True)
    print(json.dumps(r_orgs.json()))
    app.run(debug='--debug' in sys.argv)