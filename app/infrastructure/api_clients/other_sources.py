"""
Additional API Clients for WorldInsights.

This module contains clients for:
- UN Data API
- Our World in Data API
- IMF Data API
- UNESCO Institute for Statistics
- ILO (International Labour Organization)
- ITU (International Telecommunication Union)

Following Clean Architecture:
- Infrastructure layer components
- Implement BaseAPIClient interface
- Pure data fetching and normalization
"""
from typing import Dict, List, Optional, Tuple, Any
from app.infrastructure.api_clients.base_client import BaseAPIClient, CacheBackend, CircuitBreaker
from app.core.entities import DataPoint


# ============================================
# UN Data API Client
# ============================================

class UNDataClient(BaseAPIClient):
    """
    Client for UN Data API.
    
    Provides access to UN statistics on:
    - National accounts
    - Demographics
    - Trade
    - Energy
    - Environment
    - Social indicators
    
    API: https://data.un.org/
    """
    
    SOURCE_NAME = "UN Data"
    SOURCE_ID = "un_data"
    BASE_URL = 'https://data.un.org/ws/rest'
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 86400,
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
        )
        self.logger.info("UN Data API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch countries from UN Data API."""
        # UN Data uses SDMX format
        endpoint = '/dataflow/UNSD/SDG_9'
        params = {'detail': 'referenceonly'}
        
        data, error = self._make_request(endpoint, params=params)
        if error:
            return None, error
        
        # Parse SDMX response (simplified)
        countries = []
        # Implementation would parse SDMX structure
        return countries, None
    
    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch indicators from UN Data API."""
        # Return placeholder - full implementation would parse SDMX
        indicators = []
        return indicators, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch data for country and indicator."""
        # UN Data API uses SDMX format
        # Implementation would construct proper SDMX query
        return [], None


# ============================================
# Our World in Data API Client
# ============================================

class OWIDClient(BaseAPIClient):
    """
    Client for Our World in Data API.
    
    Provides research data on global challenges:
    - Poverty
    - Disease
    - Hunger
    - Climate change
    - Energy
    - Democracy
    
    API: https://ourworldindata.org/api
    """
    
    SOURCE_NAME = "Our World in Data"
    SOURCE_ID = "owid"
    BASE_URL = 'https://ourworldindata.org/api'
    
    # Key indicator categories
    CATEGORIES = {
        'poverty': 'Poverty and Inequality',
        'health': 'Health',
        'energy': 'Energy',
        'climate': 'Climate Change',
        'food': 'Food and Agriculture',
        'water': 'Water',
        'democracy': 'Democracy and Governance',
        'education': 'Education',
        'technology': 'Technology',
        'work': 'Work and Life',
    }
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 86400,
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
        )
        self.logger.info("Our World in Data API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch countries from OWID API."""
        data, error = self._make_request('/countries')
        
        if error:
            return None, error
        
        if not isinstance(data, list):
            return None, "Invalid response format"
        
        countries = []
        for country in data:
            countries.append({
                'code': country.get('code', ''),
                'name': country.get('name', ''),
                'iso3_code': country.get('iso3Code', ''),
                'region': country.get('region', ''),
            })
        
        return countries, None
    
    def get_indicators(
        self,
        category: Optional[str] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch indicators from OWID API."""
        # OWID doesn't have a single indicators endpoint
        # We need to fetch from specific chart endpoints
        indicators = []
        return indicators, None
    
    def get_chart_data(self, chart_id: int) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch data for a specific chart.
        
        Args:
            chart_id: OWID chart ID
        
        Returns:
            Tuple of (chart_data, error_message)
        """
        endpoint = f'/charts/{chart_id}/data'
        
        data, error = self._make_request(endpoint)
        
        if error:
            return None, error
        
        return data, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data for country and indicator.
        
        Note: OWID API structure requires chart ID, not indicator code.
        This method would need mapping between indicators and charts.
        """
        # Placeholder - full implementation needs chart mapping
        return [], None
    
    def _normalize_owid_data(
        self,
        chart_data: Dict,
        country_filter: Optional[str] = None
    ) -> List[Dict]:
        """Normalize OWID chart data to standard format."""
        normalized = []
        
        # OWID format varies by chart
        # Implementation would parse specific chart structure
        
        return normalized


# ============================================
# IMF Data API Client
# ============================================

class IMFClient(BaseAPIClient):
    """
    Client for IMF Data API.
    
    Provides economic and financial data:
    - GDP and national accounts
    - Inflation
    - Exchange rates
    - Government finance
    - Balance of payments
    - International investment position
    
    API: https://sdmxcentral.imf.org/
    """
    
    SOURCE_NAME = "IMF"
    SOURCE_ID = "imf"
    BASE_URL = 'https://sdmxcentral.imf.org/ws/public/sdmxapi'
    
    # Key dataflows
    DATAFLOWS = {
        'WEO': 'World Economic Outlook',
        'GFS': 'Government Finance Statistics',
        'BOP': 'Balance of Payments',
        'IFS': 'International Financial Statistics',
        'DPS': 'Debt Priority Statistics',
    }
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 86400,
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
        )
        self.logger.info("IMF API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch countries from IMF API."""
        endpoint = '/dataflow/IMF/WEO/1.0/?detail=referenceonly'
        
        data, error = self._make_request(endpoint)
        if error:
            return None, error
        
        # Parse SDMX response
        countries = []
        return countries, None
    
    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch indicators from IMF API."""
        # IMF uses SDMX format with concepts
        indicators = []
        return indicators, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch data for country and indicator."""
        # IMF uses SDMX format
        # Example: /data/IMF/WEO/{indicator}/{country}/?startPeriod={year}&endPeriod={year}
        return [], None


# ============================================
# UNESCO API Client
# ============================================

class UNESCOClient(BaseAPIClient):
    """
    Client for UNESCO Institute for Statistics API.
    
    Provides education, science, and culture data:
    - Education indicators
    - Literacy rates
    - School enrollment
    - Research and development
    - Cultural statistics
    
    API: http://uis.unesco.org/
    """
    
    SOURCE_NAME = "UNESCO"
    SOURCE_ID = "unesco"
    BASE_URL = 'http://uis.unesco.org/api'
    
    # Key indicator categories
    CATEGORIES = {
        'education': 'Education',
        'literacy': 'Literacy',
        'science': 'Science and Technology',
        'culture': 'Culture',
        'communication': 'Communication',
    }
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 86400,
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
        )
        self.logger.info("UNESCO API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch countries from UNESCO API."""
        endpoint = '/v2/country'
        
        data, error = self._make_request(endpoint)
        if error:
            return None, error
        
        countries = []
        if isinstance(data, list):
            for country in data:
                countries.append({
                    'code': country.get('isoCode', ''),
                    'name': country.get('name', ''),
                    'uid': country.get('uid', ''),
                })
        
        return countries, None
    
    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch indicators from UNESCO API."""
        endpoint = '/v2/indicator'
        
        data, error = self._make_request(endpoint)
        if error:
            return None, error
        
        indicators = []
        if isinstance(data, list):
            for indicator in data:
                indicators.append({
                    'code': indicator.get('code', ''),
                    'name': indicator.get('label', {}).get('en', ''),
                    'description': indicator.get('metadata', {}).get('description', ''),
                    'source': self.SOURCE_ID,
                })
        
        return indicators, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch data for country and indicator."""
        endpoint = f'/v2/data/{indicator_code}/{country_code}'
        
        params = {}
        if start_year:
            params['start'] = start_year
        if end_year:
            params['end'] = end_year
        
        data, error = self._make_request(endpoint, params=params)
        if error:
            return None, error
        
        if not isinstance(data, list):
            return [], None
        
        return self._normalize_unesco_data(data, indicator_code), None
    
    def _normalize_unesco_data(
        self,
        raw_data: List[Dict],
        indicator_code: str
    ) -> List[Dict]:
        """Normalize UNESCO API response."""
        normalized = []
        
        for record in raw_data:
            try:
                value = record.get('obsValue', {}).get('value')
                if value is None:
                    continue
                
                year = record.get('timePeriod', {}).get('value')
                if year is None:
                    continue
                
                normalized.append({
                    'country_code': record.get('refArea', {}).get('code', ''),
                    'country_name': record.get('refArea', {}).get('label', {}).get('en', ''),
                    'indicator_code': indicator_code,
                    'indicator_name': record.get('refIndicator', {}).get('label', {}).get('en', ''),
                    'year': int(year),
                    'value': float(value),
                    'unit': record.get('unitMeasure', {}).get('label', {}).get('en', ''),
                    'source': self.SOURCE_ID,
                })
            except Exception:
                continue
        
        return normalized


# ============================================
# ILO API Client
# ============================================

class ILOClient(BaseAPIClient):
    """
    Client for ILO (International Labour Organization) API.
    
    Provides labor and employment statistics:
    - Employment rates
    - Unemployment
    - Wages
    - Working conditions
    - Child labor
    - Occupational safety
    
    API: https://www.ilo.org/ilostat/
    """
    
    SOURCE_NAME = "ILO"
    SOURCE_ID = "ilo"
    BASE_URL = 'https://www.ilo.org/ilostat/sdmx/ws/rest'
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 86400,
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
        )
        self.logger.info("ILO API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch countries from ILO API."""
        endpoint = '/country/?detail=referenceonly'
        
        data, error = self._make_request(endpoint)
        if error:
            return None, error
        
        countries = []
        return countries, None
    
    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch indicators from ILO API."""
        indicators = []
        return indicators, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch data for country and indicator."""
        # ILO uses SDMX format
        return [], None


# ============================================
# ITU API Client
# ============================================

class ITUClient(BaseAPIClient):
    """
    Client for ITU (International Telecommunication Union) API.
    
    Provides telecommunications and ICT statistics:
    - Internet penetration
    - Mobile subscriptions
    - Broadband access
    - ICT prices
    - Network infrastructure
    
    API: https://data.itu.int/
    """
    
    SOURCE_NAME = "ITU"
    SOURCE_ID = "itu"
    BASE_URL = 'https://data.itu.int/api'
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 86400,
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
        )
        self.logger.info("ITU API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch countries from ITU API."""
        endpoint = '/countries'
        
        data, error = self._make_request(endpoint)
        if error:
            return None, error
        
        countries = []
        if isinstance(data, list):
            for country in data:
                countries.append({
                    'code': country.get('code', ''),
                    'name': country.get('name', ''),
                    'region': country.get('region', ''),
                })
        
        return countries, None
    
    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch indicators from ITU API."""
        endpoint = '/indicators'
        
        data, error = self._make_request(endpoint)
        if error:
            return None, error
        
        indicators = []
        if isinstance(data, list):
            for indicator in data:
                indicators.append({
                    'code': indicator.get('code', ''),
                    'name': indicator.get('name', ''),
                    'description': indicator.get('description', ''),
                    'source': self.SOURCE_ID,
                })
        
        return indicators, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Fetch data for country and indicator."""
        endpoint = f'/data/{country_code}/{indicator_code}'
        
        params = {}
        if start_year:
            params['startYear'] = start_year
        if end_year:
            params['endYear'] = end_year
        
        data, error = self._make_request(endpoint, params=params)
        if error:
            return None, error
        
        if not isinstance(data, list):
            return [], None
        
        return self._normalize_itu_data(data, indicator_code), None
    
    def _normalize_itu_data(
        self,
        raw_data: List[Dict],
        indicator_code: str
    ) -> List[Dict]:
        """Normalize ITU API response."""
        normalized = []
        
        for record in raw_data:
            try:
                normalized.append({
                    'country_code': record.get('countryCode', ''),
                    'country_name': record.get('countryName', ''),
                    'indicator_code': indicator_code,
                    'indicator_name': record.get('indicatorName', ''),
                    'year': int(record.get('year', 0)),
                    'value': float(record.get('value', 0)),
                    'unit': record.get('unit', ''),
                    'source': self.SOURCE_ID,
                })
            except Exception:
                continue
        
        return normalized


# ============================================
# Open-Meteo API Client (Weather)
# ============================================

class OpenMeteoClient(BaseAPIClient):
    """
    Client for Open-Meteo Weather API.
    
    Provides free weather and climate data:
    - Historical weather
    - Weather forecasts
    - Climate normals
    - Air quality data
    
    API: https://open-meteo.com/
    """
    
    SOURCE_NAME = "Open-Meteo"
    SOURCE_ID = "open_meteo"
    BASE_URL = 'https://api.open-meteo.com'
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 3600,
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
        )
        self.logger.info("Open-Meteo API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Open-Meteo doesn't provide country list."""
        return [], None
    
    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Open-Meteo doesn't use indicator codes."""
        return [], None
    
    def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        variables: Optional[List[str]] = None
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch historical weather data.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            variables: List of weather variables
        
        Returns:
            Tuple of (weather_data, error_message)
        """
        endpoint = '/v1/historical'
        
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': start_date,
            'end_date': end_date,
        }
        
        if variables:
            params['hourly'] = ','.join(variables)
        else:
            params['hourly'] = 'temperature_2m,precipitation'
        
        data, error = self._make_request(endpoint, params=params)
        if error:
            return None, error
        
        return data, None
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch climate data for country.
        
        Note: Open-Meteo uses coordinates, not country codes.
        This method would need country-to-coordinates mapping.
        """
        return [], None
