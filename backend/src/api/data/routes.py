
from flask import request, jsonify, Blueprint
from src.api.data import bp
from src.services.data_retrieval_service import DataRetrievalService
from src.services.plot_service import PlotService
import logging

logger = logging.getLogger(__name__)

# Initialize services
data_service = DataRetrievalService()
plot_service = PlotService()

@bp.route('/indicator/<source>/<indicator_code>', methods=['GET'])
def get_lake_data(source: str, indicator_code: str):
    """
    Get generic data from the Data Retrieval Service (Lake -> API Hybrid).
    """
    country = request.args.get('country')
    year = request.args.get('year', type=int)
    
    try:
        data = data_service.get_data(source, indicator_code, country, year)
        if not data:
            return jsonify({'error': 'No data found'}), 404
            
        return jsonify({'data': data, 'count': len(data)}), 200
    except Exception as e:
        logger.error(f"Error getting data: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/globe', methods=['GET'])
def get_globe_data():
    """
    Get GeoJSON data for 3D Globe visualization.
    """
    source = request.args.get('source')
    indicator = request.args.get('indicator')
    year = request.args.get('year', type=int)
    
    if not all([source, indicator, year]):
        return jsonify({'error': 'Missing source, indicator, or year params'}), 400
        
    try:
        data = data_service.get_globe_data(source, indicator, year)
        if not data:
            return jsonify({'error': 'No globe data found'}), 404
            
        # Construct FeatureCollection
        features = []
        import json
        for row in data:
            try:
                geom = json.loads(row['geometry'])
            except:
                continue
            
            features.append({
                "type": "Feature",
                "properties": {
                    "name": row['name'],
                    "iso_code": row['iso_code'],
                    "value": row['value'],
                    "year": row['year'],
                    "formatted_value": f"{row['value']:,.2f}" if row['value'] else "N/A"
                },
                "geometry": geom
            })
            
        return jsonify({
            "type": "FeatureCollection",
            "features": features
        }), 200
        
    except Exception as e:
        logger.error(f"Globe Error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/plot/indicators', methods=['GET'])
def get_indicators():
    try:
        indicators, error = plot_service.get_available_indicators()
        if error: return jsonify({'error': error}), 500
        return jsonify({'indicators': indicators, 'count': len(indicators)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/plot/countries', methods=['GET'])
def get_countries():
    try:
        countries, error = plot_service.get_available_countries()
        if error: return jsonify({'error': error}), 500
        return jsonify({'countries': countries, 'count': len(countries)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/plot/data', methods=['GET'])
def get_plot_data():
    indicators_str = request.args.get('indicators', '')
    countries_str = request.args.get('countries', '')
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    
    if not indicators_str or not countries_str:
        return jsonify({'error': 'Missing indicators or countries'}), 400
        
    indicators = [i.strip() for i in indicators_str.split(',') if i.strip()]
    countries = [c.strip() for c in countries_str.split(',') if c.strip()]
    
    try:
        data, error = plot_service.fetch_plot_data(indicators, countries, start_year, end_year)
        if not data and error: return jsonify({'error': error}), 500
        return jsonify({'data': data or [], 'warning': error}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
