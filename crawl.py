#!/usr/bin/env python3

'''
This file is to get data from Jira and Bitbucket by a backend job, it may spend time more than 1 hour.
'''

import argparse
import time
import re

from datetime import datetime
from jira import JIRA
from webpage import db, Sprints, TeamData, Members, Comments, Histories, Tickets, TicketTypes
from bitbucket import get_bitbucket_commit_data

BASE_JQL = 'project in (%s) '
EMEI_JQL = 'Teams in (xs-nanjing) AND Sprint in ("XS Nanjing Emei %s") AND '
EMEI_SPRINT = 'xsx-emei'
WUDANG_JQL = 'Teams in (xsx-wudang) AND Sprint in ("xsx-wudang %s") AND '
WUDANG_SPRINT = 'xsx-wudang'
SHAOLIN_JQL = 'Teams in (xsx-shaolin) AND Sprint in ("xsx-shaolin %s") AND '
SHAOLIN_SPRINT = 'xsx-shaolin'
NANJING_JQL = '((Teams in (xsx-wudang) AND Sprint in ("xsx-wudang {sprint}")) OR ' \
              '(Teams in (xsx-shaolin) AND Sprint in ("xsx-shaolin {sprint}"))) AND '

UNRESOLVED_JQL = 'status in (done) AND '
RESOLVED_JQL = 'status not in (done) AND '
SPRINT_JQL = 'Sprint in (%r) AND '

USER = 'svcacct_nanjing'
PASSWD = 'Citrix123'
PRODUCTION_JIRA = 'issues.citrite.net'
MAX_CPS = 5000

all_starts = [sprint.start_date for sprint in Sprints.query.all()]
start_date = min(all_starts)
all_ends = [sprint.end_date for sprint in Sprints.query.all()]
end_date = max(all_ends)

# connent to Jira
def authenticate_jira(server=PRODUCTION_JIRA, user=USER, passwd=PASSWD):
    return JIRA(options={'server': "https://{server}".format(server=server)}, basic_auth=(user, passwd))


# classify the ticket and save to DB
def get_team_data(jira, jql, team_data):
    cps = jira.search_issues(jql, maxResults=MAX_CPS)
    for cp in cps:
        status = cp.fields.status
        teams = cp.fields.customfield_11930
        team_data.project = cp.key.split('-')[0]

        if status.name == 'Done':
            if 'xs-qa' in teams:
                team_data.resolved_qa_num += 1
                team_data.resolved_num += 1
                team_data.resolved_qa += cp.key + ';'
                team_data.resolved += cp.key + ';'
                if cp.fields.customfield_11332:
                    team_data.resolved_qa_point += cp.fields.customfield_11332
                    team_data.resolved_point += cp.fields.customfield_11332
            else:
                team_data.resolved_dev_num += 1
                team_data.resolved_num += 1
                team_data.resolved_dev += cp.key + ';'
                team_data.resolved += cp.key + ';'
                if cp.fields.customfield_11332:
                    team_data.resolved_point += cp.fields.customfield_11332
                    team_data.resolved_dev_point += cp.fields.customfield_11332
        else:
            if 'xs-qa' in teams:
                team_data.unresolved_qa_num += 1
                team_data.unresolved_num += 1
                team_data.unresolved_qa += cp.key + ';'
                team_data.unresolved += cp.key + ';'
                if cp.fields.customfield_11332:
                    team_data.unresolved_qa_point += cp.fields.customfield_11332
                    team_data.unresolved_point += cp.fields.customfield_11332
            else:
                team_data.unresolved_dev_num += 1
                team_data.unresolved_num += 1
                team_data.unresolved_dev += cp.key + ';'
                team_data.unresolved += cp.key + ';'
                if cp.fields.customfield_11332:
                    team_data.unresolved_point += cp.fields.customfield_11332
                    team_data.unresolved_dev_point += cp.fields.customfield_11332


#get team data
def get_data(args):
    if not args.sprint:
        current_date = datetime.now().date()
        print("current_date = %s" % current_date)
        try:
            current_sprint = [sprint.sprint_name for sprint in Sprints.query.all()
                                   if sprint.start_date <= current_date and sprint.end_date >= current_date][0]
        except Exception as e:
            print('do not have sprint')
            return

    else:
        current_sprint = args.sprint

    # ticket_types = [tickets.ticket_type_name for tickets in TicketTypes.query.all()]
    ticket_types=['CA','CP']
    sprint_before_current = [sprint.sprint_name for sprint in Sprints.query.all() if sprint.sprint_name <= current_sprint]
    for types in ticket_types:
        for b_sprint in sprint_before_current:
            print("get data about %s, in %s" % (types,b_sprint))
            get_data_by_project(b_sprint,types)

