from flask_restful import Resource, fields, marshal_with, marshal, reqparse
from models import Project, Tool
import jieba
import json

projects_resource_fields = {
    'title': fields.String,
}

tools_resource_fields = {
    'name': fields.String,
    'size': fields.String,
    'number': fields.Integer,
    'description': fields.String,
}

parser = reqparse.RequestParser()
parser.add_argument('search')


class ProjectsAPI(Resource):
    @marshal_with(projects_resource_fields)
    def get(self, **kwargs):
        return [project for project in Project.query.all()]


class SegmentationAPI(Resource):
    def post(self):
        args = parser.parse_args()
        search = args.get('search', '')
        seg_list = jieba.cut(sentence=search)
        return [seg for seg in seg_list]


class ToolsAPI(Resource):
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
                project_tool = dict()
                project_tool[u'project_id'] = project.id
                project_tool[u'project_title'] = project.title
                project_tool[u'tools'] = []
                tools = Tool.query.filter_by(project_id=project.id).all()
                for tool in tools:
                    project_tool[u'tools'].append(
                        marshal(vars(tool), tools_resource_fields))
                results.append(project_tool)
        return results
