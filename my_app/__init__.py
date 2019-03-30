# -*- coding:utf-8 -*-
from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
import container_whooshalchemyplus
from flask_admin import Admin
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_debugtoolbar import DebugToolbarExtension
from flask_admin.menu import MenuLink
#from flask_admin.contrib.fileadmin import FileAdmin
from aliyun import OSSFileAdmin
from os import path

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
'Not Found

The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.'
in the browser.

`import my_app.index.views`

To avoid the circular import, we choose to use the `blueprint`
"""
""""
the definition is `def register_blueprint(self, blueprint, **options)`
1.the value of parameter`blueprint` in the definition can not be a `str`
for  instance, `app.register_blueprint('index')` may cause error:`AttributeError: 'str' object has no attribute 'name'`

2.first initialize a blueprint in `my_app/hello/views.py`, then import the blueprint through `from my_app.hello.views import index`

3.second insert the blueprint `index` that we just create in `my_app/hello/views.py` into the blueprints through 'app.register_blueprint(index)'

4.the name of blueprint you import here can not the same as any function name where the blueprint imported from, or will cause an error:`AttributeError: 'function' object has no attribute 'name'`
"""

db = SQLAlchemy()
admin = Admin(name=u'后台管理', template_mode='bootstrap3')
babel = Babel()
bootstrap = Bootstrap()
#toolbar = DebugToolbarExtension()


def create_app():
    from .index import index_blueprint
    from .administ import admin_blueprint
<<<<<<< HEAD
    from .document import documents_blueprint
=======
    from.document import documents_blueprint
>>>>>>> origin/master
    from models import Tool, Project, Advise, Document, ProjectModelView, ToolModelView, DocumentModelView
    app = Flask(
        __name__,
        instance_path=INSTANCE_PATH,
        static_folder=STATIC_PATH,
        instance_relative_config=True)
    app.config.from_pyfile('configuration.cfg')
    """
    local:
    if environ.get('app_name') == None:
        pass
    else:
        mysql_db = MySQLdb.connect(host = 'localhost',user = 'root',passwd = 'c')
        cursor = mysql_db.cursor()
        sql = 'CREATE DATABASE IF NOT EXISTS app_tool ;'
        cursor.execute(sql)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://%s:%s@%s:%s/%s' \
                                            %(sae.const.MYSQL_USER,sae.const.MYSQL_PASS, \
                                              sae.const.MYSQL_HOST, int(sae.const.MYSQL_PORT), sae.const.MYSQL_DB)
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///{}'.format(DATABASE_PATH)
    app.config['WHOOSH_BASE'] = '{}/whoosh'.format(BASE_URL)
    app.config['WHOOSH_DISABLED'] = False
    app.register_blueprint(index_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(documents_blueprint)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    container_whooshalchemyplus.init_app(app)
    admin.init_app(app)
    admin.add_view(ProjectModelView(model=Project, session=db.session, name=u'拆装项目清单'))
    admin.add_view(ToolModelView(model=Tool, session=db.session, name=u'拆装工具清单'))
    admin.add_view(DocumentModelView(model=Document, session=db.session, name=u'文档清单'))
    # admin.add_view(FileAdmin(base_path= UPLOAD_PATH, name = u'本地文件'))
    admin.add_view(
        OSSFileAdmin(
            access_key='2zdr2JCTOpn9viiK',
            secret_key='2EnOtEoK90ycVpmjUn4BHVYYy5zmzx',
            bucket_name='filessystem',
            endpoint='http://oss-cn-shanghai.aliyuncs.com',
            name=u'阿里云存储'))
    babel.init_app(app)
    bootstrap.init_app(app)
    # toolbar.init_app(app)
    return app
"""
the initialization of db must be after all the configuration of app have been done, or the configuration of 'SQLALCHEMY_TRACK_MODIFICATIONS = True'
may not affect and cause warning:
UserWarning: SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and will be disabled by default in the future.
Set it to True to suppress this warning.
warnings.warn('SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and will be disabled by default in the future.
Set it to True to suppress this warning.')
"""
"""
Actually, application not registered on db instance and no application bound to current context,
used in factory method to initialize the app`db.init_app(app)`
"""
