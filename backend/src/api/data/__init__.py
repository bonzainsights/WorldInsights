from flask import Blueprint

bp = Blueprint('data', __name__)

from . import routes
