"""
Integration tests for Plot API endpoints.

Tests the full request-response cycle for plot API routes.
"""
import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from app.create_app import create_app


@pytest.fixture
def app():
    """Create Flask app for testing."""
    test_config = {
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'RATE_LIMIT_ENABLED': False,
        'REQUIRE_HTTPS': False
    }
    app = create_app(config=test_config)
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestPlotAPIEndpoints:
    """Integration tests for plot API endpoints."""
    
    @patch('app.services.plot_service.PlotService.get_available_indicators')
    def test_get_indicators_success(self, mock_get_indicators, client):
        """Test GET /api/plot/indicators endpoint."""
        # Mock service response
        mock_get_indicators.return_value = (
            [
                {'code': 'NY.GDP.MKTP.CD', 'name': 'GDP', 'description': 'GDP in current US$', 'source': 'worldbank'},
                {'code': 'SP.POP.TOTL', 'name': 'Population', 'description': 'Total population', 'source': 'worldbank'}
            ],
            None
        )
        
        response = client.get('/api/plot/indicators')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'indicators' in data
        assert 'count' in data
        assert data['count'] == 2
        assert len(data['indicators']) == 2
    
    @patch('app.services.plot_service.PlotService.get_available_indicators')
    def test_get_indicators_error(self, mock_get_indicators, client):
        """Test GET /api/plot/indicators with error."""
        mock_get_indicators.return_value = (None, "API error")
        
        response = client.get('/api/plot/indicators')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    @patch('app.services.plot_service.PlotService.get_available_countries')
    def test_get_countries_success(self, mock_get_countries, client):
        """Test GET /api/plot/countries endpoint."""
        mock_get_countries.return_value = (
            [
                {'code': 'USA', 'name': 'United States', 'source': 'worldbank'},
                {'code': 'GBR', 'name': 'United Kingdom', 'source': 'worldbank'}
            ],
            None
        )
        
        response = client.get('/api/plot/countries')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'countries' in data
        assert 'count' in data
        assert data['count'] == 2
    
    @patch('app.services.plot_service.PlotService.fetch_plot_data')
    def test_get_plot_data_success(self, mock_fetch_data, client):
        """Test GET /api/plot/data endpoint."""
        mock_fetch_data.return_value = (
            [
                {'country': 'USA', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21000000000000, 'source': 'World Bank'},
                {'country': 'USA', 'year': 2019, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21400000000000, 'source': 'World Bank'}
            ],
            None
        )
        
        response = client.get('/api/plot/data?indicators=NY.GDP.MKTP.CD&countries=USA&start_year=2019&end_year=2020')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'count' in data
        assert data['count'] == 2
    
    def test_get_plot_data_missing_indicators(self, client):
        """Test GET /api/plot/data without indicators parameter."""
        response = client.get('/api/plot/data?countries=USA')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'indicators' in data['error'].lower()
    
    def test_get_plot_data_missing_countries(self, client):
        """Test GET /api/plot/data without countries parameter."""
        response = client.get('/api/plot/data?indicators=NY.GDP.MKTP.CD')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'countries' in data['error'].lower()
    
    @patch('app.services.plot_service.PlotService.fetch_plot_data')
    @patch('app.services.plot_service.PlotService.transform_for_chart_type')
    def test_get_plot_data_with_chart_type(self, mock_transform, mock_fetch_data, client):
        """Test GET /api/plot/data with chart_type parameter."""
        mock_fetch_data.return_value = (
            [{'country': 'USA', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 21000000000000}],
            None
        )
        mock_transform.return_value = (
            {'NY.GDP.MKTP.CD': {'USA': {2020: 21000000000000}}},
            None
        )
        
        response = client.get('/api/plot/data?indicators=NY.GDP.MKTP.CD&countries=USA&chart_type=line')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'transformed' in data
    
    @patch('app.services.plot_service.PlotService.fetch_plot_data')
    def test_get_plot_data_multiple_indicators_countries(self, mock_fetch_data, client):
        """Test GET /api/plot/data with multiple indicators and countries."""
        mock_fetch_data.return_value = (
            [
                {'country': 'USA', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 100},
                {'country': 'USA', 'year': 2020, 'indicator': 'SP.POP.TOTL', 'value': 200},
                {'country': 'GBR', 'year': 2020, 'indicator': 'NY.GDP.MKTP.CD', 'value': 300},
                {'country': 'GBR', 'year': 2020, 'indicator': 'SP.POP.TOTL', 'value': 400}
            ],
            None
        )
        
        response = client.get('/api/plot/data?indicators=NY.GDP.MKTP.CD,SP.POP.TOTL&countries=USA,GBR')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 4
    
    @patch('app.services.plot_service.PlotService.fetch_plot_data')
    @patch('app.services.plot_service.PlotService.calculate_correlations')
    def test_get_correlations_success(self, mock_calc_corr, mock_fetch_data, client):
        """Test GET /api/plot/correlations endpoint."""
        mock_fetch_data.return_value = (
            [
                {'country': 'USA', 'year': 2020, 'indicator': 'IND1', 'value': 10},
                {'country': 'USA', 'year': 2020, 'indicator': 'IND2', 'value': 20}
            ],
            None
        )
        mock_calc_corr.return_value = (
            {
                'IND1': {'IND1': 1.0, 'IND2': 0.85},
                'IND2': {'IND1': 0.85, 'IND2': 1.0}
            },
            None
        )
        
        response = client.get('/api/plot/correlations?indicators=IND1,IND2&countries=USA')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'correlations' in data
        assert 'IND1' in data['correlations']
        assert 'IND2' in data['correlations']
    
    def test_get_correlations_missing_indicators(self, client):
        """Test GET /api/plot/correlations without indicators."""
        response = client.get('/api/plot/correlations?countries=USA')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_get_correlations_insufficient_indicators(self, client):
        """Test GET /api/plot/correlations with only one indicator."""
        response = client.get('/api/plot/correlations?indicators=IND1&countries=USA')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert '2 indicators' in data['error'].lower()
    
    @patch('app.services.plot_service.PlotService.fetch_plot_data')
    def test_get_correlations_no_data(self, mock_fetch_data, client):
        """Test GET /api/plot/correlations when no data is available."""
        mock_fetch_data.return_value = ([], None)
        
        response = client.get('/api/plot/correlations?indicators=IND1,IND2&countries=USA')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_health_check(self, client):
        """Test GET /api/health endpoint."""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'plot-api'
