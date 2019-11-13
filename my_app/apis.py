from flask_restful import Resource, fields, marshal_with, reqparse
from models import Project
import jieba

resource_fields = {
    'title': fields.String,
}

parser = reqparse.RequestParser()
parser.add_argument('search')


class ProjectAPI(Resource):
    @marshal_with(resource_fields)
    def get(self, **kwargs):
        return [project for project in Project.query.all()]


class SegmentationAPI(Resource):
    def post(self):
        args = parser.parse_args()
        seg_list = jieba.cut(sentence=args['search'])
        return [seg for seg in seg_list]
