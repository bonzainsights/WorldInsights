"""
Availability Service for WorldInsights.

This service provides smart filtering capabilities:
- Given country → return available indicators
- Given indicator → return available countries
- Given multiple selections → return intersection of available data
- Pre-computed availability matrices for performance

Following Clean Architecture:
- Service layer component
- Coordinates infrastructure layer (API clients)
- Provides business logic for availability queries
"""
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import threading
import json
import hashlib

from app.core.logging import get_logger
from app.core.entities import AvailabilityMatrix
from app.infrastructure.api_clients.base_client import CacheBackend, InMemoryCache


@dataclass
class AvailabilityCache:
    """Cache for availability matrices."""
    matrices: Dict[str, AvailabilityMatrix] = field(default_factory=dict)
    last_updated: Dict[str, datetime] = field(default_factory=dict)
    ttl_seconds: int = 3600
    
    def get(self, source_id: str) -> Optional[AvailabilityMatrix]:
        """Get availability matrix for source."""
        if source_id in self.matrices:
            # Check if expired
            last_updated = self.last_updated.get(source_id)
            if last_updated and datetime.utcnow() - last_updated < timedelta(seconds=self.ttl_seconds):
                return self.matrices[source_id]
        return None
    
    def set(self, source_id: str, matrix: AvailabilityMatrix) -> None:
        """Set availability matrix for source."""
        self.matrices[source_id] = matrix
        self.last_updated[source_id] = datetime.utcnow()
    
    def is_expired(self, source_id: str) -> bool:
        """Check if matrix is expired."""
        last_updated = self.last_updated.get(source_id)
        if not last_updated:
            return True
        return datetime.utcnow() - last_updated >= timedelta(seconds=self.ttl_seconds)


