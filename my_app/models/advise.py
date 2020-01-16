# -*- coding:utf-8 -*-
from .. import db
from jieba.analyse import ChineseAnalyzer
from datetime import datetime


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
        return u'<Advise 关于{0!s}的一些建议>'.format(self.improve.title)
