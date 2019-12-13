# -*- coding:utf-8 -*-
from flask import Flask, url_for, session, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import container_whooshalchemyplus
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_debugtoolbar import DebugToolbarExtension
from flask_admin.menu import MenuLink
#from flask_admin.contrib.fileadmin import FileAdmin
from aliyun import OSSFileAdmin
from flask.ext.babelex import Babel
from os import path
from flask_restful import Api

BASE_URL = path.abspath(path.dirname(__file__))
UPLOAD_PATH = path.join(BASE_URL, u'upload')
INSTANCE_PATH = path.join(BASE_URL, u'instance')
STATIC_PATH = path.join(BASE_URL, u'static')
DATABASE_PATH = path.join(BASE_URL, u'database.db')
"""
pass

import sae.const
import MySQLdb
"""
"""
Must have a circular import between `my_app/__init__.py` and `my_app/index/views.py`,or it could show error
`Not Found The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.`
in the browser.

`import my_app.index.views`

To avoid the circular import, we choose to use the `blueprint`.
"""
"""
The definition is `def register_blueprint(self, blueprint, **options)`.

1. The value of parameter`blueprint` in the definition can not be a `str` for instance,
`app.register_blueprint('index')` may cause error:`AttributeError: 'str' object has no attribute 'name'`.

2. First initialize a blueprint in `my_app/hello/views.py`, then import the blueprint through `from my_app.hello.views import index`.

3. Second insert the blueprint `index` that we just create in `my_app/hello/views.py` into the blueprints through 'app.register_blueprint(index)'.

4. The name of blueprint you import here can not the same as any function name where the blueprint imported from, or will cause an error:`AttributeError: 'function' object has no attribute 'name'`.
"""

db = SQLAlchemy()
admin = Admin(name=u'后台管理',
              template_mode='bootstrap3',
              base_template='AdminLTE_master.html')
babel = Babel()
bootstrap = Bootstrap()
#toolbar = DebugToolbarExtension()


def create_app():
    from .index import index_blueprint
    from .administ import admin_blueprint
    from .document import documents_blueprint
    from .models.tool import Tool, Project, ProjectModelView, ToolModelView
    from .models.document import Document, DocumentModelView
    from .models.advise import Advise
    from .models.hierarchy import Department, Workshop, Team, Worker, DepartmentModelView, WorkshopModelView, TeamModelView, WorkerModelView
    from .models.standard import StandardTime, StandardTimeModelView
    from .models.timesheet import Timesheet, TimesheetModelView, PendingApprovedModelView
    from apis import ProjectsAPI, segmentationsAPI, ToolsAPI, Code2sessionAPI, UserInfoAPI, DocumentListAPI, DocumentAPI, TasksAPI

    app = Flask(__name__,
                instance_path=INSTANCE_PATH,
                static_folder=STATIC_PATH,
                instance_relative_config=True)
    app.config.from_pyfile('configuration.cfg')
    """
    local:
    if environ.get('app_name') == None:
        pass
    else:
        mysql_db = MySQLdb.connect(host='localhost',user='root',passwd='c')
        cursor = mysql_db.cursor()
        sql = 'CREATE DATABASE IF NOT EXISTS app_tool;'
        cursor.execute(sql)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://%s:%s@%s:%s/%s' %( \
                                               sae.const.MYSQL_USER, \
                                               sae.const.MYSQL_PASS, \
                                               sae.const.MYSQL_HOST, \
                                               int(sae.const.MYSQL_PORT), \
                                               sae.const.MYSQL_DB)
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///{}'.format(
        DATABASE_PATH)
    app.config['WHOOSH_BASE'] = '{}/whoosh'.format(BASE_URL)
    app.config['WHOOSH_DISABLED'] = False
    app.config.update(RESTFUL_JSON=dict(ensure_ascii=False))

    app.register_blueprint(index_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(documents_blueprint)

    register_errors(app)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    container_whooshalchemyplus.init_app(app)

    admin.init_app(app)
    admin.add_view(
        PendingApprovedModelView(model=Timesheet,
                                 session=db.session,
                                 name=u'工时审核',
                                 category=u'工时管理'))
    admin.add_view(
        DepartmentModelView(model=Department,
                            session=db.session,
                            name=u'处室设置',
                            category=u'机构设置'))

    admin.add_view(
        WorkshopModelView(model=Workshop,
                          session=db.session,
                          name=u'车间设置',
                          category=u'机构设置'))

    admin.add_view(
        TeamModelView(model=Team,
                      session=db.session,
                      name=u'班组设置',
                      category=u'机构设置'))

    admin.add_view(
        WorkerModelView(model=Worker, session=db.session, name=u'人员管理'))

    admin.add_view(
        StandardTimeModelView(model=StandardTime,
                              session=db.session,
                              name=u'标准工时清单'))

    admin.add_view(
        ProjectModelView(model=Project,
                         session=db.session,
                         name=u'拆装项目清单',
                         category=u'工具'))

    admin.add_view(
        ToolModelView(model=Tool,
                      session=db.session,
                      name=u'拆装工具清单',
                      category=u'工具'))

    admin.add_view(
        DocumentModelView(model=Document, session=db.session, name=u'文档清单'))
    # admin.add_view(FileAdmin(base_path=UPLOAD_PATH, name=u'本地文件'))
    admin.add_view(
        OSSFileAdmin(access_key='2zdr2JCTOpn9viiK',
                     secret_key='2EnOtEoK90ycVpmjUn4BHVYYy5zmzx',
                     bucket_name='filessystem',
                     endpoint='http://oss-cn-shanghai.aliyuncs.com',
                     name=u'阿里云存储'))

    babel.init_app(app)

    @babel.localeselector
    def get_locale():
        override = 'zh_CN'
        if override:
            session['lang'] = override
        return session.get('lang', 'en')

    bootstrap.init_app(app)
    # toolbar.init_app(app)

    api = Api(app)
    api.add_resource(ProjectsAPI, '/api/projects')
    api.add_resource(segmentationsAPI, '/api/segmentations')
    api.add_resource(ToolsAPI, '/api/tools/<int:project_id>')
    api.add_resource(Code2sessionAPI, '/api/code2session')
    api.add_resource(UserInfoAPI, '/api/userInfo')
    api.add_resource(DocumentListAPI, '/api/documents')
    api.add_resource(DocumentAPI, '/api/documents/<document_id>/')
    api.add_resource(TasksAPI, '/api/tasks')
    return app


"""
The initialization of db must be after all the configuration of app have been done, or the configuration of 'SQLALCHEMY_TRACK_MODIFICATIONS = True'
may not affect and cause warning:
UserWarning: SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and will be disabled by default in the future.
Set it to True to suppress this warning.
warnings.warn('SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and will be disabled by default in the future.
Set it to True to suppress this warning.')
"""
"""
Actually, application not registered on db instance and no application bound to current context,
used in factory method to initialize the app `db.init_app(app)`.
"""


def register_errors(app):
    @app.errorhandler(500)
    def internal_server_error(e):
        print('{!s}: {!s}'.format('__init__.py', '204'))
        print(request.accept_mimetypes)
        response = jsonify(code=500,
                           message='An internal server error occurred.')
        response.status_code = 500
        return response
        return render_template('errors.html', code=500,
                               info='Server Error'), 500
