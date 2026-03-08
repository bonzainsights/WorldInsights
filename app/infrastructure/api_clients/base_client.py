"""
Enhanced Base API Client for WorldInsights.

This module provides a robust, production-ready base class for all external API clients.
Features:
- Automatic retry with exponential backoff
- Rate limiting (token bucket algorithm)
- Multi-layer caching (Redis or in-memory)
- Request/response logging
- Timeout management
- Connection pooling
- Circuit breaker pattern for failing APIs

Following Clean Architecture:
- Infrastructure layer component
- Framework-agnostic
- Implements retry, caching, rate limiting patterns
"""
import time
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.logging import get_logger, PerformanceLogger
from app.core.entities import DataPoint


class TokenBucket:
    """
    Token bucket rate limiter.
    
    Implements token bucket algorithm for smooth rate limiting.
    Thread-safe implementation.
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.
        
        Args:
            rate: Tokens added per second
            capacity: Maximum bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
        
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        with self._lock:
            now = time.time()
            # Add tokens based on time elapsed
            time_passed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + time_passed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_token(self, tokens: int = 1, timeout: float = 30.0) -> bool:
        """
        Wait until tokens are available.
        
        Args:
            tokens: Number of tokens needed
            timeout: Maximum wait time in seconds
        
        Returns:
            True if tokens acquired, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            if self.consume(tokens):
                return True
            time.sleep(0.1)
        return False


class CircuitBreaker:
    """
    Circuit breaker pattern for failing APIs.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: API failing, requests fail immediately
    - HALF_OPEN: Testing if API recovered
    """
    
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying recovery
            half_open_max_calls: Max calls in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = self.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self._lock = threading.Lock()
    
    def can_execute(self) -> bool:
        """
        Check if request can be executed.
        
        Returns:
            True if request allowed, False otherwise
        """
        with self._lock:
            if self.state == self.CLOSED:
                return True
            
            if self.state == self.OPEN:
                # Check if recovery timeout has passed
                if self.last_failure_time and \
                   time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = self.HALF_OPEN
                    self.half_open_calls = 0
                    return True
                return False
            
            # HALF_OPEN state
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
    
    def record_success(self) -> None:
        """Record successful request."""
        with self._lock:
            if self.state == self.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    self.state = self.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            else:
                self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self) -> None:
        """Record failed request."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == self.HALF_OPEN:
                self.state = self.OPEN
                self.success_count = 0
            elif self.failure_count >= self.failure_threshold:
                self.state = self.OPEN


class CacheBackend(ABC):
    """Abstract cache backend."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in cache with TTL."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass


