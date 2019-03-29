from flask import Blueprint
from my_app import STATIC_PATH

index_blueprint = Blueprint('index', __name__, static_folder = STATIC_PATH)
from . import views