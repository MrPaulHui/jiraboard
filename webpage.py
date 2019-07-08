#!/usr/bin/python3

import datetime
from sqlalchemy.exc import IntegrityError
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from form import ConfigForm, SprintForm, QueryForm, CodeQueryForm ,SolvedNumQueryForm
import matplotlib
matplotlib.use('Agg')
from sqlalchemy import or_,and_
from matplotlib import pyplot as plt
import time
from functools import reduce

app = Flask(__name__)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.config['SECRET_KEY'] = 'xs-nanjing'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:xenroot@localhost:3306/xsnkgperf?charset=utf8mb4'
app.config['SQLALCHEMY_COMMIT_ON_TEADOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = datetime.timedelta(0)
app.config['TEMPLATES_AUTO_RELOAD']=True
Bootstrap(app)
CSRFProtect(app)
db = SQLAlchemy(app)


# DB table: comments of ticket
class Comments(db.Model):
    __table_args__={'mysql_collate':'utf8mb4_general_ci'}
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer)
    ticket_id = db.Column(db.String(10))
    author = db.Column(db.String(20))
    content = db.Column(db.UnicodeText)
    date = db.Column(db.DATETIME)

    def __repr__(self):
        return '<Comments %s>' % self.id


# DB table: changes of ticket
class Histories(db.Model):
    __table_args__ = {'mysql_collate': 'utf8mb4_general_ci'}
    id = db.Column(db.Integer, primary_key=True)
    change_id = db.Column(db.String(20))
    ticket_id = db.Column(db.String(10))
    author = db.Column(db.String(20))
    change = db.Column(db.UnicodeText)
    date = db.Column(db.DATETIME)

    def __repr__(self):
        return '<History %s>' % self.id


# DB table: commits in BitBucket
class Commits(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    commit_id = db.Column(db.String(50))
    project = db.Column(db.String(50))
    repo = db.Column(db.String(50))
    message = db.Column(db.Text)
    author = db.Column(db.String(20))
    line = db.Column(db.Integer)
    date = db.Column(db.DATETIME)

    def __repr__(self):
        return '<Commit %s %s %s>' % (self.repo, self.author, self.id)


# DB table: sprints
class Sprints(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sprint_name = db.Column(db.String(10))
    start_date = db.Column(db.DATE)
    end_date = db.Column(db.DATE)
    note = db.Column(db.Text)

    def __repr__(self):
        return '<Sprint %s>' % self.sprint_name

    def __init__(self,id,sprint_name,start_date,end_date,note=None):
        self.id=id
        self.sprint_name=sprint_name
        self.start_date=start_date
        self.end_date=end_date
        self.note=note


# DB table: tickets by sprint
class Tickets(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(15))
    sprint = db.Column(db.Text)
    assignee = db.Column(db.String(30))
    created_time = db.Column(db.DATE)
    solved_time = db.Column(db.DATE)
    story_point = db.Column(db.FLOAT)
    team = db.Column(db.Text)
    status = db.Column(db.Text)

    def __repr__(self):
        return '<Ticket %s>' % self.ticket_id

# DB table: ticket_types for query jira
class TicketTypes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_type_name = db.Column(db.String(10), unique=True)
    is_query=db.Column(db.Boolean,default=0)

    def __init__(self,id,ticket_type_name,is_query):
        self.id=id
        self.ticket_type_name=ticket_type_name
        self.is_query=is_query

# DB table: repo_types for query
class RepoTypes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repo_type_name = db.Column(db.String(10), unique=True)
    is_query=db.Column(db.Boolean,default=0)

    def __init__(self,id,repo_type_name,is_query):
        self.id=id
        self.repo_type_name=repo_type_name
        self.is_query=is_query

# DB table: teams
class Teams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(20), unique=True)
    note = db.Column(db.Text)

    def __init__(self,id,team_name,note=None):
        self.id=id
        self.team_name=team_name
        self.note=note


# DB table: members
class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    xs_nanjing = db.Column(db.Boolean, default=1)
    xsx_emei = db.Column(db.Boolean, default=0)
    xsx_wudang = db.Column(db.Boolean, default=0)
    xsx_shaolin = db.Column(db.Boolean, default=0)

    def __init__(self,id ,name,xs_nanjing,xsx_emei,xsx_wudang,xsx_shaolin):
        self.id=id
        self.name=name
        self.xs_nanjing=xs_nanjing
        self.xsx_emei=xsx_emei
        self.xsx_wudang=xsx_wudang
        self.xsx_shaolin=xsx_shaolin


# DB table: detail counts by team in every sprint
class TeamData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(20))
    sprint = db.Column(db.String(20))
    project = db.Column(db.String(20))
    unresolved_qa_num = db.Column(db.Integer)
    resolved_qa_num = db.Column(db.Integer)
    unresolved_dev_num = db.Column(db.Integer)
    resolved_dev_num = db.Column(db.Integer)
    unresolved_num = db.Column(db.Integer)
    resolved_num = db.Column(db.Integer)
    unresolved_qa_point = db.Column(db.Float)
    resolved_qa_point = db.Column(db.Float)
    unresolved_dev_point = db.Column(db.Float)
    resolved_dev_point = db.Column(db.Float)
    unresolved_point = db.Column(db.Float)
    resolved_point = db.Column(db.Float)
    unresolved_qa = db.Column(db.Text)
    resolved_qa = db.Column(db.Text)
    unresolved_dev = db.Column(db.Text)
    resolved_dev = db.Column(db.Text)
    unresolved = db.Column(db.Text)
    resolved = db.Column(db.Text)

    def __init__(self):
        self.unresolved_qa_num = 0
        self.resolved_qa_num = 0
        self.unresolved_dev_num = 0
        self.resolved_dev_num = 0
        self.unresolved_num = 0
        self.resolved_num = 0
        self.unresolved_qa_point = 0
        self.resolved_qa_point = 0
        self.unresolved_dev_point = 0
        self.resolved_dev_point = 0
        self.unresolved_point = 0
        self.resolved_point = 0
        self.unresolved_qa = ''
        self.resolved_qa = ''
        self.unresolved_dev = ''
        self.resolved_dev = ''
        self.unresolved = ''
        self.resolved = ''

