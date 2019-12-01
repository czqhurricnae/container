# -*- coding:utf-8 -*-
from flask import url_for
from jieba.analyse import ChineseAnalyzer
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from datetime import datetime
from .. import db
from ..aliyun import OSSFileAdmin


class Timesheet(db.Model):

    __tablename__ = u'timesheet'

    __searchable__ = [u'title']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.UnicodeText(64), nullable=False)
    time = db.Column(db.Float, default=1)
    type = db.Column(db.Enum(u'例行', u'非例行', u'车间杂项', u'排故'), nullable=False)

    def __init__(self, title, time, type):
        self.title = title
        self.time = time
        self.type = type

    def __repr__(self):
        return u'<Timesheet{0:s: 1:s}>'.format(self.title, self.time)


class TimesheetModelView(ModelView):

    edit_modal = True

    column_editable_list = ('title', 'time', 'type')

    column_searchable_list = ('title', )

    column_sortable_list = ('title', )

    column_labels = dict(title=u'名称', time=u'工时', type=u'工作类别')

    def scaffold_form(self):
        form_class = super(TimesheetModelView, self).scaffold_form()
        return form_class

    def create_model(self, form):
        model = self.model(
            form.title.data,
            form.time.data,
            form.type.data,
        )
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()
