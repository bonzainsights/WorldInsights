"""
Data Ingestion Service for WorldInsights.

This service orchestrates data fetching from multiple API sources:
- Parallel data fetching
- Batch processing
- Cache management
- Error handling and recovery
- Progress tracking

Following Clean Architecture:
- Service layer component
- Coordinates infrastructure layer (API clients)
- Provides business logic for data ingestion
"""
import time
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import threading

from app.core.logging import get_logger, PerformanceLogger
from app.core.entities import DataPoint, DataSource
from app.infrastructure.api_clients.base_client import BaseAPIClient
from app.infrastructure.api_clients.world_bank import WorldBankClient
from app.infrastructure.api_clients.who import WHOClient
from app.infrastructure.api_clients.fao import FAOClient
from app.infrastructure.api_clients.nasa import NASAClient, NOAAClient
from app.infrastructure.api_clients.other_sources import (
    UNDataClient, OWIDClient, IMFClient, UNESCOClient,
    ILOClient, ITUClient, OpenMeteoClient
)


@dataclass
class IngestionTask:
    """Represents a data ingestion task."""
    source_id: str
    country_code: str
    indicator_code: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    priority: int = 0
    status: str = 'pending'  # pending, running, completed, failed
    error: Optional[str] = None
    data_points: List[DataPoint] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class IngestionResult:
    """Result of a data ingestion operation."""
    success: bool
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_data_points: int
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    source_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class DataSourceRegistry:
    """Registry for managing API client instances."""
    
    def __init__(self, cache_backend=None):
        self._clients: Dict[str, BaseAPIClient] = {}
        self._cache_backend = cache_backend
        self._lock = threading.Lock()
        self.logger = get_logger(self.__class__.__name__)
    
    def register(self, source_id: str, client: BaseAPIClient) -> None:
        """Register an API client."""
        with self._lock:
            self._clients[source_id] = client
            self.logger.info(f"Registered data source: {source_id}")
    
    def get(self, source_id: str) -> Optional[BaseAPIClient]:
        """Get an API client by source ID."""
        return self._clients.get(source_id)
    
    def get_all(self) -> Dict[str, BaseAPIClient]:
        """Get all registered clients."""
        return self._clients.copy()
    
    def get_enabled(self) -> Dict[str, BaseAPIClient]:
        """Get all enabled clients."""
        return {k: v for k, v in self._clients.items()}
    
    def clear_cache(self, source_id: Optional[str] = None) -> None:
        """Clear cache for specific or all sources."""
        if source_id:
            client = self._clients.get(source_id)
            if client:
                client.clear_cache()
        else:
            for client in self._clients.values():
                client.clear_cache()


