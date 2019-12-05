# -*- coding:utf-8 -*-
from . import index_blueprint as index
from flask import render_template, jsonify, request
import jieba
from functools import reduce
import json
import ast
from datetime import datetime


@index.route('/', methods=['GET', 'POST'])
def hello():
    if request.is_xhr:
        from ..models import Project, Tool

        search = request.args.get('search', '')
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
                project_tools = dict()
                project_tools[u'project_id'] = project.id
                project_tools[u'project_title'] = project.title
                project_tools[u'tools'] = []
                tools = Tool.query.filter_by(project_id=project.id).all()
                for tool in tools:
                    project_tools[u'tools'].append(tool.to_html)
                result[u'projects_tools'].append(project_tools)
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


@index.route('/api/timesheets', methods=['POST', 'GET'])
def timesheets():
    from my_app.models.timesheet import Timesheet, db
    if request.method == 'POST':
        timesheets = request.get_json().get(u'timesheets')
        items = []
        for timesheet in timesheets:
            items.append(
                Timesheet(name=timesheet.get(u'name'),
                          number=int(timesheet.get(u'number')),
                          date=datetime.strptime(timesheet.get(u'date'),
                                                 '%Y-%m-%d'),
                          airplane=timesheet.get(u'airplane'),
                          task=timesheet.get(u'task'),
                          tasktime=float(timesheet.get(u'tasktime')),
                          kind=timesheet.get(u'kind'),
                          belongto_team=timesheet.get(u'belongto_team'),
                          approved=timesheet.get(u'approved', u'否')))
        db.session.add_all(items)
        db.session.commit()
    return 'timesheets commit successfully.'
