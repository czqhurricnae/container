# -*- coding:utf-8 -*-
from datetime import datetime
from operator import itemgetter
import os.path as op
import re
from flask import flash, redirect, request
import oss2
import time
from flask_admin import helpers
from flask_admin.actions import action
from flask_admin.base import expose
from flask_admin.babel import gettext, lazy_gettext
from flask_admin.contrib.fileadmin import BaseFileAdmin
from werkzeug.utils import secure_filename
from wtforms import validators
from wtforms.widgets.core import HTMLString, html_params, RadioInput
from wtforms.fields.core import StringField, SelectField, DateField
from flask_admin.form.widgets import DatePickerWidget
from wtforms import fields
import itertools


DEFAULT_CHAPTERS = (
    u'05时间与限制',
    u'06尺寸和区域',
    u'12勤务',
    u'20标准施工',
    u'21空调',
    u'22自动驾驶',
    u'23通讯',
    u'24电源',
    u'25设备与装饰',
    u'26防火',
    u'27飞行操纵',
    u'28燃油',
    u'29液压系统',
    u'30防冰防雨',
    u'31指示系统',
    u'32起落架',
    u'33灯光',
    u'34导航',
    u'35氧气系统',
    u'36引气系统',
    u'38饮用水和灰水系统',
    u'47NGS',
    u'49辅助动力装置',
    u'51结构',
    u'52门',
    u'53机身',
    u'54发动机短舱和吊架',
    u'55安定面',
    u'56窗户',
    u'57机翼',
    u'70standard practices',
    u'71飞行动力',
    u'72发动机',
    u'73发动机燃油和控制',
    u'74发动机点火',
    u'75发动机空气',
    u'76发动机控制',
    u'77发动机指示',
    u'78发动机排气',
    u'79发动机滑油',
    u'80发动机起动')

DEFAULT_MODELS = (u'737', u'757', u'787')

EXTENSIONS = {'png', 'bmp', 'jpg', 'gif', 'jpeg'}


class MyFileInput:
    """
        Renders a file input chooser field.
    """

    def __init__(self):
        pass

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        return HTMLString(
            '<input %s>' %
            html_params(
                name=field.name,
                multiple='',
                type='file',
                **kwargs))


class MyFileField(StringField):
    widget = MyFileInput()


class MySelectField(SelectField):
    pass


class MyListWidget:
    """
    Renders a list of fields as a `ul` or `ol` list.

    This is used for fields which encapsulate many inner fields as subfields.
    The widget will try to iterate the field to get access to the subfields and
    call them to render them.

    If `prefix_label` is set, the subfield's label is printed before the field,
    otherwise afterwards. The latter is useful for iterating radios or
    checkboxes.
    """

    def __init__(self, html_tag='ul', prefix_label=True):
        assert html_tag in ('ol', 'ul')
        self.html_tag = html_tag
        self.prefix_label = prefix_label

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('style', "margin: 0 0 0 0; border: 0;")
        html = ['<%s %s>' % (self.html_tag, html_params(**kwargs))]
        for subfield in field:
            if self.prefix_label:
                html.append('<li>%s %s</li>' % (subfield.label, subfield()))
            else:
                html.append(
                    '<li style = "list-style: none; float: left; display: inline-block; margin-right : 12px">%s %s</li>' %
                    (subfield(), subfield.label))
        html.append('</%s> <div style="clear:both;"></div>' % self.html_tag)
        return HTMLString(''.join(html))


class MyRadioField(SelectField):
    widget = MyListWidget(prefix_label=False)
    option_widget = RadioInput()


def get_default(aSet, seq):
    for item in itertools.ifilter(aSet.__contains__, seq):
        return item
    return None


