"""
Request/Response schemas for API validation.

This module defines validation schemas for API requests and responses.
"""
from typing import Dict, List, Optional, Any


class PlotDataRequestSchema:
    """
    Schema for validating plot data requests.
    
    Required fields:
        - indicators: List of indicator codes
        - countries: List of country codes
        
    Optional fields:
        - start_year: Start year (int)
        - end_year: End year (int)
        - chart_type: Chart type ('line', 'bar', 'scatter', 'choropleth')
    """
    
    VALID_CHART_TYPES = ['line', 'bar', 'scatter', 'choropleth']
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate plot data request.
        
        Args:
            data: Request data dict
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if 'indicators' not in data or not data['indicators']:
            return False, "indicators field is required and must not be empty"
        
        if 'countries' not in data or not data['countries']:
            return False, "countries field is required and must not be empty"
        
        # Validate types
        if not isinstance(data['indicators'], list):
            return False, "indicators must be a list"
        
        if not isinstance(data['countries'], list):
            return False, "countries must be a list"
        
        # Validate optional fields
        if 'start_year' in data and data['start_year'] is not None:
            if not isinstance(data['start_year'], int):
                return False, "start_year must be an integer"
        
        if 'end_year' in data and data['end_year'] is not None:
            if not isinstance(data['end_year'], int):
                return False, "end_year must be an integer"
        
        if 'chart_type' in data and data['chart_type']:
            if data['chart_type'] not in PlotDataRequestSchema.VALID_CHART_TYPES:
                return False, f"chart_type must be one of: {', '.join(PlotDataRequestSchema.VALID_CHART_TYPES)}"
        
        return True, None


class IndicatorSchema:
    """Schema for indicator response."""
    
    @staticmethod
    def serialize(indicator: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize indicator to response format.
        
        Args:
            indicator: Indicator dict
            
        Returns:
            Serialized indicator
        """
        return {
            'code': indicator.get('code', ''),
            'name': indicator.get('name', ''),
            'description': indicator.get('description', ''),
            'source': indicator.get('source', '')
        }


class CountrySchema:
    """Schema for country response."""
    
    @staticmethod
    def serialize(country: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize country to response format.
        
        Args:
            country: Country dict
            
        Returns:
            Serialized country
        """
        return {
            'code': country.get('code', ''),
            'name': country.get('name', ''),
            'source': country.get('source', '')
        }


class PlotDataResponseSchema:
    """Schema for plot data response."""
    
    @staticmethod
    def serialize(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Serialize plot data to response format.
        
        Args:
            data: List of data records
            
        Returns:
            Serialized data
        """
        return [
            {
                'country': record.get('country', ''),
                'year': record.get('year', 0),
                'indicator': record.get('indicator', ''),
                'value': record.get('value'),
                'source': record.get('source', '')
            }
            for record in data
        ]
