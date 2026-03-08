"""
Data Sources routes for WorldInsights.

Provides endpoints for browsing data sources and indicators.
"""
from flask import Blueprint, render_template, request

# Create blueprint
data_sources_bp = Blueprint('data_sources', __name__, url_prefix='/data-sources')


@data_sources_bp.route('/')
def index():
    """
    Data Sources overview page.

    Displays all available data sources with statistics and browse options.
    """
    return render_template('data_sources/index.html')


@data_sources_bp.route('/indicators')
def indicators():
    """
    Indicator Browser page.

    Searchable, filterable list of all available indicators.
    """
    return render_template('data_sources/indicators.html')


@data_sources_bp.route('/<source>')
def source_detail(source):
    """
    Data Source detail page.

    Shows indicators and statistics for a specific data source.
    """
    # TODO: Implement source detail page
    return render_template('data_sources/source_detail.html', source=source)