# home page
@app.route('/', methods=['Get', 'POST'])
def home():
    return render_template('home.html')


# the page show the commit in BitBucket
#   get methods show all of commit in project XSC, can extends to all projects in future.
#   post methods show the result of query.
@app.route('/commits', methods=['GET', 'POST'])
def bitbucket():
    members = Members.query.all()
    form = CodeQueryForm(members)
    name = 'Total'
    if request.method == 'POST':
        # query by author
        author_id = request.form.get('author')
        if author_id == '0':
            commits = Commits.query
            name = 'Total'
        else:
            author = Members.query.filter(Members.id == author_id).first()
            name = author.name
            commits = Commits.query.filter(Commits.author == name)
        # query by date
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if start_date and end_date:
            try:
                start_date = time.strptime(start_date, '%Y/%m/%d')
                end_date = time.strptime(end_date, '%Y/%m/%d')
            except Exception as e:
                flash('%s' % e.message)
                return render_template('error.html')
            commits = commits.filter(Commits.date > start_date)\
                             .filter(Commits.date < end_date)
        commits = commits.order_by(Commits.date).all()
        if commits:
            commits_line = [commit.line for commit in commits]
            total = reduce(lambda x, y: x+y, commits_line)
        else:
            total = 0

        # draw a graph
        draw_commit = {}
        all_starts=[sprint.start_date for sprint in Sprints.query.all()]
        start_date=min(all_starts)
        all_ends=[sprint.end_date for sprint in Sprints.query.all()]
        end_date=max(all_ends)

        if len(commits):
            for commit in commits:
                current_date = commit.date.date()
                if current_date>=start_date and current_date<=end_date:
                    current_sprint = [sprint.sprint_name for sprint in Sprints.query.all()
                                  if sprint.start_date <= current_date and sprint.end_date >= current_date][0]
                    if current_sprint in draw_commit:
                        draw_commit[current_sprint] = commit.line + draw_commit[current_sprint]
                    else:
                        draw_commit[current_sprint] = commit.line
                else:
                    continue
        else:
            draw_commit={'no data':0}

        draw_fig(draw_commit,'commit_lines')
        return render_template('commits.html', cmts=commits, form=form, total=total, author=name)

    # show all commits order by author
    commits = Commits.query.order_by(Commits.author).all()
    commits_line = [commit.line for commit in commits]
    total = reduce(lambda x, y: x + y, commits_line)

    return render_template('commits.html', cmts=commits, form=form, total=total, author=name)