class ALiYunStorage:

    def __init__(self, bucket_name, access_key, secret_key, endpoint):
        self.endpoint = endpoint
        self.auth = oss2.Auth(access_key, secret_key)
        self.service = oss2.Service(self.auth, self.endpoint)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, bucket_name)
        self.separator = '/'

    def get_files(self, path):
        def _strip_path(_name, _path):
            if _name.startswith(_path):
                return _name.replace(_path, '', 1)
            return _name

        def _remove_trailing_slash(_name):
            return _name[:-1]

        def _iso_to_epoch(timestamp):
            dt = time.localtime(timestamp)
            return int(time.mktime(dt))

        files = []
        directories = []
        if path and not path.endswith(self.separator):
            path += self.separator
        for obj in oss2.ObjectIterator(
                bucket=self.bucket,
                prefix=path,
                delimiter=self.separator):
            if obj.key == path:
                continue
            if obj.is_prefix():
                name = _remove_trailing_slash(_strip_path(obj.key, path))
                key_name = _remove_trailing_slash(obj.key)
                directories.append((name, key_name, True, 0, 0))
            else:
                last_modified = _iso_to_epoch(obj.last_modified)
                name = _strip_path(obj.key, path)
                files.append((name, obj.key, False, obj.size, last_modified))
        return directories + files

    def _get_bucket_list_prefix(self, path):
        parts = path.split(self.separator)
        if len(parts) == 1:
            search = ''
        else:
            search = self.separator.join(parts[:-1]) + self.separator
        return search

    def _get_path_keys(self, path):
        if path and not path.endswith(self.separator):
            path += self.separator
        return {
            obj.key for obj in oss2.ObjectIterator(
                bucket=self.bucket,
                prefix=path,
                delimiter=self.separator)}

    def is_dir(self, path):
        keys = self._get_path_keys(path)
        key_list = list(keys)
        keys_unicode = [key.decode('utf-8') for key in key_list]
        return path + self.separator in keys_unicode

    def path_exists(self, path):
        if path == '':
            return True
        path = op.dirname(path)
        keys = self._get_path_keys(path)
        key_list = list(keys)
        keys_unicode = [key.decode('utf-8') for key in key_list]
        return path in keys_unicode or (path + self.separator) in keys_unicode

    def file_exists(self, path, filename):
        path = unicode(path)
        keys = self._get_path_keys(path)
        key_list = list(keys)
        keys_unicode = [key.decode('utf-8') for key in key_list]
        return filename in keys_unicode if path == '' \
            else path + self.separator + filename in keys_unicode

    def get_base_path(self):
        return ''

    def get_breadcrumbs(self, path):
        accumulator = []
        breadcrumbs = []
        for n in path.split(self.separator):
            accumulator.append(n)
            breadcrumbs.append((n, self.separator.join(accumulator)))
        return breadcrumbs

    def send_file(self, file_path):
        return redirect(
            self.bucket.sign_url(
                method='GET',
                key=file_path,
                expires=60))

    def save_file(self, path, file_data):
        """
            :param path:
            :param file_data:
            :return:
        """
        i = path.find('/')
        """
            若在根目录上传文件'1.txt',这时path = '/1.txt',会产生错误
            i == 0 说明是'/'开头,这时将开头的'/'去除
        """
        if i == 0:
            path = path.strip('/')
        self.bucket.put_object(key=path, data=file_data.stream)

    def delete_tree(self, directory):
        self._check_empty_directory(directory)
        self.bucket.delete_object(directory + self.separator)

    def delete_file(self, file_path):
        self.bucket.delete_object(file_path)

    def _check_empty_directory(self, path):
        if not self._is_directory_empty(path):
            raise ValueError('Cannot operate on non empty '
                             'directories')
        return True

    def _is_directory_empty(self, path):
        keys = self._get_path_keys(path + self.separator)
        return len(keys) == 1

    def make_dir(self, path, directory):
        if path == '':
            dir_path = directory + self.separator
        else:
            dir_path = self.separator.join(
                [path, (directory + self.separator)])
        self.bucket.put_object(key=dir_path, data='')

    def rename_path(self, src, dst):
        if self.is_dir(src):
            self._check_empty_directory(src)
            src += self.separator
            dst += self.separator
        self.bucket.copy_object(
            source_bucket_name=self.bucket.bucket_name,
            source_key=src,
            target_key=dst)
        self.delete_file(src)

    def generate_url(self, file_path, expires):
        return self.bucket.sign_url(
            method='GET', key=file_path, expires=expires)


