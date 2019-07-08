#!/usr/bin/env python3

# this script will be invoked by the crawl.py as a sub-process to crawl the code commits.

import json
import requests
import time

from base64 import b64encode
from webpage import Members, Commits,RepoTypes, db

USERNAME = 'svcacct_nanjing'
PASSWORD = 'Citrix123'
DOMAIN = 'code.citrite.net'
PROJECT = [repo.repo_type_name for repo in RepoTypes.query.all()]
base_url = 'https://{domain}/rest/api/1.0/projects/{project}/repos/'
members = [member.name for member in Members.query.all()]
open_pr_request_data = {
    "state": "open",
    "limit": 1000
}


# get all commits in project's repo
def get_bitbucket_commit_data():

    for project in PROJECT:
        auth_string = USERNAME + ':' + PASSWORD
        basic_auth = ("Basic {auth}".format(auth=b64encode(auth_string.encode('ascii'))))
        request_headers = {'Authorization': basic_auth}
        url = base_url.format(domain=DOMAIN, project=project)
        request = requests.get(url, open_pr_request_data, headers=request_headers)
        request_text = json.loads(request.text)
        repos = request_text.get('values')

        for repo in repos:
            repo_name = repo['name']
            repo_url = base_url.format(domain=DOMAIN, project=project) + repo_name + '/commits'
            repo_request = requests.get(repo_url, open_pr_request_data, headers=request_headers)
            repo_request_text = json.loads(repo_request.text)
            commits = repo_request_text.get('values')
            if not commits:
                continue
            for commit in commits:
                author = commit['author'].get('displayName')
                if author in members:
                    commit_id = commit['id']
                    db_commit = Commits.query.filter(Commits.commit_id == commit_id).first()
                    if not db_commit:
                        db_commit = Commits()
                        db_commit.date = time.localtime(commit['committerTimestamp'] / 1000)
                        db_commit.message = commit['message']
                        db_commit.commit_id = commit['id']
                        db_commit.author = author
                        db_commit.repo = repo_name
                        db_commit.project = project
                        line_count = 0
                        commit_url = repo_url + '/' + commit['id'] + '/diff'
                        commit_request = requests.get(commit_url, open_pr_request_data, headers=request_headers)
                        commit_request_text = json.loads(commit_request.text)
                        diffs = commit_request_text['diffs']
                        for diff in diffs:
                            content = diff.get('hunks')
                            if not content:
                                continue
                            for i in content:
                                for j in i['segments']:
                                    type = j['type']
                                    if type == 'ADDED':
                                        lines = j['lines']
                                        for line in lines:
                                            if line['line'].strip() != '':
                                                line_count += 1
                        db_commit.line = line_count
                        if line_count == 0:
                            continue
                        try:
                            db.session.add(db_commit)
                            db.session.commit()
                        except:
                            print ('Something error in %s %s %s' % (db_commit.repo, db_commit.author, db_commit.id))
                            db.session.rollback()


if __name__ == '__main__':
    get_bitbucket_commit_data()