# the page to choose modify sprint or team
@app.route('/config', methods=['GET', 'POST'])
def config_page():
    # config the sprint
    if request.method == 'POST' and request.form.get('submit'):
        sprint_id = request.form.get('sprint')
        sprint = Sprints.query.filter(Sprints.id == sprint_id).first()
        session['sprint_id'] = sprint.id
        session['sprint_name'] = sprint.sprint_name
        session['sprint_start_date'] = sprint.start_date.strftime('%d-%b-%Y')
        session['sprint_end_date'] = sprint.end_date.strftime('%d-%b-%Y')
        return redirect(url_for('config_sprint'))

    # config the team
    if request.method == 'POST' and request.form.get('submit2'):
        team_id = request.form.get('team')
        team = Teams.query.filter(Teams.id == team_id).first()
        session['team_id'] = team.id
        session['team_name'] = team.team_name
        return redirect(url_for('config_team'))

    sprint_list = Sprints.query.all()
    team_list = Teams.query.all()
    config_form = ConfigForm(sprint_list, team_list)
    return render_template('config.html', form=config_form)


# the page to config team
@app.route('/config_team', methods=['GET', 'POST'])
def config_team():
    team_name = session['team_name'].replace('-', '_')
    if Members.xs_nanjing.key == team_name:
        members = Members.query.filter(Members.xs_nanjing == 1).order_by(Members.name).all()
        u_members = Members.query.filter(Members.xs_nanjing == 0).order_by(Members.name).all()
    elif Members.xsx_emei.key == team_name:
        members = Members.query.filter(Members.xsx_emei == 1).order_by(Members.name).all()
        u_members = Members.query.filter(Members.xsx_emei == 0).order_by(Members.name).all()
    elif Members.xsx_shaolin.key == team_name:
        members = Members.query.filter(Members.xsx_shaolin == 1).order_by(Members.name).all()
        u_members = Members.query.filter(Members.xsx_shaolin == 0).order_by(Members.name).all()
    elif Members.xsx_wudang.key == team_name:
        members = Members.query.filter(Members.xsx_wudang == 1).order_by(Members.name).all()
        u_members = Members.query.filter(Members.xsx_wudang == 0).order_by(Members.name).all()
    return render_template('config_team.html', team=team_name, members=members, u_members=u_members)


# add team member
@app.route('/team_member_add', methods=['POST'])
def team_member_add():
    team_name = session['team_name'].replace('-', '_')
    # add exist member to team
    for name, value in request.form.items():
        if value == 'on':
            member = Members.query.filter(Members.name == name).first()
            if Members.xs_nanjing.key == team_name:
                member.xs_nanjing = 1
            elif Members.xsx_emei.key == team_name:
                member.xsx_emei = 1
            elif Members.xsx_shaolin.key == team_name:
                member.xsx_shaolin = 1
            elif Members.xsx_wudang.key == team_name:
                member.xsx_wudang = 1
            db.session.commit()

    # add a new member
    if request.form.get('add_name'):
        add_name = request.form.get('add_name')
        id = Members.query.filter().count()+1
        new_user = Members(id,add_name,1,0,0,0)
        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            flash('%r already in DB' % str(add_name))
    return redirect(url_for('config_team'))


# delete team member
@app.route('/team_member_delete', methods=['POST'])
def team_member_delete():
    team_name = session['team_name'].replace('-', '_')
    # delete member from team
    for name, value in request.form.items():
        if value == 'on':
            member = Members.query.filter(Members.name == name).first()
            if Members.xs_nanjing.key == team_name:
                member.xs_nanjing = 0
            elif Members.xsx_emei.key == team_name:
                member.xsx_emei = 0
            elif Members.xsx_shaolin.key == team_name:
                member.xsx_shaolin = 0
            elif Members.xsx_wudang.key == team_name:
                member.xsx_wudang = 0
            db.session.commit()

    # delete member from database
    if request.form.get('delete_name'):
        delete_name = request.form.get('delete_name')
        delete_user = Members.query.filter(Members.name == delete_name).first()
        id_del = delete_user.id
        id_all = Members.query.filter().count()
        db.session.delete(delete_user)
        db.session.commit()

        if id_del<id_all:
            alter_member = Members.query.filter(Members.id>id_del)
            for member_temp in alter_member:
                member_temp.id=member_temp.id-1
            db.session.commit()

    return redirect(url_for('config_team'))