class InMemoryCache(CacheBackend):
    """In-memory cache backend with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry > time.time():
                    return value
                del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            expiry = time.time() + ttl
            self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


class RedisCache(CacheBackend):
    """Redis cache backend."""
    
    def __init__(self, redis_client):
        self._redis = redis_client
    
    def get(self, key: str) -> Optional[Any]:
        try:
            value = self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int) -> None:
        try:
            self._redis.setex(key, ttl, json.dumps(value))
        except Exception:
            pass
    
    def delete(self, key: str) -> None:
        try:
            self._redis.delete(key)
        except Exception:
            pass
    
    def clear(self) -> None:
        try:
            self._redis.flushdb()
        except Exception:
            pass


class BaseAPIClient(ABC):
    """
    Abstract base class for all API clients.
    
    Provides:
    - HTTP session with connection pooling
    - Retry logic with exponential backoff
    - Rate limiting (token bucket)
    - Caching (Redis or in-memory)
    - Circuit breaker for failing APIs
    - Request/response logging
    - Performance monitoring
    
    Subclasses must implement:
    - get_countries() - Fetch available countries
    - get_indicators() - Fetch available indicators  
    - get_data() - Fetch actual data
    - normalize_data() - Convert to standard schema
    """
    
    SOURCE_NAME = "base"
    SOURCE_ID = "base"
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        rate_limit: str = "5 per second",
        cache_ttl: int = 3600,
        cache_backend: Optional[CacheBackend] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for exponential retry
            rate_limit: Rate limit string (e.g., "5 per second")
            cache_ttl: Default cache TTL in seconds
            cache_backend: Cache backend instance (optional)
            circuit_breaker: Circuit breaker instance (optional)
            api_key: API key for authentication (optional)
            headers: Additional headers (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.api_key = api_key
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # Parse rate limit
        self._rate_limit = self._parse_rate_limit(rate_limit)
        
        # Initialize rate limiter
        self._rate_limiter = TokenBucket(
            rate=self._rate_limit['rate'],
            capacity=self._rate_limit['capacity']
        )
        
        # Initialize circuit breaker
        self._circuit_breaker = circuit_breaker or CircuitBreaker()
        
        # Initialize cache
        self._cache = cache_backend or InMemoryCache()
        
        # Create session with retry logic and connection pooling
        self._session = self._create_session(max_retries, backoff_factor)
        
        # Default headers
        self._default_headers = {
            'User-Agent': 'WorldInsights/2.0',
            'Accept': 'application/json',
        }
        if headers:
            self._default_headers.update(headers)
        if api_key:
            self._default_headers['Authorization'] = f'Bearer {api_key}'
        
        # Performance tracking
        self._request_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._errors = 0
        
        self.logger.info(
            f"{self.SOURCE_NAME} API client initialized",
            extra={
                'base_url': self.base_url,
                'timeout': timeout,
                'rate_limit': rate_limit,
                'cache_ttl': cache_ttl
            }
        )
    
    def _parse_rate_limit(self, rate_limit: str) -> Dict[str, float]:
        """
        Parse rate limit string to rate and capacity.
        
        Args:
            rate_limit: String like "5 per second" or "100 per minute"
        
        Returns:
            Dict with 'rate' (per second) and 'capacity'
        """
        parts = rate_limit.lower().split()
        if len(parts) >= 3:
            count = int(parts[0])
            period = parts[2]
            
            if 'second' in period:
                return {'rate': count, 'capacity': count * 2}
            elif 'minute' in period:
                return {'rate': count / 60, 'capacity': count}
            elif 'hour' in period:
                return {'rate': count / 3600, 'capacity': count}
        
        # Default: 5 per second
        return {'rate': 5, 'capacity': 10}
    
    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        """
        Create requests session with retry logic and connection pooling.
        
        Args:
            max_retries: Maximum retry attempts
            backoff_factor: Backoff factor
        
        Returns:
            Configured session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD", "OPTIONS"],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """
        Generate cache key for request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
        
        Returns:
            Cache key string
        """
        key_data = f"{self.base_url}:{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        return f"{self.SOURCE_ID}:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        if not self._rate_limiter.wait_for_token(timeout=30.0):
            self.logger.warning("Rate limit timeout exceeded")
            raise Exception("Rate limit timeout")
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Make HTTP GET request with full error handling and caching.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers
            use_cache: Whether to use cache
            cache_ttl: Override cache TTL
        
        Returns:
            Tuple of (response_data, error_message)
        """
        # Check circuit breaker
        if not self._circuit_breaker.can_execute():
            error_msg = f"Circuit breaker open for {self.SOURCE_NAME}"
            self.logger.warning(error_msg)
            return None, error_msg
        
        # Build cache key
        cache_key = self._get_cache_key(endpoint, params)
        
        # Try cache first
        if use_cache:
            cached_data = self._cache.get(cache_key)
            if cached_data is not None:
                self._cache_hits += 1
                self.logger.debug(f"Cache hit for {endpoint}")
                return cached_data, None
            self._cache_misses += 1
        
        # Enforce rate limiting
        self._rate_limit()
        
        # Build request
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = {**self._default_headers, **(headers or {})}
        
        self._request_count += 1
        
        with PerformanceLogger(f"{self.SOURCE_NAME} request to {endpoint}", self.logger):
            try:
                self.logger.debug(f"Making request to {url}", extra={'params': params})
                
                response = self._session.get(
                    url,
                    params=params,
                    headers=request_headers,
                    timeout=self.timeout
                )
                
                # Handle HTTP errors
                if response.status_code >= 400:
                    error_msg = f"HTTP {response.status_code} from {url}"
                    self.logger.error(error_msg)
                    self._circuit_breaker.record_failure()
                    self._errors += 1
                    return None, error_msg
                
                # Parse JSON
                try:
                    data = response.json()
                except ValueError as e:
                    error_msg = f"Invalid JSON response: {str(e)}"
                    self.logger.error(error_msg)
                    return None, error_msg
                
                # Success
                self._circuit_breaker.record_success()
                
                # Cache response
                if use_cache:
                    ttl = cache_ttl or self.cache_ttl
                    self._cache.set(cache_key, data, ttl)
                
                self.logger.debug(f"Successfully fetched data from {endpoint}")
                return data, None
                
            except requests.exceptions.Timeout:
                error_msg = f"Request timeout after {self.timeout}s"
                self.logger.error(error_msg)
                self._circuit_breaker.record_failure()
                self._errors += 1
                return None, error_msg
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Request error: {str(e)}"
                self.logger.error(error_msg)
                self._circuit_breaker.record_failure()
                self._errors += 1
                return None, error_msg
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dict with request counts, cache stats, etc.
        """
        return {
            'source': self.SOURCE_NAME,
            'request_count': self._request_count,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / max(1, self._cache_hits + self._cache_misses),
            'errors': self._errors,
            'circuit_breaker_state': self._circuit_breaker.state,
        }
    
    def clear_cache(self) -> None:
        """Clear client cache."""
        self._cache.clear()
        self.logger.info("Cache cleared")
    
    @abstractmethod
    def get_countries(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of available countries.
        
        Returns:
            Tuple of (countries_list, error_message)
        """
        pass
    
    @abstractmethod
    def get_indicators(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch list of available indicators.
        
        Returns:
            Tuple of (indicators_list, error_message)
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
        Fetch data for country and indicator.
        
        Args:
            country_code: Country code
            indicator_code: Indicator code
            start_year: Start year (optional)
            end_year: End year (optional)
        
        Returns:
            Tuple of (data_list, error_message)
        """
        pass
    
    def normalize_data(
        self,
        raw_data: List[Dict],
        source_name: str
    ) -> List[DataPoint]:
        """
        Normalize data to standard DataPoint schema.
        
        Args:
            raw_data: Raw API response data
            source_name: Source identifier
        
        Returns:
            List of normalized DataPoint objects
        """
        normalized = []
        
        for record in raw_data:
            try:
                # Extract common fields with defaults
                country_code = record.get('country_code') or record.get('country', '')
                country_name = record.get('country_name', '')
                indicator_code = record.get('indicator_code') or record.get('indicator', '')
                indicator_name = record.get('indicator_name', '')
                year = record.get('year')
                value = record.get('value')
                unit = record.get('unit')
                
                # Convert year to int
                if year is not None:
                    try:
                        year = int(year)
                    except (ValueError, TypeError):
                        continue
                
                # Convert value to float
                if value is not None:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        pass
                
                data_point = DataPoint(
                    country_code=str(country_code),
                    country_name=str(country_name),
                    indicator_code=str(indicator_code),
                    indicator_name=str(indicator_name),
                    year=year,
                    value=value,
                    unit=unit,
                    source=source_name,
                    original_value=record.get('original_value', value),
                    original_unit=record.get('original_unit', unit),
                    metadata=record.get('metadata', {})
                )
                normalized.append(data_point)
                
            except Exception as e:
                self.logger.warning(f"Failed to normalize record: {e}")
                continue
        
        return normalized
    
    def __del__(self):
        """Clean up session."""
        if hasattr(self, '_session'):
            self._session.close()
