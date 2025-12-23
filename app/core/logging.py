"""
Core logging module for WorldInsights.

This module provides structured logging setup following Clean Architecture principles.
It has NO Flask dependencies and can be used across any Python application.

The logging configuration supports:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Console and file handlers
- Rotating file logs
- Structured log format with timestamps
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Union


def _get_log_level(level_str: str) -> int:
    """
    Convert string log level to logging constant.
    
    Args:
        level_str: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logging level constant
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    return level_map.get(level_str.upper(), logging.INFO)


def _get_config_value(config: Union[Dict, Any], key: str, default: Any = None) -> Any:
    """
    Get configuration value from either a dict or object with properties.
    
    Args:
        config: Configuration dict or object
        key: Configuration key
        default: Default value if key not found
    
    Returns:
        Configuration value
    """
    # Try dict-like access first
    if isinstance(config, dict):
        return config.get(key, default)
    
    # Try object attribute/property access
    try:
        return getattr(config, key, default)
    except AttributeError:
        return default


def setup_logging(config: Union[Dict[str, Any], Any]) -> logging.Logger:
    """
    Set up and configure logging for the application.
    
    This function is framework-agnostic and can be used in any Python application.
    It configures the root logger with console output and optional file output.
    
    Args:
        config: Configuration dict or object with logging settings.
                Expected keys/attributes:
                - LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                - LOG_FILE: Path to log file (optional)
                - LOG_MAX_BYTES: Max size of log file before rotation (default: 10MB)
                - LOG_BACKUP_COUNT: Number of backup files to keep (default: 5)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> config = {'LOG_LEVEL': 'INFO', 'LOG_FILE': './logs/app.log'}
        >>> logger = setup_logging(config)
        >>> logger.info('Application started')
    """
    # Get configuration values
    log_level_str = _get_config_value(config, 'LOG_LEVEL', 'INFO')
    log_file = _get_config_value(config, 'LOG_FILE')
    log_max_bytes = _get_config_value(config, 'LOG_MAX_BYTES', 10485760)  # 10MB
    log_backup_count = _get_config_value(config, 'LOG_BACKUP_COUNT', 5)
    
    # Convert log level string to constant
    log_level = _get_log_level(log_level_str)
    
    # Get or create the application logger
    logger = logging.getLogger('worldinsights')
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates when called multiple times
    logger.handlers.clear()
    
    # Create formatter with structured format
    log_format = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(filename)s:%(lineno)d - %(message)s'
    )
    formatter = logging.Formatter(
        log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # ============================================
    # Console Handler
    # ============================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ============================================
    # File Handler (if specified)
    # ============================================
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_max_bytes,
            backupCount=log_backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    logger.debug(f"Logging configured: level={log_level_str}, file={log_file}")
    
    return logger


def get_logger(name: str = 'worldinsights') -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (default: 'worldinsights')
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f'worldinsights.{name}' if name != 'worldinsights' else name)
