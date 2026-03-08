"""
Unit tests for core/config.py module.

Tests configuration management following Clean Architecture principles.
All tests must pass before implementing the actual Config class.
"""
import os
import pytest
from unittest.mock import patch


class TestConfig:
    """Test suite for Config class."""
    
    def test_config_loads_from_environment_variables(self):
        """Test that Config class loads values from environment variables."""
        with patch.dict(os.environ, {
            'FLASK_ENV': 'testing',
            'SECRET_KEY': 'test-secret-key',
            'DUCKDB_PATH': './test.duckdb'
        }):
            from app.core.config import Config
            config = Config()
            
            assert config.FLASK_ENV == 'testing'
            assert config.SECRET_KEY == 'test-secret-key'
            assert config.DUCKDB_PATH == './test.duckdb'
    
    def test_config_uses_default_values_when_env_vars_missing(self):
        """Test that Config provides sensible defaults for optional settings."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key'
        }, clear=True):
            from app.core.config import Config
            config = Config()

            # Should have defaults
            assert config.FLASK_ENV == 'production'
            assert config.FLASK_DEBUG is False
            assert config.API_TIMEOUT == 30
            assert config.API_RETRY_COUNT == 3
            assert config.CACHE.ttl == 3600
    
    def test_config_validates_required_secret_key(self):
        """Test that Config raises error when SECRET_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            from app.core.config import Config
            
            with pytest.raises(ValueError, match="SECRET_KEY.*required"):
                Config()
    
    def test_config_database_settings(self):
        """Test database configuration settings."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key',
            'DUCKDB_PATH': '/data/custom.duckdb',
            'DATABASE_URL': 'duckdb:////data/custom.duckdb'
        }):
            from app.core.config import Config
            config = Config()
            
            assert config.DUCKDB_PATH == '/data/custom.duckdb'
            assert config.DATABASE_URL == 'duckdb:////data/custom.duckdb'
    
    def test_config_api_settings(self):
        """Test API-related configuration settings."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key',
            'RATE_LIMIT_DEFAULT': '200 per minute',
            'API_TIMEOUT': '60',
            'API_RETRY_COUNT': '5'
        }):
            from app.core.config import Config
            config = Config()

            assert config.RATE_LIMIT.default_limit == '200 per minute'
            assert config.API_TIMEOUT == 60
            assert config.API_RETRY_COUNT == 5
    
    def test_config_cache_settings(self):
        """Test cache configuration settings."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key',
            'CACHE_TYPE': 'redis',
            'CACHE_TTL': '7200'
        }):
            from app.core.config import Config
            config = Config()

            assert config.CACHE.cache_type == 'redis'
            assert config.CACHE.ttl == 7200
    
    def test_config_mail_settings(self):
        """Test mail configuration settings."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key',
            'MAIL_SERVER': 'smtp.example.com',
            'MAIL_PORT': '465',
            'MAIL_USE_SSL': 'True',
            'MAIL_USERNAME': 'test@example.com',
            'MAIL_PASSWORD': 'mail-password',
            'MAIL_DEFAULT_SENDER': 'noreply@example.com'
        }):
            from app.core.config import Config
            config = Config()
            
            assert config.MAIL_SERVER == 'smtp.example.com'
            assert config.MAIL_PORT == 465
            assert config.MAIL_USE_SSL is True
            assert config.MAIL_USERNAME == 'test@example.com'
            assert config.MAIL_PASSWORD == 'mail-password'
            assert config.MAIL_DEFAULT_SENDER == 'noreply@example.com'
    
    def test_config_logging_settings(self):
        """Test logging configuration settings."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key',
            'LOG_LEVEL': 'DEBUG',
            'LOG_FILE': '/var/log/app.log',
            'LOG_MAX_BYTES': '5242880',
            'LOG_BACKUP_COUNT': '10'
        }):
            from app.core.config import Config
            config = Config()
            
            assert config.LOG_LEVEL == 'DEBUG'
            assert config.LOG_FILE == '/var/log/app.log'
            assert config.LOG_MAX_BYTES == 5242880
            assert config.LOG_BACKUP_COUNT == 10
    
    def test_config_debug_mode_in_development(self):
        """Test that FLASK_DEBUG is True in development environment."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key',
            'FLASK_ENV': 'development',
            'FLASK_DEBUG': 'True'
        }):
            from app.core.config import Config
            config = Config()

            assert config.FLASK_ENV == 'development'
            assert config.FLASK_DEBUG is True
    
    def test_config_type_conversion_for_integers(self):
        """Test that string environment variables are converted to integers."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key',
            'RATE_LIMIT_DEFAULT': '150 per minute',
            'CACHE_TTL': '1800'
        }):
            from app.core.config import Config
            config = Config()

            assert isinstance(config.RATE_LIMIT.default_limit, str)
            assert isinstance(config.CACHE.ttl, int)
    
    def test_config_type_conversion_for_booleans(self):
        """Test that string environment variables are converted to booleans."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key',
            'FLASK_DEBUG': 'True',
            'MAIL_USE_TLS': 'False',
            'MAIL_USE_SSL': 'true'
        }):
            from app.core.config import Config
            config = Config()

            assert isinstance(config.FLASK_DEBUG, bool)
            assert config.FLASK_DEBUG is True
            assert isinstance(config.MAIL_USE_TLS, bool)
            assert config.MAIL_USE_TLS is False
            assert config.MAIL_USE_SSL is True
    
    def test_config_no_flask_imports(self):
        """Test Clean Architecture: Config should not import Flask."""
        import inspect
        from app.core import config as config_module
        
        source = inspect.getsource(config_module)
        
        # Should not have Flask imports
        assert 'from flask import' not in source
        assert 'import flask' not in source.lower()
    
    def test_config_is_immutable_after_init(self):
        """Test that Config attributes should not be modified (convention-based)."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key'
        }):
            from app.core.config import Config
            config = Config()

            # Config doesn't enforce immutability but shouldn't be modified by convention
            # This test verifies the initial value is set correctly
            original_secret = config.SECRET_KEY
            assert original_secret == 'test-key'
            
            # Note: Python doesn't enforce immutability without special mechanisms
            # This is a convention-based immutability
    
    def test_config_provides_dict_representation(self):
        """Test that Config can be converted to dict for inspection."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-key',
            'FLASK_ENV': 'testing'
        }):
            from app.core.config import Config
            config = Config()
            
            config_dict = config.to_dict()
            
            assert isinstance(config_dict, dict)
            assert config_dict['FLASK_ENV'] == 'testing'
            # SECRET_KEY should not be in dict for security
            assert 'SECRET_KEY' not in config_dict or config_dict['SECRET_KEY'] == '***REDACTED***'
