"""
Open-Meteo API client for WorldInsights.

Open-Meteo provides free weather and climate data without requiring authentication.
Offers historical weather data, forecasts, and climate projections.

API Documentation: https://open-meteo.com/en/docs

Following Clean Architecture:
- Infrastructure layer implementation
- No authentication required
- Free for non-commercial use (up to 10,000 requests/day)
"""
from typing import Dict, List, Optional, Tuple
from app.infrastructure.api_clients.base_client import BaseAPIClient


class OpenMeteoClient(BaseAPIClient):
    """
    Client for Open-Meteo API.
    
    Features:
    - No authentication required
    - Historical weather data from 1940 onwards
    - Weather forecasts up to 16 days
    - Climate projections
    - Multiple weather variables (temperature, precipitation, wind, etc.)
    
    Example usage:
        >>> client = OpenMeteoClient()
        >>> data, error = client.get_historical_weather(
        ...     latitude=40.7128,
        ...     longitude=-74.0060,
        ...     start_date='2020-01-01',
        ...     end_date='2020-12-31'
        ... )
    """
    
    BASE_URL = 'https://archive-api.open-meteo.com/v1'
    SOURCE_NAME = 'Open-Meteo'
    
    # Country capital coordinates for mapping
    COUNTRY_CAPITALS = {
        'USA': (38.9072, -77.0369),  # Washington D.C.
        'GBR': (51.5074, -0.1278),   # London
        'CHN': (39.9042, 116.4074),  # Beijing
        'IND': (28.6139, 77.2090),   # New Delhi
        'DEU': (52.5200, 13.4050),   # Berlin
        'FRA': (48.8566, 2.3522),    # Paris
        'JPN': (35.6762, 139.6503),  # Tokyo
        'BRA': (15.8267, -47.9218),  # Brasília
        'CAN': (45.4215, -75.6972),  # Ottawa
        'AUS': (35.2809, -149.1300), # Canberra
    }
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize Open-Meteo API client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            rate_limit_delay=0.1
        )
        self.logger.info("Open-Meteo API client initialized")
    
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
        Return list of available weather indicators.
        
        Returns:
            Tuple of (indicators_list, error_message)
        """
        indicators = [
            {'code': 'temperature_2m_mean', 'name': 'Mean Temperature (2m)', 'unit': '°C'},
            {'code': 'temperature_2m_max', 'name': 'Maximum Temperature (2m)', 'unit': '°C'},
            {'code': 'temperature_2m_min', 'name': 'Minimum Temperature (2m)', 'unit': '°C'},
            {'code': 'precipitation_sum', 'name': 'Precipitation Sum', 'unit': 'mm'},
            {'code': 'rain_sum', 'name': 'Rain Sum', 'unit': 'mm'},
            {'code': 'snowfall_sum', 'name': 'Snowfall Sum', 'unit': 'cm'},
            {'code': 'windspeed_10m_max', 'name': 'Maximum Wind Speed (10m)', 'unit': 'km/h'},
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
        Fetch historical weather data for a country.
        
        Args:
            country_code: Country code (must be in COUNTRY_CAPITALS)
            indicator_code: Weather variable code
            start_year: Start year
            end_year: End year
            
        Returns:
            Tuple of (data_list, error_message)
        """
        if country_code not in self.COUNTRY_CAPITALS:
            return None, f"Country {country_code} not supported. Available: {list(self.COUNTRY_CAPITALS.keys())}"
        
        latitude, longitude = self.COUNTRY_CAPITALS[country_code]
        
        # Build date range
        start_date = f"{start_year}-01-01" if start_year else "2020-01-01"
        end_date = f"{end_year}-12-31" if end_year else "2020-12-31"
        
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': start_date,
            'end_date': end_date,
            'daily': indicator_code,
            'timezone': 'UTC'
        }
        
        data, error = self._make_request('archive', params=params)
        
        if error:
            return None, error
        
        if not data or 'daily' not in data:
            return None, "Invalid response format from Open-Meteo API"
        
        # Normalize data
        normalized_data = self._normalize_openmeteo_data(
            data['daily'],
            country_code,
            indicator_code
        )
        
        self.logger.info(f"Fetched {len(normalized_data)} weather data points for {country_code}")
        return normalized_data, None
    
    def _normalize_openmeteo_data(
        self,
        raw_data: Dict,
        country_code: str,
        indicator_code: str
    ) -> List[Dict]:
        """
        Normalize Open-Meteo data to standard schema.
        
        Args:
            raw_data: Raw daily data from API
            country_code: Country code
            indicator_code: Indicator code
            
        Returns:
            List of normalized records
        """
        normalized = []
        
        dates = raw_data.get('time', [])
        values = raw_data.get(indicator_code, [])
        
        for date_str, value in zip(dates, values):
            try:
                # Extract year from date string (YYYY-MM-DD)
                year = int(date_str.split('-')[0])
                
                normalized_record = {
                    'country': country_code,
                    'year': year,
                    'indicator': indicator_code,
                    'value': float(value) if value is not None else None,
                    'source': self.SOURCE_NAME,
                    'date': date_str  # Keep full date for daily data
                }
                
                normalized.append(normalized_record)
                
            except (ValueError, TypeError, IndexError) as e:
                self.logger.warning(f"Failed to normalize Open-Meteo record: {str(e)}")
                continue
        
        return normalized
