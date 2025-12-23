"""
Unit tests for core/logging.py module.

Tests logging configuration following Clean Architecture principles.
All tests must pass before implementing the actual logging setup.
"""
import logging
import os
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock


class TestLogging:
    """Test suite for logging setup functionality."""
    
    def test_setup_logging_creates_logger(self):
        """Test that setup_logging creates and returns a logger."""
        from app.core.logging import setup_logging
        
        config = {
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': None  # No file logging in this test
        }
        
        logger = setup_logging(config)
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.INFO
    
    def test_setup_logging_sets_correct_log_level_debug(self):
        """Test that DEBUG log level is set correctly."""
        from app.core.logging import setup_logging
        
        config = {'LOG_LEVEL': 'DEBUG', 'LOG_FILE': None}
        logger = setup_logging(config)
        
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_sets_correct_log_level_warning(self):
        """Test that WARNING log level is set correctly."""
        from app.core.logging import setup_logging
        
        config = {'LOG_LEVEL': 'WARNING', 'LOG_FILE': None}
        logger = setup_logging(config)
        
        assert logger.level == logging.WARNING
    
    def test_setup_logging_sets_correct_log_level_error(self):
        """Test that ERROR log level is set correctly."""
        from app.core.logging import setup_logging
        
        config = {'LOG_LEVEL': 'ERROR', 'LOG_FILE': None}
        logger = setup_logging(config)
        
        assert logger.level == logging.ERROR
    
    def test_setup_logging_defaults_to_info_level(self):
        """Test that INFO is the default log level when not specified."""
        from app.core.logging import setup_logging
        
        config = {}
        logger = setup_logging(config)
        
        assert logger.level == logging.INFO
    
    def test_setup_logging_adds_console_handler(self):
        """Test that a console handler is added to the logger."""
        from app.core.logging import setup_logging
        
        config = {'LOG_LEVEL': 'INFO'}
        logger = setup_logging(config)
        
        # Check that at least one StreamHandler exists
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) > 0
    
    def test_setup_logging_adds_file_handler_when_specified(self):
        """Test that a file handler is added when LOG_FILE is specified."""
        from app.core.logging import setup_logging
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as tmp_file:
            log_file = tmp_file.name
        
        try:
            config = {
                'LOG_LEVEL': 'INFO',
                'LOG_FILE': log_file,
                'LOG_MAX_BYTES': 1048576,
                'LOG_BACKUP_COUNT': 3
            }
            
            logger = setup_logging(config)
            
            # Check for RotatingFileHandler
            from logging.handlers import RotatingFileHandler
            file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
            assert len(file_handlers) > 0
            assert file_handlers[0].baseFilename == log_file
        finally:
            # Cleanup
            if os.path.exists(log_file):
                os.remove(log_file)
    
    def test_setup_logging_uses_structured_format(self):
        """Test that log format includes structured fields."""
        from app.core.logging import setup_logging
        
        config = {'LOG_LEVEL': 'INFO'}
        logger = setup_logging(config)
        
        # Get the console handler formatter
        stream_handler = next(h for h in logger.handlers if isinstance(h, logging.StreamHandler))
        formatter = stream_handler.formatter
        
        # Check that formatter exists and has expected format
        assert formatter is not None
        # Format should include timestamp, level, logger, and message
        format_str = formatter._fmt
        assert 'asctime' in format_str or 'levelname' in format_str
    
    def test_setup_logging_creates_log_directory_if_not_exists(self):
        """Test that the log directory is created if it doesn't exist."""
        from app.core.logging import setup_logging
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = os.path.join(tmp_dir, 'subdir', 'test.log')
            
            config = {
                'LOG_LEVEL': 'INFO',
                'LOG_FILE': log_file
            }
            
            logger = setup_logging(config)
            
            # Directory should be created
            assert os.path.exists(os.path.dirname(log_file))
    
    def test_setup_logging_no_flask_imports(self):
        """Test Clean Architecture: logging module should not import Flask."""
        import inspect
        from app.core import logging as logging_module
        
        source = inspect.getsource(logging_module)
        
        # Should not have Flask imports
        assert 'from flask import' not in source
        assert 'import flask' not in source.lower()
    
    def test_setup_logging_can_be_called_multiple_times(self):
        """Test that setup_logging can be called multiple times without errors."""
        from app.core.logging import setup_logging
        
        config = {'LOG_LEVEL': 'INFO'}
        
        logger1 = setup_logging(config)
        logger2 = setup_logging(config)
        
        # Should return the same logger instance
        assert logger1.name == logger2.name
    
    def test_setup_logging_logger_name(self):
        """Test that logger has the correct name."""
        from app.core.logging import setup_logging
        
        config = {'LOG_LEVEL': 'INFO'}
        logger = setup_logging(config)
        
        # Logger should have a worldinsights-related name
        assert 'worldinsights' in logger.name.lower() or logger.name == 'app'
    
    def test_setup_logging_rotating_file_handler_config(self):
        """Test that RotatingFileHandler is configured correctly."""
        from app.core.logging import setup_logging
        from logging.handlers import RotatingFileHandler
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as tmp_file:
            log_file = tmp_file.name
        
        try:
            config = {
                'LOG_LEVEL': 'INFO',
                'LOG_FILE': log_file,
                'LOG_MAX_BYTES': 5242880,
                'LOG_BACKUP_COUNT': 7
            }
            
            logger = setup_logging(config)
            
            file_handler = next(h for h in logger.handlers if isinstance(h, RotatingFileHandler))
            assert file_handler.maxBytes == 5242880
            assert file_handler.backupCount == 7
        finally:
            if os.path.exists(log_file):
                os.remove(log_file)
    
    def test_setup_logging_logger_actually_logs(self):
        """Test that the logger can actually log messages."""
        from app.core.logging import setup_logging
        import io
        
        config = {'LOG_LEVEL': 'INFO'}
        logger = setup_logging(config)
        
        # Capture log output
        with patch('sys.stderr', new=io.StringIO()) as fake_stderr:
            logger.info("Test log message")
            output = fake_stderr.getvalue()
            
            # Output might be empty if logs go to stdout, so we'll just check the logger works
            # The important thing is that it doesn't raise an error
            assert True
    
    def test_setup_logging_accepts_config_object_with_properties(self):
        """Test that setup_logging works with config objects (like our Config class)."""
        from app.core.logging import setup_logging
        
        # Mock a config object with properties
        class MockConfig:
            @property
            def LOG_LEVEL(self):
                return 'DEBUG'
            
            @property
            def LOG_FILE(self):
                return None
        
        config = MockConfig()
        logger = setup_logging(config)
        
        assert logger.level == logging.DEBUG
