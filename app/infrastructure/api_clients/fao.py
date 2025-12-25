"""
FAO (Food and Agriculture Organization) API client for WorldInsights.

Provides access to FAOSTAT data covering agriculture, food production,
and food security statistics.

API Documentation: https://fenixservices.fao.org/faostat/api/v1/en/

Following Clean Architecture:
- Infrastructure layer implementation
- No authentication required
"""
from typing import Dict, List, Optional, Tuple
from app.infrastructure.api_clients.base_client import BaseAPIClient


class FAOClient(BaseAPIClient):
    """
    Client for FAO FAOSTAT API.
    
    Features:
    - Agriculture and food production data
    - Data from 1961 onwards
    - Coverage for 245+ countries and territories
    - No authentication required
    
    Example usage:
        >>> client = FAOClient()
        >>> data, error = client.get_data('USA', 'QC', start_year=2015, end_year=2020)
    """
    
    BASE_URL = 'https://fenixservices.fao.org/faostat/api/v1/en'
    SOURCE_NAME = 'FAO'
    
    # Common domains (datasets)
    DOMAINS = {
        'QC': 'Crops and livestock products',
        'QCL': 'Crops and livestock products',
        'QI': 'Production Indices',
        'QV': 'Value of Agricultural Production',
        'RL': 'Land Use',
        'RF': 'Fertilizers',
        'RP': 'Pesticides',
        'RT': 'Land Cover',
        'FBS': 'Food Balances',
        'FBSH': 'Food Balances (Historic)',
        'FS': 'Food Security',
        'SUA': 'Supply Utilization Accounts',
    }
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize FAO API client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            rate_limit_delay=0.2  # Be respectful to FAO API
        )
        self.logger.info("FAO API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of countries/regions from FAO.
        
        Returns:
            Tuple of (countries_list, error_message)
        """
        # Use QCL domain to get countries
        data, error = self._make_request('dimensions/area/QCL')
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'data' not in data:
            return None, "Invalid response format from FAO API"
        
        countries = []
        for country in data['data']:
            countries.append({
                'code': str(country.get('code', '')),
                'name': country.get('label', ''),
                'fao_code': country.get('code', '')
            })
        
        self.logger.info(f"Fetched {len(countries)} countries from FAO API")
        return countries, None
    
    def get_indicators(self, domain: str = 'QCL') -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of available indicators (items/elements) for a domain.
        
        Args:
            domain: FAO domain code (e.g., 'QCL' for crops and livestock)
            
        Returns:
            Tuple of (indicators_list, error_message)
        """
        # Get items (products/commodities)
        data, error = self._make_request(f'dimensions/item/{domain}')
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'data' not in data:
            return None, "Invalid response format from FAO API"
        
        indicators = []
        for item in data['data'][:100]:  # Limit to first 100
            indicators.append({
                'code': f"{domain}_{item.get('code', '')}",
                'name': item.get('label', ''),
                'domain': domain,
                'description': self.DOMAINS.get(domain, '')
            })
        
        self.logger.info(f"Fetched {len(indicators)} indicators from FAO API")
        return indicators, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch agricultural data for a specific country and indicator.
        
        Note: FAO API structure is complex. This is a simplified implementation.
        For production use, consider using bulk download approach.
        
        Args:
            country_code: FAO country code
            indicator_code: Domain code (e.g., 'QCL')
            start_year: Optional start year
            end_year: Optional end year
            
        Returns:
            Tuple of (data_list, error_message)
        """
        # For now, return a simplified response
        # Full implementation would require complex query building
        self.logger.warning("FAO get_data is simplified - consider using bulk download for production")
        
        # Simplified: just return structure without actual API call
        # In production, this would build complex SDMX queries
        return [], None
    
    def _normalize_fao_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Normalize FAO data to standard schema.
        
        Args:
            raw_data: Raw data from FAO API
            
        Returns:
            List of normalized records
        """
        normalized = []
        
        for record in raw_data:
            try:
                country_code = record.get('Area Code', '')
                year = int(record.get('Year', 0))
                indicator_code = f"{record.get('Domain Code', '')}_{record.get('Item Code', '')}"
                value = record.get('Value')
                
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
                self.logger.warning(f"Failed to normalize FAO record: {str(e)}")
                continue
        
        return normalized
