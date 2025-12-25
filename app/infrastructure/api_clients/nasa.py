"""
NASA POWER API client for WorldInsights.

Provides access to NASA's Prediction Of Worldwide Energy Resources (POWER) data,
including solar and meteorological data.

API Documentation: https://power.larc.nasa.gov/docs/

Following Clean Architecture:
- Infrastructure layer implementation
- Requires API key (free registration at api.nasa.gov)
"""
from typing import Dict, List, Optional, Tuple
from app.infrastructure.api_clients.base_client import BaseAPIClient


class NASAClient(BaseAPIClient):
    """
    Client for NASA POWER API.
    
    Features:
    - Solar and meteorological data
    - Data from 1981 onwards
    - Global coverage
    - Requires free API key
    
    Example usage:
        >>> client = NASAClient(api_key='your_api_key')
        >>> data, error = client.get_data('USA', 'T2M', start_year=2015, end_year=2020)
    """
    
    BASE_URL = 'https://power.larc.nasa.gov/api/temporal/daily'
    SOURCE_NAME = 'NASA POWER'
    
    # Country capital coordinates
    COUNTRY_CAPITALS = {
        'USA': (38.9072, -77.0369),
        'GBR': (51.5074, -0.1278),
        'CHN': (39.9042, 116.4074),
        'IND': (28.6139, 77.2090),
        'DEU': (52.5200, 13.4050),
        'FRA': (48.8566, 2.3522),
        'JPN': (35.6762, 139.6503),
        'BRA': (15.8267, -47.9218),
        'CAN': (45.4215, -75.6972),
        'AUS': (35.2809, -149.1300),
    }
    
    # Available parameters
    PARAMETERS = {
        'T2M': 'Temperature at 2 Meters',
        'T2M_MAX': 'Maximum Temperature at 2 Meters',
        'T2M_MIN': 'Minimum Temperature at 2 Meters',
        'PRECTOTCORR': 'Precipitation Corrected',
        'WS2M': 'Wind Speed at 2 Meters',
        'RH2M': 'Relative Humidity at 2 Meters',
        'ALLSKY_SFC_SW_DWN': 'All Sky Surface Shortwave Downward Irradiance',
    }
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialize NASA POWER API client.
        
        Args:
            api_key: NASA API key (get from api.nasa.gov)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            rate_limit_delay=0.1
        )
        self.api_key = api_key or 'DEMO_KEY'  # Use demo key if none provided
        self.logger.info("NASA POWER API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Return list of supported countries (based on capital coordinates).
        
        Returns:
            Tuple of (countries_list, error_message)
        """
        countries = [
            {'code': code, 'name': code, 'latitude': coords[0], 'longitude': coords[1]}
            for code, coords in self.COUNTRY_CAPITALS.items()
        ]
        return countries, None
    
    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Return list of available climate/solar parameters.
        
        Returns:
            Tuple of (indicators_list, error_message)
        """
        indicators = [
            {'code': code, 'name': name, 'description': name}
            for code, name in self.PARAMETERS.items()
        ]
        return indicators, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch climate/solar data for a country.
        
        Args:
            country_code: Country code (must be in COUNTRY_CAPITALS)
            indicator_code: Parameter code (e.g., 'T2M')
            start_year: Start year
            end_year: End year
            
        Returns:
            Tuple of (data_list, error_message)
        """
        if country_code not in self.COUNTRY_CAPITALS:
            return None, f"Country {country_code} not supported"
        
        latitude, longitude = self.COUNTRY_CAPITALS[country_code]
        
        # Build date range
        start_date = f"{start_year}0101" if start_year else "20200101"
        end_date = f"{end_year}1231" if end_year else "20201231"
        
        params = {
            'parameters': indicator_code,
            'community': 'RE',
            'longitude': longitude,
            'latitude': latitude,
            'start': start_date,
            'end': end_date,
            'format': 'JSON',
            'api_key': self.api_key
        }
        
        data, error = self._make_request('point', params=params)
        
        if error:
            return None, error
        
        if not data or 'properties' not in data or 'parameter' not in data['properties']:
            return None, "Invalid response format from NASA POWER API"
        
        # Normalize data
        normalized_data = self._normalize_nasa_data(
            data['properties']['parameter'],
            country_code,
            indicator_code
        )
        
        self.logger.info(f"Fetched {len(normalized_data)} climate data points for {country_code}")
        return normalized_data, None
    
    def _normalize_nasa_data(
        self,
        raw_data: Dict,
        country_code: str,
        indicator_code: str
    ) -> List[Dict]:
        """
        Normalize NASA POWER data to standard schema.
        
        Args:
            raw_data: Raw parameter data from API
            country_code: Country code
            indicator_code: Indicator code
            
        Returns:
            List of normalized records
        """
        normalized = []
        
        parameter_data = raw_data.get(indicator_code, {})
        
        for date_str, value in parameter_data.items():
            try:
                # Date format: YYYYMMDD
                year = int(date_str[:4])
                
                normalized_record = {
                    'country': country_code,
                    'year': year,
                    'indicator': indicator_code,
                    'value': float(value) if value not in [-999, -999.0] else None,  # -999 is missing data
                    'source': self.SOURCE_NAME,
                    'date': date_str
                }
                
                normalized.append(normalized_record)
                
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Failed to normalize NASA record: {str(e)}")
                continue
        
        return normalized
