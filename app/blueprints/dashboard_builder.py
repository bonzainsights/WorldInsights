"""
Dashboard Builder routes for WorldInsights.

This blueprint provides the advanced dashboard builder with:
- Movable, resizable panels
- Smart data filtering (cascade filters)
- Chart customization
- Annotations and shapes
- Save/load/export functionality

Following Clean Architecture:
- Routes delegate to services
- No business logic in routes
- Request/response handling only
"""
from flask import Blueprint, render_template, request, jsonify, session
from typing import Dict, Any
import uuid
from datetime import datetime

from app.core.logging import get_logger
from app.services.availability import AvailabilityService
from app.services.data_ingestion import DataIngestionService
from app.services.plot_service import PlotService

# Create blueprint
dashboard_builder_bp = Blueprint('dashboard_builder', __name__, url_prefix='/dashboard')

# Initialize services
availability_service = AvailabilityService()
ingestion_service = DataIngestionService()
plot_service = PlotService()

logger = get_logger(__name__)


# ==========================================================================
# Dashboard Builder UI
# ==========================================================================

@dashboard_builder_bp.route('/builder')
def builder():
    """
    Dashboard Builder - Main Interface.

    Provides a canvas-based interface for creating custom dashboards with:
    - Draggable, resizable panels
    - Data source selection with smart filtering
    - Chart customization
    - Annotations and shapes
    """
    return render_template('dashboard/builder.html')


@dashboard_builder_bp.route('/saved')
def saved_dashboards():
    """
    List saved dashboards for current user.
    """
    return render_template('dashboard/saved.html')


# ==========================================================================
# Smart Filtering API Endpoints
# ==========================================================================

