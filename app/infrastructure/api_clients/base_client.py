"""
Base API client for WorldInsights data sources.

This module provides an abstract base class for all external API clients,
implementing common functionality like retry logic, rate limiting, error handling,
and data normalization.

Following Clean Architecture:
- This is the infrastructure layer
- Provides reusable patterns for API integration
- Framework-agnostic (can be used outside Flask)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.core.logging import get_logger


class BaseAPIClient(ABC):
    """
    Abstract base class for all API clients.
    
    Provides common functionality:
    - HTTP session with retry logic
    - Rate limiting
    - Error handling
    - Response validation
    - Data normalization to standard schema
    
    Subclasses must implement:
    - get_countries() - Fetch available countries
    - get_indicators() - Fetch available indicators
    - get_data() - Fetch actual data
    - normalize_data() - Convert to standard schema
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        rate_limit_delay: float = 0.1
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for exponential retry
            rate_limit_delay: Minimum delay between requests in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.logger = get_logger(self.__class__.__name__)
        
        # Create session with retry logic
        self.session = self._create_session(max_retries, backoff_factor)
        
        # Track last request time for rate limiting
        self._last_request_time = 0.0
    
    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        """
        Create a requests session with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for exponential retry
            
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _rate_limit(self) -> None:
        """
        Enforce rate limiting by ensuring minimum delay between requests.
        """
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Make an HTTP GET request with error handling.
        
        Args:
            endpoint: API endpoint (will be appended to base_url)
            params: Query parameters
            headers: Request headers
            
        Returns:
            Tuple of (response_data, error_message)
            - On success: (data, None)
            - On failure: (None, error_message)
        """
        # Enforce rate limiting
        self._rate_limit()
        
        # Build full URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            self.logger.debug(f"Making request to {url} with params: {params}")
            
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
                self.logger.debug(f"Successfully fetched data from {url}")
                return data, None
            except ValueError as e:
                error_msg = f"Invalid JSON response from {url}: {str(e)}"
                self.logger.error(error_msg)
                return None, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = f"Request to {url} timed out after {self.timeout} seconds"
            self.logger.error(error_msg)
            return None, error_msg
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error from {url}: {e.response.status_code} - {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error from {url}: {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg
    
    @abstractmethod
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of available countries from the API.
        
        Returns:
            Tuple of (countries_list, error_message)
            Each country dict should contain at least: {'code': str, 'name': str}
        """
        pass
    
    @abstractmethod
    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of available indicators from the API.
        
        Returns:
            Tuple of (indicators_list, error_message)
            Each indicator dict should contain at least: {'code': str, 'name': str}
        """
        pass
    
    @abstractmethod
    def get_data(
        self,
        country_code: str,
        indicator_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch data for a specific country and indicator.
        
        Args:
            country_code: Country code (e.g., 'USA', 'GBR')
            indicator_code: Indicator code
            start_year: Optional start year for filtering
            end_year: Optional end year for filtering
            
        Returns:
            Tuple of (data_list, error_message)
            Data should be normalized to standard schema
        """
        pass
    
    def normalize_data(
        self,
        raw_data: List[Dict],
        source_name: str
    ) -> List[Dict]:
        """
        Normalize data to standard WorldInsights schema.
        
        Standard schema:
        {
            'country': str,        # Country code (ISO 3166-1 alpha-3)
            'year': int,           # Year
            'indicator': str,      # Indicator code
            'value': float,        # Numeric value
            'source': str          # Data source name
        }
        
        Args:
            raw_data: Raw data from API
            source_name: Name of the data source
            
        Returns:
            List of normalized data records
        """
        # Default implementation - subclasses should override
        normalized = []
        
        for record in raw_data:
            try:
                normalized_record = {
                    'country': str(record.get('country', '')),
                    'year': int(record.get('year', 0)),
                    'indicator': str(record.get('indicator', '')),
                    'value': float(record.get('value', 0.0)) if record.get('value') is not None else None,
                    'source': source_name
                }
                normalized.append(normalized_record)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Failed to normalize record {record}: {str(e)}")
                continue
        
        return normalized
    
    def __del__(self):
        """Clean up session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()
