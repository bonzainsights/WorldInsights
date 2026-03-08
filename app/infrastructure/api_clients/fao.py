"""
FAO (Food and Agriculture Organization) API Client for WorldInsights.

This module provides access to FAO's FAOSTAT API:
- Agricultural production statistics
- Food security indicators
- Land use and forestry data
- Fisheries and aquaculture statistics
- Crop and livestock data
- Food balance sheets
- Prices and trade data

API Documentation: https://www.fao.org/faostat/en/#home

Features:
- No authentication required for basic access
- Comprehensive agricultural data
- Country-level and global statistics
- Time-series data from 1961 onwards

Following Clean Architecture:
- Infrastructure layer component
- Implements BaseAPIClient interface
- Pure data fetching and normalization
"""
from typing import Dict, List, Optional, Tuple, Any
from app.infrastructure.api_clients.base_client import BaseAPIClient, CacheBackend, CircuitBreaker
from app.core.entities import DataPoint


class FAOClient(BaseAPIClient):
    """
    Client for FAO FAOSTAT API.
    
    Key Features:
    - Access to 3000+ agricultural indicators
    - Coverage of 200+ countries and territories
    - Data from 1961 onwards
    - Free, no authentication required for basic access
    
    Example usage:
        >>> client = FAOClient()
        >>> countries, error = client.get_countries()
        >>> indicators, error = client.get_indicators()
        >>> data, error = client.get_data('USA', '5510', 2018, 2023)
    """
    
    SOURCE_NAME = "FAO"
    SOURCE_ID = "fao"
    BASE_URL = 'https://www.fao.org/faostat/api/v2'
    
    # Data domain categories
    CATEGORIES = {
        'production': 'Production - Crops, Livestock, Forestry, Fisheries',
        'trade': 'Trade - Imports, Exports',
        'food_security': 'Food Security - Food Balance Sheets',
        'prices': 'Prices - Producer Prices, Food Prices',
        'inputs': 'Inputs - Fertilizers, Pesticides, Machinery',
        'land': 'Land Use - Area, Irrigation',
        'population': 'Population - Rural, Agricultural Population',
        'emissions': 'Emissions - Agriculture GHG Emissions',
        'sdg': 'SDG Indicators - Sustainable Development Goals',
    }
    
    # Key indicator codes by category (FAO uses numeric codes)
    KEY_INDICATORS = {
        'production': [
            '5510',    # Production quantity (tonnes)
            '5312',    # Yield (hg/ha)
            '5218',    # Area harvested (ha)
            '5419',    # Producing animals
            '5420',    # Producing animals slaughtered
        ],
        'trade': [
            '5910',    # Import quantity (tonnes)
            '5920',    # Import value (1000 USD)
            '5912',    # Export quantity (tonnes)
            '5922',    # Export value (1000 USD)
        ],
        'food_security': [
            '661',     # Food supply quantity (kg/capita/year)
            '664',     # Food supply calories (kcal/capita/day)
            '667',     # Protein supply quantity (g/capita/day)
            '674',     # Fat supply quantity (g/capita/day)
        ],
        'land': [
            '5101',    # Agricultural area (ha)
            '5105',    # Arable land (ha)
            '5110',    # Permanent crops (ha)
            '5120',    # Forest area (ha)
        ],
        'inputs': [
            '5201',    # Fertilizers consumption (tonnes)
            '5202',    # Pesticides consumption (tonnes)
            '5210',    # Tractors (number)
        ],
        'emissions': [
            '7301',    # Total GHG emissions (CO2 equivalent)
            '7302',    # CH4 emissions (CO2 equivalent)
            '7303',    # N2O emissions (CO2 equivalent)
        ],
    }
    
    # Common crop/item codes
    KEY_ITEMS = {
        'wheat': '15',
        'rice': '27',
        'maize': '56',
        'soybeans': '236',
        'potatoes': '48',
        'vegetables': '2617',
        'fruits': '2622',
        'meat_total': '1005',
        'milk': '1076',
        'fish': '10000',
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
        Initialize FAO API client.
        
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
            headers={
                'Accept': 'application/json',
            }
        )
        self.logger.info("FAO API client initialized")
    
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch all countries from FAO API.
        
        Returns:
            Tuple of (countries_list, error_message)
            Each country: {code, name, iso3_code, region}
        """
        data, error = self._make_request('/codes/countries')
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'Data' not in data:
            return None, "Invalid response format from FAO API"
        
        countries = []
        for country in data['Data']:
            countries.append({
                'code': str(country.get('Code', '')),  # FAO uses numeric codes
                'name': country.get('Description', ''),
                'iso3_code': country.get('ISO3', ''),
                'iso2_code': country.get('ISO2', ''),
                'region': country.get('Region', ''),
            })
        
        self.logger.info(f"Fetched {len(countries)} countries from FAO API")
        return countries, None
    
    def get_indicators(
        self,
        domain: Optional[str] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch indicators (elements) from FAO API.
        
        Args:
            domain: Optional domain filter (e.g., 'production', 'trade')
        
        Returns:
            Tuple of (indicators_list, error_message)
            Each indicator: {code, name, description, source, unit}
        """
        data, error = self._make_request('/codes/elements')
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'Data' not in data:
            return None, "Invalid response format from FAO API"
        
        indicators = []
        for indicator in data['Data']:
            indicators.append({
                'code': str(indicator.get('Code', '')),
                'name': indicator.get('Description', ''),
                'description': '',  # FAO doesn't provide descriptions
                'source': self.SOURCE_ID,
                'unit': indicator.get('Unit', ''),
                'category': None,
            })
        
        self.logger.info(f"Fetched {len(indicators)} indicators from FAO API")
        return indicators, None
    
    def get_items(self, domain: Optional[str] = None) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch items (crops, livestock, products) from FAO API.
        
        Args:
            domain: Optional domain filter
        
        Returns:
            Tuple of (items_list, error_message)
            Each item: {code, name, category}
        """
        data, error = self._make_request('/codes/items')
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'Data' not in data:
            return None, "Invalid response format from FAO API"
        
        items = []
        for item in data['Data']:
            items.append({
                'code': str(item.get('Code', '')),
                'name': item.get('Description', ''),
                'category': item.get('ItemGroup', ''),
            })
        
        self.logger.info(f"Fetched {len(items)} items from FAO API")
        return items, None
    
    def get_key_indicators(self, category: str) -> List[str]:
        """
        Get list of key indicator codes for a category.
        
        Args:
            category: Category name (e.g., 'production', 'trade')
        
        Returns:
            List of indicator codes
        """
        return self.KEY_INDICATORS.get(category, [])
    
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        item_code: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data for country and indicator.
        
        Args:
            country_code: FAO country code (numeric)
            indicator_code: FAO element code (numeric)
            item_code: Optional item code (crop/product)
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_list, error_message)
        """
        # Build request body for FAO API
        payload = {
            'Area': [country_code],
            'Element': [indicator_code],
            'Item': [item_code] if item_code else None,
            'Year': self._build_year_range(start_year, end_year),
            'OutputFormat': 'JSON'
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # FAO API uses POST for data queries
        data, error = self._make_post_request('/data', payload)
        
        if error:
            return None, error
        
        if not isinstance(data, dict) or 'Data' not in data:
            return None, "Invalid response format from FAO API"
        
        raw_data = data['Data']
        
        if not raw_data:
            self.logger.debug(f"No data found for {country_code} - {indicator_code}")
            return [], None
        
        # Normalize to standard format
        normalized_data = self._normalize_fao_data(raw_data, indicator_code)
        
        self.logger.debug(f"Fetched {len(normalized_data)} data points for {country_code} - {indicator_code}")
        return normalized_data, None
    
    def get_data_by_iso3(
        self,
        iso3_code: str,
        indicator_code: str,
        item_code: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data using ISO3 country code.
        
        Args:
            iso3_code: ISO3 country code (e.g., 'USA', 'CHN')
            indicator_code: FAO element code
            item_code: Optional item code
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_list, error_message)
        """
        # First, get FAO country code from ISO3
        countries, error = self.get_countries()
        if error:
            return None, error
        
        fao_code = None
        for country in countries:
            if country.get('iso3_code') == iso3_code:
                fao_code = str(country.get('code'))
                break
        
        if not fao_code:
            return None, f"Country {iso3_code} not found in FAO database"
        
        return self.get_data(fao_code, indicator_code, item_code, start_year, end_year)
    
    def _make_post_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        use_cache: bool = True
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Make HTTP POST request (for FAO data queries).
        
        Args:
            endpoint: API endpoint
            payload: Request body
            use_cache: Whether to use cache
        
        Returns:
            Tuple of (response_data, error_message)
        """
        import hashlib
        import json
        import time
        import requests
        
        # Generate cache key from payload
        cache_key = f"{self.SOURCE_ID}:post:{endpoint}:{hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()}"
        
        # Try cache first
        if use_cache:
            cached_data = self._cache.get(cache_key)
            if cached_data is not None:
                self._cache_hits += 1
                return cached_data, None
            self._cache_misses += 1
        
        # Rate limiting
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self._session.post(
                url,
                json=payload,
                headers=self._default_headers,
                timeout=self.timeout
            )
            
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}"
                self.logger.error(error_msg)
                return None, error_msg
            
            data = response.json()
            
            # Cache response
            if use_cache:
                self._cache.set(cache_key, data, self.cache_ttl)
            
            return data, None
            
        except Exception as e:
            error_msg = f"Request error: {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg
    
    def _build_year_range(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Optional[List[int]]:
        """
        Build year range list for FAO API.
        
        Args:
            start_year: Start year
            end_year: End year
        
        Returns:
            List of years or None for all years
        """
        if not start_year and not end_year:
            return None
        
        # Default range if only one specified
        if not start_year:
            start_year = 1961
        if not end_year:
            end_year = 2023
        
        return list(range(start_year, end_year + 1))
    
    def _normalize_fao_data(
        self,
        raw_data: List[Dict],
        indicator_code: str
    ) -> List[Dict]:
        """
        Normalize FAO API response to standard format.
        
        FAO format:
        {
            'Area': {'Code': '231', 'Description': 'Ethiopia'},
            'Item': {'Code': '15', 'Description': 'Wheat'},
            'Element': {'Code': '5510', 'Description': 'Production'},
            'Year': {'Code': '2020', 'Value': '2020'},
            'Value': 5000000,
            'Unit': 'tonnes',
            'Symbol': 'F'
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
                area = record.get('Area', {})
                if isinstance(area, dict):
                    country_code = area.get('ISO3', '') or area.get('Code', '')
                    country_name = area.get('Description', '')
                else:
                    country_code = str(area)
                    country_name = country_code
                
                # Extract item info
                item = record.get('Item', {})
                if isinstance(item, dict):
                    item_name = item.get('Description', '')
                else:
                    item_name = ''
                
                # Extract indicator info
                element = record.get('Element', {})
                if isinstance(element, dict):
                    indicator_name = element.get('Description', indicator_code)
                else:
                    indicator_name = indicator_code
                
                # Extract year
                year = record.get('Year', {})
                if isinstance(year, dict):
                    year = year.get('Value', year.get('Code', ''))
                if year is None:
                    continue
                try:
                    year = int(year)
                except (ValueError, TypeError):
                    continue
                
                # Extract value
                value = record.get('Value')
                if value is None:
                    continue
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue
                
                # Extract unit
                unit = record.get('Unit', '')
                
                normalized_record = {
                    'country_code': str(country_code),
                    'country_name': str(country_name) if country_name else country_code,
                    'indicator_code': str(indicator_code),
                    'indicator_name': f"{indicator_name} - {item_name}" if item_name else str(indicator_name),
                    'year': year,
                    'value': value,
                    'unit': unit if unit else None,
                    'source': self.SOURCE_ID,
                    'original_value': value,
                    'original_unit': unit,
                    'metadata': {
                        'item_code': record.get('Item', {}).get('Code', '') if isinstance(record.get('Item'), dict) else '',
                        'item_name': item_name,
                        'symbol': record.get('Symbol', ''),
                        'flag': record.get('Flag', ''),
                    }
                }
                
                normalized.append(normalized_record)
                
            except Exception as e:
                self.logger.warning(f"Failed to normalize FAO record: {e}")
                continue
        
        return normalized
    
    def get_production_data(
        self,
        country_iso3: str,
        item_codes: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch agricultural production data.
        
        Args:
            country_iso3: ISO3 country code
            item_codes: Optional list of item codes (crops/products)
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_list, error_message)
        """
        indicator_code = '5510'  # Production quantity
        
        if item_codes:
            all_data = []
            for item_code in item_codes:
                data, error = self.get_data_by_iso3(
                    country_iso3, indicator_code, item_code, start_year, end_year
                )
                if error:
                    self.logger.warning(f"Error fetching {item_code}: {error}")
                    continue
                if data:
                    all_data.extend(data)
            return all_data, None
        else:
            return self.get_data_by_iso3(country_iso3, indicator_code, None, start_year, end_year)
    
    def get_trade_data(
        self,
        country_iso3: str,
        item_codes: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch trade data (imports/exports).
        
        Args:
            country_iso3: ISO3 country code
            item_codes: Optional list of item codes
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_list, error_message)
        """
        # Fetch both imports and exports
        all_data = []
        
        for indicator_code in ['5910', '5912']:  # Import qty, Export qty
            if item_codes:
                for item_code in item_codes:
                    data, error = self.get_data_by_iso3(
                        country_iso3, indicator_code, item_code, start_year, end_year
                    )
                    if error:
                        continue
                    if data:
                        all_data.extend(data)
            else:
                data, error = self.get_data_by_iso3(
                    country_iso3, indicator_code, None, start_year, end_year
                )
                if error:
                    continue
                if data:
                    all_data.extend(data)
        
        return all_data, None
