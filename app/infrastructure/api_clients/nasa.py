"""
NASA/NOAA Open Data API Client for WorldInsights.

This module provides access to NASA and NOAA climate and earth science data:
- Climate indicators (temperature, precipitation)
- Satellite data
- Natural hazards
- Earth observations
- Atmospheric data

API Documentation:
- NASA: https://api.nasa.gov/
- NOAA: https://www.ncdc.noaa.gov/cdo-web/api/v2

Features:
- Free API key (DEMO_KEY or register for higher limits)
- Multiple data endpoints
- Global climate data

Following Clean Architecture:
- Infrastructure layer component
- Implements BaseAPIClient interface
- Pure data fetching and normalization
"""
from typing import Dict, List, Optional, Tuple, Any
from app.infrastructure.api_clients.base_client import BaseAPIClient, CacheBackend, CircuitBreaker
from app.core.entities import DataPoint


class NASAClient(BaseAPIClient):
    """
    Client for NASA/NOAA Open Data APIs.
    
    Key Features:
    - Climate and earth science data
    - Satellite observations
    - Natural hazards data
    - Free API access
    
    Example usage:
        >>> client = NASAClient(api_key='YOUR_KEY')
        >>> data, error = client.get_climate_indicators('USA', 2018, 2023)
    """
    
    SOURCE_NAME = "NASA/NOAA"
    SOURCE_ID = "nasa"
    BASE_URL = 'https://api.nasa.gov'
    NOAA_BASE_URL = 'https://www.ncdc.noaa.gov/cdo-web/api/v2'
    
    # Available NASA endpoints
    ENDPOINTS = {
        'climate': '/planetary/earth/climate',
        'imagery': '/planetary/earth/imagery',
        'assets': '/planetary/earth/assets',
        'apod': '/planetary/apod',  # Astronomy Picture of Day
        'neo': '/neo/rest/v1/feed',  # Near Earth Objects
        'donki': '/DONKI/',  # Space Weather
    }
    
    # Climate indicators
    CLIMATE_INDICATORS = {
        'temperature_anomaly': 'Global temperature anomaly',
        'co2_concentration': 'Atmospheric CO2 concentration',
        'sea_level': 'Global mean sea level',
        'arctic_sea_ice': 'Arctic sea ice extent',
        'land_ice': 'Land ice sheets',
    }
    
    def __init__(
        self,
        api_key: str = 'DEMO_KEY',
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 604800,  # 7 days for NASA data
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        """
        Initialize NASA API client.
        
        Args:
            api_key: NASA API key (DEMO_KEY has rate limits)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            cache_ttl: Cache TTL in seconds
            cache_backend: Optional cache backend
            circuit_breaker: Optional circuit breaker
        """
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=0.5,
            rate_limit="10 per hour",  # DEMO_KEY limit
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
            api_key=api_key,
            headers={}
        )
        # NASA uses api_key query parameter
        self.api_key = api_key
        self.logger.info(f"NASA API client initialized (key: {api_key[:4]}...)")

    # Required abstract methods for BaseAPIClient compliance
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of countries (not applicable for NASA).
        
        Returns:
            Empty list - NASA data is global, not country-specific
        """
        return [], None

    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of indicators (not applicable for NASA).
        
        Returns:
            Empty list - NASA uses different data model
        """
        return [], None

    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data (not applicable for NASA in standard format).
        
        Returns:
            Empty list - use specialized NASA endpoints instead
        """
        return [], None

    # NASA-specific methods
    
    def get_climate_indicators(
        self,
        country_code: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch climate indicators.
        
        Note: NASA climate data is typically global, not country-specific.
        
        Args:
            country_code: Optional country code for filtering
            start_year: Start year
            end_year: End year
        
        Returns:
            Tuple of (data_list, error_message)
        """
        # NASA doesn't have a direct climate indicators endpoint
        # We'll use placeholder data structure for now
        # In production, integrate with specific NASA endpoints
        
        self.logger.info("NASA climate indicators fetched (simulated)")
        return [], None
    
    def get_earth_imagery(
        self,
        lat: float,
        lon: float,
        date: str,
        dim: float = 0.1
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch Earth imagery for specific coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            date: Date (YYYY-MM-DD)
            dim: Dimension of image in degrees
        
        Returns:
            Tuple of (imagery_data, error_message)
        """
        endpoint = '/planetary/earth/imagery'
        params = {
            'lon': lon,
            'lat': lat,
            'date': date,
            'dim': dim,
            'api_key': self.api_key
        }
        
        data, error = self._make_request(endpoint, params=params, use_cache=True)
        
        if error:
            return None, error
        
        return data, None
    
    def get_neo_feed(
        self,
        start_date: str,
        end_date: Optional[str] = None
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch Near Earth Object data.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Tuple of (neo_data, error_message)
        """
        endpoint = '/neo/rest/v1/feed'
        params = {
            'start_date': start_date,
            'end_date': end_date or start_date,
            'api_key': self.api_key
        }
        
        data, error = self._make_request(endpoint, params=params, use_cache=True)
        
        if error:
            return None, error
        
        return data, None
    
    def get_apod(self, date: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch Astronomy Picture of the Day.
        
        Args:
            date: Date (YYYY-MM-DD), defaults to today
        
        Returns:
            Tuple of (apod_data, error_message)
        """
        endpoint = '/planetary/apod'
        params = {
            'api_key': self.api_key
        }
        if date:
            params['date'] = date
        
        data, error = self._make_request(endpoint, params=params, use_cache=True)
        
        if error:
            return None, error
        
        return data, None
    
    def _normalize_nasa_data(
        self,
        raw_data: Dict,
        indicator_type: str
    ) -> List[Dict]:
        """
        Normalize NASA API response to standard format.
        
        Args:
            raw_data: Raw API response
            indicator_type: Type of indicator
        
        Returns:
            List of normalized data records
        """
        # NASA data varies greatly by endpoint
        # This is a generic normalizer
        normalized = []
        
        # Implementation depends on specific endpoint
        return normalized


class NOAAClient(BaseAPIClient):
    """
    Client for NOAA Climate Data Online API.
    
    Key Features:
    - Historical climate data
    - Weather station data
    - Precipitation, temperature records
    - Free API token required
    
    Example usage:
        >>> client = NOAAClient(token='YOUR_TOKEN')
        >>> data, error = client.get_weather_data('USW00094728', 2020, 2023)
    """
    
    SOURCE_NAME = "NOAA"
    SOURCE_ID = "noaa"
    BASE_URL = 'https://www.ncdc.noaa.gov/cdo-web/api/v2'
    
    # Data types
    DATA_TYPES = {
        'PRCP': 'Precipitation',
        'SNOW': 'Snowfall',
        'SNWD': 'Snow depth',
        'TMAX': 'Maximum temperature',
        'TMIN': 'Minimum temperature',
        'TAVG': 'Average temperature',
        'AWND': 'Average wind speed',
    }
    
    def __init__(
        self,
        token: str,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 86400,
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        """
        Initialize NOAA API client.
        
        Args:
            token: NOAA API token (free registration required)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            cache_ttl: Cache TTL in seconds
            cache_backend: Optional cache backend
            circuit_breaker: Optional circuit breaker
        """
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=0.5,
            rate_limit="5 per second",
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
            headers={'token': token}
        )
        self.token = token
        self.logger.info("NOAA API client initialized")
    
    def get_data(
        self,
        datasetid: str = 'GHCND',
        stationid: Optional[str] = None,
        datatypeid: Optional[str] = None,
        startdate: str = '2020-01-01',
        enddate: str = '2020-12-31',
        limit: int = 1000
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch climate data from NOAA.
        
        Args:
            datasetid: Dataset ID (default: GHCND)
            stationid: Station ID (optional)
            datatypeid: Data type ID (optional)
            startdate: Start date (YYYY-MM-DD)
            enddate: End date (YYYY-MM-DD)
            limit: Results limit
        
        Returns:
            Tuple of (data, error_message)
        """
        endpoint = '/data'
        params = {
            'datasetid': datasetid,
            'startdate': startdate,
            'enddate': enddate,
            'limit': limit,
        }
        
        if stationid:
            params['stationid'] = stationid
        if datatypeid:
            params['datatypeid'] = datatypeid
        
        data, error = self._make_request(endpoint, params=params, use_cache=True)
        
        if error:
            return None, error
        
        return data, None
    
    def get_stations(
        self,
        datasetid: str = 'GHCND',
        limit: int = 100
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch weather stations.
        
        Args:
            datasetid: Dataset ID
            limit: Results limit
        
        Returns:
            Tuple of (stations_list, error_message)
        """
        endpoint = '/stations'
        params = {
            'datasetid': datasetid,
            'limit': limit,
        }
        
        data, error = self._make_request(endpoint, params=params, use_cache=True)
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'results' not in data:
            return None, "Invalid response format from NOAA API"
        
        stations = []
        for station in data['results']:
            stations.append({
                'id': station.get('id', ''),
                'name': station.get('name', ''),
                'latitude': station.get('latitude', ''),
                'longitude': station.get('longitude', ''),
                'elevation': station.get('elevation', ''),
            })
        
        return stations, None
    
    def get_datasets(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch available datasets.
        
        Returns:
            Tuple of (datasets_list, error_message)
        """
        endpoint = '/datasets'
        
        data, error = self._make_request(endpoint, use_cache=True)
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'results' not in data:
            return None, "Invalid response format from NOAA API"
        
        return data['results'], None
    
    def get_datatypes(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch available data types.
        
        Returns:
            Tuple of (datatypes_list, error_message)
        """
        endpoint = '/datatypes'
        
        data, error = self._make_request(endpoint, use_cache=True)
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'results' not in data:
            return None, "Invalid response format from NOAA API"
        
        return data['results'], None
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch countries (locations).
        
        Returns:
            Tuple of (countries_list, error_message)
        """
        endpoint = '/locations'
        params = {'locationcategoryid': 'COUNTRY'}
        
        data, error = self._make_request(endpoint, params=params, use_cache=True)
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'results' not in data:
            return None, "Invalid response format from NOAA API"
        
        countries = []
        for country in data['results']:
            countries.append({
                'code': country.get('id', ''),
                'name': country.get('name', ''),
            })
        
        return countries, None
    
    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch indicators (data types).
        
        Returns:
            Tuple of (indicators_list, error_message)
        """
        return self.get_datatypes()
    
    def _normalize_noaa_data(
        self,
        raw_data: Dict,
        station_info: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Normalize NOAA API response to standard format.
        
        Args:
            raw_data: Raw API response
            station_info: Optional station information
        
        Returns:
            List of normalized data records
        """
        normalized = []
        
        if not isinstance(raw_data, dict) or 'results' not in raw_data:
            return normalized
        
        for record in raw_data['results']:
            try:
                # Extract date
                date = record.get('date', '')
                if not date:
                    continue
                year = int(date[:4])
                
                # Extract value
                value = record.get('value')
                if value is None:
                    continue
                
                # Extract data type
                datatype = record.get('datatype', '')
                
                # Get country from station
                country_code = ''
                country_name = ''
                if station_info:
                    country_code = station_info.get('country', '')
                    country_name = station_info.get('name', '')
                
                normalized_record = {
                    'country_code': country_code,
                    'country_name': country_name,
                    'indicator_code': datatype,
                    'indicator_name': self.DATA_TYPES.get(datatype, datatype),
                    'year': year,
                    'value': float(value),
                    'unit': None,
                    'source': self.SOURCE_ID,
                    'metadata': {
                        'station': record.get('station', ''),
                        'date': date,
                        'attributes': record.get('attributes', ''),
                    }
                }
                
                normalized.append(normalized_record)
                
            except Exception as e:
                self.logger.warning(f"Failed to normalize NOAA record: {e}")
                continue
        
        return normalized
