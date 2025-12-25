"""
Tests for World Bank API client.

Following TDD - these tests define expected behavior before implementation.
"""
import pytest
from unittest.mock import Mock, patch
from app.infrastructure.api_clients.worldbank import WorldBankClient


class TestWorldBankClient:
    """Test suite for World Bank API client."""
    
    def test_initialization(self):
        """Test client initializes with correct World Bank API URL."""
        client = WorldBankClient()
        
        assert 'worldbank.org' in client.base_url
        assert client.session is not None
    
    @patch('requests.Session.get')
    def test_get_countries_success(self, mock_get):
        """Test fetching list of countries."""
        # Mock World Bank API response format
        mock_response = Mock()
        mock_response.json.return_value = [
            {'page': 1, 'pages': 1, 'per_page': 50, 'total': 2},
            [
                {'id': 'USA', 'name': 'United States', 'capitalCity': 'Washington D.C.'},
                {'id': 'GBR', 'name': 'United Kingdom', 'capitalCity': 'London'}
            ]
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = WorldBankClient()
        countries, error = client.get_countries()
        
        assert error is None
        assert len(countries) == 2
        assert countries[0]['code'] == 'USA'
        assert countries[0]['name'] == 'United States'
        assert countries[1]['code'] == 'GBR'
    
    @patch('requests.Session.get')
    def test_get_indicators_success(self, mock_get):
        """Test fetching list of indicators."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {'page': 1, 'pages': 1, 'per_page': 50, 'total': 2},
            [
                {
                    'id': 'NY.GDP.MKTP.CD',
                    'name': 'GDP (current US$)',
                    'sourceNote': 'GDP at purchaser prices'
                },
                {
                    'id': 'SP.POP.TOTL',
                    'name': 'Population, total',
                    'sourceNote': 'Total population'
                }
            ]
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = WorldBankClient()
        indicators, error = client.get_indicators()
        
        assert error is None
        assert len(indicators) == 2
        assert indicators[0]['code'] == 'NY.GDP.MKTP.CD'
        assert indicators[0]['name'] == 'GDP (current US$)'
        assert 'description' in indicators[0]
    
    @patch('requests.Session.get')
    def test_get_data_success(self, mock_get):
        """Test fetching data for specific country and indicator."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {'page': 1, 'pages': 1, 'per_page': 50, 'total': 3},
            [
                {
                    'indicator': {'id': 'NY.GDP.MKTP.CD', 'value': 'GDP (current US$)'},
                    'country': {'id': 'USA', 'value': 'United States'},
                    'countryiso3code': 'USA',
                    'date': '2020',
                    'value': 21000000000000,
                    'unit': '',
                    'obs_status': '',
                    'decimal': 0
                },
                {
                    'indicator': {'id': 'NY.GDP.MKTP.CD', 'value': 'GDP (current US$)'},
                    'country': {'id': 'USA', 'value': 'United States'},
                    'countryiso3code': 'USA',
                    'date': '2019',
                    'value': 21400000000000,
                    'unit': '',
                    'obs_status': '',
                    'decimal': 0
                }
            ]
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = WorldBankClient()
        data, error = client.get_data('USA', 'NY.GDP.MKTP.CD', start_year=2019, end_year=2020)
        
        assert error is None
        assert len(data) == 2
        # Check normalization to standard schema
        assert data[0]['country'] == 'USA'
        assert data[0]['year'] == 2020
        assert data[0]['indicator'] == 'NY.GDP.MKTP.CD'
        assert data[0]['value'] == 21000000000000
        assert data[0]['source'] == 'World Bank'
    
    @patch('requests.Session.get')
    def test_get_data_with_null_values(self, mock_get):
        """Test handling of null/missing values in data."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {'page': 1, 'pages': 1, 'per_page': 50, 'total': 2},
            [
                {
                    'indicator': {'id': 'NY.GDP.MKTP.CD', 'value': 'GDP'},
                    'country': {'id': 'USA', 'value': 'United States'},
                    'countryiso3code': 'USA',
                    'date': '2020',
                    'value': None,  # Null value
                    'unit': '',
                    'obs_status': '',
                    'decimal': 0
                },
                {
                    'indicator': {'id': 'NY.GDP.MKTP.CD', 'value': 'GDP'},
                    'country': {'id': 'USA', 'value': 'United States'},
                    'countryiso3code': 'USA',
                    'date': '2019',
                    'value': 21400000000000,
                    'unit': '',
                    'obs_status': '',
                    'decimal': 0
                }
            ]
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = WorldBankClient()
        data, error = client.get_data('USA', 'NY.GDP.MKTP.CD')
        
        assert error is None
        assert len(data) == 2
        assert data[0]['value'] is None
        assert data[1]['value'] == 21400000000000
    
    @patch('requests.Session.get')
    def test_get_data_with_date_range(self, mock_get):
        """Test that date range is properly included in request."""
        mock_response = Mock()
        mock_response.json.return_value = [{'page': 1}, []]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = WorldBankClient()
        client.get_data('USA', 'NY.GDP.MKTP.CD', start_year=2015, end_year=2020)
        
        # Verify the date parameter was included
        call_args = mock_get.call_args
        assert 'params' in call_args[1]
        assert 'date' in call_args[1]['params']
        assert call_args[1]['params']['date'] == '2015:2020'
    
    @patch('requests.Session.get')
    def test_get_countries_handles_empty_response(self, mock_get):
        """Test handling of empty country list."""
        mock_response = Mock()
        mock_response.json.return_value = [{'page': 1}, []]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = WorldBankClient()
        countries, error = client.get_countries()
        
        assert error is None
        assert countries == []
    
    @patch('requests.Session.get')
    def test_pagination_support(self, mock_get):
        """Test that client properly handles pagination parameters."""
        mock_response = Mock()
        mock_response.json.return_value = [{'page': 1}, []]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = WorldBankClient()
        client.get_indicators(per_page=100)
        
        # Verify per_page parameter
        call_args = mock_get.call_args
        assert call_args[1]['params']['per_page'] == 100
    
    def test_normalize_worldbank_data(self):
        """Test normalization of World Bank specific data format."""
        client = WorldBankClient()
        
        raw_data = [
            {
                'indicator': {'id': 'NY.GDP.MKTP.CD', 'value': 'GDP'},
                'country': {'id': 'USA', 'value': 'United States'},
                'countryiso3code': 'USA',
                'date': '2020',
                'value': 21000000000000
            }
        ]
        
        normalized = client._normalize_worldbank_data(raw_data)
        
        assert len(normalized) == 1
        assert normalized[0]['country'] == 'USA'
        assert normalized[0]['year'] == 2020
        assert normalized[0]['indicator'] == 'NY.GDP.MKTP.CD'
        assert normalized[0]['value'] == 21000000000000
        assert normalized[0]['source'] == 'World Bank'
