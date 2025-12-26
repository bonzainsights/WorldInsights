"""
API routes for plot functionality.

This module provides RESTful endpoints for fetching plot data,
indicators, and countries.

Following Clean Architecture:
- Routes delegate to PlotService
- No business logic in routes
- Request validation via schemas
"""
from flask import Blueprint, request, jsonify
from typing import Dict, Any
from app.services.plot_service import PlotService
from app.core.logging import get_logger


logger = get_logger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize service
plot_service = PlotService()


@api_bp.route('/plot/indicators', methods=['GET'])
def get_indicators() -> tuple[Dict[str, Any], int]:
    """
    Get list of available indicators from all data sources.
    
    Returns:
        JSON response with indicators list or error
        
    Example response:
        {
            "indicators": [
                {
                    "code": "NY.GDP.MKTP.CD",
                    "name": "GDP (current US$)",
                    "description": "GDP at purchaser prices",
                    "source": "worldbank"
                },
                ...
            ],
            "count": 500
        }
    """
    logger.info("Fetching available indicators")
    
    try:
        indicators, error = plot_service.get_available_indicators()
        
        if error:
            logger.error(f"Failed to fetch indicators: {error}")
            return jsonify({'error': error}), 500
        
        logger.info(f"Successfully fetched {len(indicators)} indicators")
        return jsonify({
            'indicators': indicators,
            'count': len(indicators)
        }), 200
        
    except Exception as e:
        logger.error(f"Exception in get_indicators: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/plot/countries', methods=['GET'])
def get_countries() -> tuple[Dict[str, Any], int]:
    """
    Get list of available countries from all data sources.
    
    Returns:
        JSON response with countries list or error
        
    Example response:
        {
            "countries": [
                {
                    "code": "USA",
                    "name": "United States",
                    "source": "worldbank"
                },
                ...
            ],
            "count": 200
        }
    """
    logger.info("Fetching available countries")
    
    try:
        countries, error = plot_service.get_available_countries()
        
        if error:
            logger.error(f"Failed to fetch countries: {error}")
            return jsonify({'error': error}), 500
        
        logger.info(f"Successfully fetched {len(countries)} countries")
        return jsonify({
            'countries': countries,
            'count': len(countries)
        }), 200
        
    except Exception as e:
        logger.error(f"Exception in get_countries: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/plot/data', methods=['GET'])
def get_plot_data() -> tuple[Dict[str, Any], int]:
    """
    Get plot data for specified indicators and countries.
    
    Query Parameters:
        indicators (str): Comma-separated list of indicator codes
        countries (str): Comma-separated list of country codes
        start_year (int, optional): Start year for data range
        end_year (int, optional): End year for data range
        chart_type (str, optional): Chart type for data transformation
            Options: 'line', 'bar', 'scatter', 'choropleth'
    
    Returns:
        JSON response with plot data or error
        
    Example request:
        GET /api/plot/data?indicators=NY.GDP.MKTP.CD,SP.POP.TOTL&countries=USA,GBR&start_year=2015&end_year=2020&chart_type=line
        
    Example response:
        {
            "data": [...],
            "transformed": {...},  # If chart_type specified
            "count": 12
        }
    """
    logger.info("Fetching plot data")
    
    try:
        # Parse query parameters
        indicators_str = request.args.get('indicators', '')
        countries_str = request.args.get('countries', '')
        start_year = request.args.get('start_year', type=int)
        end_year = request.args.get('end_year', type=int)
        chart_type = request.args.get('chart_type', '')
        
        # Validate required parameters
        if not indicators_str:
            return jsonify({'error': 'indicators parameter is required'}), 400
        
        if not countries_str:
            return jsonify({'error': 'countries parameter is required'}), 400
        
        # Parse comma-separated lists
        indicators = [ind.strip() for ind in indicators_str.split(',') if ind.strip()]
        countries = [country.strip() for country in countries_str.split(',') if country.strip()]
        
        if not indicators:
            return jsonify({'error': 'At least one indicator is required'}), 400
        
        if not countries:
            return jsonify({'error': 'At least one country is required'}), 400
        
        logger.info(f"Fetching data for {len(indicators)} indicators, {len(countries)} countries")
        
        # Fetch data
        data, error = plot_service.fetch_plot_data(
            indicators=indicators,
            countries=countries,
            start_year=start_year,
            end_year=end_year
        )
        
        if error:
            logger.error(f"Failed to fetch plot data: {error}")
            return jsonify({'error': error}), 500
        
        response = {
            'data': data,
            'count': len(data)
        }
        
        # Transform data if chart_type specified
        if chart_type:
            logger.info(f"Transforming data for {chart_type} chart")
            transformed, transform_error = plot_service.transform_for_chart_type(data, chart_type)
            
            if transform_error:
                logger.warning(f"Failed to transform data: {transform_error}")
                response['transform_error'] = transform_error
            else:
                response['transformed'] = transformed
        
        logger.info(f"Successfully fetched {len(data)} data points")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Exception in get_plot_data: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/plot/correlations', methods=['GET'])
def get_correlations() -> tuple[Dict[str, Any], int]:
    """
    Calculate correlations between indicators.
    
    Query Parameters:
        indicators (str): Comma-separated list of indicator codes
        countries (str): Comma-separated list of country codes
        start_year (int, optional): Start year for data range
        end_year (int, optional): End year for data range
    
    Returns:
        JSON response with correlation matrix or error
        
    Example request:
        GET /api/plot/correlations?indicators=NY.GDP.MKTP.CD,SP.POP.TOTL&countries=USA,GBR,DEU&start_year=2010&end_year=2020
        
    Example response:
        {
            "correlations": {
                "NY.GDP.MKTP.CD": {
                    "NY.GDP.MKTP.CD": 1.0,
                    "SP.POP.TOTL": 0.85
                },
                "SP.POP.TOTL": {
                    "NY.GDP.MKTP.CD": 0.85,
                    "SP.POP.TOTL": 1.0
                }
            }
        }
    """
    logger.info("Calculating correlations")
    
    try:
        # Parse query parameters
        indicators_str = request.args.get('indicators', '')
        countries_str = request.args.get('countries', '')
        start_year = request.args.get('start_year', type=int)
        end_year = request.args.get('end_year', type=int)
        
        # Validate required parameters
        if not indicators_str:
            return jsonify({'error': 'indicators parameter is required'}), 400
        
        if not countries_str:
            return jsonify({'error': 'countries parameter is required'}), 400
        
        # Parse comma-separated lists
        indicators = [ind.strip() for ind in indicators_str.split(',') if ind.strip()]
        countries = [country.strip() for country in countries_str.split(',') if country.strip()]
        
        if len(indicators) < 2:
            return jsonify({'error': 'At least 2 indicators are required for correlation'}), 400
        
        logger.info(f"Calculating correlations for {len(indicators)} indicators")
        
        # Fetch data first
        data, error = plot_service.fetch_plot_data(
            indicators=indicators,
            countries=countries,
            start_year=start_year,
            end_year=end_year
        )
        
        if error:
            logger.error(f"Failed to fetch data for correlations: {error}")
            return jsonify({'error': error}), 500
        
        if not data:
            return jsonify({'error': 'No data available for correlation calculation'}), 404
        
        # Calculate correlations
        correlations, corr_error = plot_service.calculate_correlations(data)
        
        if corr_error:
            logger.error(f"Failed to calculate correlations: {corr_error}")
            return jsonify({'error': corr_error}), 500
        
        logger.info("Successfully calculated correlations")
        return jsonify({'correlations': correlations}), 200
        
    except Exception as e:
        logger.error(f"Exception in get_correlations: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


# Health check endpoint
@api_bp.route('/health', methods=['GET'])
def health_check() -> tuple[Dict[str, str], int]:
    """
    Health check endpoint for API.
    
    Returns:
        JSON response with status
    """
    return jsonify({'status': 'healthy', 'service': 'plot-api'}), 200
