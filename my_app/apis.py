# -*- coding:utf-8 -*-
from flask_restful import Resource, fields, marshal_with, marshal, reqparse
from flask import jsonify, current_app
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

parser = reqparse.RequestParser()
parser.add_argument('search')
parser.add_argument('code', type=str, help='code must be a string.')
parser.add_argument('session_key', type=str, help='code must be a string.')
parser.add_argument('encrypted_data', type=str, help='code must be a string.')
parser.add_argument('iv', type=str, help='code must be a string.')


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
            if user_info.get(u'openId', None):
                worker = Worker.query.filter_by(
                    openId=user_info['openId']).first()
                if worker and worker.number and worker.belongto_team:
                    user_info.update(number=worker.number,
                                     authority=worker.authority,
                                     belongto_team=str(worker.belongto_team),
                                     binded=True,
                                     login=True)
                elif worker:
                    user_info.update(binded=False, login=True)
                # XXX: 没有 openId 对应的记录则返回 None.
                elif worker is None:
                    new_worker = Worker(name=user_info.get('nickName'),
                                        number=None,
                                        openId=user_info.get('openId'),
                                        major=None,
                                        post=None,
                                        authority=u'普通用户',
                                        belongto_department=None,
                                        belongto_workshop=None,
                                        belongto_team=None)
                    db.session.add(new_worker)
                    db.session.commit()
                    user_info.update(binded=False, login=True)
            return jsonify(user_info)


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
    @marshal_with(teams_resource_fields)
    def get(self):
        return [team for team in Team.query.all()]
