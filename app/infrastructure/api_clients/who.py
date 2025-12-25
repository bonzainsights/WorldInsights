"""
WHO (World Health Organization) API client for WorldInsights.

Provides access to Global Health Observatory (GHO) data with 10,000+ health indicators.

API Documentation: https://www.who.int/data/gho/info/gho-odata-api

Following Clean Architecture:
- Infrastructure layer implementation
- Optional API key (recommended for future-proofing)
"""
from typing import Dict, List, Optional, Tuple
from app.infrastructure.api_clients.base_client import BaseAPIClient


class WHOClient(BaseAPIClient):
    """
    Client for WHO Global Health Observatory API.
    
    Features:
    - 10,000+ health indicators
    - Data from 1990 onwards
    - Coverage for 194 WHO member states
    - Optional API key
    
    Example usage:
        >>> client = WHOClient()
        >>> data, error = client.get_data('USA', 'WHOSIS_000001', start_year=2015, end_year=2020)
    """
    
    BASE_URL = 'https://ghoapi.azureedge.net/api'
    SOURCE_NAME = 'WHO'
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialize WHO API client.
        
        Args:
            api_key: Optional API key (recommended)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            rate_limit_delay=0.2  # Be conservative with WHO API
        )
        self.api_key = api_key
        self.logger.info("WHO API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of WHO member states.
        
        Returns:
            Tuple of (countries_list, error_message)
        """
        data, error = self._make_request('DIMENSION/COUNTRY/DimensionValues')
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'value' not in data:
            return None, "Invalid response format from WHO API"
        
        countries = []
        for country in data['value']:
            countries.append({
                'code': country.get('Code', ''),
                'name': country.get('Title', ''),
                'region': country.get('ParentTitle', '')
            })
        
        self.logger.info(f"Fetched {len(countries)} countries from WHO API")
        return countries, None
    
    def get_indicators(self, limit: int = 100) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of available health indicators.
        
        Args:
            limit: Maximum number of indicators to fetch
            
        Returns:
            Tuple of (indicators_list, error_message)
        """
        params = {'$top': limit}
        data, error = self._make_request('Indicator', params=params)
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'value' not in data:
            return None, "Invalid response format from WHO API"
        
        indicators = []
        for indicator in data['value']:
            indicators.append({
                'code': indicator.get('IndicatorCode', ''),
                'name': indicator.get('IndicatorName', ''),
                'description': indicator.get('IndicatorName', '')
            })
        
        self.logger.info(f"Fetched {len(indicators)} indicators from WHO API")
        return indicators, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch health data for a specific country and indicator.
        
        Args:
            country_code: WHO country code (3-letter)
            indicator_code: Indicator code
            start_year: Optional start year
            end_year: Optional end year
            
        Returns:
            Tuple of (data_list, error_message)
        """
        # Build filter
        filter_parts = [f"SpatialDim eq '{country_code}'"]
        if indicator_code:
            filter_parts.append(f"IndicatorCode eq '{indicator_code}'")
        
        params = {
            '$filter': ' and '.join(filter_parts)
        }
        
        data, error = self._make_request(indicator_code, params=params)
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'value' not in data:
            return None, "Invalid response format from WHO API"
        
        raw_data = data['value']
        
        if not raw_data:
            self.logger.warning(f"No data found for {country_code} - {indicator_code}")
            return [], None
        
        # Filter by year if specified
        if start_year or end_year:
            filtered_data = []
            for record in raw_data:
                try:
                    year = int(record.get('TimeDim', 0))
                    if start_year and year < start_year:
                        continue
                    if end_year and year > end_year:
                        continue
                    filtered_data.append(record)
                except (ValueError, TypeError):
                    continue
            raw_data = filtered_data
        
        # Normalize data
        normalized_data = self._normalize_who_data(raw_data)
        
        self.logger.info(f"Fetched {len(normalized_data)} health data points for {country_code}")
        return normalized_data, None
    
    def _normalize_who_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Normalize WHO data to standard schema.
        
        Args:
            raw_data: Raw data from WHO API
            
        Returns:
            List of normalized records
        """
        normalized = []
        
        for record in raw_data:
            try:
                country_code = record.get('SpatialDim', '')
                year = int(record.get('TimeDim', 0))
                indicator_code = record.get('IndicatorCode', '')
                value = record.get('NumericValue')
                
                if value is not None:
                    value = float(value)
                
                normalized_record = {
                    'country': country_code,
                    'year': year,
                    'indicator': indicator_code,
                    'value': value,
                    'source': self.SOURCE_NAME
                }
                
                normalized.append(normalized_record)
                
            except (ValueError, TypeError, KeyError) as e:
                self.logger.warning(f"Failed to normalize WHO record: {str(e)}")
                continue
        
        return normalized