# the page to config ticket types
@app.route('/config_ticket_type', methods=['GET', 'POST'])
def config_ticket_type():
    ticket_types_exist=TicketTypes.query.filter(TicketTypes.is_query == 1).order_by(TicketTypes.ticket_type_name).all()
    ticket_types_notexist = TicketTypes.query.filter(TicketTypes.is_query == 0).order_by(TicketTypes.ticket_type_name).all()
    return render_template('config_ticket_type.html',ticket_types_exist=ticket_types_exist,ticket_types_notexist=ticket_types_notexist)

# add ticket types
@app.route('/ticket_type_add', methods=['POST'])
def ticket_type_add():
    # add exist type to query
    for name, value in request.form.items():
        if value == 'on':
            types = TicketTypes.query.filter(TicketTypes.ticket_type_name == name).first()
            types.is_query = 1
            db.session.commit()

    # add a new member
    if request.form.get('add_ticket_type'):
        type_name = request.form.get('add_ticket_type')
        id=TicketTypes.query.filter().count()+1
        new_type=TicketTypes(id,type_name,0)
        try:
            db.session.add(new_type)
            db.session.commit()
        except IntegrityError:
            flash('%r already in DB' % str(type_name))
    return redirect(url_for('config_ticket_type'))

# delete ticket types
@app.route('/ticket_type_delete', methods=['POST'])
def ticket_type_delete():
    # delete type from ticket_types
    for name, value in request.form.items():
        if value == 'on':
            types = TicketTypes.query.filter(TicketTypes.ticket_type_name == name).first()
            types.is_query=0
            db.session.commit()

    # delete member from database
    if request.form.get('delete_type'):
        type_name = request.form.get('delete_type')
        delete_type = TicketTypes.query.filter(TicketTypes.ticket_type_name == type_name).first()
        id_del = delete_type.id
        id_all = TicketTypes.query.filter().count()
        db.session.delete(delete_type)
        db.session.commit()

        # recover id sequence
        if id_del < id_all:
            alter_type = TicketTypes.query.filter(TicketTypes.id>id_del).all()
            for type_temp in alter_type:
                type_temp.id=type_temp.id-1
            db.session.commit()

    return redirect(url_for('config_ticket_type'))
#######
# the page to config repo types
@app.route('/config_repo_type', methods=['GET', 'POST'])
def config_repo_type():
    repo_types_exist=RepoTypes.query.filter(RepoTypes.is_query == 1).order_by(RepoTypes.repo_type_name).all()
    repo_types_notexist = RepoTypes.query.filter(RepoTypes.is_query == 0).order_by(RepoTypes.repo_type_name).all()
    return render_template('config_repo_type.html',repo_types_exist=repo_types_exist,repo_types_notexist=repo_types_notexist)

# add ticket types
@app.route('/repo_type_add', methods=['POST'])
def repot_type_add():
    # add exist type to query
    for name, value in request.form.items():
        if value == 'on':
            types = RepoTypes.query.filter(RepoTypes.repo_type_name == name).first()
            types.is_query = 1
            db.session.commit()

    # add a new member
    if request.form.get('add_repo_type'):
        type_name = request.form.get('add_repo_type')
        id=RepoTypes.query.filter().count()+1
        new_type=RepoTypes(id,type_name,0)
        try:
            db.session.add(new_type)
            db.session.commit()
        except IntegrityError:
            flash('%r already in DB' % str(type_name))
    return redirect(url_for('config_repo_type'))

# delete ticket types
@app.route('/repo_type_delete', methods=['POST'])
def repot_type_delete():
    # delete type from ticket_types
    for name, value in request.form.items():
        if value == 'on':
            types = RepoTypes.query.filter(RepoTypes.repo_type_name == name).first()
            types.is_query=0
            db.session.commit()

    # delete member from database
    if request.form.get('delete_type'):
        type_name = request.form.get('delete_type')
        delete_type = RepoTypes.query.filter(RepoTypes.repo_type_name == type_name).first()
        id_del = delete_type.id
        id_all = RepoTypes.query.filter().count()
        db.session.delete(delete_type)
        db.session.commit()

        # recover id sequence
        if id_del < id_all:
            alter_type = RepoTypes.query.filter(RepoTypes.id>id_del).all()
            for type_temp in alter_type:
                type_temp.id=type_temp.id-1
            db.session.commit()

    return redirect(url_for('config_repo_type'))