class OSSFileAdmin(BaseFileAdmin):
    """
        Simple Amazon Simple Storage Service file-management interface.

            :param bucket_name:
                Name of the bucket that the files are on.

            :param region:
                Region that the bucket is located

            :param aws_access_key_id:
                AWS Access Key ID

            :param aws_secret_access_key:
                AWS Secret Access Key

        Sample usage::

            from flask_admin import Admin
            from flask_admin.contrib.fileadmin.s3 import S3FileAdmin

            admin = Admin()

            admin.add_view(S3FileAdmin('files_bucket', 'us-east-1', 'key_id', 'secret_key')
    """
    """
    把从BaseFileAdmin继承的upload_template改写成自定义的'my_upload.html'
    """
    upload_template = 'admin/my_upload.html'
    list_template = 'admin/my_list.html'
    mkdir_modal_template = 'admin/my_form.html'
    mkdir_template = 'admin/my_form.html'
    rename_template = 'admin/my_form.html'

    def __init__(
            self,
            bucket_name,
            access_key,
            secret_key,
            endpoint,
            *args,
            **kwargs):
        storage = ALiYunStorage(bucket_name, access_key, secret_key, endpoint)
        super(OSSFileAdmin, self).__init__(*args, storage=storage, **kwargs)

    def get_base_path(self):
        """
            Return base path. Override to customize behavior (per-user
            directories, etc)
        """
        return self.storage.get_base_path()

    def is_newname_existed(self, dir_base, filename):
        """
           :param dir_base:  os.path.normpath(full_path)
           :param filename:  used to rename the name of path or file
           :return:
        """
        existed_name = [
            item[0] for item in self.storage.get_files(
                path=dir_base)]
        return filename in existed_name

    def on_rename(self, full_path, dir_base, filename):
        """
            Perform some actions after a file or directory has been renamed.

            Called from rename method

            By default do nothing.
        """
        pass

    def on_edit_document(
            self,
            full_path,
            dir_base,
            filename,
            office,
            chapter,
            date):
        """
        :param full_path:
        :param dir_base:  os.path.normpath(full_path)
        :param filename:  used to rename the name of path or file
        :return:
        """
        from my_app.models import Document
        from my_app import db
        for item in self.storage.get_files(path=dir_base):
            if item[2] is False:
                try:
                    db_obj = Document.query.filter_by(
                        path=unicode(full_path)).first()
                    db_obj.title = unicode(filename)
                    db_obj.path = unicode(
                        dir_base + self._separator + filename)
                    db_obj.search_column = db_obj.path.replace(
                        self._separator, '')
                    db_obj.office = office
                    db_obj.chapter = chapter
                    db_obj.date = date
                    db.session.add(db_obj)
                    db.session.commit()
                    break
                except Exception as ex:
                    gettext(u'重命名时重写数据库失败,错误:%(error)', error=ex)
                    db.session.rollback()

    def on_file_delete(self, full_path, filename):
        """
            Perform some actions after a file has successfully been deleted.

            Called from delete method

            By default do nothing.
        """
        from my_app.models import Document, db
        try:
            document = Document.query.filter_by(
                path=unicode(full_path)).first()
            db.session.delete(document)
            db.session.commit()
        except Exception as ex:
            flash(
                gettext(
                    u'从数据库删除相应记录%(full_path)s失败,错误:%(error)s',
                    full_path=full_path,
                    error=ex),
                'error')
            db.session.rollback()

    def get_upload_form(self, directory):
        """
            Upload form class for file upload view.

            Override to implement customized behavior.
        """

        class UploadForm(self.form_base_class):
            """
                File upload form. Works with FileAdmin instance to check if it
                is allowed to upload file with given extension.
            """
            if directory is not None:
                try:
                    default = directory.split('/')
                    default_model = get_default(DEFAULT_MODELS, default)
                    default_chapter = get_default(DEFAULT_CHAPTERS, default)
                except ValueError:
                    default_model = None
                    default_chapter = None
            upload = MyFileField(lazy_gettext(u'上传文件'))
            office = MySelectField(label=lazy_gettext(u'处室'), coerce=unicode, choices=[
                (u'航线处', u'航线处'), (u'技术服务处', u'技术服务处'), (u'质量处', u'质量处')])
            model = MySelectField(
                label=lazy_gettext(u'机型'),
                coerce=int,
                choices=[
                    (737,
                     '737'),
                    (757,
                     '757'),
                    (787,
                     '787')],
                default=default_model if default_model is not None and default_model in DEFAULT_MODELS else None)
            chapter = MyRadioField(label=u'章节号', coerce=int,
                                   choices=[
                                       (0o5, u'05时间与限制'), (0o6, u'06尺寸和区域'),
                                       (12, u'12勤务'), (20, u'20标准施工'),
                                       (21, u'21空调'), (22, u'22自动驾驶'),
                                       (23, u'23通讯'), (24, u'24电源'),
                                       (25, u'25设备与装饰'), (26, u'26防火'),
                                       (27, u'27飞行操纵'), (28, u'28燃油'),
                                       (29, u'29液压系统'), (30, u'30防冰防雨'),
                                       (31, u'31指示系统'), (32, u'32起落架'),
                                       (33, u'33灯光'), (34, u'34导航'),
                                       (35, u'35氧气系统'), (36, u'36引气系统'),
                                       (38, u'38饮用水和灰水系统'), (47, u'47NGS'),
                                       (49, u'49辅助动力装置'),
                                       (51, u'51结构'), (52, u'52门'),
                                       (53, u'53机身'), (54, u'54发动机短舱和吊架'),
                                       (55, u'55安定面'), (56, u'56窗户'),
                                       (57, u'57机翼'), (70, u'70standard practices'),
                                       (71, u'71飞行动力'), (72, u'72发动机'),
                                       (73, u'73发动机燃油和控制'), (74, u'74发动机点火'),
                                       (75, u'75发动机空气'), (76, u'76发动机控制'),
                                       (77, u'77发动机指示'), (78, u'78发动机排气'),
                                       (79, u'79发动机滑油'), (80, u'80发动机起动'),
                                   ],
                                   default=default_chapter[
                                       0:2] if default_chapter is not None and default_chapter in DEFAULT_CHAPTERS else None
                                   )
            date = DateField(
                label=u'编辑日期',
                format='%m/%d/%Y',
                widget=DatePickerWidget())

            def __init__(self, *args, **kwargs):
                super(UploadForm, self).__init__(*args, **kwargs)
                self.admin = kwargs['admin']

            def validate_upload(self, field):
                if not self.upload.data:
                    raise validators.ValidationError(gettext('File required.'))

                filename = self.upload.data.filename

                if not self.admin.is_file_allowed(filename):
                    raise validators.ValidationError(
                        gettext('Invalid file type.'))

        return UploadForm

    def get_name_form(self):
        """
            Create form class for renaming and mkdir views.

            Override to implement customized behavior.
        """

        def validate_name(self, field):
            regexp = re.compile(
                r'^(?!^(PRN|AUX|CLOCK\$|NUL|CON|COM\d|LPT\d|\..*)(\..+)?$)[^\x00-\x1f\\?*:\";|/]+$')
            if not regexp.match(field.data):
                raise validators.ValidationError(gettext('Invalid name'))

        class NameForm(self.form_base_class):
            """
                Form with a filename input field.

                Validates if provided name is valid for *nix and Windows systems.
            """
            name = fields.StringField(lazy_gettext('Name'),
                                      validators=[validators.Required(),
                                                  validate_name])
            path = fields.HiddenField()

        return NameForm

    def get_edit_document_form(self, directory):
        """
            Create form class for renaming and mkdir views.

            Override to implement customized behavior.
        """

        def validate_name(self, field):
            regexp = re.compile(
                r'^(?!^(PRN|AUX|CLOCK\$|NUL|CON|COM\d|LPT\d|\..*)(\..+)?$)[^\x00-\x1f\\?*:\";|/]+$')
            if not regexp.match(field.data):
                raise validators.ValidationError(gettext('Invalid name'))

        class NameForm(self.form_base_class):
            """
                Form with a filename input field.

                Validates if provided name is valid for *nix and Windows systems.
            """
            if directory is not None:
                try:
                    default = directory.split('/')
                    default_model = get_default(DEFAULT_MODELS, default)
                    default_chapter = get_default(DEFAULT_CHAPTERS, default)
                except ValueError:
                    default_model = None
                    default_chapter = None
            name = fields.StringField(lazy_gettext(u'重名命'),
                                      validators=[validators.Required(),
                                                  validate_name])
            path = fields.HiddenField()

            office = MySelectField(label=lazy_gettext(u'处室'), coerce=unicode, choices=[
                (u'航线处', u'航线处'), (u'技术服务处', u'技术服务处'), (u'质量处', u'质量处')])
            model = MySelectField(
                label=lazy_gettext(u'机型'), coerce=int, choices=[
                    (737, '737'), (757, '757'), (787, '787')],
                default=default_model if default_model is not None and default_model in DEFAULT_MODELS else None)
            chapter = MyRadioField(label=u'章节号', coerce=int,
                                   choices=[
                                       (0o5, u'05时间限制'), (0o6, u'06尺寸和区域'),
                                       (12, u'12勤务'), (20, u'20标准施工'),
                                       (21, u'21空调'), (22, u'22自动驾驶'),
                                       (23, u'23通讯'), (24, u'24电源'),
                                       (25, u'25设备与装饰'), (26, u'26防火'),
                                       (27, u'27飞行操纵'), (28, u'28燃油'),
                                       (29, u'29液压系统'), (30, u'30防冰防雨'),
                                       (31, u'31指示系统'), (32, u'32起落架'),
                                       (33, u'33灯光'), (34, u'34导航'),
                                       (35, u'35氧气系统'), (36, u'36引气系统'),
                                       (38, u'38饮用水和灰水系统'), (47, u'47NGS'),
                                       (49, u'49辅助动力装置'),
                                       (51, u'51结构'), (52, u'52门'),
                                       (53, u'53机身'), (54, u'54发动机短舱和吊架'),
                                       (55, u'55安定面'), (56, u'56窗户'),
                                       (57, u'57机翼'), (70, u'70standard practices'),
                                       (71, u'71飞行动力'), (72, u'72发动机'),
                                       (73, u'73发动机燃油和控制'), (74, u'74发动机点火'),
                                       (75, u'75发动机空气'), (76, u'76发动机控制'),
                                       (77, u'77发动机指示'), (78, u'78发动机排气'),
                                       (79, u'79发动机滑油'), (80, u'80发动机起动'),
                                   ],
                                   default=default_chapter[0:2] if default_chapter is not None and default_chapter in DEFAULT_CHAPTERS else None
                                   )
            date = DateField(
                label=u'编辑日期',
                format='%m/%d/%Y',
                widget=DatePickerWidget())

        return NameForm

    def upload_form(self, directory):
        """
            Instantiate file upload form and return it.

            Override to implement custom behavior.
        """
        upload_form_class = self.get_upload_form(directory)
        if request.form:
            # Workaround for allowing both CSRF token + FileField to be submitted
            # https://bitbucket.org/danjac/flask-wtf/issue/12/fieldlist-filefield-does-not-follow
            formdata = request.form.copy()  # as request.form is immutable
            formdata.update(request.files)

            # admin=self allows the form to use self.is_file_allowed
            return upload_form_class(formdata, admin=self)
        elif request.files:
            return upload_form_class(request.files, admin=self)
        else:
            return upload_form_class(admin=self)

    def _save_form_files(self, directory, path, form):

        from my_app.models import Document
        from my_app import db
        uploadfiles = request.files.getlist('upload')

        for file in uploadfiles:
            save_path = self._separator.join([directory, file.filename])
            if self.storage.file_exists(path, file.filename):
                secure_name = self._separator.join(
                    [path, secure_filename(form.upload.data.filename)])
                raise Exception(gettext('File "%(name)s" already exists.',
                                        name=secure_name))
            else:
                self.save_file(save_path, file)
                try:
                    file_extension = file.filename.rsplit('.', 1)[1]
                    if file_extension in EXTENSIONS:
                        title = directory.strip(
                            self._separator) if directory.strip(
                            self._separator) != '' else file.filename
                    else:
                        title = file.filename
                except IndexError:
                    title = file.filename
                file_path = save_path.strip(
                    self._separator) if save_path.find(
                    self._separator) == 0 else save_path
                search_column = file_path.replace(self._separator, '')
                office = form.office.data
                model = form.model.data
                chapter = form.chapter.data
                date = form.date.data

                document = Document(
                    title=unicode(title),
                    path=unicode(file_path),
                    search_column=unicode(search_column),
                    model=unicode(model),
                    chapter=unicode(chapter),
                    date=unicode(date),
                    office=unicode(office))
                db.session.add(document)
                try:
                    db.session.commit()
                except Exception as ex:
                    flash(
                        gettext(
                            u'上传文件时保存数据库失败,错误:%(error)s',
                            error=ex),
                        'error')
                    db.session.rollback()
                self.on_file_upload(directory, path, save_path)

    def name_form(self):
        """
            Instantiate form used in rename and mkdir then return it.

            Override to implement custom behavior.
        """
        name_form_class = self.get_name_form()
        if request.form:
            return name_form_class(request.form)
        elif request.args:
            return name_form_class(request.args)
        else:
            return name_form_class()

    def edit_document_form(self, directory):
        name_form_class = self.get_edit_document_form(directory)
        if request.form:
            return name_form_class(request.form)
        elif request.args:
            return name_form_class(request.args)
        else:
            return name_form_class()

    @expose('/upload/', methods=('GET', 'POST'))
    @expose('/upload/<path:path>', methods=('GET', 'POST'))
    def upload(self, path=None):
        """
            Upload view method

            :param path:
                Optional directory path. If not provided, will use the base directory
        """
        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        if not self.can_upload:
            flash(gettext('File uploading is disabled.'), 'error')
            return redirect(self._get_dir_url('.index_view', path))

        if not self.is_accessible_path(path):
            flash(gettext('Permission denied.'), 'error')
            return redirect(self._get_dir_url('.index_view'))

        form = self.upload_form(directory)
        if self.validate_form(form):
            try:
                self._save_form_files(directory, path, form)
                flash(gettext('Successfully saved file: %(name)s',
                              name=form.upload.data.filename), 'success')
                return redirect(self._get_dir_url('.index_view', path))
            except Exception as ex:
                flash(
                    gettext(
                        'Failed to save file: %(error)s',
                        error=ex),
                    'error')

        if self.upload_modal and request.args.get('modal'):
            template = self.upload_modal_template
        else:
            template = self.upload_template

        return self.render(template, form=form,
                           header_text=gettext('Upload File'),
                           modal=request.args.get('modal'))

    @expose('/')
    @expose('/b/<path:path>')
    def index_view(self, path=None):
        """
            Index view method

            :param path:
                Optional directory path. If not provided, will use the base directory
        """
        from my_app.models import Document
        if self.can_delete:
            delete_form = self.delete_form()
        else:
            delete_form = None

        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        if not self.is_accessible_path(path):
            flash(gettext('Permission denied.'), 'error')
            return redirect(self._get_dir_url('.index_view'))

        # Get directory listing
        items = []

        # Parent directory
        if directory != base_path:
            parent_path = op.normpath(self._separator.join([path, '..']))
            if parent_path == '.':
                parent_path = None

            items.append(
                ('..',
                 parent_path,
                 True,
                 0,
                 0,
                 'null',
                 'null',
                 'null',
                 'null'))
        for item in self.storage.get_files(path):
            file_name, rel_path, is_dir, size, last_modified = item
            if is_dir is True:
                file_meta = ('null', 'null', 'null', 'null')
                item = item + file_meta
            if is_dir is False:
                file_obj = Document.query.filter_by(
                    path=unicode(rel_path)).first()
                try:
                    file_meta = (
                        file_obj.office,
                        file_obj.model,
                        file_obj.chapter,
                        file_obj.date)
                except Exception as ex:
                    flash(
                        gettext(
                            u'从数据库读取文档的元信息失败:错误:%(error)s',
                            error=ex),
                        'error')
                    file_meta = ('null', 'null', 'null', 'null')
                item = item + file_meta
            if self.is_accessible_path(rel_path):
                items.append(item)
        # Sort by name
        items.sort(key=itemgetter(0))

        # Sort by type
        items.sort(key=itemgetter(2), reverse=True)

        # Sort by modified date
        items.sort(
            key=lambda values: (
                values[0],
                values[1],
                values[2],
                values[3],
                datetime.fromtimestamp(
                    values[4])),
            reverse=True)

        # Generate breadcrumbs
        breadcrumbs = self._get_breadcrumbs(path)

        # Actions
        actions, actions_confirmation = self.get_actions_list()

        return self.render(self.list_template,
                           dir_path=path,
                           breadcrumbs=breadcrumbs,
                           get_dir_url=self._get_dir_url,
                           get_file_url=self._get_file_url,
                           items=items,
                           actions=actions,
                           actions_confirmation=actions_confirmation,
                           delete_form=delete_form)

    @expose('/mkdir/', methods=('GET', 'POST'))
    @expose('/mkdir/<path:path>', methods=('GET', 'POST'))
    def mkdir(self, path=None):
        """
            Directory creation view method

            :param path:
                Optional directory path. If not provided, will use the base directory
        """
        # Get path and verify if it is valid

        base_path, directory, path = self._normalize_path(path)

        dir_url = self._get_dir_url('.index_view', path)

        if not self.can_mkdir:
            flash(gettext('Directory creation is disabled.'), 'error')
            return redirect(dir_url)

        if not self.is_accessible_path(path):
            flash(gettext('Permission denied.'), 'error')
            return redirect(self._get_dir_url('.index_view'))

        form = self.name_form()

        if self.validate_form(form):
            try:
                if self.is_newname_existed(path, form.name.data):
                    raise Exception('新文件夹"%s"已经存在' % form.name.data)
                self.storage.make_dir(directory, form.name.data)
                self.on_mkdir(directory, form.name.data)
                flash(gettext('Successfully created directory: %(directory)s',
                              directory=form.name.data), 'success')
                return redirect(dir_url)
            except Exception as ex:
                flash(
                    gettext(
                        'Failed to create directory: %(error)s',
                        error=ex),
                    'error')
        else:
            helpers.flash_errors(
                form, message='Failed to create directory: %(error)s')

        if self.mkdir_modal and request.args.get('modal'):
            template = self.mkdir_modal_template
        else:
            template = self.mkdir_template

        return self.render(template, form=form, dir_url=dir_url,
                           header_text=gettext('Create Directory'))

    @expose('/delete/', methods=('POST',))
    def delete(self):
        """
            Delete view method
        """
        form = self.delete_form()
        path = form.path.data
        if path:
            return_url = self._get_dir_url('.index_view', op.dirname(path))
        else:
            return_url = self.get_url('.index_view')

        if self.validate_form(form):
            # Get path and verify if it is valid
            base_path, full_path, path = self._normalize_path(path)

            if not self.can_delete:
                flash(gettext('Deletion is disabled.'), 'error')
                return redirect(return_url)

            if not self.is_accessible_path(path):
                flash(gettext('Permission denied.'), 'error')
                return redirect(self._get_dir_url('.index_view'))

            if self.storage.is_dir(full_path):
                if not self.can_delete_dirs:
                    flash(gettext('Directory deletion is disabled.'), 'error')
                    return redirect(return_url)
                try:
                    self.before_directory_delete(full_path, path)
                    self.storage.delete_tree(full_path)
                    self.on_directory_delete(full_path, path)
                    flash(
                        gettext(
                            'Directory "%(path)s" was successfully deleted.',
                            path=path),
                        'success')
                except Exception as ex:
                    flash(
                        gettext(
                            'Failed to delete directory: %(error)s',
                            error=ex),
                        'error')
            else:
                try:
                    self.before_file_delete(full_path, path)
                    self.delete_file(full_path)
                    self.on_file_delete(full_path, path)
                    flash(
                        gettext(
                            'File "%(name)s" was successfully deleted.',
                            name=path),
                        'success')
                except Exception as ex:
                    flash(
                        gettext(
                            'Failed to delete file: %(name)s',
                            name=ex),
                        'error')
        else:
            helpers.flash_errors(
                form, message='Failed to delete file. %(error)s')

        return redirect(return_url)

    @expose('/rename/', methods=('GET', 'POST'))
    @expose('/rename/<path:path>', methods=('GET', 'POST'))
    def rename(self, path=None):
        """
            Rename view method
        """
        path = unicode(path)
        if self.storage.is_dir(path):
            form = self.name_form()
        else:
            form = self.edit_document_form(directory=path)
        if path:
            base_path, full_path, path = self._normalize_path(path)
            return_url = self._get_dir_url('.index_view', op.dirname(path))
        else:
            return redirect(self.get_url('.index_view'))

        if not self.can_rename:
            flash(gettext('Renaming is disabled.'), 'error')
            return redirect(return_url)

        if not self.is_accessible_path(path):
            flash(gettext('Permission denied.'), 'error')
            return redirect(self._get_dir_url('.index_view'))

        if not self.storage.path_exists(full_path):
            flash(gettext('Path does not exist.'), 'error')
            return redirect(return_url)

        if self.validate_form(form) and not self.storage.is_dir(path):
            try:
                dir_base = op.dirname(full_path)
                filename = form.name.data
                office = form.office.data
                chapter = form.chapter.data
                date = form.date.data
                if self.is_newname_existed(dir_base, filename):
                    raise Exception(u'新名称"%s"已经存在' % filename)
                self.storage.rename_path(
                    full_path, self._separator.join([dir_base, filename]))
                self.on_edit_document(
                    full_path, dir_base, filename, office, chapter, date)
                flash(gettext('Successfully renamed "%(src)s" to "%(dst)s"',
                              src=op.basename(path),
                              dst=filename), 'success')
            except Exception as ex:
                flash(
                    gettext(
                        'Failed to rename: %(error)s',
                        error=ex),
                    'error')

            return redirect(return_url)
        else:
            helpers.flash_errors(form, message='Failed to rename: %(error)s')

        if self.validate_form(form) and self.storage.is_dir(path):
            try:
                dir_base = op.dirname(full_path)
                filename = form.name.data
                self.storage.rename_path(
                    full_path, self._separator.join([dir_base, filename]))
                self.on_rename(full_path, dir_base, filename)
                flash(gettext('Successfully renamed "%(src)s" to "%(dst)s"',
                              src=op.basename(path),
                              dst=filename), 'success')
            except Exception as ex:
                flash(
                    gettext(
                        'Failed to rename: %(error)s',
                        error=ex),
                    'error')

            return redirect(return_url)
        else:
            helpers.flash_errors(form, message='Failed to rename: %(error)s')

        if self.rename_modal and request.args.get('modal'):
            template = self.rename_modal_template
        else:
            template = self.rename_template

        return self.render(template, form=form, path=op.dirname(path),
                           name=op.basename(path), dir_url=return_url,
                           header_text=gettext('Rename %(name)s',
                                               name=op.basename(path)))

    @expose('/action/', methods=('POST',))
    def action_view(self):
        return self.handle_action()

    # Actions
    @action('delete',
            lazy_gettext('Delete'),
            lazy_gettext('Are you sure you want to delete these files?'))
    def action_delete(self, items):
        if not self.can_delete:
            flash(gettext('File deletion is disabled.'), 'error')
            return

        for path in items:
            base_path, full_path, path = self._normalize_path(path)

            if self.is_accessible_path(path):
                try:
                    self.delete_file(full_path)
                    self.on_file_delete(full_path, path)
                    flash(
                        gettext(
                            'File "%(name)s" was successfully deleted.',
                            name=path),
                        'success')
                except Exception as ex:
                    flash(
                        gettext(
                            'Failed to delete file: %(name)s',
                            name=ex),
                        'error')
