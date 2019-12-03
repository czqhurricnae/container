# -*- coding:utf-8 -*-
import sys
import jieba
from flask_script import Shell, Manager
from flask_migrate import MigrateCommand, Migrate
from container_whooshalchemyplus import whoosh_index
from my_app import create_app, db
from my_app.models.tool import Tool, Project
from my_app.models.document import Document
from my_app.models.advise import Advise
from my_app.models.hierarchy import Worker
# from my_app.scrapper import Scrapper

reload(sys)
sys.setdefaultencoding('utf8')

jieba.load_userdict('userdict.txt')

app = create_app()
migrate = Migrate(app, db)
manager = Manager(app)


def _make_context():
    return dict(app=app,
                db=db,
                Tool=Tool,
                Project=Project,
                Document=Document,
                Advise=Advise,
                Worker=Worker)


manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)
whoosh_index(app, Project)
whoosh_index(app, Document)

if __name__ == '__main__':
    manager.run()
    # app.run()