# page to config sprint
@app.route('/config_sprint', methods=['GET', 'POST'])
def config_sprint():
    form = SprintForm(session)
    if form.validate_on_submit():
        sprint_id = session['sprint_id']
        start_time = time.strptime(request.form.get('start_date'), '%d-%b-%Y')
        end_time = time.strptime(request.form.get('end_date'), '%d-%b-%Y')
        sprint = Sprints.query.filter(Sprints.id == sprint_id).first()
        sprint.start_date = start_time
        sprint.end_date = end_time
        db.session.commit()
        return redirect(url_for('config_page'))
    return render_template('config_sprint.html', form=form)


# page to query tickets
#   GET methods to show the query page
#   POST methods to show the result of query
@app.route('/query_ticket', methods=['Get', 'POST'])
def query_sprint():
    sprints = Sprints.query.all()
    teams = Teams.query.all()
    members = Members.query.all()
    member_name = ''
    type_name = ''
    team_name = ''
    form = QueryForm(sprints, teams, members)
    team_or_member_flag = 1
    if request.method == 'POST':
        choice = request.form.get('choice')
        team_or_member = int(request.form.get('team_or_member'))
        # query by team
        for team in teams:
            if team.id == team_or_member:
                team_or_member_flag = 0
                team_name = team.team_name
                break
        if team_or_member_flag:
            # now the DB has four teams, if add/delete team, this int values need to modify
            team_or_member -= 4
            for member in members:
                if member.id == team_or_member:
                    member_name = member.name
                    break
        # query by type
        if request.form.get('type'):
            type_name = request.form.get('type')
        # query by sprint
        if choice == 'sprint':
            sprint_id = request.form.get('sprint')
            choice_sprint = Sprints.query.filter(Sprints.id == sprint_id).first()
            start_date = choice_sprint.start_date
            end_date = choice_sprint.end_date

        # query by date
        elif choice == 'date':
            try:
                start_date = time.strptime(request.form.get('start_date'), '%Y/%m/%d')
                end_date = time.strptime(request.form.get('end_date'), '%Y/%m/%d')
            except Exception as e:
                flash('Error: %s' % e.message)
                return redirect(url_for('query_sprint'))
        # query from DB
        cmts = Comments.query.filter(Comments.date <= end_date).filter(Comments.date >= start_date)
        changes = Histories.query.filter(Histories.date <= end_date).filter(Histories.date >= start_date)
        if type_name:
            type_f = or_(Comments.ticket_id.startswith(t.strip()) for t in type_name.strip().strip(',').split(','))
            cmts = cmts.filter(type_f)
            type_f = or_(Histories.ticket_id.startswith(t.strip()) for t in type_name.strip().strip(',').split(','))
            changes = changes.filter(type_f)
        if member_name:
            cmts = cmts.filter(Comments.author == member_name)
            changes = changes.filter(Histories.author == member_name)
        if team_name:
            if team_name == 'xs-nanjing':
                members_f = Members.query.filter(Members.xs_nanjing == 1).all()
            elif team_name == 'xsx-wudang':
                members_f = Members.query.filter(Members.xsx_wudang == 1).all()
            elif team_name == 'xsx-shaolin':
                members_f = Members.query.filter(Members.xsx_shaolin == 1).all()
            elif team_name == 'xsx-emei':
                members_f = Members.query.filter(Members.xsx_emei == 1).all()
            c_team_f = or_(Comments.author == m.name for m in members_f)
            cmts = cmts.filter(c_team_f)
            h_team_f = or_(Histories.author == m.name for m in members_f)
            changes = changes.filter(h_team_f)

        cmts = cmts.order_by(Comments.date).all()
        changes = changes.order_by(Histories.date).all()

        # draw a graph
        draw_cmts = {}
        draw_changes = {}
        ## if choice == sprint: draw figure about people and numbers
        if choice=='sprint':
            # collect data of comments
            if len(cmts):
                for cmt in cmts:
                    people_cmt=cmt.author
                    if people_cmt not in draw_cmts:
                        draw_cmts[people_cmt]=1
                    else:
                        draw_cmts[people_cmt] = 1+draw_cmts[people_cmt]
            else:
                draw_cmts={'no data':0}
            # collect data of changes
            if len(changes):
                for change in changes:
                    people_change = change.author
                    if people_change not in draw_changes:
                        draw_changes[people_change]=1
                    else:
                        draw_changes[people_change] = 1+draw_changes[people_change]
            else:
                draw_changes={'no data':0}
            # draw
            draw_fig(draw_cmts,'comment_lines',1)
            draw_fig(draw_changes,'change_lines',1)

        ## if choice == date: draw figure about sprints and numbers
        elif choice == 'date':
            all_starts = [sprint.start_date for sprint in Sprints.query.all()]
            all_ends = [sprint.end_date for sprint in Sprints.query.all()]
            start_date = min(all_starts)
            end_date = max(all_ends)
            if len(cmts):
                for cmt in cmts:
                    current_date = cmt.date.date()
                    if current_date >= start_date and current_date <= end_date:
                        current_sprint = [sprint.sprint_name for sprint in Sprints.query.all()
                                          if sprint.start_date <= current_date and sprint.end_date >= current_date][0]
                        if current_sprint in draw_cmts:
                            draw_cmts[current_sprint] = draw_cmts[current_sprint]+1
                        else:
                            draw_cmts[current_sprint] = 1
                    else:
                        continue
            else:
                draw_cmts={'no data':0}

            if len(changes):
                for change in changes:
                    current_date = change.date.date()
                    if current_date >= start_date and current_date <= end_date:
                        current_sprint = [sprint.sprint_name for sprint in Sprints.query.all()
                                          if sprint.start_date <= current_date and sprint.end_date >= current_date][0]
                        if current_sprint in draw_changes:
                            draw_changes[current_sprint] = draw_changes[current_sprint]+1
                        else:
                            draw_changes[current_sprint] = 1
                    else:
                        continue
            else:
                draw_changes={'no data':0}

            draw_fig(draw_cmts,'comment_lines')
            draw_fig(draw_changes,'change_lines')
        return render_template('comments.html', cmts=cmts, changes=changes)
    return render_template('query_sprint.html', form=form)

