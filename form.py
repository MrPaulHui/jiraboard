#!/usr/bin/python3

from flask_wtf import FlaskForm as Form
from wtforms import StringField, SubmitField, RadioField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired

class NameForm(Form):
    filter_id = StringField('Filter Id', validators=[DataRequired()])
    submit = SubmitField('Submit')


class ConfigForm(Form):
    sprint = SelectField('choose a sprint to modify')
    submit = SubmitField('modify')
    team = SelectField('choose a team to modify')
    submit2 = SubmitField('modify')

    def __init__(self, sprints_list, teams_list):
        super(Form, self).__init__()
        self.sprint.choices = [(sprint.id, str(sprint.sprint_name))
                               for sprint in sprints_list]
        self.team.choices = [(team.id, str(team.team_name)) for team in teams_list]



class QueryForm(Form):
    choice = RadioField('choice', choices=[('sprint', 'Choice a sprint: '),
                                           ('date', 'Enter start date and end date:  eg.(yyyy/mm/dd)')])
    sprint = SelectField('Select a sprint')
    start_date = StringField('Enter a start date (yyyy/mm/dd)')
    end_date = StringField('Enter a end date (yyyy/mm/dd)')
    team_or_member = SelectField('Select a team or member')
    type = StringField('Enter the project(s)  eg.(CA, CP)')
    submit = SubmitField('Query')

    def __init__(self, sprints_list, teams_list, members_list):
        super(Form, self).__init__()
        self.sprint.choices = [(sprint.id, str(sprint.sprint_name))
                               for sprint in sprints_list]
        self.team_or_member.choices = [(team.id, str(team.team_name)) for team in teams_list] + \
                                      [(member.id + 4, member.name) for member in members_list]

class SolvedNumQueryForm(Form):
    member_name = SelectField('Select a member')
    submit = SubmitField('Query')

    def __init__(self,members):
        super(Form, self).__init__()
        self.member_name.choices=[member.name for member in members]

class CodeQueryForm(Form):
    author = SelectField('Select a author:')
    start_date = StringField('Enter a start date (yyyy/mm/dd)')
    end_date = StringField('Enter a end date (yyyy/mm/dd)')
    submit = SubmitField('Query')

    def __init__(self, members_list):
        super(Form, self).__init__()
        self.author.choices = [(0, 'All')] + \
                              [(member.id, member.name) for member in members_list]


class SprintForm(Form):
    sprint_name = StringField('sprint_name')
    start_date = StringField('start_date')
    end_date = StringField('end_date')
    submit = SubmitField('Save')

    def __init__(self, session):
        super(Form, self).__init__()
        self.sprint_name.data = session['sprint_name']
        self.start_date.data = session['sprint_start_date']
        self.end_date.data = session['sprint_end_date']


class TeamForm(Form):
    members = SelectMultipleField('Add the member to the team: ')
    submit = SubmitField('Add')

    def __init__(self, members):
        super(Form, self).__init__()
        self.members.choices = [(member.id, member.name)
                                for member in members]
