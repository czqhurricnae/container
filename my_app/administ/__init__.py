from flask import Blueprint
from my_app import STATIC_PATH
admin_blueprint = Blueprint('administ', __name__, static_folder = STATIC_PATH)
from . import views