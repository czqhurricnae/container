# -*- coding:utf-8 -*-
from flask import url_for
from jieba.analyse import ChineseAnalyzer
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from datetime import datetime
from .. import db
from ..aliyun import OSSFileAdmin


class TimesheetTable(db.Model):

    __tablename__ = u'timesheet_table'

    __searchable__ = [u'name', 'task']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64), nullable=False)
    NO = db.Column(db.Integer, nullable=False)
    task = db.Column(db.UnicodeText(64), nullable=False)
    taskTime = db.Column(db.Float, default=1)
    type = db.Column(db.Enum(u'例行', u'非例行', u'车间杂项', u'排故'),
                     nullable=False,
                     default=u'例行')
    approved = db.Column(db.Enum(u'是', u'否'), nullable=False, default=u'否')

    def __init__(self, name, NO, task, taskTime, type, approved):
        self.name = name
        self.NO = NO
        self.task = task
        self.taskTime = taskTime
        self.type = type
        self.approved = approved

    def __repr__(self):
        return u'<TimesheetTable{0:s: [1:s, 2:s]}>'.format(
            self.name, self.task, self.taskTime)


class TimesheetTableModelView(ModelView):

    edit_modal = True

    column_editable_list = ('task', 'taskTime', 'type', 'approved')

    column_searchable_list = ('name', 'task', 'approved')

    column_sortable_list = ('task', )

    column_labels = dict(name=u'工作者',
                         NO=u'工号',
                         task=u'工作名称',
                         taskTime=u'工时',
                         type=u'工作类别',
                         approved=u'是否审核')

    def scaffold_form(self):
        form_class = super(TimesheetTableModelView, self).scaffold_form()
        return form_class

    def create_model(self, form):
        model = self.model(form.name.data, form.NO.data, form.task.data,
                           form.taskTime.data, form.type.data,
                           form.approved.data)
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()
