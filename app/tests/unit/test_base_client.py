"""
Tests for the base API client.

Following TDD principles - these tests define the expected behavior
of the BaseAPIClient class.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests
from app.infrastructure.api_clients.base_client import BaseAPIClient


class ConcreteAPIClient(BaseAPIClient):
    """Concrete implementation for testing the abstract base class."""
    
    def get_countries(self):
        data, error = self._make_request('countries')
        if error:
            return None, error
        return data.get('countries', []), None
    
    def get_indicators(self):
        data, error = self._make_request('indicators')
        if error:
            return None, error
        return data.get('indicators', []), None
    
    def get_data(self, country_code, indicator_code, start_year=None, end_year=None):
        params = {
            'country': country_code,
            'indicator': indicator_code
        }
        if start_year:
            params['start_year'] = start_year
        if end_year:
            params['end_year'] = end_year
        
        data, error = self._make_request('data', params=params)
        if error:
            return None, error
        return data.get('data', []), None


class TestBaseAPIClient:
    """Test suite for BaseAPIClient."""
    
    def test_initialization(self):
        """Test that client initializes with correct defaults."""
        client = ConcreteAPIClient('https://api.example.com')
        
        assert client.base_url == 'https://api.example.com'
        assert client.timeout == 30
        assert client.rate_limit_delay == 0.1
        assert client.session is not None
    
    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        client = ConcreteAPIClient(
            'https://api.example.com/',
            timeout=60,
            max_retries=5,
            rate_limit_delay=0.5
        )
        
        assert client.base_url == 'https://api.example.com'
        assert client.timeout == 60
        assert client.rate_limit_delay == 0.5
    
    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base URL."""
        client = ConcreteAPIClient('https://api.example.com/')
        assert client.base_url == 'https://api.example.com'
    
    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'success', 'data': [1, 2, 3]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = ConcreteAPIClient('https://api.example.com')
        data, error = client._make_request('test-endpoint')
        
        assert error is None
        assert data == {'status': 'success', 'data': [1, 2, 3]}
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_make_request_with_params(self, mock_get):
        """Test API request with query parameters."""
        mock_response = Mock()
        mock_response.json.return_value = {'result': 'ok'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = ConcreteAPIClient('https://api.example.com')
        params = {'country': 'USA', 'year': 2020}
        data, error = client._make_request('data', params=params)
        
        assert error is None
        assert data == {'result': 'ok'}
        
        # Verify params were passed
        call_args = mock_get.call_args
        assert call_args[1]['params'] == params
    
    @patch('requests.Session.get')
    def test_make_request_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        client = ConcreteAPIClient('https://api.example.com')
        data, error = client._make_request('test-endpoint')
        
        assert data is None
        assert 'timed out' in error.lower()
    
    @patch('requests.Session.get')
    def test_make_request_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        client = ConcreteAPIClient('https://api.example.com')
        data, error = client._make_request('test-endpoint')
        
        assert data is None
        assert 'HTTP error' in error
        assert '404' in error
    
    @patch('requests.Session.get')
    def test_make_request_invalid_json(self, mock_get):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError('Invalid JSON')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = ConcreteAPIClient('https://api.example.com')
        data, error = client._make_request('test-endpoint')
        
        assert data is None
        assert 'Invalid JSON' in error
    
    @patch('requests.Session.get')
    def test_make_request_network_error(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = requests.exceptions.ConnectionError('Network error')
        
        client = ConcreteAPIClient('https://api.example.com')
        data, error = client._make_request('test-endpoint')
        
        assert data is None
        assert 'Request error' in error
    
    @patch('time.sleep')
    @patch('requests.Session.get')
    def test_rate_limiting(self, mock_get, mock_sleep):
        """Test that rate limiting enforces delay between requests."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': 'test'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = ConcreteAPIClient('https://api.example.com', rate_limit_delay=0.5)
        
        # Make first request
        client._make_request('endpoint1')
        
        # Make second request immediately
        client._make_request('endpoint2')
        
        # Sleep should have been called to enforce rate limit
        assert mock_sleep.called
    
    def test_normalize_data_basic(self):
        """Test basic data normalization."""
        client = ConcreteAPIClient('https://api.example.com')
        
        raw_data = [
            {'country': 'USA', 'year': 2020, 'indicator': 'GDP', 'value': 21000},
            {'country': 'GBR', 'year': 2020, 'indicator': 'GDP', 'value': 2800}
        ]
        
        normalized = client.normalize_data(raw_data, 'TestSource')
        
        assert len(normalized) == 2
        assert normalized[0]['country'] == 'USA'
        assert normalized[0]['year'] == 2020
        assert normalized[0]['indicator'] == 'GDP'
        assert normalized[0]['value'] == 21000.0
        assert normalized[0]['source'] == 'TestSource'
    
    def test_normalize_data_with_null_values(self):
        """Test normalization handles null values correctly."""
        client = ConcreteAPIClient('https://api.example.com')
        
        raw_data = [
            {'country': 'USA', 'year': 2020, 'indicator': 'GDP', 'value': None},
            {'country': 'GBR', 'year': 2020, 'indicator': 'GDP', 'value': 2800}
        ]
        
        normalized = client.normalize_data(raw_data, 'TestSource')
        
        assert len(normalized) == 2
        assert normalized[0]['value'] is None
        assert normalized[1]['value'] == 2800.0
    
    def test_normalize_data_skips_invalid_records(self):
        """Test that invalid records are skipped during normalization."""
        client = ConcreteAPIClient('https://api.example.com')
        
        raw_data = [
            {'country': 'USA', 'year': 2020, 'indicator': 'GDP', 'value': 21000},
            {'country': 'GBR', 'year': 'invalid', 'indicator': 'GDP', 'value': 2800},  # Invalid year
            {'country': 'FRA', 'year': 2020, 'indicator': 'GDP', 'value': 2700}
        ]
        
        normalized = client.normalize_data(raw_data, 'TestSource')
        
        # Should skip the invalid record
        assert len(normalized) == 2
        assert normalized[0]['country'] == 'USA'
        assert normalized[1]['country'] == 'FRA'
    
    def test_session_cleanup(self):
        """Test that session is properly closed on deletion."""
        client = ConcreteAPIClient('https://api.example.com')
        session = client.session
        
        # Mock the close method
        session.close = Mock()
        
        # Delete client
        del client
        
        # Session should be closed
        session.close.assert_called_once()