class DataIngestionService:
    """
    Service for orchestrating data ingestion from multiple sources.
    
    Features:
    - Parallel data fetching with configurable workers
    - Batch processing for large requests
    - Automatic retry on failures
    - Progress tracking
    - Cache management
    """
    
    def __init__(
        self,
        registry: Optional[DataSourceRegistry] = None,
        max_workers: int = 4,
        batch_size: int = 100
    ):
        """
        Initialize the data ingestion service.
        
        Args:
            registry: DataSourceRegistry instance
            max_workers: Maximum parallel workers
            batch_size: Batch size for processing
        """
        self.registry = registry or DataSourceRegistry()
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.logger = get_logger(self.__class__.__name__)
        
        # Auto-register default clients if registry is empty
        if not self.registry.get_all():
            self._register_default_clients()
    
    def _register_default_clients(self) -> None:
        """Register default API clients."""
        self.registry.register('world_bank', WorldBankClient())
        self.registry.register('who', WHOClient())
        self.registry.register('fao', FAOClient())
        self.registry.register('nasa', NASAClient())
        self.registry.register('un_data', UNDataClient())
        self.registry.register('owid', OWIDClient())
        self.registry.register('imf', IMFClient())
        self.registry.register('unesco', UNESCOClient())
        self.registry.register('ilo', ILOClient())
        self.registry.register('itu', ITUClient())
        self.logger.info("Registered all default API clients")
    
    def fetch_data(
        self,
        source_id: str,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[DataPoint]], Optional[str]]:
        """
        Fetch data from a single source.
        
        Args:
            source_id: Data source ID
            country_code: Country code
            indicator_code: Indicator code
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_points, error_message)
        """
        client = self.registry.get(source_id)
        if not client:
            return None, f"Unknown data source: {source_id}"
        
        with PerformanceLogger(f"Fetch data from {source_id}", self.logger):
            raw_data, error = client.get_data(
                country_code, indicator_code, start_year, end_year
            )
            
            if error:
                return None, error
            
            if not raw_data:
                return [], None
            
            # Normalize data
            normalized = client.normalize_data(raw_data, source_id)
            
            self.logger.debug(
                f"Fetched {len(normalized)} data points from {source_id}",
                extra={
                    'source': source_id,
                    'country': country_code,
                    'indicator': indicator_code,
                }
            )
            
            return normalized, None
    
    def fetch_from_multiple_sources(
        self,
        country_code: str,
        indicator_code: str,
        sources: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Dict[str, List[DataPoint]], List[str]]:
        """
        Fetch data from multiple sources in parallel.
        
        Args:
            country_code: Country code
            indicator_code: Indicator code
            sources: List of source IDs (None = all enabled)
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_by_source, errors)
        """
        if sources is None:
            sources = list(self.registry.get_enabled().keys())
        
        results = {}
        errors = []
        
        def fetch_task(source_id: str) -> Tuple[str, Optional[List[DataPoint]], Optional[str]]:
            data, error = self.fetch_data(
                source_id, country_code, indicator_code, start_year, end_year
            )
            return source_id, data, error
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(fetch_task, src): src for src in sources}
            
            for future in as_completed(futures):
                source_id, data, error = future.result()
                
                if error:
                    errors.append(f"{source_id}: {error}")
                    self.logger.warning(f"Error fetching from {source_id}: {error}")
                else:
                    results[source_id] = data or []
        
        return results, errors
    
    def fetch_multiple_indicators(
        self,
        source_id: str,
        country_code: str,
        indicator_codes: List[str],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Dict[str, List[DataPoint]], List[str]]:
        """
        Fetch multiple indicators from a single source.
        
        Args:
            source_id: Data source ID
            country_code: Country code
            indicator_codes: List of indicator codes
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_by_indicator, errors)
        """
        results = {}
        errors = []
        
        def fetch_task(indicator_code: str) -> Tuple[str, Optional[List[DataPoint]], Optional[str]]:
            data, error = self.fetch_data(
                source_id, country_code, indicator_code, start_year, end_year
            )
            return indicator_code, data, error
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(fetch_task, ind): ind for ind in indicator_codes}
            
            for future in as_completed(futures):
                indicator_code, data, error = future.result()
                
                if error:
                    errors.append(f"{indicator_code}: {error}")
                else:
                    results[indicator_code] = data or []
        
        return results, errors
    
    def ingest_batch(
        self,
        tasks: List[IngestionTask],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> IngestionResult:
        """
        Ingest data for a batch of tasks.
        
        Args:
            tasks: List of ingestion tasks
            progress_callback: Optional callback(completed, total)
        
        Returns:
            IngestionResult with summary
        """
        start_time = time.time()
        completed = 0
        failed = 0
        total_data_points = 0
        errors = []
        source_stats = {}
        
        def process_task(task: IngestionTask) -> IngestionTask:
            task.status = 'running'
            task.started_at = datetime.utcnow()
            
            data, error = self.fetch_data(
                task.source_id,
                task.country_code,
                task.indicator_code,
                task.start_year,
                task.end_year
            )
            
            if error:
                task.status = 'failed'
                task.error = error
            else:
                task.status = 'completed'
                task.data_points = data or []
            
            task.completed_at = datetime.utcnow()
            return task
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(process_task, task): task for task in tasks}
            
            for future in as_completed(futures):
                task = future.result()
                completed += 1
                
                if task.status == 'completed':
                    total_data_points += len(task.data_points)
                    
                    # Update source stats
                    if task.source_id not in source_stats:
                        source_stats[task.source_id] = {'success': 0, 'failed': 0, 'data_points': 0}
                    source_stats[task.source_id]['success'] += 1
                    source_stats[task.source_id]['data_points'] += len(task.data_points)
                else:
                    failed += 1
                    errors.append(f"{task.source_id}/{task.country_code}/{task.indicator_code}: {task.error}")
                    
                    if task.source_id not in source_stats:
                        source_stats[task.source_id] = {'success': 0, 'failed': 0, 'data_points': 0}
                    source_stats[task.source_id]['failed'] += 1
                
                if progress_callback:
                    progress_callback(completed, len(tasks))
        
        return IngestionResult(
            success=failed == 0,
            total_tasks=len(tasks),
            completed_tasks=completed - failed,
            failed_tasks=failed,
            total_data_points=total_data_points,
            errors=errors,
            duration_seconds=time.time() - start_time,
            source_stats=source_stats
        )
    
    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all data sources.
        
        Returns:
            Dict of source_id -> status info
        """
        status = {}
        
        for source_id, client in self.registry.get_all().items():
            stats = client.get_stats()
            status[source_id] = {
                'enabled': True,
                'circuit_breaker': stats.get('circuit_breaker_state', 'unknown'),
                'cache_hit_rate': stats.get('cache_hit_rate', 0),
                'request_count': stats.get('request_count', 0),
                'errors': stats.get('errors', 0),
            }
        
        return status
    
    def clear_all_caches(self) -> None:
        """Clear cache for all data sources."""
        self.registry.clear_cache()
        self.logger.info("Cleared all data source caches")
    
    def get_available_sources(self) -> List[DataSource]:
        """
        Get list of available data sources.
        
        Returns:
            List of DataSource entities
        """
        sources = []
        
        source_configs = {
            'world_bank': {
                'name': 'World Bank Open Data',
                'description': 'Over 16,000 development indicators for 200+ countries',
                'documentation_url': 'https://datahelpdesk.worldbank.org/knowledgebase/api',
                'categories': ['Economy', 'Demographics', 'Health', 'Education', 'Environment'],
            },
            'who': {
                'name': 'WHO Global Health Observatory',
                'description': 'Health statistics and indicators from WHO',
                'documentation_url': 'https://www.who.int/data/gho/data/gho-api',
                'categories': ['Health', 'Mortality', 'Diseases', 'Nutrition'],
            },
            'fao': {
                'name': 'FAO FAOSTAT',
                'description': 'Food and agriculture statistics',
                'documentation_url': 'https://www.fao.org/faostat/en/',
                'categories': ['Agriculture', 'Food Security', 'Trade', 'Land Use'],
            },
            'nasa': {
                'name': 'NASA/NOAA Climate Data',
                'description': 'Climate and earth science data',
                'documentation_url': 'https://api.nasa.gov/',
                'categories': ['Climate', 'Earth Science', 'Satellite Data'],
            },
            'un_data': {
                'name': 'UN Data',
                'description': 'United Nations statistics',
                'documentation_url': 'https://data.un.org/',
                'categories': ['National Accounts', 'Demographics', 'Trade'],
            },
            'owid': {
                'name': 'Our World in Data',
                'description': 'Research data on global challenges',
                'documentation_url': 'https://ourworldindata.org/api',
                'categories': ['Poverty', 'Health', 'Energy', 'Climate'],
            },
            'imf': {
                'name': 'IMF Data',
                'description': 'International Monetary Fund economic data',
                'documentation_url': 'https://data.imf.org/',
                'categories': ['Economy', 'Finance', 'Government'],
            },
            'unesco': {
                'name': 'UNESCO Institute for Statistics',
                'description': 'Education, science, and culture data',
                'documentation_url': 'http://uis.unesco.org/',
                'categories': ['Education', 'Science', 'Culture'],
            },
            'ilo': {
                'name': 'International Labour Organization',
                'description': 'Labor and employment statistics',
                'documentation_url': 'https://www.ilo.org/ilostat/',
                'categories': ['Employment', 'Wages', 'Working Conditions'],
            },
            'itu': {
                'name': 'International Telecommunication Union',
                'description': 'Telecommunications and ICT statistics',
                'documentation_url': 'https://data.itu.int/',
                'categories': ['Technology', 'Internet', 'Communications'],
            },
        }
        
        for source_id, client in self.registry.get_all().items():
            config = source_configs.get(source_id, {})
            sources.append(DataSource(
                id=source_id,
                name=config.get('name', source_id),
                description=config.get('description', ''),
                base_url=client.base_url,
                documentation_url=config.get('documentation_url'),
                enabled=True,
                categories=config.get('categories', []),
            ))
        
        return sources
