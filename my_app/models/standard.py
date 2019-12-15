# -*- coding:utf-8 -*-
from flask import url_for, redirect, request, flash
from jieba.analyse import ChineseAnalyzer
from flask_admin import expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from flask_admin.actions import action
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json
from .. import db
from ..aliyun import OSSFileAdmin


class StandardTime(db.Model):

    __tablename__ = u'standard_time'

    __searchable__ = [u'title']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.UnicodeText(64), nullable=False)
    tasktime = db.Column(db.Float, default=1.0)
    kind = db.Column(db.Enum(u'例行', u'非例行排故', u'车间杂项', u'其他', u'勤务'),
                     nullable=False)
    airplane_type = db.Column(db.Enum('737', '787', '7M8', '757', u'通用'),
                              default='737')
    worker_number = db.Column(db.Integer, default=1)
    description = db.Column(db.UnicodeText(), nullable=True)

    def __init__(self, title, tasktime, kind, airplane_type, worker_number,
                 description):
        self.title = title
        self.tasktime = tasktime
        self.kind = kind
        self.airplane_type = airplane_type
        self.worker_number = worker_number
        self.description = description

    def __repr__(self):
        return u'<StandardTime{0}: {1}>'.format(self.title, self.tasktime)


class StandardTimeModelView(ModelView):

    list_template = 'admin/model/CSV_import_list.html'

    edit_modal = True

    column_editable_list = ('title', 'tasktime', 'kind')

    column_searchable_list = ('title', )

    column_sortable_list = ('title', )

    column_labels = dict(title=u'工作项目',
                         tasktime=u'标准工作量',
                         kind=u'工作类别',
                         airplane_type=u'机型',
                         worker_number=u'标准人数',
                         description=u'说明')

    def scaffold_form(self):
        form_class = super(StandardTimeModelView, self).scaffold_form()
        return form_class

    def create_model(self, form):
        model = self.model(form.title.data, form.tasktime.data, form.kind.data,
                           form.airplane_type.data, form.worker_number.data,
                           form.description.data)
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()

    @action('export', u'导出')
    def action_export(self, ids):
        try:
            items = StandardTime.query.all()

            if items:
                items = [{
                    'title': item.title,
                    'tasktime': item.tasktime,
                    'kind': item.kind,
                    'airplane_type': item.airplane_type,
                    'worker_number': item.worker_number,
                    'description': item.description
                } for item in items]

                return (json.dumps(items, indent=4), 200, {
                    'Content-type':
                    'application/json',
                    'Pragma':
                    'no-cache',
                    'Cache-Control':
                    'no-cache, no-store, must-revalidate',
                    'Expires':
                    '0',
                    'Content-Disposition':
                    'attachment; filename="mymodel.json"'
                })

        except Exception as e:
            if not self.handle_view_exception(e):
                raise
            flash(u'导出失败: {}'.format(str(e)), 'error')

    @expose('/import', methods=['POST'])
    def import_csv(self):
        redirect_response = redirect(url_for('standardtime.index_view'))

        if 'file' not in request.files:
            flash(u'没有发现文件块!', 'error')
            return redirect_response

        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            flash(u'没有选择上传的文件!', 'error')
            return redirect_response

        if uploaded_file:
            try:
                items = json.loads(uploaded_file.read().decode('utf-8'))
            except (ValueError, TypeError, UnicodeDecodeError) as e:
                flash(u'无法从文件读取 json 数据!', 'error')
                return redirect_response

            standard_times = []
            for item in items:
                standard_times.append(
                    StandardTime(title=item.get('title'),
                                 tasktime=item.get('tasktime'),
                                 kind=item.get('kind'),
                                 airplane_type=item.get('airplane_type'),
                                 worker_number=item.get('worker_item'),
                                 description=item.get('description')))
            db.session.add_all(standard_times)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(u'导入数据库失败! 请检查数据或者数据库字段定义是否正确!', 'error')
        flash(u'导入数据库成功.', 'success')
        return redirect_response
