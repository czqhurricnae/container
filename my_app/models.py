# -*- coding:utf-8 -*-
from my_app import db
from jieba.analyse import ChineseAnalyzer
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from aliyun import OSSFileAdmin
from datetime import datetime


class Tool(db.Model):
    __tablename__ = u'tools'
    __searchable__ = [u'project_title']
    __analyzer__ = ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True)
    project_title = db.Column(db.UnicodeText(64))
    name = db.Column(db.UnicodeText(64))
    size = db.Column(db.UnicodeText(64))
    number = db.Column(db.Integer, default=1)
    description = db.Column(db.UnicodeText(64))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))

    def __repr__(self):
        return u'<Tool {0:s}>'.format(self.name)

    @property
    def to_json(self):
        return u"<tr><th><span class='glyphicon glyphicon-wrench' aria-hidden='true'>" \
               u"</span></th><th>{0}</th><th>{1}</th><th>{2}</th><th>{3}</th></tr>"\
            .format(self.name, self.size, self.number, self.description)


class Project(db.Model):
    __tablename__ = u'projects'
    __searchable__ = [u'title']
    __analyzer__ = ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True)
    """
    title = db.Column(db.VARCHAR(255), unique=True)
    """
    title = db.Column(db.UnicodeText(256))
    model = db.Column(db.UnicodeText(64))
    chapter = db.Column(db.UnicodeText(64))
    date = db.Column(db.DATE, default=datetime.now)
    the_tools = db.relationship(u'Tool', backref=u'belong', lazy=u'dynamic')
    the_advises = db.relationship(
        u'Advise',
        backref=u'improve',
        lazy=u'dynamic')

    def __init__(self, title, model, chapter, date):
        self.title = title
        self.model = model
        self.chapter = chapter
        self.date = date

    def __repr__(self):
        return u'项目:%s, 机型:%s, 章节:%s, 时间:%s' % (
            self.title, self.model, self.chapter, self.date)


class Document(db.Model):
    __tablename__ = u'documents'
    __searchable__ = [u'search_column']
    __analyzer__ = ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True)
    """
    title = db.Column(db.UnicodeText(64))
    path = db.Column(db.UnicodeText(256))
    """
    title = db.Column(db.UnicodeText(256))
    path = db.Column(db.UnicodeText(256))
    search_column = db.Column(db.UnicodeText(256))
    office = db.Column(db.UnicodeText(64))
    model = db.Column(db.UnicodeText(64))
    chapter = db.Column(db.UnicodeText(64))
    date = db.Column(db.UnicodeText(64))

    @property
    def get_url(self):
        filesystem = OSSFileAdmin(
            access_key='2zdr2JCTOpn9viiK',
            secret_key='2EnOtEoK90ycVpmjUn4BHVYYy5zmzx',
            bucket_name='filessystem',
            endpoint='http://oss-cn-shanghai.aliyuncs.com')
        return filesystem.storage.generate_url(
            file_path=self.path, expires=5 * 60)


class Advise(db.Model):
    __tablename__ = u'advises'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText(64))
    advise = db.Column(db.UnicodeText(256))
    date = db.Column(db.DATE, default=datetime.now)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))


    def __init__(self, name, advise, project_id):
        self.name = name
        self.advise = advise
        self.project_id = project_id


    def __repr__(self):
        return u'<Advise 关于{0:s}的一些建议>'.format(self.improve.title)


class ProjectModelView(ModelView):
    inline_models = [
        (Tool, dict(
            form_label=u'工具清单')), (Advise, dict(
                form_label=u"Advise"))]
    column_searchable_list = ('title',)
    column_labels = dict(
        title=u'拆装项目',
        model=u'机型',
        chapter=u'章节号',
        date=u'更新日期')
    """
    column_descriptions = dict(the_tools = u'点击",Add Tool = "按钮,添加工具清单')
    对于描述数据库模型关系的字段(如'the_tools','project_id')使用`column_descriptions`
    进行内容填写的说明是不起作用的
    """

    def scaffold_form(self):
        form_class = super(ProjectModelView, self).scaffold_form()
        return form_class

    def create_model(self, form):
        model = self.model(
            form.title.data,
            form.model.data,
            form.chapter.data,
            form.date.data,
        )
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()


class ToolModelView(ModelView):
    form_rules = [
        rules.FieldSet((), u'工具详情'),
        rules.Field(u'project_title'),
        rules.Field(u'size'),
        rules.Field(u'name'),
        rules.Field(u'description'),
        rules.Field(u'number'),
        rules.Header(u'校验'),
        rules.Field(u'belong'),
    ]
    column_searchable_list = ('project_title',)
    column_sortable_list = ('project_title', 'name')
    column_labels = dict(
        project_title=u'项目',
        name=u'名称',
        size=u'尺寸',
        number=u'数量',
        description=u'备注',
        Belong=u'校验')
    column_descriptions = dict(
        project_title=u'工具所用于的拆装项目,请保证"Belong"列的内容与项目名一致(例如"737更换滑行灯工具"对应"<"Object 737更换滑行灯工具">"),保证录入工具和拆装项目匹配',
        number=u'若不填,系统默认为1',
        name=u'工具的名称',
        size=u'工具的大小或者尺寸')


class DocumentModelView(ModelView):
    form_rules = [
        rules.FieldSet((), u'文档详情'),
        rules.Field(u'title'),
        rules.Field(u'path'),
        rules.Field(u'search_column'),
        rules.Field(u'office'),
        rules.Field(u'model'),
        rules.Field(u'chapter'),
        rules.Field(u'date'),
    ]
    column_searchable_list = (
        'title',
        'path',
        'office',
        'model',
        'chapter',
        'date')
    column_sortable_list = (
        'title',
        'path',
        'office',
        'model',
        'chapter',
        'date')
    column_labels = dict(
        title=u'文档名称',
        path=u'存放路径',
        search_column=u'搜索路径',
        office=u'处室',
        model=u'机型',
        chapter=u'章节号',
        date=u'日期',
    )
    column_descriptions = dict(
        search_column=u'用于程序搜索文档使用,无参考意义',
    )