class AvailabilityService:
    """
    Service for smart country-indicator availability queries.
    
    Features:
    - Country → Available indicators
    - Indicator → Available countries
    - Multiple selections → Intersection
    - Cached availability matrices
    - Pre-computed common queries
    """
    
    def __init__(
        self,
        data_ingestion_service=None,
        cache_ttl: int = 3600
    ):
        """
        Initialize availability service.
        
        Args:
            data_ingestion_service: DataIngestionService instance
            cache_ttl: Cache TTL in seconds
        """
        from app.services.data_ingestion import DataIngestionService
        self.ingestion = data_ingestion_service or DataIngestionService()
        self.cache_ttl = cache_ttl
        self._cache = AvailabilityCache(ttl_seconds=cache_ttl)
        self._lock = threading.Lock()
        self.logger = get_logger(self.__class__.__name__)
        
        # Pre-computed availability data (lazy loaded)
        self._availability_loaded = False
        self._country_indicators: Dict[str, Set[str]] = {}  # country → indicators
        self._indicator_countries: Dict[str, Set[str]] = {}  # indicator → countries
        self._source_matrices: Dict[str, AvailabilityMatrix] = {}
    
    def get_available_indicators(
        self,
        country_codes: List[str],
        sources: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get indicators available for given countries.
        
        Args:
            country_codes: List of country codes
            sources: Optional list of sources to query
        
        Returns:
            List of available indicator codes
        """
        if not country_codes:
            return self._get_all_indicators(sources)
        
        # Get indicators for each country
        all_indicators = []
        
        for source_id in (sources or self.ingestion.registry.get_enabled().keys()):
            matrix = self._get_or_build_matrix(source_id)
            if matrix:
                indicators = matrix.get_available_indicators(country_codes)
                all_indicators.extend(indicators)
        
        # Return unique indicators
        return list(set(all_indicators))
    
    def get_available_countries(
        self,
        indicator_codes: List[str],
        sources: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get countries available for given indicators.
        
        Args:
            indicator_codes: List of indicator codes
            sources: Optional list of sources to query
        
        Returns:
            List of available country codes
        """
        if not indicator_codes:
            return self._get_all_countries(sources)
        
        # Get countries for each indicator
        all_countries = []
        
        for source_id in (sources or self.ingestion.registry.get_enabled().keys()):
            matrix = self._get_or_build_matrix(source_id)
            if matrix:
                countries = matrix.get_available_countries(indicator_codes)
                all_countries.extend(countries)
        
        # Return unique countries
        return list(set(all_countries))
    
    def get_availability_matrix(
        self,
        source_id: str,
        rebuild: bool = False
    ) -> Optional[AvailabilityMatrix]:
        """
        Get availability matrix for a data source.
        
        Args:
            source_id: Data source ID
            rebuild: Force rebuild matrix
        
        Returns:
            AvailabilityMatrix or None
        """
        # Check cache first
        if not rebuild:
            cached = self._cache.get(source_id)
            if cached:
                return cached
        
        # Build matrix
        matrix = self._build_availability_matrix(source_id)
        
        if matrix:
            self._cache.set(source_id, matrix)
            self._source_matrices[source_id] = matrix
        
        return matrix
    
    def check_availability(
        self,
        country_codes: List[str],
        indicator_codes: List[str],
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Check availability for specific country-indicator combinations.
        
        Args:
            country_codes: List of country codes
            indicator_codes: List of indicator codes
            sources: Optional list of sources
        
        Returns:
            Dict with availability info:
            {
                'available': True/False,
                'missing_countries': [...],
                'missing_indicators': [...],
                'sources_with_data': [...],
                'data_points_estimate': int
            }
        """
        result = {
            'available': True,
            'missing_countries': [],
            'missing_indicators': [],
            'sources_with_data': [],
            'data_points_estimate': 0,
        }
        
        available_countries = set(self.get_available_countries(indicator_codes, sources))
        available_indicators = set(self.get_available_indicators(country_codes, sources))
        
        # Check missing countries
        for country in country_codes:
            if country.upper() not in available_countries:
                result['missing_countries'].append(country)
                result['available'] = False
        
        # Check missing indicators
        for indicator in indicator_codes:
            if indicator not in available_indicators:
                result['missing_indicators'].append(indicator)
                result['available'] = False
        
        # Find sources with data
        for source_id in (sources or self.ingestion.registry.get_enabled().keys()):
            matrix = self._get_or_build_matrix(source_id)
            if matrix:
                countries = matrix.get_available_countries(indicator_codes)
                if any(c in countries for c in country_codes):
                    result['sources_with_data'].append(source_id)
        
        # Estimate data points (rough estimate)
        if result['available']:
            result['data_points_estimate'] = len(country_codes) * len(indicator_codes) * 5  # ~5 years avg
        
        return result
    
    def get_indicator_metadata(
        self,
        indicator_code: str,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get metadata for an indicator from available sources.
        
        Args:
            indicator_code: Indicator code
            sources: Optional list of sources
        
        Returns:
            List of metadata dicts from each source
        """
        metadata = []
        
        for source_id in (sources or self.ingestion.registry.get_enabled().keys()):
            client = self.ingestion.registry.get(source_id)
            if not client:
                continue
            
            try:
                indicators, error = client.get_indicators()
                if error or not indicators:
                    continue
                
                # Find matching indicator
                for ind in indicators:
                    if ind.get('code') == indicator_code:
                        metadata.append({
                            'source': source_id,
                            'code': ind.get('code'),
                            'name': ind.get('name'),
                            'description': ind.get('description'),
                            'unit': ind.get('unit'),
                            'category': ind.get('category'),
                        })
                        break
            except Exception as e:
                self.logger.warning(f"Error fetching metadata from {source_id}: {e}")
        
        return metadata
    
    def get_country_metadata(
        self,
        country_code: str,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get metadata for a country from available sources.
        
        Args:
            country_code: Country code
            sources: Optional list of sources
        
        Returns:
            List of metadata dicts from each source
        """
        metadata = []
        
        for source_id in (sources or self.ingestion.registry.get_enabled().keys()):
            client = self.ingestion.registry.get(source_id)
            if not client:
                continue
            
            try:
                countries, error = client.get_countries()
                if error or not countries:
                    continue
                
                # Find matching country
                for country in countries:
                    code = country.get('code', '').upper()
                    iso3 = country.get('iso3_code', '').upper()
                    if code == country_code.upper() or iso3 == country_code.upper():
                        metadata.append({
                            'source': source_id,
                            'code': country.get('code'),
                            'name': country.get('name'),
                            'iso3_code': country.get('iso3_code'),
                            'region': country.get('region'),
                            'income_level': country.get('income_level'),
                        })
                        break
            except Exception as e:
                self.logger.warning(f"Error fetching country metadata from {source_id}: {e}")
        
        return metadata
    
    def search_indicators(
        self,
        query: str,
        country_code: Optional[str] = None,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search indicators by keyword.
        
        Args:
            query: Search query
            country_code: Optional country filter
            sources: Optional list of sources
        
        Returns:
            List of matching indicators with availability info
        """
        results = []
        query_lower = query.lower()
        
        for source_id in (sources or self.ingestion.registry.get_enabled().keys()):
            client = self.ingestion.registry.get(source_id)
            if not client:
                continue
            
            try:
                indicators, error = client.get_indicators()
                if error or not indicators:
                    continue
                
                # Filter by query
                for ind in indicators:
                    name = ind.get('name', '').lower()
                    desc = ind.get('description', '').lower()
                    
                    if query_lower in name or query_lower in desc:
                        # Check availability for country if specified
                        available = True
                        if country_code:
                            matrix = self._get_or_build_matrix(source_id)
                            if matrix:
                                available = country_code.upper() in matrix.country_indicators
                        
                        results.append({
                            'source': source_id,
                            'code': ind.get('code'),
                            'name': ind.get('name'),
                            'description': ind.get('description'),
                            'unit': ind.get('unit'),
                            'category': ind.get('category'),
                            'available': available,
                        })
            except Exception as e:
                self.logger.warning(f"Error searching indicators from {source_id}: {e}")
        
        return results
    
    def search_countries(
        self,
        query: str,
        indicator_code: Optional[str] = None,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search countries by name.
        
        Args:
            query: Search query
            indicator_code: Optional indicator filter
            sources: Optional list of sources
        
        Returns:
            List of matching countries with availability info
        """
        results = []
        query_lower = query.lower()
        
        for source_id in (sources or self.ingestion.registry.get_enabled().keys()):
            client = self.ingestion.registry.get(source_id)
            if not client:
                continue
            
            try:
                countries, error = client.get_countries()
                if error or not countries:
                    continue
                
                # Filter by query
                for country in countries:
                    name = country.get('name', '').lower()
                    
                    if query_lower in name:
                        # Check availability for indicator if specified
                        available = True
                        if indicator_code:
                            matrix = self._get_or_build_matrix(source_id)
                            if matrix:
                                code = country.get('code', '').upper()
                                available = indicator_code in matrix.country_indicators.get(code, [])
                        
                        results.append({
                            'source': source_id,
                            'code': country.get('code'),
                            'name': country.get('name'),
                            'iso3_code': country.get('iso3_code'),
                            'region': country.get('region'),
                            'available': available,
                        })
            except Exception as e:
                self.logger.warning(f"Error searching countries from {source_id}: {e}")
        
        return results
    
    def _get_or_build_matrix(self, source_id: str) -> Optional[AvailabilityMatrix]:
        """Get cached matrix or build new one."""
        # Check in-memory cache
        if source_id in self._source_matrices:
            return self._source_matrices[source_id]
        
        # Check TTL cache
        cached = self._cache.get(source_id)
        if cached:
            self._source_matrices[source_id] = cached
            return cached
        
        # Build new matrix
        return self._build_availability_matrix(source_id)
    
    def _build_availability_matrix(self, source_id: str) -> Optional[AvailabilityMatrix]:
        """
        Build availability matrix for a data source.
        
        This fetches countries and indicators from the source and
        builds a matrix of what data is available.
        
        Args:
            source_id: Data source ID
        
        Returns:
            AvailabilityMatrix or None
        """
        client = self.ingestion.registry.get(source_id)
        if not client:
            return None
        
        self.logger.info(f"Building availability matrix for {source_id}")
        start_time = time.time()
        
        try:
            # Fetch countries
            countries, error = client.get_countries()
            if error or not countries:
                self.logger.warning(f"Failed to fetch countries for {source_id}: {error}")
                return None
            
            # Fetch indicators (sample for performance)
            indicators, error = client.get_indicators()
            if error or not indicators:
                self.logger.warning(f"Failed to fetch indicators for {source_id}: {error}")
                return None
            
            # Build matrix
            country_indicators: Dict[str, List[str]] = {}
            indicator_countries: Dict[str, List[str]] = {}
            
            # For performance, we'll sample a subset of indicators
            # In production, this would be pre-computed and cached
            sample_indicators = indicators[:100]  # Sample first 100
            
            for country in countries:
                country_code = country.get('code', '').upper()
                if not country_code:
                    continue
                
                country_indicators[country_code] = []
                
                for indicator in sample_indicators:
                    indicator_code = indicator.get('code', '')
                    if not indicator_code:
                        continue
                    
                    # Check if data exists (sample check)
                    # In production, this would use a more efficient method
                    data, error = client.get_data(country_code, indicator_code, start_year=2020, end_year=2020)
                    if data and len(data) > 0:
                        country_indicators[country_code].append(indicator_code)
                        
                        if indicator_code not in indicator_countries:
                            indicator_countries[indicator_code] = []
                        indicator_countries[indicator_code].append(country_code)
            
            matrix = AvailabilityMatrix(
                country_indicators=country_indicators,
                indicator_countries=indicator_countries,
                source=source_id,
                version=1
            )
            
            elapsed = time.time() - start_time
            self.logger.info(
                f"Built availability matrix for {source_id} in {elapsed:.2f}s",
                extra={
                    'countries': len(country_indicators),
                    'indicators': len(indicator_countries),
                }
            )
            
            return matrix
            
        except Exception as e:
            self.logger.error(f"Error building matrix for {source_id}: {e}")
            return None
    
    def _get_all_countries(self, sources: Optional[List[str]] = None) -> List[str]:
        """Get all available countries."""
        countries = set()
        
        for source_id in (sources or self.ingestion.registry.get_enabled().keys()):
            matrix = self._get_or_build_matrix(source_id)
            if matrix:
                countries.update(matrix.country_indicators.keys())
        
        return list(countries)
    
    def _get_all_indicators(self, sources: Optional[List[str]] = None) -> List[str]:
        """Get all available indicators."""
        indicators = set()
        
        for source_id in (sources or self.ingestion.registry.get_enabled().keys()):
            matrix = self._get_or_build_matrix(source_id)
            if matrix:
                indicators.update(matrix.indicator_countries.keys())
        
        return list(indicators)
    
    def invalidate_cache(self, source_id: Optional[str] = None) -> None:
        """
        Invalidate availability cache.

        Args:
            source_id: Optional source ID to invalidate (None = all)
        """
        with self._lock:
            if source_id:
                self._cache.matrices.pop(source_id, None)
                self._source_matrices.pop(source_id, None)
            else:
                self._cache.matrices.clear()
                self._source_matrices.clear()

        self.logger.info(f"Invalidated availability cache for {source_id or 'all sources'}")

    # =========================================================================
    # Cascade Filtering Methods (NEW - for Dashboard Builder)
    # =========================================================================

    def get_indicators_for_provider(self, provider: str) -> List[Dict[str, Any]]:
        """
        Get all indicators available from a specific provider.

        Args:
            provider: Provider ID (e.g., 'who', 'world_bank', 'fao')

        Returns:
            List of indicator dictionaries with metadata
        """
        client = self.ingestion.registry.get(provider)
        if not client:
            return []

        indicators, error = client.get_indicators()
        if error or not indicators:
            return []

        return indicators

    def get_countries_for_indicators(
        self,
        provider: str,
        indicator_codes: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get countries that have ALL specified indicators from a provider.

        This implements the cascade filter:
        Provider → Select Indicators → Filter Countries

        Args:
            provider: Provider ID
            indicator_codes: List of indicator codes

        Returns:
            List of country dictionaries that have ALL indicators
        """
        if not indicator_codes:
            # Return all countries for provider
            return self.get_countries_for_provider(provider)

        # Get availability matrix
        matrix = self.get_availability_matrix(provider)
        if not matrix:
            return []

        # Get intersection of countries for all indicators
        available_countries = matrix.get_available_countries(indicator_codes)

        # Get full country metadata
        countries = []
        client = self.ingestion.registry.get(provider)
        if client:
            country_data, _ = client.get_countries()
            if country_data:
                country_map = {c.get('code', '').upper(): c for c in country_data}
                for country_code in available_countries:
                    if country_code in country_map:
                        countries.append(country_map[country_code])

        return countries

    def get_indicators_for_countries(
        self,
        provider: str,
        country_codes: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get indicators available for ALL specified countries from a provider.

        This implements the reverse cascade filter:
        Provider → Select Countries → Filter Indicators

        Args:
            provider: Provider ID
            country_codes: List of country codes

        Returns:
            List of indicator dictionaries available for ALL countries
        """
        if not country_codes:
            # Return all indicators for provider
            return self.get_indicators_for_provider(provider)

        # Get availability matrix
        matrix = self.get_availability_matrix(provider)
        if not matrix:
            return []

        # Get intersection of indicators for all countries
        available_indicators = matrix.get_available_indicators(country_codes)

        # Get full indicator metadata
        indicators = []
        client = self.ingestion.registry.get(provider)
        if client:
            indicator_data, _ = client.get_indicators()
            if indicator_data:
                indicator_map = {i.get('code', ''): i for i in indicator_data}
                for ind_code in available_indicators:
                    if ind_code in indicator_map:
                        indicators.append(indicator_map[ind_code])

        return indicators

    def get_years_for_selection(
        self,
        provider: str,
        country_codes: List[str],
        indicator_codes: List[str]
    ) -> Dict[str, Any]:
        """
        Get available year range for a specific selection.

        Args:
            provider: Provider ID
            country_codes: List of country codes
            indicator_codes: List of indicator codes

        Returns:
            Dictionary with min_year, max_year, and available_years
        """
        if not country_codes or not indicator_codes:
            return {'min_year': None, 'max_year': None, 'available_years': []}

        # Fetch sample data to determine year range
        client = self.ingestion.registry.get(provider)
        if not client:
            return {'min_year': None, 'max_year': None, 'available_years': []}

        # Get data for first country-indicator pair
        data, error = client.get_data(
            country_codes[0],
            indicator_codes[0],
            start_year=None,
            end_year=None
        )

        if error or not data:
            return {'min_year': None, 'max_year': None, 'available_years': []}

        # Extract years from data
        years = set()
        for record in data:
            if 'year' in record and record['year']:
                years.add(record['year'])

        if not years:
            return {'min_year': None, 'max_year': None, 'available_years': []}

        return {
            'min_year': min(years),
            'max_year': max(years),
            'available_years': sorted(list(years))
        }

    def get_countries_for_provider(self, provider: str) -> List[Dict[str, Any]]:
        """
        Get all countries available from a provider.

        Args:
            provider: Provider ID

        Returns:
            List of country dictionaries
        """
        client = self.ingestion.registry.get(provider)
        if not client:
            return []

        countries, error = client.get_countries()
        if error or not countries:
            return []

        return countries

    def get_availability_summary(
        self,
        provider: str,
        country_codes: Optional[List[str]] = None,
        indicator_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive availability summary for dashboard builder.

        This is the main endpoint used by the dashboard builder UI.

        Args:
            provider: Provider ID
            country_codes: Optional list of selected country codes
            indicator_codes: Optional list of selected indicator codes

        Returns:
            Dictionary with:
            - providers: List of all providers
            - indicators: Filtered indicators (or all if none selected)
            - countries: Filtered countries (or all if none selected)
            - years: Available year range
            - counts: Various counts for UI badges
        """
        result = {
            'providers': [],
            'indicators': [],
            'countries': [],
            'years': {'min_year': None, 'max_year': None, 'available_years': []},
            'counts': {
                'total_providers': 0,
                'total_indicators': 0,
                'total_countries': 0,
                'filtered_indicators': 0,
                'filtered_countries': 0
            }
        }

        # Get all providers
        result['providers'] = list(self.ingestion.registry.get_enabled().keys())
        result['counts']['total_providers'] = len(result['providers'])

        if not provider:
            return result

        # Get indicators based on selection
        if country_codes and len(country_codes) > 0:
            # Filter by countries
            result['indicators'] = self.get_indicators_for_countries(provider, country_codes)
        else:
            # All indicators for provider
            result['indicators'] = self.get_indicators_for_provider(provider)

        result['counts']['filtered_indicators'] = len(result['indicators'])
        result['counts']['total_indicators'] = len(result['indicators'])

        # Get countries based on selection
        if indicator_codes and len(indicator_codes) > 0:
            # Filter by indicators
            result['countries'] = self.get_countries_for_indicators(provider, indicator_codes)
        else:
            # All countries for provider
            result['countries'] = self.get_countries_for_provider(provider)

        result['counts']['filtered_countries'] = len(result['countries'])
        result['counts']['total_countries'] = len(result['countries'])

        # Get year range
        if country_codes and indicator_codes:
            result['years'] = self.get_years_for_selection(
                provider, country_codes, indicator_codes
            )

        return result
