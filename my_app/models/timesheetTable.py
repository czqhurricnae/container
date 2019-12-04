# -*- coding:utf-8 -*-
from flask import url_for, flash, redirect, request
from jieba.analyse import ChineseAnalyzer
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.helpers import get_redirect_target, flash_errors
from sqlalchemy import func
from flask_admin.form import rules
from flask_admin import expose
from flask_babel import gettext
from datetime import datetime
from .. import db
from ..aliyun import OSSFileAdmin


class TimesheetTable(db.Model):

    __tablename__ = u'timesheet_table'

    __searchable__ = [u'name', 'task']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DATE, default=datetime.now)
    airplane = db.Column(db.UnicodeText(64), nullable=False)
    task = db.Column(db.UnicodeText(64), nullable=False)
    tasktime = db.Column(db.Float, default=1)
    belongto_team = db.Column(db.UnicodeText(64),
                              nullable=False,
                              default=u'其他')
    kind = db.Column(db.Enum(u'例行', u'非例行', u'车间杂项', u'排故', u'其他'),
                     nullable=False,
                     default=u'例行')
    approved = db.Column(db.Enum(u'是', u'否'), nullable=False, default=u'否')

    def __init__(self, name, number, date, airplane, task, tasktime,
                 belongto_team, kind, approved):
        self.name = name
        self.number = number
        self.date = date
        self.airplane = airplane
        self.task = task
        self.tasktime = tasktime
        self.belongto_team = belongto_team
        self.kind = kind
        self.approved = approved

    def __repr__(self):
        return u'<TimesheetTable{0}: {1}-{2}>'.format(self.name, self.task,
                                                      self.tasktime)


class TimesheetTableModelView(ModelView):

    edit_modal = True

    column_editable_list = ('task', 'tasktime', 'kind', 'approved')

    column_searchable_list = ('name', 'task', 'approved')

    column_sortable_list = ('task', )

    column_labels = dict(name=u'工作者',
                         number=u'工号',
                         date=u'日期',
                         airplane=u'飞机',
                         task=u'工作名称',
                         tasktime=u'工时',
                         belongto_team=u'班组',
                         kind=u'工作类别',
                         approved=u'是否审核')

    def scaffold_form(self):
        form_class = super(TimesheetTableModelView, self).scaffold_form()
        return form_class

    def create_model(self, form):
        model = self.model(form.name.data, form.number.data, form.date.data,
                           form.airplane.data, form.task.data,
                           form.tasktime.data, form.kind.data,
                           form.approved.data)
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()


class PendingApprovedModelView(ModelView):

    edit_modal = True

    column_editable_list = ('task', 'tasktime', 'kind', 'approved')

    column_searchable_list = ('name', 'task', 'approved', 'belongto_team')

    column_sortable_list = ('task', )

    column_labels = dict(name=u'工作者',
                         number=u'工号',
                         date=u'日期',
                         airplane=u'飞机',
                         task=u'工作名称',
                         tasktime=u'工时',
                         belongto_team=u'班组',
                         kind=u'工作类别',
                         approved=u'是否审核')

    column_extra_row_actions = [
        EndpointLinkRowAction(
            'off glyphicon glyphicon-off',
            'timesheettable.approve_view',
        )
    ]

    def get_query(self):
        return self.session.query(
            self.model).filter(self.model.approved == u'否')

    def get_count_query(self):
        return self.session.query(
            func.count('*')).filter(TimesheetTable.approved == u'否')

    @expose('/approve/', methods=('GET', ))
    def approve_view(self):
        """
            Activate user model view. Only GET method is allowed.
        """
        return_url = get_redirect_target() or self.get_url('admin.index')

        id = request.args["id"]
        model = self.get_one(id)

        if model is None:
            flash(u'用户不存在', u'error')
            return redirect(return_url)

        if model.approved == u'是':
            flash(u'已经审核, 无需重复审核.', u'warning')
            return redirect(return_url)

        model.approved = u'是'
        self.session.add(model)
        self.session.commit()

        flash(u'已审核', u'success')
        # return redirect(return_url)
        return u'审核成功.'
