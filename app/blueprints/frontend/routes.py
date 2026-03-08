"""
Frontend routes for WorldInsights.

Serves HTML pages for the user interface.
"""
from flask import Blueprint, render_template

# Create blueprint
frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/')
def index():
    """
    Homepage.

    Main landing page with hero section, features, and data sources overview.
    """
    return render_template('index.html')


@frontend_bp.route('/plot')
def plot():
    """
    Plot exploration page (legacy).

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


@frontend_bp.route('/about')
def about():
    """
    About page.

    Information about WorldInsights platform.
    """
    return render_template('about.html')


@frontend_bp.route('/contact')
def contact():
    """
    Contact page.

    Contact form and information.
    """
    return render_template('contact.html')


@frontend_bp.route('/privacy')
def privacy():
    """
    Privacy policy page.
    """
    return render_template('privacy.html')


@frontend_bp.route('/terms')
def terms():
    """
    Terms of service page.
    """
    return render_template('terms.html')
