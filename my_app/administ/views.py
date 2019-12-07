# -*- coding:utf-8 -*-
import os
import re
from flask import render_template, request, json
from my_app.administ import admin_blueprint as administ
from werkzeug.utils import secure_filename
from my_app import UPLOAD_PATH


@administ.route('/upload/', methods=['GET', 'POST'])
def upload():
    result = {}
    action = request.args.get('action')
    with open(
            os.path.join(administ.static_folder, 'ueditor', 'php',
                         'config.json')) as fp:
        try:
            CONFIG = json.loads(re.sub(r'\/\*.*\*\/', '', fp.read()))
        except:
            CONFIG = {}

    if action == 'config':
        result = CONFIG

    if action in ('uploadimage', 'uploadvideo', 'uploadfile'):
        upfile = request.files['upfile']  # 这个表单名称以配置文件为准
        # upfile 为 FileStorage 对象
        # 这里保存文件并返回相应的URL
        filename = secure_filename(upfile.filename)
        upfile.save(UPLOAD_PATH, filename)
        result = {
            "state": "SUCCESS",
            "url": "upload/demo.jpg",
            "title": "demo.jpg",
            "original": "demo.jpg"
        }
    return json.dumps(result)
