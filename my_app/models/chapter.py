# -*- coding: utf-8 -*-
from flask_admin.contrib.sqla import ModelView
from .. import db


class Chapter(db.Model):

    __tablename__ = 'chapter'

    __searchable__ = ['model', 'chapter_section_number']

    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.UnicodeText(64), nullable=False)
    chapter_section_number = db.Column(db.UnicodeText(64), nullable=False)
    english_description = db.Column(db.UnicodeText(64), nullable=False)
    chinese_description = db.Column(db.UnicodeText(64), nullable=False)
    belongto_chapter = db.Column(db.UnicodeText(64), nullable=False)
    chapter_description = db.Column(db.UnicodeText(64), nullable=False)

    def __init__(self, model, chapter_section_number, english_description,
                 chinese_description, belongto_chapter, chapter_description):
        self.model = model
        self.chapter_section_number = chapter_section_number
        self.english_description = english_description
        self.chinese_description = chinese_description
        self.belongto_chapter = belongto_chapter
        self.chapter_description = chinese_description

    def __repr__(self):
        return '<Chapter {0}: {1}>'.format(self.model,
                                           self.chinese_description)


class ChapterModelView(ModelView):

    edit_model = True

    column_editable_list = ('model', 'chapter_section_number',
                            'belongto_chapter')

    column_labels = dict(model=u'机型',
                         chapter_section_number=u'章节号',
                         english_description=u'英文说明',
                         chinese_description=u'中文说明',
                         belongto_chapter=u'所属章节',
                         chapter_description=u'章号说明')

    def scaffold_form(self):
        form_class = super(ChapterModelView, self).scaffold_form()
        return form_class

    def create_model(self, form):
        model = self.model(form.model.data, form.chapter_section_number.data,
                           form.english_description.data,
                           form.chinese_description.data,
                           form.belongto_chapter.data,
                           form.chapter_description.data)
        form.populate_obj(model)
        self.session.add(model)
        self._on_model_change(form, model, True)
        self.session.commit()
