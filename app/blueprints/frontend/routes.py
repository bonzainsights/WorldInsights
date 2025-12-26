"""
Frontend routes for WorldInsights.

Serves HTML pages for the user interface.
"""
from flask import Blueprint, render_template

# Create blueprint
frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/plot')
def plot():
    """
    Plot exploration page.
    
    Allows users to select indicators, countries, and generate interactive plots.
    """
    return render_template('plot.html')


@frontend_bp.route('/api')
def api_docs():
    """
    API documentation page.
    
    Displays information about all data sources and internal API endpoints.
    """
    return render_template('api_docs.html')
