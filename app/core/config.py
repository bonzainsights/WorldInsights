"""
Core configuration module for WorldInsights Backend v2.

This module provides comprehensive configuration management following Clean Architecture.
It loads settings from environment variables and provides type-safe access to all configurations.

Features:
- Environment-based configuration (development, staging, production)
- API source configurations
- Cache configurations (Redis or in-memory)
- Rate limiting configurations
- Logging configurations
- Performance tuning parameters
"""
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class APISourceConfig:
    """Configuration for a single API source."""
    id: str
    name: str
    base_url: str
    enabled: bool = True
    requires_auth: bool = False
    api_key: Optional[str] = None
    rate_limit: str = "5 per second"
    cache_ttl: int = 3600
    timeout: int = 30
    retry_count: int = 3
    documentation_url: Optional[str] = None


@dataclass
class CacheConfig:
    """Cache configuration."""
    cache_type: str = "simple"  # 'simple' or 'redis'
    ttl: int = 3600
    default_timeout: int = 300
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_url: Optional[str] = None


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    storage_url: str = "memory://"
    default_limit: str = "100 per minute"
    api_limit: str = "60 per minute"


@dataclass
class PerformanceConfig:
    """Performance tuning configuration."""
    max_concurrent_requests: int = 10
    connection_pool_size: int = 20
    enable_compression: bool = True
    ingestion_batch_size: int = 100
    ingestion_workers: int = 4
    availability_cache_ttl: int = 3600


def _get_env(key: str, default: Any = None, cast_type: type = str) -> Any:
    """
    Get environment variable with type casting and default value.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        cast_type: Type to cast the value to (str, int, bool, float)
    
    Returns:
        Environment variable value cast to specified type
    """
    value = os.getenv(key, default)
    
    if value is None:
        return None
    
    # Handle boolean conversion
    if cast_type == bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', '1', 'yes', 'on')
    
    # Handle other type conversions
    if cast_type != str and value is not None:
        try:
            return cast_type(value)
        except (ValueError, TypeError):
            return default
    
    return value


