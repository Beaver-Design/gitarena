import json
import requests
import config
import re

def getRequest(url, username, password, parameters = {}, debug = False, drill = False): 
    r = requests.get(url, params=parameters, auth=(username, password))
    if debug:
        print('Status Code: %i'%r.status_code)
    if not drill:
        return r
    return r
    page_count = findPageCount(r.links['last']['url'],'page=([^,]+)')
    if page_count == 1:
        return r

def headRequest(url, username, password, parameters = {}, debug = False): 
    r = requests.head(url, params=parameters, auth=(username, password))
    if degug:
        print('Status Code: %i'%r.status_code)
    return r

def findPageCount(url, search):
    match = re.search(search, url)
    if match:
        return int(match.group(1))
    else:
        return False

if __name__ == '__main__':
    repos = getRequest(config.URL_REPOS, config.USER, config.TOKEN)
    for index, repo in enumerate(repos.json()):
        print(json.dumps(index, repo['name'], indent = 2))
    print(repos.links['next']['url'])
    
    teams = getRequest(config.URL_TEAMS, config.USER, config.TOKEN)
    for index, team in enumerate(teams.json()):
        print(index, team['name'])
    parameters = {'filter':'all'}
    
    issues = getRequest(config.URL_ISSUES, config.USER, config.TOKEN, parameters)
    for index, issue in enumerate(issues.json()):
        print(index, issue['title'])
    print(issues.links)
    
    next = issues.links['last']['url']
    issues = getRequest(next, config.USER, config.TOKEN, parameters)
    for index, issue in enumerate(issues.json()):
        print(index, issue['title'])
    print(issues.links)        

