"""
World Bank API Client for WorldInsights.

This module provides comprehensive access to World Bank's open data API:
- 16,000+ development indicators
- 200+ countries and regions
- Data from 1960 onwards
- Topics: Economy, Population, Health, Education, Environment, etc.

API Documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

Features:
- No authentication required
- Automatic pagination handling
- Comprehensive indicator categories
- Country and indicator metadata
- Time-series data fetching

Following Clean Architecture:
- Infrastructure layer component
- Implements BaseAPIClient interface
- Pure data fetching and normalization
"""
from typing import Dict, List, Optional, Tuple, Any
from app.infrastructure.api_clients.base_client import BaseAPIClient, CacheBackend, CircuitBreaker
from app.core.entities import DataPoint


class WorldBankClient(BaseAPIClient):
    """
    Client for World Bank Open Data API.
    
    Key Features:
    - Access to 16,000+ indicators across multiple topics
    - Coverage of 266 countries/regions
    - Historical data from 1960
    - Free, no authentication required
    
    Example usage:
        >>> client = WorldBankClient()
        >>> countries, error = client.get_countries()
        >>> indicators, error = client.get_indicators()
        >>> data, error = client.get_data('USA', 'NY.GDP.MKTP.CD', 2018, 2023)
    """
    
    SOURCE_NAME = "World Bank"
    SOURCE_ID = "world_bank"
    BASE_URL = 'https://api.worldbank.org/v2'
    
    # Popular indicator categories
    CATEGORIES = {
        'economy': 'Economy & Growth',
        'population': 'Population & Demographics',
        'health': 'Health & Nutrition',
        'education': 'Education',
        'environment': 'Environment & Energy',
        'poverty': 'Poverty & Inequality',
        'trade': 'Trade & Competitiveness',
        'infrastructure': 'Infrastructure',
        'financial': 'Financial Sector',
        'public_sector': 'Public Sector',
        'social_protection': 'Social Protection & Labor',
        'urban': 'Urban Development',
        'gender': 'Gender',
        'climate': 'Climate Change',
    }
    
    # Common indicator codes by category
    KEY_INDICATORS = {
        'economy': [
            'NY.GDP.MKTP.CD',      # GDP (current US$)
            'NY.GDP.PCAP.CD',      # GDP per capita (current US$)
            'NY.GDP.MKTP.KD.ZG',   # GDP growth (annual %)
            'FP.CPI.TOTL.ZG',      # Inflation, consumer prices (annual %)
            'NY.GDP.DEFL.KD.ZG',   # Inflation, GDP deflator (annual %)
        ],
        'population': [
            'SP.POP.TOTL',         # Population, total
            'SP.POP.GROW',         # Population growth (annual %)
            'SP.URB.TOTL.IN.ZS',   # Urban population (% of total)
            'SP.DYN.CBRT.IN',      # Birth rate, crude (per 1,000 people)
            'SP.DYN.CDRT.IN',      # Death rate, crude (per 1,000 people)
        ],
        'health': [
            'SH.DYN.MORT',         # Mortality rate, under-5 (per 1,000)
            'SH.STA.MMRT',         # Maternal mortality ratio
            'SH.IMM.MEAS',         # Immunization, measles (% children)
            'SH.DYN.AIDS.ZS',      # Prevalence of HIV (% ages 15-49)
            'SH.STA.MALN.ZS',      # Prevalence of undernourishment (% population)
        ],
        'education': [
            'SE.PRM.NENR',         # School enrollment, primary (% net)
            'SE.SEC.NENR',         # School enrollment, secondary (% net)
            'SE.TER.ENRR',         # School enrollment, tertiary (% gross)
            'SE.ADT.LITR.ZS',      # Literacy rate, adult total (% ages 15+)
            'SE.XPD.TOTL.GD.ZS',   # Government expenditure on education (% GDP)
        ],
        'environment': [
            'EN.ATM.CO2E.PC',      # CO2 emissions (metric tons per capita)
            'EN.ATM.CO2E.KT',      # CO2 emissions (kt)
            'EN.ATM.PM25.MC.M3',   # PM2.5 air pollution (mean annual exposure)
            'ER.LND.PRCP.MM',      # Average precipitation in depth (mm per year)
            'EG.USE.ELEC.KH.PC',   # Electric power consumption (kWh per capita)
        ],
        'poverty': [
            'SI.POV.DDAY',         # Poverty headcount ratio at $2.15/day
            'SI.POV.GINI',         # Gini index (measure of inequality)
            'SI.POV.NAHC',         # Poverty headcount ratio at national poverty lines
        ],
        'trade': [
            'NE.EXP.GNFS.CD',      # Exports of goods and services (current US$)
            'NE.IMP.GNFS.CD',      # Imports of goods and services (current US$)
            'NE.TRD.GNFS.ZS',      # Trade (% of GDP)
            'BX.KLT.DINV.CD.WD',   # Foreign direct investment, net inflows
        ],
    }
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 86400,
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        """
        Initialize World Bank API client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            cache_ttl: Cache TTL in seconds (default: 24 hours)
            cache_backend: Optional cache backend
            circuit_breaker: Optional circuit breaker
        """
        super().__init__(
            base_url=self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=0.5,
            rate_limit="10 per second",
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
            headers={'Accept': 'application/json'}
        )
        self.logger.info("World Bank API client initialized")
    
    def get_countries(self, per_page: int = 300) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch all countries from World Bank API.
        
        Args:
            per_page: Results per page (max 300)
        
        Returns:
            Tuple of (countries_list, error_message)
            Each country: {code, name, capital, region, income_level}
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
            # Handle nested region/income objects
            region = country.get('region', {})
            if isinstance(region, dict):
                region = region.get('value', '')
            
            income = country.get('incomeLevel', {})
            if isinstance(income, dict):
                income = income.get('value', '')
            
            capital = country.get('capitalCity', '')
            
            countries.append({
                'code': country.get('id', ''),
                'name': country.get('name', ''),
                'iso2_code': country.get('iso2Code', ''),
                'capital': capital if capital else None,
                'region': region if region else None,
                'income_level': income if income else None,
                'latitude': country.get('latitude', ''),
                'longitude': country.get('longitude', ''),
            })
        
        self.logger.info(f"Fetched {len(countries)} countries from World Bank API")
        return countries, None
    
    def get_indicators(
        self,
        per_page: int = 500,
        category: Optional[str] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch indicators from World Bank API.
        
        Note: There are 16,000+ indicators. Use category filter or pagination.
        
        Args:
            per_page: Results per page (max 500)
            category: Optional category filter (e.g., 'economy', 'health')
        
        Returns:
            Tuple of (indicators_list, error_message)
            Each indicator: {code, name, description, source, topic}
        """
        params = {
            'format': 'json',
            'per_page': per_page
        }
        
        # If category specified, fetch from topic endpoint
        if category and category in self.CATEGORIES:
            # Get topic ID from category name
            topic_id = self._get_topic_id(category)
            if topic_id:
                endpoint = f'topic/{topic_id}/indicator'
            else:
                endpoint = 'indicator'
        else:
            endpoint = 'indicator'
        
        data, error = self._make_request(endpoint, params=params)
        
        if error:
            return None, error
        
        if not isinstance(data, list) or len(data) < 2:
            return None, "Invalid response format from World Bank API"
        
        raw_indicators = data[1]
        
        # Transform to standard format
        indicators = []
        for indicator in raw_indicators:
            source = indicator.get('source', {})
            if isinstance(source, dict):
                source = source.get('value', '')
            
            topic = indicator.get('topic', {})
            if isinstance(topic, list) and len(topic) > 0:
                topic = topic[0].get('value', '')
            elif isinstance(topic, dict):
                topic = topic.get('value', '')
            
            indicators.append({
                'code': indicator.get('id', ''),
                'name': indicator.get('name', ''),
                'description': indicator.get('sourceNote', ''),
                'source': 'world_bank',
                'topic': topic if topic else None,
                'unit': '',  # World Bank doesn't provide unit in indicator metadata
            })
        
        self.logger.info(f"Fetched {len(indicators)} indicators from World Bank API")
        return indicators, None
    
    def get_key_indicators(self, category: str) -> List[str]:
        """
        Get list of key indicator codes for a category.
        
        Args:
            category: Category name (e.g., 'economy', 'health')
        
        Returns:
            List of indicator codes
        """
        return self.KEY_INDICATORS.get(category, [])
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        per_page: int = 1000
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data for country and indicator.
        
        Args:
            country_code: Country code (e.g., 'USA', 'all' for all countries)
            indicator_code: Indicator code (e.g., 'NY.GDP.MKTP.CD')
            start_year: Start year (optional)
            end_year: End year (optional)
            per_page: Results per page
        
        Returns:
            Tuple of (data_list, error_message)
        """
        endpoint = f'country/{country_code}/indicator/{indicator_code}'
        
        params = {
            'format': 'json',
            'per_page': per_page
        }
        
        # Add date range
        if start_year and end_year:
            params['date'] = f'{start_year}:{end_year}'
        elif start_year:
            params['date'] = f'{start_year}'
        elif end_year:
            params['date'] = f'1960:{end_year}'
        
        data, error = self._make_request(endpoint, params=params)
        
        if error:
            return None, error
        
        if not isinstance(data, list) or len(data) < 2:
            return None, "Invalid response format from World Bank API"
        
        raw_data = data[1]
        
        if not raw_data:
            self.logger.debug(f"No data found for {country_code} - {indicator_code}")
            return [], None
        
        # Normalize to standard format
        normalized_data = self._normalize_worldbank_data(raw_data, indicator_code)
        
        self.logger.debug(f"Fetched {len(normalized_data)} data points for {country_code} - {indicator_code}")
        return normalized_data, None
    
    def get_data_for_multiple_countries(
        self,
        country_codes: List[str],
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data for multiple countries at once.
        
        Args:
            country_codes: List of country codes
            indicator_code: Indicator code
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_list, error_message)
        """
        # Join country codes with semicolon
        countries_str = ';'.join(country_codes)
        return self.get_data(countries_str, indicator_code, start_year, end_year)
    
    def get_data_for_multiple_indicators(
        self,
        country_code: str,
        indicator_codes: List[str],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data for multiple indicators at once.
        
        Args:
            country_code: Country code
            indicator_codes: List of indicator codes
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_list, error_message)
        """
        all_data = []
        
        for indicator_code in indicator_codes:
            data, error = self.get_data(country_code, indicator_code, start_year, end_year)
            if error:
                self.logger.warning(f"Error fetching {indicator_code}: {error}")
                continue
            if data:
                all_data.extend(data)
        
        return all_data, None
    
    def _normalize_worldbank_data(
        self,
        raw_data: List[Dict],
        indicator_code: str
    ) -> List[Dict]:
        """
        Normalize World Bank API response to standard format.
        
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
        
        Args:
            raw_data: Raw API response
            indicator_code: Indicator code for lookup
        
        Returns:
            List of normalized data records
        """
        normalized = []
        
        # Cache for country names
        country_names = {}
        
        for record in raw_data:
            try:
                # Skip if value is null
                value = record.get('value')
                if value is None:
                    continue
                
                # Extract country info
                country_code = record.get('countryiso3code')
                if not country_code:
                    country = record.get('country', {})
                    if isinstance(country, dict):
                        country_code = country.get('id', '')
                
                # Get country name
                country_name = record.get('country', {})
                if isinstance(country_name, dict):
                    country_name = country_name.get('value', '')
                
                # Extract indicator info
                indicator = record.get('indicator', {})
                if isinstance(indicator, dict):
                    indicator_name = indicator.get('value', indicator_code)
                else:
                    indicator_name = indicator_code
                
                # Extract year
                year = record.get('date')
                if year is None:
                    continue
                try:
                    year = int(year)
                except (ValueError, TypeError):
                    continue
                
                # Convert value to float
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue
                
                normalized_record = {
                    'country_code': str(country_code),
                    'country_name': str(country_name) if country_name else country_code,
                    'indicator_code': str(indicator_code),
                    'indicator_name': str(indicator_name),
                    'year': year,
                    'value': value,
                    'unit': None,  # World Bank doesn't provide unit in data response
                    'source': self.SOURCE_ID,
                    'original_value': value,
                    'original_unit': None,
                    'metadata': {
                        'decimal': record.get('decimal', 0),
                        'obs_status': record.get('obs_status', ''),
                    }
                }
                
                normalized.append(normalized_record)
                
            except Exception as e:
                self.logger.warning(f"Failed to normalize World Bank record: {e}")
                continue
        
        return normalized
    
    def _get_topic_id(self, category: str) -> Optional[str]:
        """
        Get World Bank topic ID for category.
        
        Args:
            category: Category name
        
        Returns:
            Topic ID or None
        """
        # World Bank topic IDs (common ones)
        topic_mapping = {
            'economy': '3',      # Economy & Growth
            'population': '8',   # Social Protection & Labor (includes demographics)
            'health': '8',       # Health, Nutrition & Population
            'education': '4',    # Education
            'environment': '6',  # Environment & Energy
            'poverty': '11',     # Poverty
            'trade': '20',       # Trade
            'infrastructure': '9',  # Infrastructure
            'financial': '7',    # Financial & Private Sector
            'public_sector': '12',  # Public Sector
        }
        return topic_mapping.get(category)
    
    def search_indicators(
        self,
        query: str,
        per_page: int = 50
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Search indicators by keyword.
        
        Note: World Bank API doesn't have a direct search endpoint.
        This fetches all indicators and filters client-side.
        
        Args:
            query: Search query
            per_page: Results to return
        
        Returns:
            Tuple of (matching_indicators, error_message)
        """
        # Fetch all indicators
        indicators, error = self.get_indicators(per_page=500)
        
        if error:
            return None, error
        
        # Filter by query (case-insensitive)
        query_lower = query.lower()
        matching = [
            ind for ind in indicators
            if query_lower in ind.get('name', '').lower() or
               query_lower in ind.get('description', '').lower()
        ]
        
        return matching[:per_page], None
