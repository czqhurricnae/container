from flask_restful import Resource, fields, marshal_with
from models import Project

resource_fields = {
    'title': fields.String,
}


class ProjectAPI(Resource):
    @marshal_with(resource_fields)
    def get(self, **kwargs):
        return [project for project in Project.query.all()]
