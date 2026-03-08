"""
WHO (World Health Organization) API Client for WorldInsights.

This module provides access to WHO's Global Health Observatory (GHO) API:
- Health indicators and statistics
- Disease surveillance data
- Mortality and morbidity rates
- Vaccination coverage
- Health system metrics
- Nutrition and malnutrition data

API Documentation: https://www.who.int/data/gho/data/gho-api

Features:
- No authentication required
- RESTful JSON API
- Comprehensive health indicators
- Country-level and global statistics

Following Clean Architecture:
- Infrastructure layer component
- Implements BaseAPIClient interface
- Pure data fetching and normalization
"""
from typing import Dict, List, Optional, Tuple, Any
from app.infrastructure.api_clients.base_client import BaseAPIClient, CacheBackend, CircuitBreaker
from app.core.entities import DataPoint


class WHOClient(BaseAPIClient):
    """
    Client for WHO Global Health Observatory API.
    
    Key Features:
    - Access to 1000+ health indicators
    - Coverage of 194 WHO member states
    - Data from 2000 onwards for most indicators
    - Free, no authentication required
    
    Example usage:
        >>> client = WHOClient()
        >>> countries, error = client.get_countries()
        >>> indicators, error = client.get_indicators()
        >>> data, error = client.get_data('USA', 'WHOSIS_000001', 2018, 2023)
    """
    
    SOURCE_NAME = "WHO"
    SOURCE_ID = "who"
    BASE_URL = 'https://ghoapi.azureedge.net/api'
    
    # Key health indicator categories
    CATEGORIES = {
        'mortality': 'Mortality and Global Health Estimates',
        'diseases': 'Diseases and Conditions',
        'vaccination': 'Immunization',
        'nutrition': 'Nutrition and Malnutrition',
        'health_system': 'Health Systems',
        'maternal': 'Maternal Health',
        'child_health': 'Child Health',
        'infectious': 'Infectious Diseases',
        'ncd': 'Noncommunicable Diseases',
        'mental_health': 'Mental Health',
        'substance_use': 'Substance Use',
        'environment': 'Environmental Health',
        'injuries': 'Injuries and Violence',
        'universal_health': 'Universal Health Coverage',
    }
    
    # Key indicator codes by category
    KEY_INDICATORS = {
        'mortality': [
            'WHOSIS_000001',     # Crude death rate (per 1000 population)
            'WHOSIS_000004',     # Life expectancy at birth (years)
            'WHOSIS_000005',     # Life expectancy at age 60 (years)
            'SDG_MORT_NMR',      # Neonatal mortality rate (per 1000 live births)
            'SDG_MORT_U5MR',     # Under-5 mortality rate (per 1000 live births)
        ],
        'diseases': [
            'DATASOURCE_MALARIA',     # Malaria cases
            'DATASOURCE_TB',          # Tuberculosis cases
            'DATASOURCE_HIV',         # HIV prevalence
            'DATASOURCE_HEPATITIS',   # Hepatitis cases
        ],
        'vaccination': [
            'IMDTC',             # Immunization DTP3 coverage (%)
            'IMDTC_MCV',         # Immunization MCV coverage (%)
            'IMBCG',             # Immunization BCG coverage (%)
        ],
        'nutrition': [
            'GHO_NUT_000001',    # Prevalence of undernourishment (%)
            'GHO_NUT_000002',    # Prevalence of stunting (%)
            'GHO_NUT_000003',    # Prevalence of wasting (%)
            'GHO_BF_EXCL',       # Exclusive breastfeeding rate (%)
        ],
        'maternal': [
            'MATERNAL_MORTALITY_RATIO',  # Maternal mortality ratio
            'ANTENATAL_CARE',            # Antenatal care coverage (%)
            'DELIVERY_BY_SKILLED',       # Deliveries by skilled attendant (%)
        ],
        'infectious': [
            'DATASOURCE_MALARIA_INCIDENCE',    # Malaria incidence
            'DATASOURCE_TB_INCIDENCE',         # TB incidence
            'DATASOURCE_HIV_PREVALENCE',       # HIV prevalence
            'DATASOURCE_HEPATITIS_B',          # Hepatitis B prevalence
        ],
        'ncd': [
            'NCD_RIS_9',           # Raised blood pressure prevalence (%)
            'NCD_RIS_10',          # Raised blood glucose prevalence (%)
            'NCD_RIS_11',          # Obesity prevalence (%)
            'TOB_PREV',            # Tobacco use prevalence (%)
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
        Initialize WHO API client.
        
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
            rate_limit="5 per second",
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker=circuit_breaker,
            headers={'Accept': 'application/json'}
        )
        self.logger.info("WHO API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch all countries from WHO API.
        
        Returns:
            Tuple of (countries_list, error_message)
            Each country: {code, name, region, income_level}
        """
        data, error = self._make_request('COUNTRY')
        
        if error:
            return None, error
        
        if not isinstance(data, list):
            return None, "Invalid response format from WHO API"
        
        countries = []
        for country in data:
            countries.append({
                'code': country.get('Code', ''),
                'name': country.get('DisplayName', ''),
                'iso2_code': country.get('ISO4217', ''),  # WHO uses different codes
                'region': country.get('Region', ''),
                'income_level': country.get('IncomeGroup', ''),
            })
        
        self.logger.info(f"Fetched {len(countries)} countries from WHO API")
        return countries, None
    
    def get_indicators(
        self,
        category: Optional[str] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch indicators from WHO API.
        
        Args:
            category: Optional category filter
        
        Returns:
            Tuple of (indicators_list, error_message)
            Each indicator: {code, name, description, source, category}
        """
        data, error = self._make_request('INDICATOR')
        
        if error:
            return None, error
        
        if not isinstance(data, list):
            return None, "Invalid response format from WHO API"
        
        indicators = []
        for indicator in data:
            # Get category from indicator metadata
            indicator_category = indicator.get('Category', {})
            if isinstance(indicator_category, dict):
                indicator_category = indicator_category.get('id', '')
            
            indicators.append({
                'code': indicator.get('Code', ''),
                'name': indicator.get('DisplayName', ''),
                'description': indicator.get('Indicator', {}).get('description', '') if isinstance(indicator.get('Indicator'), dict) else '',
                'source': self.SOURCE_ID,
                'category': indicator_category if indicator_category else None,
                'unit': indicator.get('Unit', {}).get('Unit', '') if isinstance(indicator.get('Unit'), dict) else '',
            })
        
        # Filter by category if specified
        if category and category in self.CATEGORIES:
            category_keywords = self.CATEGORIES[category].lower().split()
            filtered = []
            for ind in indicators:
                name_lower = ind.get('name', '').lower()
                if any(kw in name_lower for kw in category_keywords):
                    filtered.append(ind)
            indicators = filtered
        
        self.logger.info(f"Fetched {len(indicators)} indicators from WHO API")
        return indicators, None
    
    def get_key_indicators(self, category: str) -> List[str]:
        """
        Get list of key indicator codes for a category.
        
        Args:
            category: Category name (e.g., 'mortality', 'vaccination')
        
        Returns:
            List of indicator codes
        """
        return self.KEY_INDICATORS.get(category, [])
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data for country and indicator.
        
        Args:
            country_code: Country code (e.g., 'USA', 'CHN')
            indicator_code: Indicator code (e.g., 'WHOSIS_000001')
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_list, error_message)
        """
        # WHO API endpoint format: /{indicator_code}?filter=COUNTRY:{country_code}
        endpoint = indicator_code
        
        params = {
            'filter': f'COUNTRY:{country_code}'
        }
        
        data, error = self._make_request(endpoint, params=params)
        
        if error:
            return None, error
        
        if not isinstance(data, list):
            return None, "Invalid response format from WHO API"
        
        if not data:
            self.logger.debug(f"No data found for {country_code} - {indicator_code}")
            return [], None
        
        # Normalize to standard format
        normalized_data = self._normalize_who_data(data, indicator_code)
        
        # Filter by year range if specified
        if start_year or end_year:
            filtered = []
            for record in normalized_data:
                year = record.get('year')
                if year:
                    if start_year and year < start_year:
                        continue
                    if end_year and year > end_year:
                        continue
                filtered.append(record)
            normalized_data = filtered
        
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
        Fetch data for multiple countries.
        
        Args:
            country_codes: List of country codes
            indicator_code: Indicator code
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_list, error_message)
        """
        all_data = []
        
        for country_code in country_codes:
            data, error = self.get_data(country_code, indicator_code, start_year, end_year)
            if error:
                self.logger.warning(f"Error fetching {country_code}: {error}")
                continue
            if data:
                all_data.extend(data)
        
        return all_data, None
    
    def _normalize_who_data(
        self,
        raw_data: List[Dict],
        indicator_code: str
    ) -> List[Dict]:
        """
        Normalize WHO API response to standard format.
        
        WHO format:
        {
            'COUNTRY': {'Code': 'USA', 'DisplayName': 'United States of America'},
            'INDICATOR': {'Code': 'WHOSIS_000001', 'DisplayName': 'Crude death rate'},
            'Period': '2020',
            'Numeric': 8.5,
            'Unit': {'Unit': 'per 1000 population'},
            'Sex': {'Code': 'BOTHSEX', 'DisplayName': 'Both sexes'},
        }
        
        Args:
            raw_data: Raw API response
            indicator_code: Indicator code for lookup
        
        Returns:
            List of normalized data records
        """
        normalized = []
        
        for record in raw_data:
            try:
                # Extract country info
                country = record.get('COUNTRY', {})
                if isinstance(country, dict):
                    country_code = country.get('Code', '')
                    country_name = country.get('DisplayName', '')
                else:
                    country_code = str(country)
                    country_name = country_code
                
                # Extract indicator info
                indicator = record.get('INDICATOR', {})
                if isinstance(indicator, dict):
                    indicator_name = indicator.get('DisplayName', indicator_code)
                else:
                    indicator_name = indicator_code
                
                # Extract year (Period field)
                year = record.get('Period')
                if year is None:
                    continue
                try:
                    year = int(year)
                except (ValueError, TypeError):
                    continue
                
                # Extract value (Numeric field)
                value = record.get('Numeric')
                if value is None:
                    continue
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue
                
                # Extract unit
                unit = record.get('Unit', {})
                if isinstance(unit, dict):
                    unit = unit.get('Unit', '')
                
                # Extract dimension info (sex, age, etc.)
                sex = record.get('Sex', {})
                if isinstance(sex, dict):
                    sex = sex.get('DisplayName', '')
                
                normalized_record = {
                    'country_code': str(country_code),
                    'country_name': str(country_name) if country_name else country_code,
                    'indicator_code': str(indicator_code),
                    'indicator_name': str(indicator_name),
                    'year': year,
                    'value': value,
                    'unit': unit if unit else None,
                    'source': self.SOURCE_ID,
                    'original_value': value,
                    'original_unit': unit,
                    'metadata': {
                        'sex': sex if sex else None,
                        'dim1': record.get('Dim1', {}).get('DisplayName', '') if isinstance(record.get('Dim1'), dict) else '',
                        'dim2': record.get('Dim2', {}).get('DisplayName', '') if isinstance(record.get('Dim2'), dict) else '',
                    }
                }
                
                normalized.append(normalized_record)
                
            except Exception as e:
                self.logger.warning(f"Failed to normalize WHO record: {e}")
                continue
        
        return normalized
    
    def get_indicator_categories(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch indicator categories from WHO API.
        
        Returns:
            Tuple of (categories_list, error_message)
        """
        data, error = self._make_request('CATEGORY')
        
        if error:
            return None, error
        
        if not isinstance(data, list):
            return None, "Invalid response format from WHO API"
        
        categories = []
        for category in data:
            categories.append({
                'id': category.get('id', ''),
                'name': category.get('label', ''),
                'parent': category.get('parent', {}).get('id', '') if isinstance(category.get('parent'), dict) else '',
            })
        
        self.logger.info(f"Fetched {len(categories)} categories from WHO API")
        return categories, None
    
    def search_indicators(
        self,
        query: str,
        per_page: int = 50
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Search indicators by keyword.
        
        Args:
            query: Search query
            per_page: Results to return
        
        Returns:
            Tuple of (matching_indicators, error_message)
        """
        indicators, error = self.get_indicators()
        
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