class Config:
    """
    Application configuration class.
    
    Provides centralized, type-safe access to all application settings.
    Organized by functional area for clarity.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # ============================================
        # Application Settings
        # ============================================
        self.FLASK_ENV = _get_env('FLASK_ENV', 'production')
        self.FLASK_DEBUG = _get_env('FLASK_DEBUG', False, bool)
        self.FLASK_APP = _get_env('FLASK_APP', 'run.py')
        self.SECRET_KEY = _get_env('SECRET_KEY')
        self.HOST = _get_env('HOST', '0.0.0.0')
        self.PORT = _get_env('PORT', 5000, int)
        
        # Validate required settings
        if not self.SECRET_KEY and self.FLASK_ENV == 'production':
            raise ValueError("SECRET_KEY environment variable is required for production")
        
        # ============================================
        # Database Configuration
        # ============================================
        self.DUCKDB_PATH = _get_env('DUCKDB_PATH', './data/worldinsights.duckdb')
        self.DATABASE_URL = _get_env('DATABASE_URL', f'duckdb:///{self.DUCKDB_PATH}')
        
        # SQLAlchemy configuration (for Flask-SQLAlchemy)
        # Using SQLite for auth since DuckDB has limited SQLAlchemy support
        import os as _os
        _abs_db_path = _os.path.abspath('./data/worldinsights.db')
        self.SQLALCHEMY_DATABASE_URI = _get_env('SQLALCHEMY_DATABASE_URI', f'sqlite:///{_abs_db_path}')
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        # ============================================
        # Cache Configuration
        # ============================================
        self.CACHE = CacheConfig(
            cache_type=_get_env('CACHE_TYPE', 'simple'),
            ttl=_get_env('CACHE_TTL', 3600, int),
            default_timeout=_get_env('CACHE_DEFAULT_TIMEOUT', 300, int),
            redis_host=_get_env('REDIS_HOST', 'localhost'),
            redis_port=_get_env('REDIS_PORT', 6379, int),
            redis_db=_get_env('REDIS_DB', 0, int),
            redis_password=_get_env('REDIS_PASSWORD'),
            redis_url=_get_env('REDIS_URL')
        )
        
        # ============================================
        # Rate Limiting Configuration
        # ============================================
        self.RATE_LIMIT = RateLimitConfig(
            enabled=_get_env('RATE_LIMIT_ENABLED', True, bool),
            storage_url=_get_env('RATE_LIMIT_STORAGE_URL', 'memory://'),
            default_limit=_get_env('RATE_LIMIT_DEFAULT', '100 per minute'),
            api_limit=_get_env('RATE_LIMIT_API', '60 per minute')
        )
        
        # ============================================
        # Global API Client Configuration
        # ============================================
        self.API_TIMEOUT = _get_env('API_TIMEOUT', 30, int)
        self.API_RETRY_COUNT = _get_env('API_RETRY_COUNT', 3, int)
        self.API_RETRY_BACKOFF = _get_env('API_RETRY_BACKOFF', 0.5, float)
        self.API_USER_AGENT = _get_env('API_USER_AGENT', 'WorldInsights/2.0')
        
        # ============================================
        # Performance Configuration
        # ============================================
        self.PERFORMANCE = PerformanceConfig(
            max_concurrent_requests=_get_env('MAX_CONCURRENT_REQUESTS', 10, int),
            connection_pool_size=_get_env('CONNECTION_POOL_SIZE', 20, int),
            enable_compression=_get_env('ENABLE_COMPRESSION', True, bool),
            ingestion_batch_size=_get_env('INGESTION_BATCH_SIZE', 100, int),
            ingestion_workers=_get_env('INGESTION_WORKERS', 4, int),
            availability_cache_ttl=_get_env('AVAILABILITY_CACHE_TTL', 3600, int)
        )
        
        # ============================================
        # Logging Configuration
        # ============================================
        self.LOG_LEVEL = _get_env('LOG_LEVEL', 'INFO')
        self.LOG_FILE = _get_env('LOG_FILE', './logs/worldinsights.log')
        self.LOG_MAX_BYTES = _get_env('LOG_MAX_BYTES', 10485760, int)
        self.LOG_BACKUP_COUNT = _get_env('LOG_BACKUP_COUNT', 5, int)
        self.LOG_FORMAT = _get_env('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # ============================================
        # Security Configuration
        # ============================================
        self.SESSION_LIFETIME = _get_env('SESSION_LIFETIME', 60, int)
        self.WTF_CSRF_ENABLED = _get_env('WTF_CSRF_ENABLED', True, bool)
        self.REQUIRE_HTTPS = _get_env('REQUIRE_HTTPS', False, bool)
        
        # ============================================
        # Mail Configuration
        # ============================================
        self.MAIL_SERVER = _get_env('MAIL_SERVER', 'smtp.gmail.com')
        self.MAIL_PORT = _get_env('MAIL_PORT', 587, int)
        self.MAIL_USE_TLS = _get_env('MAIL_USE_TLS', True, bool)
        self.MAIL_USE_SSL = _get_env('MAIL_USE_SSL', False, bool)
        self.MAIL_USERNAME = _get_env('MAIL_USERNAME')
        self.MAIL_PASSWORD = _get_env('MAIL_PASSWORD')
        self.MAIL_DEFAULT_SENDER = _get_env('MAIL_DEFAULT_SENDER', 'noreply@worldinsights.bonzainsights.com')
        
        # ============================================
        # Monitoring Configuration
        # ============================================
        self.HEALTH_CHECK_INTERVAL = _get_env('HEALTH_CHECK_INTERVAL', 60, int)
        self.ENABLE_METRICS = _get_env('ENABLE_METRICS', True, bool)
        
        # ============================================
        # API Source Configurations
        # ============================================
        self.API_SOURCES = self._init_api_sources()
    
    def _init_api_sources(self) -> Dict[str, APISourceConfig]:
        """Initialize API source configurations."""
        sources = {}
        
        # World Bank
        sources['world_bank'] = APISourceConfig(
            id='world_bank',
            name='World Bank Open Data',
            base_url=_get_env('WORLD_BANK_BASE_URL', 'https://api.worldbank.org/v2'),
            enabled=_get_env('WORLD_BANK_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('WORLD_BANK_RATE_LIMIT', '10 per second'),
            cache_ttl=_get_env('WORLD_BANK_CACHE_TTL', 86400, int),
            documentation_url='https://datahelpdesk.worldbank.org/knowledgebase/api'
        )
        
        # WHO
        sources['who'] = APISourceConfig(
            id='who',
            name='WHO Global Health Observatory',
            base_url=_get_env('WHO_BASE_URL', 'https://ghoapi.azureedge.net/api'),
            enabled=_get_env('WHO_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('WHO_RATE_LIMIT', '5 per second'),
            cache_ttl=_get_env('WHO_CACHE_TTL', 86400, int)
        )
        
        # FAO
        sources['fao'] = APISourceConfig(
            id='fao',
            name='FAO FAOSTAT',
            base_url=_get_env('FAO_BASE_URL', 'https://www.fao.org/faostat/api'),
            enabled=_get_env('FAO_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('FAO_RATE_LIMIT', '5 per second'),
            cache_ttl=_get_env('FAO_CACHE_TTL', 86400, int)
        )
        
        # NASA
        sources['nasa'] = APISourceConfig(
            id='nasa',
            name='NASA Open Data',
            base_url=_get_env('NASA_BASE_URL', 'https://api.nasa.gov'),
            enabled=_get_env('NASA_ENABLED', True, bool),
            requires_auth=_get_env('NASA_API_KEY') is not None,
            api_key=_get_env('NASA_API_KEY', 'DEMO_KEY'),
            rate_limit=_get_env('NASA_RATE_LIMIT', '10 per hour'),
            cache_ttl=_get_env('NASA_CACHE_TTL', 604800, int),
            documentation_url='https://api.nasa.gov/'
        )
        
        # UN Data
        sources['un_data'] = APISourceConfig(
            id='un_data',
            name='UN Data',
            base_url=_get_env('UN_DATA_BASE_URL', 'https://data.un.org/ws/rest'),
            enabled=_get_env('UN_DATA_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('UN_DATA_RATE_LIMIT', '5 per second'),
            cache_ttl=_get_env('UN_DATA_CACHE_TTL', 86400, int)
        )
        
        # Our World in Data
        sources['owid'] = APISourceConfig(
            id='owid',
            name='Our World in Data',
            base_url=_get_env('OWID_BASE_URL', 'https://ourworldindata.org/api'),
            enabled=_get_env('OWID_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('OWID_RATE_LIMIT', '5 per second'),
            cache_ttl=_get_env('OWID_CACHE_TTL', 86400, int)
        )
        
        # IMF
        sources['imf'] = APISourceConfig(
            id='imf',
            name='IMF Data',
            base_url=_get_env('IMF_BASE_URL', 'https://sdmxcentral.imf.org/ws/public/sdmxapi'),
            enabled=_get_env('IMF_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('IMF_RATE_LIMIT', '5 per second'),
            cache_ttl=_get_env('IMF_CACHE_TTL', 86400, int)
        )
        
        # UNESCO
        sources['unesco'] = APISourceConfig(
            id='unesco',
            name='UNESCO Institute for Statistics',
            base_url=_get_env('UNESCO_BASE_URL', 'http://uis.unesco.org/api'),
            enabled=_get_env('UNESCO_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('UNESCO_RATE_LIMIT', '5 per second'),
            cache_ttl=_get_env('UNESCO_CACHE_TTL', 86400, int)
        )
        
        # ILO
        sources['ilo'] = APISourceConfig(
            id='ilo',
            name='International Labour Organization',
            base_url=_get_env('ILO_BASE_URL', 'https://www.ilo.org/ilostat/sdmx/ws/rest'),
            enabled=_get_env('ILO_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('ILO_RATE_LIMIT', '5 per second'),
            cache_ttl=_get_env('ILO_CACHE_TTL', 86400, int)
        )
        
        # ITU
        sources['itu'] = APISourceConfig(
            id='itu',
            name='International Telecommunication Union',
            base_url=_get_env('ITU_BASE_URL', 'https://data.itu.int/api'),
            enabled=_get_env('ITU_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('ITU_RATE_LIMIT', '5 per second'),
            cache_ttl=_get_env('ITU_CACHE_TTL', 86400, int)
        )
        
        # UNWTO
        sources['unwto'] = APISourceConfig(
            id='unwto',
            name='World Tourism Organization',
            base_url=_get_env('UNWTO_BASE_URL', 'https://www.unwto.org/api'),
            enabled=_get_env('UNWTO_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('UNWTO_RATE_LIMIT', '5 per second'),
            cache_ttl=_get_env('UNWTO_CACHE_TTL', 86400, int)
        )
        
        # Open-Meteo
        sources['open_meteo'] = APISourceConfig(
            id='open_meteo',
            name='Open-Meteo Weather API',
            base_url=_get_env('OPEN_METEO_BASE_URL', 'https://api.open-meteo.com'),
            enabled=_get_env('OPEN_METEO_ENABLED', True, bool),
            requires_auth=False,
            rate_limit=_get_env('OPEN_METEO_RATE_LIMIT', '10 per second'),
            cache_ttl=_get_env('OPEN_METEO_CACHE_TTL', 3600, int)
        )
        
        return sources
    
    def get_enabled_sources(self) -> List[str]:
        """Get list of enabled API source IDs."""
        return [source_id for source_id, config in self.API_SOURCES.items() if config.enabled]
    
    def get_source_config(self, source_id: str) -> Optional[APISourceConfig]:
        """Get configuration for a specific API source."""
        return self.API_SOURCES.get(source_id)
    
    def to_dict(self, redact_secrets: bool = True) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Args:
            redact_secrets: If True, redact sensitive values
        
        Returns:
            Dictionary representation of configuration
        """
        config_dict = {
            'FLASK_ENV': self.FLASK_ENV,
            'FLASK_DEBUG': self.FLASK_DEBUG,
            'HOST': self.HOST,
            'PORT': self.PORT,
            'DUCKDB_PATH': self.DUCKDB_PATH,
            'DATABASE_URL': self.DATABASE_URL,
            'CACHE': {
                'cache_type': self.CACHE.cache_type,
                'ttl': self.CACHE.ttl,
                'redis_host': self.CACHE.redis_host,
                'redis_port': self.CACHE.redis_port,
            },
            'RATE_LIMIT': {
                'enabled': self.RATE_LIMIT.enabled,
                'storage_url': self.RATE_LIMIT.storage_url,
                'default_limit': self.RATE_LIMIT.default_limit,
            },
            'API_TIMEOUT': self.API_TIMEOUT,
            'API_RETRY_COUNT': self.API_RETRY_COUNT,
            'PERFORMANCE': {
                'max_concurrent_requests': self.PERFORMANCE.max_concurrent_requests,
                'connection_pool_size': self.PERFORMANCE.connection_pool_size,
                'enable_compression': self.PERFORMANCE.enable_compression,
            },
            'LOG_LEVEL': self.LOG_LEVEL,
            'LOG_FILE': self.LOG_FILE,
            'ENABLED_SOURCES': self.get_enabled_sources(),
        }
        
        if redact_secrets:
            config_dict['SECRET_KEY'] = '***REDACTED***'
        else:
            config_dict['SECRET_KEY'] = self.SECRET_KEY
        
        return config_dict
    
    def __repr__(self) -> str:
        """String representation of Config."""
        return f"<Config env={self.FLASK_ENV} debug={self.FLASK_DEBUG} sources={len(self.get_enabled_sources())}>"


# Global config instance (lazy initialization)
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create the global configuration instance.
    
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global _config
    _config = None
