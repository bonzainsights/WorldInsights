"""
Core configuration module for WorldInsights.

This module provides configuration management following Clean Architecture principles.
It has NO Flask dependencies and loads settings from environment variables.

The Config class is framework-agnostic and can be used across the application.
"""
import os
from typing import Any, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def _get_env(key: str, default: Any = None, cast_type: type = str) -> Any:
    """
    Get environment variable with type casting and default value.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        cast_type: Type to cast the value to (str, int, bool)
    
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
    
    Loads configuration from environment variables with sensible defaults.
    Validates required settings and ensures type safety.
    
    This class is immutable after initialization to prevent accidental modifications.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Validate required settings
        self._SECRET_KEY = _get_env('SECRET_KEY')
        if not self._SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required for security")
        
        # ============================================
        # Application Settings
        # ============================================
        self._FLASK_ENV = _get_env('FLASK_ENV', 'production')
        self._DEBUG = _get_env('FLASK_DEBUG', False, bool)
        
        # ============================================
        # Database Configuration
        # ============================================
        self._DUCKDB_PATH = _get_env('DUCKDB_PATH', './data/worldinsights.duckdb')
        self._DATABASE_URL = _get_env(
            'DATABASE_URL', 
            f'duckdb:///{self._DUCKDB_PATH}'
        )
        # SQLAlchemy configuration - using SQLite for auth due to DuckDB/SQLAlchemy limitations
        # DuckDB will be used directly for data analytics
        import os
        abs_db_path = os.path.abspath('./data/worldinsights.db')
        self._SQLALCHEMY_DATABASE_URI = _get_env('SQLALCHEMY_DATABASE_URI', f'sqlite:///{abs_db_path}')
        self._SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        # ============================================
        # Mail Configuration
        # ============================================
        self._MAIL_SERVER = _get_env('MAIL_SERVER', 'smtp.gmail.com')
        self._MAIL_PORT = _get_env('MAIL_PORT', 587, int)
        self._MAIL_USE_TLS = _get_env('MAIL_USE_TLS', True, bool)
        self._MAIL_USE_SSL = _get_env('MAIL_USE_SSL', False, bool)
        self._MAIL_USERNAME = _get_env('MAIL_USERNAME')
        self._MAIL_PASSWORD = _get_env('MAIL_PASSWORD')
        self._MAIL_DEFAULT_SENDER = _get_env('MAIL_DEFAULT_SENDER', 'noreply@worldinsights.com')
        
        # ============================================
        # API Configuration
        # ============================================
        self._API_RATE_LIMIT = _get_env('API_RATE_LIMIT', 100, int)
        self._API_TIMEOUT = _get_env('API_TIMEOUT', 30, int)
        self._API_RETRY_COUNT = _get_env('API_RETRY_COUNT', 3, int)
        
        # ============================================
        # Cache Configuration
        # ============================================
        self._CACHE_TYPE = _get_env('CACHE_TYPE', 'simple')
        self._CACHE_TTL = _get_env('CACHE_TTL', 3600, int)
        
        # ============================================
        # Logging Configuration
        # ============================================
        self._LOG_LEVEL = _get_env('LOG_LEVEL', 'INFO')
        self._LOG_FILE = _get_env('LOG_FILE', './logs/worldinsights.log')
        self._LOG_MAX_BYTES = _get_env('LOG_MAX_BYTES', 10485760, int)
        self._LOG_BACKUP_COUNT = _get_env('LOG_BACKUP_COUNT', 5, int)
        
        # ============================================
        # Security Configuration
        # ============================================
        self._SESSION_LIFETIME = _get_env('SESSION_LIFETIME', 60, int)
        self._WTF_CSRF_ENABLED = _get_env('WTF_CSRF_ENABLED', True, bool)
        
        # ============================================
        # Subscription Configuration
        # ============================================
        self._DEVELOPER_MODE = _get_env('DEVELOPER_MODE', True, bool)
        self._STRIPE_PUBLISHABLE_KEY = _get_env('STRIPE_PUBLISHABLE_KEY', 'pk_test_mock')
        self._STRIPE_SECRET_KEY = _get_env('STRIPE_SECRET_KEY', 'sk_test_mock')
        self._SUBSCRIPTION_TIERS = {
            'free': {'price': 0.00, 'name': 'Free'},
            'researcher': {'price': 29.00, 'name': 'Researcher'},
            'admin': {'price': None, 'name': 'Admin'}
        }
    
    # Property accessors to make attributes read-only
    @property
    def SECRET_KEY(self) -> str:
        return self._SECRET_KEY
    
    @property
    def FLASK_ENV(self) -> str:
        return self._FLASK_ENV
    
    @property
    def DEBUG(self) -> bool:
        return self._DEBUG
    
    @property
    def DUCKDB_PATH(self) -> str:
        return self._DUCKDB_PATH
    
    @property
    def DATABASE_URL(self) -> str:
        return self._DATABASE_URL
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self._SQLALCHEMY_DATABASE_URI
    
    @property
    def SQLALCHEMY_TRACK_MODIFICATIONS(self) -> bool:
        return self._SQLALCHEMY_TRACK_MODIFICATIONS
    
    @property
    def MAIL_SERVER(self) -> str:
        return self._MAIL_SERVER
    
    @property
    def MAIL_PORT(self) -> int:
        return self._MAIL_PORT
    
    @property
    def MAIL_USE_TLS(self) -> bool:
        return self._MAIL_USE_TLS
    
    @property
    def MAIL_USE_SSL(self) -> bool:
        return self._MAIL_USE_SSL
    
    @property
    def MAIL_USERNAME(self) -> str:
        return self._MAIL_USERNAME
    
    @property
    def MAIL_PASSWORD(self) -> str:
        return self._MAIL_PASSWORD
    
    @property
    def MAIL_DEFAULT_SENDER(self) -> str:
        return self._MAIL_DEFAULT_SENDER
    
    @property
    def API_RATE_LIMIT(self) -> int:
        return self._API_RATE_LIMIT
    
    @property
    def API_TIMEOUT(self) -> int:
        return self._API_TIMEOUT
    
    @property
    def API_RETRY_COUNT(self) -> int:
        return self._API_RETRY_COUNT
    
    @property
    def CACHE_TYPE(self) -> str:
        return self._CACHE_TYPE
    
    @property
    def CACHE_TTL(self) -> int:
        return self._CACHE_TTL
    
    @property
    def LOG_LEVEL(self) -> str:
        return self._LOG_LEVEL
    
    @property
    def LOG_FILE(self) -> str:
        return self._LOG_FILE
    
    @property
    def LOG_MAX_BYTES(self) -> int:
        return self._LOG_MAX_BYTES
    
    @property
    def LOG_BACKUP_COUNT(self) -> int:
        return self._LOG_BACKUP_COUNT
    
    @property
    def SESSION_LIFETIME(self) -> int:
        return self._SESSION_LIFETIME
    
    @property
    def WTF_CSRF_ENABLED(self) -> bool:
        return self._WTF_CSRF_ENABLED
    
    @property
    def DEVELOPER_MODE(self) -> bool:
        return self._DEVELOPER_MODE
    
    @property
    def STRIPE_PUBLISHABLE_KEY(self) -> str:
        return self._STRIPE_PUBLISHABLE_KEY
    
    @property
    def STRIPE_SECRET_KEY(self) -> str:
        return self._STRIPE_SECRET_KEY
    
    @property
    def SUBSCRIPTION_TIERS(self) -> Dict:
        return self._SUBSCRIPTION_TIERS
    
    def to_dict(self, redact_secrets: bool = True) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Args:
            redact_secrets: If True, redact sensitive values like SECRET_KEY
        
        Returns:
            Dictionary representation of configuration
        """
        config_dict = {
            'FLASK_ENV': self._FLASK_ENV,
            'DEBUG': self._DEBUG,
            'DUCKDB_PATH': self._DUCKDB_PATH,
            'DATABASE_URL': self._DATABASE_URL,
            'SQLALCHEMY_DATABASE_URI': self._SQLALCHEMY_DATABASE_URI,
            'SQLALCHEMY_TRACK_MODIFICATIONS': self._SQLALCHEMY_TRACK_MODIFICATIONS,
            'MAIL_SERVER': self._MAIL_SERVER,
            'MAIL_PORT': self._MAIL_PORT,
            'MAIL_USE_TLS': self._MAIL_USE_TLS,
            'MAIL_USE_SSL': self._MAIL_USE_SSL,
            'MAIL_DEFAULT_SENDER': self._MAIL_DEFAULT_SENDER,
            'API_RATE_LIMIT': self._API_RATE_LIMIT,
            'API_TIMEOUT': self._API_TIMEOUT,
            'API_RETRY_COUNT': self._API_RETRY_COUNT,
            'CACHE_TYPE': self._CACHE_TYPE,
            'CACHE_TTL': self._CACHE_TTL,
            'LOG_LEVEL': self._LOG_LEVEL,
            'LOG_FILE': self._LOG_FILE,
            'LOG_MAX_BYTES': self._LOG_MAX_BYTES,
            'LOG_BACKUP_COUNT': self._LOG_BACKUP_COUNT,
            'SESSION_LIFETIME': self._SESSION_LIFETIME,
            'WTF_CSRF_ENABLED': self._WTF_CSRF_ENABLED,
            'DEVELOPER_MODE': self._DEVELOPER_MODE,
            'SUBSCRIPTION_TIERS': self._SUBSCRIPTION_TIERS,
        }
        
        # Add sensitive fields with redaction option
        if redact_secrets:
            config_dict['SECRET_KEY'] = '***REDACTED***'
            config_dict['MAIL_USERNAME'] = '***REDACTED***' if self._MAIL_USERNAME else None
            config_dict['MAIL_PASSWORD'] = '***REDACTED***' if self._MAIL_PASSWORD else None
            config_dict['STRIPE_PUBLISHABLE_KEY'] = '***REDACTED***'
            config_dict['STRIPE_SECRET_KEY'] = '***REDACTED***'
        else:
            config_dict['SECRET_KEY'] = self._SECRET_KEY
            config_dict['MAIL_USERNAME'] = self._MAIL_USERNAME
            config_dict['MAIL_PASSWORD'] = self._MAIL_PASSWORD
            config_dict['STRIPE_PUBLISHABLE_KEY'] = self._STRIPE_PUBLISHABLE_KEY
            config_dict['STRIPE_SECRET_KEY'] = self._STRIPE_SECRET_KEY
        
        return config_dict
    
    def __repr__(self) -> str:
        """String representation of Config."""
        return f"<Config env={self._FLASK_ENV} debug={self._DEBUG}>"