def draw_fig(dict_draw,name,if_bar=0):
    fig=plt.figure()
    ax = fig.add_subplot(111)
    x_label = dict_draw.keys()
    x_label = sorted(x_label)
    y_label = [dict_draw[x] for x in x_label]
    # Draw histogram
    if if_bar:
        ax.bar(x_label,y_label)
    # Draw line chart
    else:
        ax.plot(x_label,y_label)
    # Rotary font
    for x in ax.get_xticklabels():
        x.set_rotation(45)
    # Show numbers in figs
    for a,b in zip(x_label,y_label):
        plt.text(a,b,b)
    # plt.xticks(fontsize=5)
    save_name = './static/'+name
    plt.tight_layout()
    plt.savefig(save_name)
    fig.clear()
    plt.close()
    return

def which_sprint(current_date):
    current_sprint_name = [sprint.sprint_name for sprint in Sprints.query.all()
                           if sprint.start_date <= current_date and sprint.end_date >= current_date][0]
    return current_sprint_name

# page to show current sprint results
@app.route('/current_sprint', methods=['GET', 'POST'])
def current_sprint():
    # get current sprint
    current_date = datetime.datetime.now().date()
    try:
        current_sprint_name = which_sprint(current_date)
    except Exception as e:
        flash('%s' % e.message)
        return render_template('error.html')

    # query from DB
    # team_data = TeamData.query.filter(TeamData.sprint == current_sprint_name).all()
    # if not team_data:
    #     flash('DB don\'t have %s sprint, please run crawl.py to get data' % current_sprint_name)
    #     return render_template('error.html')

    CA = dict()
    CA['xsx_emei'] = TeamData.query.filter(TeamData.sprint == current_sprint_name)\
                                  .filter(TeamData.team_name == 'xsx-emei') \
                                  .filter(TeamData.project == 'CA').first()
    CA['xsx_shaolin'] = TeamData.query.filter(TeamData.sprint == current_sprint_name)\
                                      .filter(TeamData.team_name == 'xsx-shaolin') \
                                      .filter(TeamData.project == 'CA').first()
    CA['xsx_wudang'] = TeamData.query.filter(TeamData.sprint == current_sprint_name)\
                                      .filter(TeamData.team_name == 'xsx-wudang') \
                                      .filter(TeamData.project == 'CA').first()
    CA['xs_nanjing'] = TeamData.query.filter(TeamData.sprint == current_sprint_name) \
                                     .filter(TeamData.team_name == 'xs-nanjing') \
                                     .filter(TeamData.project == 'CA').first()

    CP = dict()
    CP['xsx_emei'] = TeamData.query.filter(TeamData.sprint == current_sprint_name) \
        .filter(TeamData.team_name == 'xsx-emei') \
        .filter(TeamData.project == 'CP').first()
    CP['xsx_shaolin'] = TeamData.query.filter(TeamData.sprint == current_sprint_name) \
        .filter(TeamData.team_name == 'xsx-shaolin') \
        .filter(TeamData.project == 'CP').first()
    CP['xsx_wudang'] = TeamData.query.filter(TeamData.sprint == current_sprint_name) \
        .filter(TeamData.team_name == 'xsx-wudang') \
        .filter(TeamData.project == 'CP').first()
    CP['xs_nanjing'] = TeamData.query.filter(TeamData.sprint == current_sprint_name) \
        .filter(TeamData.team_name == 'xs-nanjing') \
        .filter(TeamData.project == 'CP').first()

    # query historical details by member
    member_list = Members.query.all()
    form = SolvedNumQueryForm(member_list)
    current_date = datetime.datetime.now().date()
    all_sprints = [sprint.sprint_name for sprint in Sprints.query.all() if sprint.start_date <= current_date]
    if request.method=='POST':
        member_name = request.form.get('member_name')
        member_tickets = Tickets.query.filter(and_(Tickets.assignee==member_name ,Tickets.status=='Done'))
        draw_member_solved={}
        draw_member_solved = draw_member_solved.fromkeys(all_sprints,0)
        show_ticket={}
        show_ticket=show_ticket.fromkeys(all_sprints,'')
        for member_ticket in member_tickets:
            solved_time = member_ticket.solved_time
            sprint = which_sprint(solved_time)
            if sprint <= all_sprints[0] and sprint >= all_sprints[-1]:
                draw_member_solved[sprint] = draw_member_solved[sprint] + 1
                show_ticket[sprint]=show_ticket[sprint]+member_ticket.ticket_id+','
        if not draw_member_solved:
            draw_member_solved['no data']=0
        draw_fig(draw_member_solved,member_name)
        draw_sprint = draw_member_solved.keys()
        draw_sprint=sorted(draw_sprint)
        draw_solved_num = [draw_member_solved[i] for i in draw_sprint]
        show_ticket = [show_ticket[i] for i in draw_sprint]
        for i in range(len(show_ticket)):
            tick = show_ticket[i]
            show_ticket[i]=tick.strip(',')
        return render_template('member_solved.html',draw_sprint=draw_sprint,draw_solved_num=draw_solved_num,show_ticket=show_ticket,\
                               count = len(show_ticket),member_name=member_name)
    return render_template('current_sprint.html',
                           CA=CA, CP=CP,form=form)

