"""
Structured logging module for WorldInsights.

This module provides centralized logging configuration with:
- JSON-formatted logs for production
- Colored console output for development
- File rotation with size limits
- Structured logging with context
- Log levels and filtering

Following Clean Architecture:
- Framework-agnostic (no Flask dependencies)
- Can be used across all application layers
"""
import logging
import sys
import os
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Produces JSON-formatted log entries suitable for:
    - Log aggregation systems (ELK, Splunk)
    - Cloud logging services
    - Production monitoring
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
        
        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName'):
                try:
                    json.dumps(value)  # Check if serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for development.
    
    Provides color-coded log levels for better readability:
    - DEBUG: Gray
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Bold Red
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.
        
        Args:
            record: Log record to format
        
        Returns:
            Color-formatted log string
        """
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build formatted message
        message = super().format(record)
        
        return f"{color}[{record.levelname}]{reset} {timestamp} - {message}"


def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,
    backup_count: int = 5,
    use_json: bool = False,
    log_format: Optional[str] = None
) -> None:
    """
    Configure application-wide logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
        use_json: Use JSON formatting (True for production)
        log_format: Custom log format string
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        default_format = log_format or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        if os.isatty(sys.stdout.fileno()):
            # Use colored formatter for terminal
            formatter = ColoredFormatter(default_format)
        else:
            formatter = logging.Formatter(default_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log file specified)
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__ or class name)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding structured context to logs.
    
    Usage:
        with LogContext(user_id='123', action='login'):
            logger.info('User logged in')
    """
    
    def __init__(self, **context: Any):
        """
        Initialize log context.
        
        Args:
            **context: Key-value pairs to add to log records
        """
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        """Add context to log records."""
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original log record factory."""
        logging.setLogRecordFactory(self.old_factory)


class PerformanceLogger:
    """
    Logger for performance metrics.
    
    Usage:
        with PerformanceLogger('database_query', logger):
            # execute query
    """
    
    def __init__(self, operation: str, logger: logging.Logger):
        """
        Initialize performance logger.
        
        Args:
            operation: Operation name for logging
            logger: Logger instance
        """
        self.operation = operation
        self.logger = logger
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log performance metrics."""
        duration = (datetime.now() - self.start_time).total_seconds() * 1000  # ms
        
        if exc_type:
            self.logger.error(
                f"{self.operation} failed after {duration:.2f}ms",
                extra={'duration_ms': duration, 'success': False}
            )
        else:
            self.logger.info(
                f"{self.operation} completed in {duration:.2f}ms",
                extra={'duration_ms': duration, 'success': True}
            )


# Default logging setup (called on module import if not configured)
def _ensure_logging_setup() -> None:
    """Ensure logging is set up with defaults."""
    if not logging.getLogger().handlers:
        setup_logging(
            level='INFO',
            log_file=None,  # Console only by default
            use_json=False
        )


# Auto-setup on import
_ensure_logging_setup()