# get current sprint's team data
def get_data_by_project(current_sprint, project):
    jira = authenticate_jira()
    
    xsx_emei = TeamData()
    xsx_emei.sprint = current_sprint
    xsx_emei.team_name = 'xsx-emei'
    xsx_emei.project = project
    xsx_emei = create_or_update(xsx_emei)
    # get_team_data(jira, EMEI_JQL % current_sprint + BASE_JQL % project, xsx_emei)

    xsx_shaolin = TeamData()
    xsx_shaolin.sprint = current_sprint
    xsx_shaolin.team_name = 'xsx-shaolin'
    xsx_shaolin.project = project
    xsx_shaolin = create_or_update(xsx_shaolin)
    get_team_data(jira, SHAOLIN_JQL % current_sprint + BASE_JQL % project, xsx_shaolin)

    xsx_wudang = TeamData()
    xsx_wudang.sprint = current_sprint
    xsx_wudang.team_name = 'xsx-wudang'
    xsx_wudang.project = project
    xsx_wudang = create_or_update(xsx_wudang)
    get_team_data(jira, WUDANG_JQL % current_sprint + BASE_JQL % project, xsx_wudang)

    xs_nanjing = TeamData()
    xs_nanjing.sprint = current_sprint
    xs_nanjing.team_name = 'xs-nanjing'
    xs_nanjing.project = project
    xs_nanjing = create_or_update(xs_nanjing)
    get_team_data(jira, NANJING_JQL.format(sprint=current_sprint) + BASE_JQL % project, xs_nanjing)

    save_to_db(xsx_emei)
    save_to_db(xsx_wudang)
    save_to_db(xsx_shaolin)
    save_to_db(xs_nanjing)


# if DB already have current sprint, will update
# if don't exist, add a new one
def create_or_update(data):
    if TeamData.query.filter(data.team_name == TeamData.team_name)\
            .filter(data.sprint == TeamData.sprint)\
            .filter(data.project == TeamData.project).first():
        data = TeamData.query.filter(data.team_name == TeamData.team_name)\
                             .filter(data.sprint == TeamData.sprint)\
                             .filter(data.project == TeamData.project).first()
        data.unresolved_num = 0
        data.unresolved_dev_num = 0
        data.unresolved_qa_num = 0
        data.unresolved_point = 0
        data.unresolved_dev_point = 0
        data.unresolved_qa_point = 0
        data.unresolved = ''
        data.unresolved_qa = ''
        data.unresolved_dev = ''
        data.resolved_num = 0
        data.resolved_dev_num = 0
        data.resolved_qa_num = 0
        data.resolved = ''
        data.resolved_qa = ''
        data.resolved_dev = ''
        data.resolved_point = 0
        data.resolved_dev_point = 0
        data.resolved_qa_point = 0
    return data


# save to DB
def save_to_db(data):
    db.session.add(data)
    db.session.commit()

# judge is in current year,if true,then it can be saved in db
def is_current_year(ticket_solved_time):
    if ticket_solved_time>=start_date and ticket_solved_time<=end_date:
        return True
    else:
        return False

# get all nanjing team memeber's(in DB) tickets
def get_ticket_by_sprint(ticket, members):
    ticket_detail = ticket.fields
    ticket_sprints = ticket_detail.customfield_11335
    ticket_id = ticket.key
    db_ticket = Tickets.query.filter(Tickets.ticket_id == ticket_id).first()
    if not db_ticket:
        db_ticket = Tickets()
    db_ticket.ticket_id = ticket_id
    sprint = ''
    if ticket_sprints:
        for ticket_sprint in ticket_sprints:
            sprint_pattern = re.compile(r'.*?name=(.*?),')
            result = sprint_pattern.search(ticket_sprint)
            if result:
                sprint += result.group(1)
                sprint += ';'
    db_ticket.sprint = sprint
    try:
        ticket_assignee = ticket_detail.assignee.displayName
    except:
        return
    if ticket_assignee not in members:
        return
    status = ticket_detail.status.name
    created_time = time.strptime(ticket_detail.created[:10], '%Y-%m-%d')
    db_ticket.created_time = datetime.fromtimestamp(time.mktime(created_time)).date()
    if status=='Done':
        resolved_time = time.strptime(ticket_detail.resolutiondate[:10], '%Y-%m-%d')
        db_ticket.solved_time = datetime.fromtimestamp(time.mktime(resolved_time)).date()

    if is_current_year(db_ticket.created_time) or (status=='Done' and is_current_year(db_ticket.solved_time)):
        db_ticket.story_point = ticket_detail.customfield_11332 or 0
        db_ticket.status = ticket_detail.status.name
        teams = ''
        if ticket_detail.customfield_11930:
            for team in ticket_detail.customfield_11930:
                teams += team
                teams += ';'
        else:
            teams='xs-nanjing'
        db_ticket.assignee = ticket_assignee
        db_ticket.team = teams
        db.session.add(db_ticket)
        db.session.commit()
    else:
        return


