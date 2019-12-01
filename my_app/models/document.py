# -*- coding:utf-8 -*-
from flask import url_for
from .. import db
from jieba.analyse import ChineseAnalyzer
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from ..aliyun import OSSFileAdmin
from datetime import datetime


class Document(db.Model):

    __tablename__ = u'documents'

    __searchable__ = [u'search_column']

    __analyzer__ = ChineseAnalyzer()

    id = db.Column(db.Integer, primary_key=True)
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
        return filesystem.storage.generate_url(file_path=self.path,
                                               expires=5 * 60)


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

    column_searchable_list = ('title', 'path', 'office', 'model', 'chapter',
                              'date')

    column_sortable_list = ('title', 'path', 'office', 'model', 'chapter',
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

    column_descriptions = dict(search_column=u'用于程序搜索文档使用,无参考意义', )