# page to
@app.route('/current_sprint/detail/<string:team_name>')
def current_sprint_detail(team_name):
    # get current sprint
    current_date = datetime.datetime.now().date()
    try:
        current_sprint_name = [sprint.sprint_name for sprint in Sprints.query.all()
                               if sprint.start_date <= current_date and sprint.end_date >= current_date][0]
    except Exception as e:
        flash('%s' % e.message)
        return render_template('error.html')
    # nanjing team is the sum of other three team
    if team_name == 'nanjing':
        teams_filter = or_(Tickets.sprint.like('%wudang%'), Tickets.sprint.like('%shaolin%'), Tickets.sprint.like('%emei%'))
        tickets = Tickets.query.filter(Tickets.sprint.like('%%%s%%' % current_sprint_name)) \
            .filter(teams_filter).filter(or_(Tickets.ticket_id.like('CP'),Tickets.ticket_id.like('CA'))).order_by(Tickets.assignee).all()
    else:
        tickets = Tickets.query.filter(Tickets.sprint.like('%%%s%%' % current_sprint_name)) \
                           .filter(Tickets.sprint.like('%%%s%%' % team_name)).filter(or_(Tickets.ticket_id.like('CP'),Tickets.ticket_id.like('CA'))).\
                            order_by(Tickets.assignee).all()
    # statistical
    r_tickets = dict()
    total = {'name': 'Total', 'Resolved_num': 0, 'Resolved_sp': 0,
                              'UnResolved_num': 0, 'UnResolved_sp': 0,
                              'Ratio': 0}
    for ticket in tickets:
        if not r_tickets.get(ticket.assignee):
            r_tickets[ticket.assignee] = {'name': ticket.assignee,
                                          'Resolved': '', 'Resolved_num': 0, 'Resolved_sp': 0,
                                          'UnResolved': '', 'UnResolved_num': 0, 'UnResolved_sp': 0,
                                          'Ratio': 0}
        if ticket.status == 'Done':
            r_tickets[ticket.assignee]['Resolved'] += ticket.ticket_id + ','
            r_tickets[ticket.assignee]['Resolved_num'] += 1
            r_tickets[ticket.assignee]['Resolved_sp'] += ticket.story_point
            total['Resolved_num'] += 1
            total['Resolved_sp'] += ticket.story_point
        else:
            r_tickets[ticket.assignee]['UnResolved'] += ticket.ticket_id + ','
            r_tickets[ticket.assignee]['UnResolved_num'] += 1
            r_tickets[ticket.assignee]['UnResolved_sp'] += ticket.story_point
            total['UnResolved_num'] += 1
            total['UnResolved_sp'] += ticket.story_point

        sum_sp = r_tickets[ticket.assignee]['Resolved_sp'] + r_tickets[ticket.assignee]['UnResolved_sp']
        r_tickets[ticket.assignee]['Ratio'] = '%1.2f' % (r_tickets[ticket.assignee]['Resolved_sp'] / sum_sp) \
                                              if sum_sp else 'Nan'
    total['Ratio'] = '%1.2f' % (total['Resolved_sp'] / (total['Resolved_sp'] + total['UnResolved_sp'])) \
                     if (total['Resolved_sp'] + total['UnResolved_sp']) else 'Nan'


    # draw a graph to show last five sprint's data
    ana_ca_tickets = TeamData.query.filter(TeamData.team_name.like('%%%s%%' % team_name))\
                                   .filter(TeamData.project == 'CA').order_by(TeamData.sprint.asc()).all()
    draw_CA = {}
    for ticket in ana_ca_tickets:
        draw_CA.setdefault(ticket.sprint,ticket.resolved_num)
    save_name='CA_'+team_name
    draw_fig(draw_CA,save_name)

    ana_cp_tickets = TeamData.query.filter(TeamData.team_name.like('%%%s%%' % team_name)) \
                                   .filter(TeamData.project == 'CP').order_by(TeamData.sprint.asc()).all()
    draw_CP = {}
    for ticket in ana_cp_tickets:
        draw_CP.setdefault(ticket.sprint, ticket.resolved_num)
    save_name = 'CP_' + team_name
    draw_fig(draw_CP, save_name)
    return render_template('sprint_detail.html',
                           team=team_name, r_tickets=r_tickets, total=total, _val=time.time())