# get all nanjing team's tickets
def get_ticket_from_jira():
    jira = authenticate_jira()
    members = [member.name for member in Members.query.all()]
    cps=[]
    for member in members:
        member_name = member.lower().split()
        member_name = member_name[0]+member_name[1][0]
        if member_name=='minl':
            member_name='minl1'
        if member_name=='yangq':
            member_name='yangqi'
        if member_name=='michaelz':
            member_name='fengyangz'
        if member_name=='xinl':
            member_name='xinl1'
        query_member = 'issueFunction in commented(\'by '+member_name+'\') and updatedDate >='+ str(start_date)
        print(query_member)
        cps.extend(jira.search_issues(query_member, maxResults=False, expand='changelog'))
    have_done=[]
    for cp in cps:
        if cp.key in have_done:
            continue
        get_ticket_by_sprint(cp, members)
        get_all_changelog(cp, members)
        get_all_comment(jira, cp, members)
        have_done.append(cp.key)


# get all nanjing team member's comments
def get_all_comment(jira, ticket, members):
    comments = jira.comments(ticket)
    ticket_id = ticket.key
    for c in comments:
        if c.author.displayName in members:
            if not Comments.query.filter(Comments.comment_id == c.id).first():
                comment = Comments()
                comment.date = time.strptime(c.created.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                comment_time = time.strptime(c.created[:10], '%Y-%m-%d')
                comment_date =datetime.fromtimestamp(time.mktime(comment_time)).date()
                if not is_current_year(comment_date):
                    continue
                comment.comment_id = c.id
                comment.ticket_id = ticket_id
                comment.author = c.author.displayName
                # comment.content = c.body
                print("comments; ticket_id: %s" % comment.ticket_id)

                py_string=c.body
                if len(py_string)>65530:
                    comment.content=py_string[0:65530]+'...'
                else :
                    comment.content = py_string
                try:
                    db.session.add(comment)
                    db.session.commit()
                except:
                    db.session.rollback()
                    print("Some things error when save ticket: %s to comments" % ticket_id)

# get all nanjing team member's changelog.
def get_all_changelog(ticket, members):
    histories = ticket.changelog.histories
    for history in histories:
        id = history.id
        if Histories.query.filter(Histories.change_id == id).first():
            continue
        try:
            displayname = history.author.displayName
        except:
            displayname = 'Anonymous'
        if displayname in members:
            change = Histories()
            change.author = displayname
            change.change_id = id
            change.date = time.strptime(history.created.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            change_time = time.strptime(history.created[:10], '%Y-%m-%d')
            change_date = datetime.fromtimestamp(time.mktime(change_time)).date()
            if not is_current_year(change_date):
                continue
            change.ticket_id = ticket.key
            items = history.items[0]
            fromstring = items.fromString
            if not fromstring:
                fromstring = 'None'
            tostring = items.toString
            if not tostring:
                tostring = 'None'
            change.change = 'Change %s from \'%s\' to \'%s\'' % (items.field, fromstring, tostring)

            print('histories; ticket_id: %s' % change.ticket_id)

            if len(change.change)>65530:
                change.change = change.change[0:65530]+'...'

            try:
                db.session.add(change)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print('Some things error when save ticket: %s to histories' % change.ticket_id)
                print(change.change)

def main():
    PARSER = argparse.ArgumentParser(description='get the data by team based from jira')
    PARSER.add_argument('--sprint', help='sprint')
    args = PARSER.parse_args()
    print("#get data(args):")
    get_data(args)
    print("#get_bitbucket_commit_data:")
    get_bitbucket_commit_data()
    print("#get_ticket_from jira:")
    get_ticket_from_jira()

if __name__ == '__main__':
    main()
