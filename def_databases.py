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
from config_database import *

app = Flask(__name__)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.config['SECRET_KEY'] = 'xs-nanjing'
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{passwd}@localhost:3306/{database_name}?charset=utf8mb4'
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
    id = db.Column(db.Integer, primary_key = True)
    ticket_id = db.Column(db.Text)
    sprint = db.Column(db.Text)
    assignee = db.Column(db.Text)
    created_time = db.Column(db.DATE)
    solved_time = db.Column(db.DATE)
    story_point = db.Column(db.FLOAT)
    team = db.Column(db.Text)
    status = db.Column(db.Text)
    assignee = db.Column(db.Text)
    Type = db.Column(db.Text)
    priority = db.Column(db.Text)
    qrf = db.Column(db.FLOAT)
    release = db.Column(db.Text)
    component = db.Column(db.Text)
    affect_version = db.Column(db.Text)

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
    #repo_type_name = db.Column(db.String(10), unique=False)
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

class Score(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    ticket_id = db.Column(db.Text)
    assignee = db.Column(db.Text)
    created_time = db.Column(db.DATE)
    solved_time = db.Column(db.DATE)
    duration = db.Column(db.Integer)
    story_point = db.Column(db.FLOAT)
    #team = db.Column(db.Text)
    #status = db.Column(db.Text)
    Type = db.Column(db.Text)
    priority = db.Column(db.Text)
    qrf = db.Column(db.FLOAT)
    release = db.Column(db.Text)
    component = db.Column(db.Text)
    affect_version = db.Column(db.Text)
    line = db.Column(db.Integer)
    comment_number = db.Column(db.Integer)
    score_result = db.Column(db.FLOAT)
