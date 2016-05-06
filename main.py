import json
import requests
import config

def getRequest(url, username, password, drill = False): 
    r = requests.get(url, auth=(username, password))
    print('Status Code: %i'%r.status_code)
    #if 'next' in r.links.keys():
    #    print('extra')
    #    next_url = r.links['next']['url']
    #    if drill:
    #        r.json+=getRequest(next_url, username, password).json
    #else:
    #    return r
    return r

if __name__ == '__main__':
    repos = getRequest(config.URL_REPOS, config.USER, config.TOKEN)
    for index, repo in enumerate(repos.json()):
        print(json.dumps(index, repo['name'], indent = 2))
    print(repos.links['next']['url'])

    teams = getRequest(config.URL_TEAMS, config.USER, config.TOKEN)
    for index, team in enumerate(teams.json()):
        print(index, team['name'])

    issues = getRequest(config.URL_ISSUES, config.USER, config.TOKEN)
    for index, issue in enumerate(issues.json()):
        print(index, issue['title'])