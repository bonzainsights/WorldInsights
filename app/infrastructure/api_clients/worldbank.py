"""
World Bank API client for WorldInsights.

This module provides access to World Bank's open data API, which offers
over 16,000 development indicators covering economic, social, environmental,
and institutional data for 200+ countries.

API Documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

Following Clean Architecture:
- This is the infrastructure layer
- Implements BaseAPIClient interface
- No business logic - pure data fetching and normalization
"""
from typing import Dict, List, Optional, Tuple
from app.infrastructure.api_clients.base_client import BaseAPIClient


class WorldBankClient(BaseAPIClient):
    """
    Client for World Bank API.
    
    Features:
    - No authentication required
    - Access to 16,000+ indicators
    - Data from 1960 onwards for most indicators
    - Covers 200+ countries and regions
    
    Example usage:
        >>> client = WorldBankClient()
        >>> countries, error = client.get_countries()
        >>> data, error = client.get_data('USA', 'NY.GDP.MKTP.CD', start_year=2015, end_year=2020)
    """
    
    BASE_URL = 'https://api.worldbank.org/v2'
    SOURCE_NAME = 'World Bank'
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize World Bank API client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            rate_limit_delay=0.1  # Be respectful to free API
        )
        self.logger.info("World Bank API client initialized")
    
    def get_countries(self, per_page: int = 300) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of all countries from World Bank API.
        
        Args:
            per_page: Number of results per page (max 300)
            
        Returns:
            Tuple of (countries_list, error_message)
            Each country dict contains: {'code': str, 'name': str, 'capital': str, 'region': str}
        """
        params = {
            'format': 'json',
            'per_page': per_page
        }
        
        data, error = self._make_request('country', params=params)
        
        if error:
            return None, error
        
        # World Bank API returns [metadata, data]
        if not isinstance(data, list) or len(data) < 2:
            return None, "Invalid response format from World Bank API"
        
        raw_countries = data[1]
        
        # Transform to standard format
        countries = []
        for country in raw_countries:
            countries.append({
                'code': country.get('id', ''),
                'name': country.get('name', ''),
                'capital': country.get('capitalCity', ''),
                'region': country.get('region', {}).get('value', '') if isinstance(country.get('region'), dict) else '',
                'income_level': country.get('incomeLevel', {}).get('value', '') if isinstance(country.get('incomeLevel'), dict) else ''
            })
        
        self.logger.info(f"Fetched {len(countries)} countries from World Bank API")
        return countries, None
    
    def get_indicators(self, per_page: int = 100) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of available indicators from World Bank API.
        
        Note: There are 16,000+ indicators, so this may take multiple requests.
        Consider using a smaller per_page value or filtering by topic.
        
        Args:
            per_page: Number of results per page (max 300)
            
        Returns:
            Tuple of (indicators_list, error_message)
            Each indicator dict contains: {'code': str, 'name': str, 'description': str}
        """
        params = {
            'format': 'json',
            'per_page': per_page
        }
        
        data, error = self._make_request('indicator', params=params)
        
        if error:
            return None, error
        
        # World Bank API returns [metadata, data]
        if not isinstance(data, list) or len(data) < 2:
            return None, "Invalid response format from World Bank API"
        
        raw_indicators = data[1]
        
        # Transform to standard format
        indicators = []
        for indicator in raw_indicators:
            indicators.append({
                'code': indicator.get('id', ''),
                'name': indicator.get('name', ''),
                'description': indicator.get('sourceNote', ''),
                'source': indicator.get('source', {}).get('value', '') if isinstance(indicator.get('source'), dict) else ''
            })
        
        self.logger.info(f"Fetched {len(indicators)} indicators from World Bank API")
        return indicators, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        per_page: int = 1000
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data for a specific country and indicator.
        
        Args:
            country_code: Country code (e.g., 'USA', 'GBR', 'all' for all countries)
            indicator_code: Indicator code (e.g., 'NY.GDP.MKTP.CD')
            start_year: Optional start year for filtering
            end_year: Optional end year for filtering
            per_page: Number of results per page
            
        Returns:
            Tuple of (data_list, error_message)
            Data is normalized to standard schema
        """
        # Build endpoint: /countries/{country}/indicators/{indicator}
        endpoint = f'country/{country_code}/indicator/{indicator_code}'
        
        params = {
            'format': 'json',
            'per_page': per_page
        }
        
        # Add date range if specified
        if start_year and end_year:
            params['date'] = f'{start_year}:{end_year}'
        elif start_year:
            params['date'] = f'{start_year}:{start_year + 50}'  # Default to 50 year range
        elif end_year:
            params['date'] = f'{end_year - 50}:{end_year}'
        
        data, error = self._make_request(endpoint, params=params)
        
        if error:
            return None, error
        
        # World Bank API returns [metadata, data]
        if not isinstance(data, list) or len(data) < 2:
            return None, "Invalid response format from World Bank API"
        
        raw_data = data[1]
        
        if not raw_data:
            self.logger.warning(f"No data found for {country_code} - {indicator_code}")
            return [], None
        
        # Normalize to standard schema
        normalized_data = self._normalize_worldbank_data(raw_data)
        
        self.logger.info(f"Fetched {len(normalized_data)} data points for {country_code} - {indicator_code}")
        return normalized_data, None
    
    def _normalize_worldbank_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Normalize World Bank API response to standard schema.
        
        World Bank format:
        {
            'indicator': {'id': 'NY.GDP.MKTP.CD', 'value': 'GDP (current US$)'},
            'country': {'id': 'USA', 'value': 'United States'},
            'countryiso3code': 'USA',
            'date': '2020',
            'value': 21000000000000,
            'unit': '',
            'obs_status': '',
            'decimal': 0
        }
        
        Standard schema:
        {
            'country': 'USA',
            'year': 2020,
            'indicator': 'NY.GDP.MKTP.CD',
            'value': 21000000000000,
            'source': 'World Bank'
        }
        
        Args:
            raw_data: Raw data from World Bank API
            
        Returns:
            List of normalized data records
        """
        normalized = []
        
        for record in raw_data:
            try:
                # Extract country code (prefer iso3code, fallback to id)
                country_code = record.get('countryiso3code') or record.get('country', {}).get('id', '')
                
                # Extract indicator code
                indicator_code = record.get('indicator', {}).get('id', '')
                
                # Extract year (convert from string)
                year = int(record.get('date', 0))
                
                # Extract value (may be None)
                value = record.get('value')
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
                self.logger.warning(f"Failed to normalize World Bank record {record}: {str(e)}")
                continue
        
        return normalized
