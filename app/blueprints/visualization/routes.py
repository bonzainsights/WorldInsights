"""
Visualization routes for WorldInsights.

Provides endpoints for data visualizations including 3D globe.
"""
from flask import Blueprint, render_template

# Create blueprint
visualization_bp = Blueprint('visualization', __name__, url_prefix='/visualization')


@visualization_bp.route('/globe')
def globe():
    """
    3D Globe Visualization page.

    Interactive 3D globe with choropleth mapping for global data visualization.
    """
    return render_template('visualization/globe.html')


@visualization_bp.route('/charts')
def charts():
    """
    Charts overview page.

    Gallery of available chart types and visualizations.
    """
    # TODO: Implement charts gallery
    return render_template('visualization/charts.html')


@visualization_bp.route('/map')
def map():
    """
    Interactive Map page.

    2D map visualization with data overlays.
    """
    # TODO: Implement map visualization
    return render_template('visualization/map.html')
