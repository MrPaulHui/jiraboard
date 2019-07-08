#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
import datetime
from webpage import db, Sprints,Members,Teams,TicketTypes,RepoTypes
db.create_all()

app = Flask(__name__)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.config['SECRET_KEY'] = 'xs-nanjing'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:xenroot@localhost:3306/xsnkgperf'
app.config['SQLALCHEMY_COMMIT_ON_TEADOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
CSRFProtect(app)
db = SQLAlchemy(app)

def init_teams():
    id=1
    team1=Teams(id,'xs-nanjing');id=id+1
    team2=Teams(id,'xsx-shaolin');id=id+1
    team3=Teams(id,'xsx-wudang');id=id+1
    team4=Teams(id,'xsx-emei')
    db.session.add(team1)
    db.session.add(team2)
    db.session.add(team3)
    db.session.add(team4)
    db.session.commit()


def init_sprint():
    id=1
    sprint_num=52
    start_time= datetime.date(2018, 12, 12)
    end_time=datetime.date(2018,12,26)

    while(end_time.year==2018):
        if sprint_num<2:
            sprint_num=52
        
        year='18S'

        if sprint_num<10:
            sprint_name=year+str(0)+str(sprint_num)
        else:
            sprint_name=year+str(sprint_num)

        sprint=Sprints(id=id,sprint_name=sprint_name,start_date=start_time,end_date=end_time)
        db.session.add(sprint)
        db.session.commit()

        id=id+1
        sprint_num=sprint_num-2
        start_time=start_time-datetime.timedelta(14)
        end_time=end_time-datetime.timedelta(14)

def init_members():
    file=open('members.txt')
    for line in file:
        member_info=line.strip('\n').split(',')
        id=int(member_info[0])
        name=member_info[1]
        is_nanjing=int(member_info[2])
        is_emei=int(member_info[3])
        is_wudang=int(member_info[4])
        is_shaolin=int(member_info[5])
        member=Members(id,name,is_nanjing,is_emei,is_wudang,is_shaolin)
        db.session.add(member)
        db.session.commit()

def init_ticket_types():
    id=1
    type1=TicketTypes(id,'CA',1);id=id+1
    type2=TicketTypes(id,'CP',1);id=id+1
    type3=TicketTypes(id,'SCTX',0);id=id+1
    type4=TicketTypes(id,'REQ',0);id=id+1
    type5=TicketTypes(id,'XSI',0);id=id+1
    type6=TicketTypes(id,'XOP',0);id=id+1
    type7=TicketTypes(id,'HFX',0);id=id+1
    type8=TicketTypes(id,'HFP',0);id=id+1
    type9=TicketTypes(id,'UPD',0);
    db.session.add(type1)
    db.session.add(type2)
    db.session.add(type3)
    db.session.add(type4)
    db.session.add(type5)
    db.session.add(type6)
    db.session.add(type7)
    db.session.add(type8)
    db.session.add(type9)
    db.session.commit()

def init_repo_types():
    id=1
    type1=RepoTypes(id,'XSC',1);id=id+1
    type2=RepoTypes(id,'XRT',1);id=id+1
    type3 = RepoTypes(id, 'XSD', 1);id = id + 1
    type4 = RepoTypes(id, 'XSHCL', 1);id = id + 1
    type5 = RepoTypes(id, 'XS', 1);id = id + 1
    type6 = RepoTypes(id, 'XSU', 1);
    db.session.add(type1)
    db.session.add(type2)
    db.session.add(type3)
    db.session.add(type4)
    db.session.add(type5)
    db.session.add(type6)
    
    db.session.commit()

def main():
    init_repo_types()
    init_ticket_types()
    init_teams()
    init_sprint()
    init_members()

if __name__ == '__main__':
    main()

