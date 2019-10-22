# -*- coding:utf-8 -*-
from flask import Blueprint
from my_app import UPLOAD_PATH
documents_blueprint = Blueprint('documents',
                                __name__,
                                static_folder=UPLOAD_PATH)
from my_app.document import views
