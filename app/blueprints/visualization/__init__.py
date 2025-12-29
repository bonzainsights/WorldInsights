from flask import Blueprint

visualization_bp = Blueprint('visualization', __name__, url_prefix='/visualization')

from . import routes
