
import pytest
from unittest.mock import MagicMock, patch
from app.services.data_retrieval_service import DataRetrievalService

@pytest.fixture
def service():
    with patch('app.services.data_retrieval_service.DataLakeService') as MockLake:
        idx = DataRetrievalService()
        idx.lake = MockLake.return_value
        return idx
        
def test_get_data_lake_hit(service):
    """Test that data is returned from lake if available."""
    # Setup
    expected_data = [{'country': 'USA', 'value': 100}]
    service.lake.query.return_value = expected_data
    
    # Execute
    result = service.get_data('worldbank', 'NY.GDP.MKTP.CD', 'USA', 2024)
    
    # Verify
    assert result == expected_data
    service.lake.query.assert_called_once()
    
def test_get_data_lake_miss_fallback(service):
    """Test that data is fetched from API if lake returns empty."""
    # Setup
    service.lake.query.return_value = [] # Lake Miss
    
    expected_data = [{'country': 'USA', 'value': 200}]
    
    # Mock the specific client
    mock_client = MagicMock()
    mock_client.get_data.return_value = (expected_data, None)
    service._clients['worldbank'] = mock_client
    
    # Execute
    result = service.get_data('worldbank', 'NY.GDP.MKTP.CD', 'USA', 2024)
    
    # Verify
    assert result == expected_data
    mock_client.get_data.assert_called_once() 

def test_get_globe_data_success(service):
    """Test joining shapes and data."""
    # Setup
    mock_shapes = [{'iso_code': 'USA', 'geometry': '...'}] # Not really used in join logic mock
    # The service calls query() with a JOIN.
    expected_result = [
        {'iso_code': 'USA', 'geometry': '{"type":"Polygon"}', 'value': 100, 'year': 2024}
    ]
    service.lake.query.return_value = expected_result
    
    # Execute
    result = service.get_globe_data('worldbank', 'NY.GDP.MKTP.CD', 2024)
    
    # Verify
    assert result == expected_result
    # Ensure query contained JOIN
    args, _ = service.lake.query.call_args
    assert "JOIN" in args[0]
