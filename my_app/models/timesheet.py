# -*- coding:utf-8 -*-
from flask import url_for, flash, redirect, request
from jieba.analyse import ChineseAnalyzer
from flask_admin import expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import BaseSQLAFilter, FilterEqual
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.helpers import get_redirect_target, flash_errors
from flask_admin.form import rules
from flask_admin.actions import action
from sqlalchemy import func
from flask_babel import gettext
from datetime import datetime
from .hierarchy import Team
from .. import db
from ..aliyun import OSSFileAdmin


class Timesheet(db.Model):

    __tablename__ = u'timesheet_table'

    __searchable__ = [u'name', 'task']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DATE, default=datetime.now)
    airplane = db.Column(db.UnicodeText(64), nullable=False)
    task = db.Column(db.UnicodeText(64), nullable=False)
    calculated_time = db.Column(db.Float, default=1)
    completed = db.Column(db.Enum(u'全部完成', u'部分完成'), default=u'全部完成')
    belongto_team = db.Column(db.UnicodeText(64),
                              nullable=False,
                              default=u'其他')
    kind = db.Column(db.Enum(u'例行', u'非例行排故', u'车间杂项', u'其他', u'勤务'),
                     nullable=False,
                     default=u'例行')
    approved = db.Column(db.Enum(u'是', u'否'), nullable=False, default=u'否')

    def __init__(self, name, number, date, airplane, task, calculated_time,
                 completed, belongto_team, kind, approved):
        self.name = name
        self.number = number
        self.date = date
        self.airplane = airplane
        self.task = task
        self.calculated_time = calculated_time
        self.completed = completed
        self.belongto_team = belongto_team
        self.kind = kind
        self.approved = approved

    def __repr__(self):
        return u'<Timesheet{0}: {1}-{2}>'.format(self.name, self.task,
                                                 self.calculated_time)


class TimesheetModelView(ModelView):

    edit_modal = True

    column_editable_list = ('task', 'calculated_time', 'kind', 'approved')

    column_searchable_list = ('name', 'task', 'approved')

    column_sortable_list = ('task', )

    column_labels = dict(name=u'工作者',
                         number=u'工号',
                         date=u'日期',
                         airplane=u'飞机',
                         task=u'工作名称',
                         calculated_time=u'工时',
                         completed=u'完成情况',
                         belongto_team=u'班组',
                         kind=u'工作类别',
                         approved=u'是否审核')

    def scaffold_form(self):
        form_class = super(TimesheetModelView, self).scaffold_form()
        return form_class

    def create_model(self, form):
        model = self.model(form.name.data, form.number.data, form.date.data,
                           form.airplane.data, form.task.data,
                           form.calculated_time.data, form.kind.data,
                           form.approved.data)
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()


def get_all_team_names():
    unique_team_names = Team.query.all()
    return [(str(team), str(team)) for team in unique_team_names]


class PendingApprovedModelView(ModelView):

    edit_modal = True

    column_editable_list = ('task', 'calculated_time', 'kind', 'approved')

    column_searchable_list = ('name', 'task', 'approved', 'belongto_team')

    column_sortable_list = ('task', )

    column_labels = dict(name=u'工作者',
                         number=u'工号',
                         date=u'日期',
                         airplane=u'飞机',
                         task=u'工作名称',
                         calculated_time=u'工时',
                         belongto_team=u'班组',
                         kind=u'工作类别',
                         approved=u'是否审核')

    column_extra_row_actions = [
        EndpointLinkRowAction(
            'off glyphicon glyphicon-check',
            'timesheet.approve_view',
        )
    ]

    def get_query(self):
        return self.session.query(
            self.model).filter(self.model.approved == u'否')

    def get_count_query(self):
        return self.session.query(
            func.count('*')).filter(Timesheet.approved == u'否')

    def get_filters(self):
        _dynamic_filters = getattr(self, 'dynamic_filters', None)
        if _dynamic_filters:
            return (super(PendingApprovedModelView, self).get_filters()
                    or []) + _dynamic_filters
        else:
            return super(PendingApprovedModelView, self).get_filters()

    @expose('/')
    def index_view(self):
        self.dynamic_filters = []
        self.dynamic_filters.extend([
            FilterEqual(column=Timesheet.belongto_team,
                        name=u'班组',
                        options=get_all_team_names),
            # Add further dynamic filters here
        ])
        self._refresh_filters_cache()
        return super(PendingApprovedModelView, self).index_view()

    @expose('/approve/', methods=('GET', ))
    def approve_view(self):
        """
            Approve user model view. Only GET method is allowed.
        """
        return_url = get_redirect_target() or self.get_url(
            'timesheet.details_view')

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
        return redirect(return_url)

    @action('approve', u'审核', u'你确定要将所选择的项目设置为已审核?')
    def action_approve(self, ids):
        redirect_response = redirect(url_for('timesheet.index_view'))
        try:
            query = Timesheet.query.filter(Timesheet.id.in_(ids))

            count = 0
            for timesheet in query.all():
                if timesheet.approved == u'是':
                    pass
                else:
                    timesheet.approved = u'是'
                    count += 1
            db.session.commit()
            flash(u'审核 {} 个工时成功.'.format(count), 'success')
            return redirect_response
        except Exception as e:
            if not self.handle_view_exception(e):
                raise
            flash(u'审核失败:{}'.format(str(e)), 'error')


class ApprovedTimesheetView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index_view(self):
        return self.render('admin/model/approved_timesheets_list.html',
                           title=u'已核工时查看',
                           API='/api/approvedTimesheets')