@dashboard_builder_bp.route('/api/availability/summary', methods=['GET'])
def get_availability_summary():
    """
    Get comprehensive availability summary for dashboard builder.

    Query Parameters:
        provider (str): Provider ID (e.g., 'who', 'world_bank')
        countries (str): Comma-separated country codes (optional)
        indicators (str): Comma-separated indicator codes (optional)

    Returns:
        JSON with providers, indicators, countries, years, and counts
    """
    provider = request.args.get('provider')
    countries_str = request.args.get('countries', '')
    indicators_str = request.args.get('indicators', '')

    country_codes = [c.strip() for c in countries_str.split(',') if c.strip()] if countries_str else []
    indicator_codes = [i.strip() for i in indicators_str.split(',') if i.strip()] if indicators_str else []

    try:
        summary = availability_service.get_availability_summary(
            provider=provider,
            country_codes=country_codes,
            indicator_codes=indicator_codes
        )

        return jsonify(summary), 200

    except Exception as e:
        logger.error(f"Error getting availability summary: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_builder_bp.route('/api/availability/countries', methods=['GET'])
def get_countries_for_indicators():
    """
    Get countries that have ALL specified indicators.

    Implements cascade filter: Provider → Indicators → Countries

    Query Parameters:
        provider (str): Provider ID (required)
        indicators (str): Comma-separated indicator codes (required)

    Returns:
        JSON list of countries
    """
    provider = request.args.get('provider')
    indicators_str = request.args.get('indicators', '')

    if not provider or not indicators_str:
        return jsonify({'error': 'provider and indicators are required'}), 400

    indicator_codes = [i.strip() for i in indicators_str.split(',') if i.strip()]

    try:
        countries = availability_service.get_countries_for_indicators(
            provider=provider,
            indicator_codes=indicator_codes
        )

        return jsonify({
            'countries': countries,
            'count': len(countries)
        }), 200

    except Exception as e:
        logger.error(f"Error getting countries for indicators: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_builder_bp.route('/api/availability/indicators', methods=['GET'])
def get_indicators_for_countries():
    """
    Get indicators available for ALL specified countries.

    Implements reverse cascade filter: Provider → Countries → Indicators

    Query Parameters:
        provider (str): Provider ID (required)
        countries (str): Comma-separated country codes (required)

    Returns:
        JSON list of indicators
    """
    provider = request.args.get('provider')
    countries_str = request.args.get('countries', '')

    if not provider or not countries_str:
        return jsonify({'error': 'provider and countries are required'}), 400

    country_codes = [c.strip() for c in countries_str.split(',') if c.strip()]

    try:
        indicators = availability_service.get_indicators_for_countries(
            provider=provider,
            country_codes=country_codes
        )

        return jsonify({
            'indicators': indicators,
            'count': len(indicators)
        }), 200

    except Exception as e:
        logger.error(f"Error getting indicators for countries: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_builder_bp.route('/api/availability/years', methods=['GET'])
def get_years_for_selection():
    """
    Get available year range for selection.

    Query Parameters:
        provider (str): Provider ID (required)
        countries (str): Comma-separated country codes (required)
        indicators (str): Comma-separated indicator codes (required)

    Returns:
        JSON with min_year, max_year, available_years
    """
    provider = request.args.get('provider')
    countries_str = request.args.get('countries', '')
    indicators_str = request.args.get('indicators', '')

    if not provider or not countries_str or not indicators_str:
        return jsonify({'error': 'provider, countries, and indicators are required'}), 400

    country_codes = [c.strip() for c in countries_str.split(',') if c.strip()]
    indicator_codes = [i.strip() for i in indicators_str.split(',') if i.strip()]

    try:
        years = availability_service.get_years_for_selection(
            provider=provider,
            country_codes=country_codes,
            indicator_codes=indicator_codes
        )

        return jsonify(years), 200

    except Exception as e:
        logger.error(f"Error getting years for selection: {e}")
        return jsonify({'error': str(e)}), 500


# ==========================================================================
# Data Fetching Endpoints
# ==========================================================================

@dashboard_builder_bp.route('/api/data', methods=['POST'])
def fetch_dashboard_data():
    """
    Fetch data for dashboard panel.

    Request Body:
        provider (str): Provider ID
        countries (list): List of country codes
        indicators (list): List of indicator codes
        start_year (int): Start year
        end_year (int): End year
        chart_type (str): Chart type ('line', 'bar', 'scatter', etc.)

    Returns:
        JSON with data and plot configuration
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    provider = data.get('provider')
    countries = data.get('countries', [])
    indicators = data.get('indicators', [])
    start_year = data.get('start_year')
    end_year = data.get('end_year')
    chart_type = data.get('chart_type', 'line')

    if not provider or not countries or not indicators:
        return jsonify({'error': 'provider, countries, and indicators are required'}), 400

    try:
        # Fetch data
        plot_data, error = plot_service.fetch_plot_data(
            indicators=indicators,
            countries=countries,
            start_year=start_year,
            end_year=end_year,
            sources=[provider]
        )

        if error:
            return jsonify({'error': error}), 404

        if not plot_data:
            return jsonify({'error': 'No data found for selection'}), 404

        # Transform for chart type
        transformed, transform_error = plot_service.transform_for_chart_type(
            plot_data,
            chart_type
        )

        response = {
            'data': plot_data,
            'count': len(plot_data),
            'provider': provider
        }

        if transformed:
            response['plot_config'] = transformed

        if transform_error:
            response['transform_warning'] = transform_error

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        return jsonify({'error': str(e)}), 500


# ==========================================================================
# Dashboard Management Endpoints
# ==========================================================================

@dashboard_builder_bp.route('/api/save', methods=['POST'])
def save_dashboard():
    """
    Save dashboard configuration.

    For now, saves to session storage.
    Future: Save to database with user association.

    Request Body:
        title (str): Dashboard title
        description (str): Dashboard description (optional)
        layout (dict): Panel positions and sizes
        panels (list): Panel configurations
        filters (dict): Applied filters
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    # Generate dashboard ID
    dashboard_id = str(uuid.uuid4())

    # Create dashboard record
    dashboard = {
        'id': dashboard_id,
        'title': data.get('title', 'Untitled Dashboard'),
        'description': data.get('description', ''),
        'layout': data.get('layout', {}),
        'panels': data.get('panels', []),
        'filters': data.get('filters', {}),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'user_id': session.get('user_id') if 'user_id' in session else None,
        'is_public': data.get('is_public', False)
    }

    # Save to session (temporary - will move to database)
    if 'dashboards' not in session:
        session['dashboards'] = {}

    session['dashboards'][dashboard_id] = dashboard
    session.modified = True

    logger.info(f"Saved dashboard {dashboard_id}")

    return jsonify({
        'id': dashboard_id,
        'message': 'Dashboard saved successfully'
    }), 200


@dashboard_builder_bp.route('/api/load/<dashboard_id>', methods=['GET'])
def load_dashboard(dashboard_id):
    """
    Load dashboard by ID.
    """
    if 'dashboards' not in session:
        return jsonify({'error': 'Dashboard not found'}), 404

    dashboard = session['dashboards'].get(dashboard_id)
    if not dashboard:
        return jsonify({'error': 'Dashboard not found'}), 404

    return jsonify(dashboard), 200


@dashboard_builder_bp.route('/api/list', methods=['GET'])
def list_dashboards():
    """
    List all saved dashboards for current user.
    """
    if 'dashboards' not in session:
        return jsonify({'dashboards': []}), 200

    dashboards = []
    for id, dashboard in session['dashboards'].items():
        dashboards.append({
            'id': dashboard['id'],
            'title': dashboard['title'],
            'description': dashboard.get('description', ''),
            'created_at': dashboard['created_at'],
            'updated_at': dashboard['updated_at'],
            'is_public': dashboard.get('is_public', False)
        })

    return jsonify({'dashboards': dashboards}), 200


@dashboard_builder_bp.route('/api/delete/<dashboard_id>', methods=['DELETE'])
def delete_dashboard(dashboard_id):
    """
    Delete dashboard by ID.
    """
    if 'dashboards' not in session:
        return jsonify({'error': 'Dashboard not found'}), 404

    if dashboard_id in session['dashboards']:
        del session['dashboards'][dashboard_id]
        session.modified = True
        logger.info(f"Deleted dashboard {dashboard_id}")

    return jsonify({'message': 'Dashboard deleted successfully'}), 200


# ==========================================================================
# Export Endpoints
# ==========================================================================

@dashboard_builder_bp.route('/api/export/<dashboard_id>/png', methods=['GET'])
def export_dashboard_png(dashboard_id):
    """
    Export dashboard as PNG image.

    Future implementation:
    - Render dashboard to image using headless browser
    - Return high-resolution PNG
    """
    return jsonify({
        'error': 'Not implemented yet',
        'message': 'PNG export will be available in future update'
    }), 501


@dashboard_builder_bp.route('/api/export/<dashboard_id>/json', methods=['GET'])
def export_dashboard_json(dashboard_id):
    """
    Export dashboard configuration as JSON.
    """
    if 'dashboards' not in session:
        return jsonify({'error': 'Dashboard not found'}), 404

    dashboard = session['dashboards'].get(dashboard_id)
    if not dashboard:
        return jsonify({'error': 'Dashboard not found'}), 404

    return jsonify(dashboard), 200
