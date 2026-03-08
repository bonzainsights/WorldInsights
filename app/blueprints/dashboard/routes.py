"""
Dashboard routes for WorldInsights.

Provides endpoints for dashboard builder and saved dashboards.
"""
from flask import Blueprint, render_template

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/builder')
def builder():
    """
    Dashboard Builder page.

    Interactive dashboard builder with country/indicator selection,
    chart type options, and save/load functionality.
    """
    return render_template('dashboard/builder.html')


@dashboard_bp.route('/saved')
def saved():
    """
    Saved Dashboards page.

    List of user's saved dashboard configurations.
    """
    # TODO: Implement saved dashboards list
    return render_template('dashboard/saved.html')
