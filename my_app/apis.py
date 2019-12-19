# -*- coding:utf-8 -*-
from flask_restful import Resource, fields, marshal_with, marshal, reqparse
from flask import jsonify, current_app
from sqlalchemy.exc import IntegrityError
import jieba
import json
from weixin import WXAPPAPI
from WXBizDataCrypt import WXBizDataCrypt
from .models.tool import Tool, Project
from .models.document import Document
from .models.standard import StandardTime
from .models.advise import Advise
from .models.hierarchy import Team, Worker
from .models.timesheet import Timesheet
from .errors import api_abort
from my_app import db

projects_resource_fields = {
    'title': fields.String,
    'id': fields.Integer,
}

tools_resource_fields = {
    'name': fields.String,
    'size': fields.String,
    'number': fields.Integer,
    'description': fields.String,
}

documents_resource_fields = {
    'title': fields.String,
    'id': fields.Integer,
}

tasks_resource_fields = {
    'title': fields.String,
    'id': fields.Integer,
    'tasktime': fields.Float,
    'kind': fields.String,
}

teams_resource_fields = {
    'id': fields.Integer,
    'name': fields.String,
}

timesheet_resource_fields = {
    'name': fields.String,
    'number': fields.Integer,
    'date': fields.String,
    'airplane': fields.String,
    'task': fields.String,
    'calculated_time': fields.Float,
    'completed': fields.String,
    'kind': fields.String,
    'approved': fields.String
}

parser = reqparse.RequestParser()
parser.add_argument('search')
parser.add_argument('code', type=str, help='code must be a string.')
parser.add_argument('session_key',
                    type=str,
                    help='session_key must be a string.')
parser.add_argument('encrypted_data',
                    type=str,
                    help='encrypted_data must be a string.')
parser.add_argument('iv', type=str, help='iv must be a string.')
parser.add_argument('nickName', type=str, help='nickName must be a string.')
# XXX: 工号.
parser.add_argument('number', type=str, help='number must be a string.')
parser.add_argument('openId', type=str, help='openId must be a string.')
parser.add_argument('teamID', type=str, help='teamID must be a string.')


class ProjectsAPI(Resource):
    @marshal_with(projects_resource_fields)
    def get(self):
        return [project for project in Project.query.all()]

    def post(self):
        args = parser.parse_args()
        search = args.get('search', '')
        results = []

        seg_list = jieba.cut(sentence=search)
        ars_list = []
        for seg in seg_list:
            projects = Project.query.whoosh_search(seg, or_=True).all()
            if len(projects) != 0:
                ars_list.append(projects)
        try:
            projects_set = reduce(lambda x, y: set(x).intersection(set(y)),
                                  ars_list)
        except TypeError:
            projects_set = []

        if len(projects_set) != 0:
            for project in projects_set:
                tools = Tool.query.filter_by(project_id=project.id).all()
                project_tools = dict()
                project_tools[u'project_id'] = project.id
                project_tools[u'project_title'] = project.title
                project_tools[u'tools'] = [
                    marshal(tool, tools_resource_fields) for tool in tools
                ]
                results.append(project_tools)
        return results


class segmentationsAPI(Resource):
    def post(self):
        args = parser.parse_args()
        search = args.get('search', '')
        if not (search):
            return []
        else:
            seg_list = jieba.cut(sentence=search)
            return [seg for seg in seg_list]


class ToolsAPI(Resource):
    def get(self, project_id):
        project_tools = dict()
        project = Project.query.filter_by(id=project_id).first()
        project_tools[u'project_id'] = project.id
        project_tools[u'project_title'] = project.title
        project_tools[u'tools'] = [
            marshal(tool, tools_resource_fields)
            for tool in project.the_tools.all()
        ]
        return [project_tools]


class Code2sessionAPI(Resource):
    def post(self):
        APP_ID = current_app.config.get('APP_ID')
        APP_SECRET = current_app.config.get('APP_SECRET')
        wx_api = WXAPPAPI(appid=APP_ID, app_secret=APP_SECRET)

        args = parser.parse_args()
        code = args.get('code', None)

        if code:
            session_info = wx_api.exchange_code_for_session_key(code=code)
            session_key = session_info.get('session_key')
            return jsonify(session_key)
        else:
            return jsonify({'error': 'No code!!!'})


