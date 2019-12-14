# -*- coding:utf-8 -*-
from flask import url_for
from jieba.analyse import ChineseAnalyzer
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from datetime import datetime
from .. import db
from ..aliyun import OSSFileAdmin


class Department(db.Model):

    __tablename__ = u'departments'

    __searchable__ = [u'name']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64))
    the_workshops = db.relationship(u'Workshop',
                                    backref=u'belongto_department',
                                    lazy=u'dynamic')
    the_teams = db.relationship(u'Team',
                                backref=u'belongto_department',
                                lazy=u'dynamic')
    the_workers = db.relationship(u'Worker',
                                  backref=u'belongto_department',
                                  lazy=u'dynamic')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return u'<Department {0!s}>'.format(self.name)


class Workshop(db.Model):

    __tablename__ = u'workshops'

    __searchable__ = [u'name']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    the_teams = db.relationship(u'Team',
                                backref=u'belongto_workshop',
                                lazy=u'dynamic')
    the_workers = db.relationship(u'Worker',
                                  backref=u'belongto_workshop',
                                  lazy=u'dynamic')

    def __repr__(self):
        return u'<Workshop {0!s}>'.format(self.name)


class Team(db.Model):

    __tablename__ = u'teams'

    __searchable__ = [u'name']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    Workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.id'))
    the_workers = db.relationship(u'Worker',
                                  backref=u'belongto_team',
                                  lazy=u'dynamic')

    def __repr__(self):
        return u'<Team {0!s}>'.format(self.name)


class Worker(db.Model):

    __tablename__ = u'workers'

    __searchable__ = [u'name']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64), nullable=False)
    number = db.Column(db.Integer, nullable=True)
    openId = db.Column(db.UnicodeText, nullable=True)
    major = db.Column(db.Enum(u'机械', u'电子', u'结构', u'电气'),
                      nullable=True,
                      default=u'机械')
    post = db.Column(db.Enum(u'经理', u'高级主管领班', u'高级领班', u'领班', u'技师', u'维修员',
                             u'新员'),
                     nullable=True,
                     default=u'维修员')
    authority = db.Column(db.Enum(u'管理者', u'普通用户'),
                          nullable=True,
                          default=u'普通用户')
    department_id = db.Column(db.Integer,
                              db.ForeignKey('departments.id'),
                              nullable=True)
    Workshop_id = db.Column(db.Integer,
                            db.ForeignKey('workshops.id'),
                            nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)

    def __init__(self, name, number, openId, major, post, authority,
                 belongto_department, belongto_workshop, belongto_team):
        self.name = name
        self.number = number
        self.openId = openId
        self.major = major
        self.post = post
        self.authority = authority
        self.belongto_department = belongto_department
        self.belongto_workshop = belongto_workshop
        self.belongto_team = belongto_team

    def __repr__(self):
        return u'<Worker {0}: {1}>'.format(self.name, self.number)


class DepartmentModelView(ModelView):

    column_editable_list = ('name', )

    column_sortable_list = ('name', )

    column_labels = dict(name=u'处室',
                         the_workshops=u'下属车间',
                         the_teams=u'下属班组',
                         the_workers=u'下属人员')

    def scaffold_form(self):
        form_class = super(DepartmentModelView, self).scaffold_form()
        return form_class

    def create_model(self, form):
        model = self.model(form.name.data)
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()


class WorkshopModelView(ModelView):

    column_editable_list = ('name', )

    column_sortable_list = ('name', )

    column_labels = dict(name=u'车间',
                         belongto_department=u'所属处室',
                         the_teams=u'下属班组',
                         the_workers=u'下属人员')


class TeamModelView(ModelView):

    column_editable_list = ('name', )

    column_sortable_list = ('name', )

    column_labels = dict(name=u'班组',
                         belongto_workshop=u'所属车间',
                         belongto_department=u'所属处室',
                         the_workers=u'下属人员')


class WorkerModelView(ModelView):

    edit_modal = True

    column_editable_list = ('name', 'number', 'major', 'post', 'authority',
                            'belongto_department', 'belongto_workshop',
                            'belongto_team')

    column_sortable_list = ('name', 'number')

    column_labels = dict(name=u'姓名',
                         number=u'工号',
                         openId='openId',
                         major=u'专业',
                         post=u'职位',
                         authority=u'管理权限',
                         belongto_workshop=u'所属车间',
                         belongto_department=u'所属处室',
                         belongto_team=u'所属班组')

    def scaffold_form(self):
        form_class = super(WorkerModelView, self).scaffold_form()
        return form_class

    def create_model(self, form):
        model = self.model(form.name.data, form.number.data, form.openId.data,
                           form.major.data, form.post.data,
                           form.authority.data, form.belongto_department.data,
                           form.belongto_workshop.data,
                           form.belongto_team.data)
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()
