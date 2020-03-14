# -*- coding:utf-8 -*-
from . import index_blueprint as index
from flask import render_template, jsonify, request
import jieba
from functools import reduce
import json
import ast
from datetime import datetime
from my_app.errors import api_abort


@index.route('/', methods=['GET', 'POST'])
def hello():
    if request.is_xhr:
        from ..models.tool import Project, Tool

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
        timesheets = request.get_json().get('timesheets')

        items = []
        for timesheet in timesheets:
            name = timesheet.get('name', None)
            number = timesheet.get('number', None)
            date = timesheet.get('date', None)
            airplane = timesheet.get('airplane', u'无')
            task = timesheet.get('task', None)
            calculatedTime = timesheet.get('calculatedTime', None)
            completed = timesheet.get('completed', u'全部完成')
            kind = timesheet.get('kind', None)
            belongto_team = timesheet.get('belongto_team', None)
            approved = timesheet.get('approved', u'否')

            if calculatedTime == u'Infinity':
                return api_abort(403,
                                 u'你的工时里出现了 Infinity 代表无穷大的工时,这是不允许的,请联系管理员!')
            else:
                try:
                    number = int(number)
                    date = datetime.strptime(date, '%Y-%m-%d')
                    calculated_time = float(calculatedTime)
                except (UnicodeEncodeError, ValueError, TypeError) as e:
                    return api_abort(400, e.args[0])

                items.append(
                    Timesheet(name=name,
                              number=number,
                              date=date,
                              airplane=airplane,
                              task=task,
                              calculated_time=calculated_time,
                              completed=completed,
                              kind=kind,
                              belongto_team=belongto_team,
                              approved=approved))
        try:
            db.session.add_all(items)
            db.session.commit()
            return jsonify({
                'message': 'Timesheets created.',
                'count': len(items)
            }), 201
        except IntegrityError as e:
            db.session.rollback()
            return api_abort(409, e.args[0])
