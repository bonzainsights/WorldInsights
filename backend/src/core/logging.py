
"""
Core logging module for WorldInsights Backend.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Union

def _get_log_level(level_str: str) -> int:
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return level_map.get(level_str.upper(), logging.INFO)

def _get_config_value(config: Union[Dict, Any], key: str, default: Any = None) -> Any:
    if isinstance(config, dict):
        return config.get(key, default)
    try:
        return getattr(config, key, default)
    except AttributeError:
        return default

def setup_logging(config: Union[Dict[str, Any], Any]) -> logging.Logger:
    log_level_str = _get_config_value(config, 'LOG_LEVEL', 'INFO')
    log_file = _get_config_value(config, 'LOG_FILE')
    log_max_bytes = _get_config_value(config, 'LOG_MAX_BYTES', 10485760)
    log_backup_count = _get_config_value(config, 'LOG_BACKUP_COUNT', 5)
    
    log_level = _get_log_level(log_level_str)
    
    logger = logging.getLogger('worldinsights')
    logger.setLevel(log_level)
    logger.handlers.clear()
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(log_file, maxBytes=log_max_bytes, backupCount=log_backup_count)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.propagate = False
    logger.debug(f"Logging configured: level={log_level_str}, file={log_file}")
    
    return logger

def get_logger(name: str = 'worldinsights') -> logging.Logger:
    return logging.getLogger(f'worldinsights.{name}' if name != 'worldinsights' else name)