class UserInfoAPI(Resource):
    def post(self):

        args = parser.parse_args()

        APP_ID = current_app.config.get('APP_ID')
        session_key = args.get('session_key', None)
        encrypted_data = args.get('encrypted_data', None)
        iv = args.get('iv', None)

        if APP_ID and session_key and encrypted_data and iv:
            crypt = WXBizDataCrypt(APP_ID, session_key)
            user_info = crypt.decrypt(encrypted_data, iv)

            try:
                openId = user_info.get('openId', None)
                name = user_info.get('nickName', None)
            except (UnicodeEncodeError, ValueError, TypeError) as e:
                return api_abort(400, e.args[0], binded=False, login=False)

            if openId:
                print('{!s}: {!s}'.format('apis.py', '160'), openId)
                worker = Worker.query.filter_by(openId=openId).first()
                if worker and worker.number and worker.belongto_team:
                    user_info.update(number=worker.number,
                                     authority=worker.authority,
                                     belongto_team=str(worker.belongto_team),
                                     binded=True,
                                     login=True)
                elif worker:
                    user_info.update(binded=False,
                                     login=True,
                                     authority=worker.authority)
                # XXX: 没有 openId 对应的记录则 SQLALchemy返回 None.
                elif worker is None:
                    # XXX: 尝试使用用户名去查找记录, 可能管理员预先在后台录入用户的名字和工号.
                    # 这时需要更新用户的 openId.
                    worker = Worker.query.filter_by(name=name).all()
                    # XXX: 如果有重名的用户则不写入 openId.
                    if len(worker) > 1:
                        user_info.update(binded=False, login=True)
                    elif len(worker) == 1:
                        try:
                            worker[0].openId = openId
                            db.session.commit()
                            user_info.update(binded=False,
                                             login=True,
                                             authority=worker[0].authority)
                        except IntegrityError as e:
                            db.session.rollback()
                            api_abort(400,
                                      e.args[0],
                                      binded=False,
                                      login=True,
                                      authority=worker.authority)
                    elif len(worker) == 0:
                        new_worker = Worker(name=name,
                                            number=None,
                                            openId=openId,
                                            major=None,
                                            post=None,
                                            authority=u'普通用户',
                                            belongto_department=None,
                                            belongto_workshop=None,
                                            belongto_team=None)
                        try:
                            db.session.add(new_worker)
                            db.session.commit()
                            user_info.update(binded=False,
                                             login=True,
                                             authority=u'普通用户')
                        except IntegrityError as e:
                            db.session.rollback()
                            api_abort(400, e.args[0], binded=False, login=True)
                return jsonify(user_info)


class UpdateUserInfoAPI(Resource):
    def post(self):

        args = parser.parse_args()

        nickName = args.get('nickName', None)
        number = args.get('number', None)
        openId = args.get('openId', None)
        teamID = args.get('teamID', None)

        try:
            name = unicode(nickName, 'utf-8')
            number = int(number)
            team_id = int(teamID)
            belongto_team = str(Team.query.get(team_id))
        except (UnicodeEncodeError, ValueError, TypeError) as e:
            return api_abort(400, e.args[0], binded=False)

        if name and number:
            worker = Worker.query.filter(Worker.name == name,
                                         Worker.number == number).first()
            # XXX: 仅当后台有录入工号和名字, 用户首次绑定.
            if worker and worker.openId == u'':
                try:
                    worker.openId = openId
                    worker.team_id = team_id
                    db.session.commit()
                    return jsonify({
                        'binded': True,
                        'number': number,
                        'authority': worker.authority,
                        'belongto_team': belongto_team
                    })
                except IntegrityError as e:
                    db.session.rollback()
                    return api_abort(400, e.args[0], binded=False)
            # XXX: 对于使用名字和工号无法查询到的, 可能是只开始使用小程序.
            # 但是有一种情况: 后台记录用户的名字和工号和 openId, 但是用户需要
            # 更改工号(第一次录入错误),更改班组.
            #  elif worker is None: 如此判断不够严谨.
            else:
                worker = Worker.query.filter_by(openId=openId).first()
                if worker:
                    try:
                        worker.number = number
                        worker.team_id = team_id
                        db.session.commit()
                        return jsonify({
                            'binded': True,
                            'number': number,
                            'authority': worker.authority,
                            'belongto_team': belongto_team
                        })
                    except IntegrityError as e:
                        db.session.rollback()
                        return api_abort(409, e.args[0], binded=False)


class DocumentListAPI(Resource):
    @marshal_with(documents_resource_fields)
    def get(self):
        return [document for document in Document.query.all()]

    def post(self):
        args = parser.parse_args()
        search = args.get('search', '')
        seg_list = jieba.cut(sentence=search)
        ars_list = []
        for seg in seg_list:
            documents = Document.query.whoosh_search(seg, or_=True).all()
            if len(documents) != 0:
                ars_list.append(documents)
        try:
            document_set = reduce(lambda x, y: set(x).intersection(set(y)),
                                  ars_list)
        except TypeError:
            document_set = []

        results = []

        if len(document_set) != 0:
            for document in document_set:
                meta_information = dict()
                meta_information[u'id'] = document.id
                meta_information[u'title'] = document.title
                meta_information[u'office'] = document.office
                meta_information[u'model'] = document.model
                meta_information[u'chapter'] = document.chapter
                meta_information[u'date'] = document.date
                meta_information[u'get_url'] = document.get_url
                results.append(meta_information)
        return results


class DocumentAPI(Resource):
    def get(self, document_id):
        result = dict()
        document = Document.query.filter_by(id=document_id).first()
        result[u'id'] = document.id
        result[u'title'] = document.title
        result[u'office'] = document.office
        result[u'model'] = document.model
        result[u'chapter'] = document.chapter
        result[u'date'] = document.date
        result[u'get_url'] = document.get_url
        return [result]


class TasksAPI(Resource):
    @marshal_with(tasks_resource_fields)
    def get(self):
        return [task for task in StandardTime.query.all()]


class TeamsAPI(Resource):
    def get(self):
        result = dict()
        for team in Team.query.all():
            result[team.name] = team.id
        return result


class TimesheetAPI(Resource):
    @marshal_with(timesheet_resource_fields)
    def get(self):
        return [timesheet for timesheet in Timesheet.query.all()]