# page to show all ticket key and link by project and team
@app.route('/current_sprint/team/<string:project>/<string:team_name>')
def current_sprint_team(project, team_name):
    current_date = datetime.datetime.now().date()
    try:
        current_sprint_name = [sprint.sprint_name for sprint in Sprints.query.all()
                               if sprint.start_date <= current_date and sprint.end_date >= current_date][0]
    except Exception as e:
        flash('%s' % e.message)
        return render_template('error.html')
    team = TeamData.query.filter(TeamData.sprint == current_sprint_name)\
                         .filter(TeamData.team_name == team_name)\
                         .filter(TeamData.project == project).first()
    resolved_qa = ''
    resolved_dev = ''
    unresolved_qa = ''
    unresolved_dev = ''
    resolved_qa_link = ''
    resolved_dev_link = ''
    unresolved_qa_link = ''
    unresolved_dev_link = ''
    if team.resolved_qa:
        resolved_qa = team.resolved_qa.strip(';').split(';')
        resolved_qa_link = ','.join(resolved_qa)
    if team.resolved_dev:
        resolved_dev = team.resolved_dev.strip(';').split(';')
        resolved_dev_link = ','.join(resolved_dev)
    if team.unresolved_qa:
        unresolved_qa = team.unresolved_qa.strip(';').split(';')
        unresolved_qa_link = ','.join(unresolved_qa)
    if team.unresolved_dev:
        unresolved_dev = team.unresolved_dev.strip(';').split(';')
        unresolved_dev_link = ','.join(unresolved_dev)
    return render_template('current_sprint_team.html',
                           resolved_qa=resolved_qa,
                           resolved_qa_link=resolved_qa_link,
                           resolved_dev=resolved_dev,
                           resolved_dev_link=resolved_dev_link,
                           unresolved_qa=unresolved_qa,
                           unresolved_qa_link=unresolved_qa_link,
                           unresolved_dev=unresolved_dev,
                           unresolved_dev_link=unresolved_dev_link)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
