# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
from flask_migrate import MigrateCommand, Migrate
from container_whooshalchemyplus import whoosh_index
from my_app import create_app, db
from my_app.models import Tool, Project, Document, Advise
#from my_app.scrapper import Scrapper
from flask_script import Shell, Manager
import jieba
jieba.load_userdict('userdict.txt')
app = create_app()
migrate = Migrate(app, db)
manager = Manager(app)


def _make_context():
    return dict(
        app=app,
        db=db,
        Tool=Tool,
        Project=Project,
        Document=Document,
        Advise=Advise)
manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)
whoosh_index(app, Project)
whoosh_index(app, Document)


if __name__ == '__main__':
    manager.run()
