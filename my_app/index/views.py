# -*- coding:utf-8 -*-

from . import index_blueprint as index
from flask import render_template, jsonify, request
import jieba
from functools import reduce
import json
import ast


@index.route('/', methods=['GET', 'POST'])
def hello():
    if request.is_xhr:
        search = request.args.get('search')
        from ..models import Project, Tool
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

        result = dict()
        result[u'projects_tools'] = []
        if len(projects_set) != 0:
            for project in projects_set:
                project_tool = dict()
                project_tool[u'project_id'] = project.id
                project_tool[u'project_title'] = project.title
                project_tool[u'tools'] = []
                tools = Tool.query.filter_by(project_id=project.id).all()
                for tool in tools:
                    project_tool[u'tools'].append(tool.to_json)
                result[u'projects_tools'].append(project_tool)
            if len(result[u'projects_tools']):
                return jsonify(result=result)
        else:
            return jsonify(result=result)
    return render_template('index.html')


@index.route('/advise/', methods=['POST', 'GET'])
def advise():
    advises = dict()
    if request.is_xhr:
        new_advise_str = request.args.get('advise').strip('"').replace(
            "'", "\"")
        new_advise = json.loads(new_advise_str)
        if new_advise['advise'] != '':
            from ..models import Advise, db
            advise = Advise(name=new_advise['name'],
                            advise=new_advise['advise'],
                            project_id=new_advise['project_id'])
            db.session.add(advise)
            db.session.commit()
        return jsonify(advises=advises)
