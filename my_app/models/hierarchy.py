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

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return u'<Department {0:s}>'.format(self.name)


class Workshop(db.Model):

    __tablename__ = u'workshops'

    __searchable__ = [u'name']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    the_teams = db.relationship(u'Team',
                                backref=u'belongto_workshop',
                                lazy=u'dynamic')

    def __repr__(self):
        return u'<Workshop {0:s}>'.format(self.name)


class Team(db.Model):

    __tablename__ = u'teams'

    __searchable__ = [u'name']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    Workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.id'))

    def __repr__(self):
        return u'<Team {0:s}>'.format(self.name)


class DepartmentModelView(ModelView):

    column_editable_list = ('name', 'the_workshops', 'the_teams')

    column_sortable_list = ('name', )

    column_labels = dict(name=u'处室', the_workshops=u'下属车间', the_teams=u'下属班组')

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
                         the_teams=u'下属班组')


class TeamModelView(ModelView):

    column_editable_list = ('name', )

    column_sortable_list = ('name', )

    column_labels = dict(name=u'班组',
                         belongto_workshop=u'所属车间',
                         belongto_department=u'所属处室')
