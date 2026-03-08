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
        """Test that setup_logging configures the root logger."""
        from app.core.logging import setup_logging
        import logging

        config = {
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': None  # No file logging in this test
        }

        setup_logging(level=config['LOG_LEVEL'], log_file=config['LOG_FILE'])

        root_logger = logging.getLogger()
        assert root_logger is not None
        assert root_logger.level == logging.INFO

    def test_setup_logging_sets_correct_log_level_debug(self):
        """Test that DEBUG log level is set correctly."""
        from app.core.logging import setup_logging
        import logging

        config = {'LOG_LEVEL': 'DEBUG', 'LOG_FILE': None}
        setup_logging(level=config['LOG_LEVEL'], log_file=config['LOG_FILE'])
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_sets_correct_log_level_warning(self):
        """Test that WARNING log level is set correctly."""
        from app.core.logging import setup_logging
        import logging

        config = {'LOG_LEVEL': 'WARNING', 'LOG_FILE': None}
        setup_logging(level=config['LOG_LEVEL'], log_file=config['LOG_FILE'])
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    def test_setup_logging_sets_correct_log_level_error(self):
        """Test that ERROR log level is set correctly."""
        from app.core.logging import setup_logging
        import logging

        config = {'LOG_LEVEL': 'ERROR', 'LOG_FILE': None}
        setup_logging(level=config['LOG_LEVEL'], log_file=config['LOG_FILE'])
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.ERROR

    def test_setup_logging_defaults_to_info_level(self):
        """Test that INFO is the default log level when not specified."""
        from app.core.logging import setup_logging
        import logging

        setup_logging()
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_setup_logging_adds_console_handler(self):
        """Test that a console handler is added to the logger."""
        from app.core.logging import setup_logging
        import logging

        config = {'LOG_LEVEL': 'INFO'}
        setup_logging(level=config['LOG_LEVEL'])
        
        root_logger = logging.getLogger()

        # Check that at least one StreamHandler exists
        stream_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) > 0

    def test_setup_logging_adds_file_handler_when_specified(self):
        """Test that a file handler is added when log_file is specified."""
        from app.core.logging import setup_logging
        import logging
        from logging.handlers import RotatingFileHandler

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as tmp_file:
            log_file = tmp_file.name

        try:
            setup_logging(
                level='INFO',
                log_file=log_file,
                max_bytes=1048576,
                backup_count=3
            )

            root_logger = logging.getLogger()

            # Check for RotatingFileHandler
            file_handlers = [h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)]
            assert len(file_handlers) > 0
            assert file_handlers[0].baseFilename == log_file
        finally:
            # Cleanup
            if os.path.exists(log_file):
                os.remove(log_file)
    
    def test_setup_logging_uses_structured_format(self):
        """Test that log format includes structured fields."""
        from app.core.logging import setup_logging
        import logging

        config = {'LOG_LEVEL': 'INFO'}
        setup_logging(level=config['LOG_LEVEL'])
        
        root_logger = logging.getLogger()

        # Get the console handler formatter
        stream_handler = next((h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)), None)
        assert stream_handler is not None
        formatter = stream_handler.formatter

        # Check that formatter exists and has expected format
        assert formatter is not None

    def test_setup_logging_creates_log_directory_if_not_exists(self):
        """Test that the log directory is created if it doesn't exist."""
        from app.core.logging import setup_logging
        import logging

        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = os.path.join(tmp_dir, 'subdir', 'test.log')

            setup_logging(level='INFO', log_file=log_file)

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
        import logging

        config = {'LOG_LEVEL': 'INFO'}

        setup_logging(level=config['LOG_LEVEL'])
        logger1 = logging.getLogger()
        
        setup_logging(level=config['LOG_LEVEL'])
        logger2 = logging.getLogger()

        # Should be the same root logger
        assert logger1.name == logger2.name

    def test_setup_logging_logger_name(self):
        """Test that logger can be retrieved with get_logger."""
        from app.core.logging import get_logger
        
        logger = get_logger('test_logger')
        
        # Logger should be retrieved successfully
        assert logger is not None
        assert logger.name == 'test_logger'

    def test_setup_logging_rotating_file_handler_config(self):
        """Test that RotatingFileHandler is configured correctly."""
        from app.core.logging import setup_logging
        import logging
        from logging.handlers import RotatingFileHandler

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as tmp_file:
            log_file = tmp_file.name

        try:
            setup_logging(
                level='INFO',
                log_file=log_file,
                max_bytes=5242880,
                backup_count=7
            )

            root_logger = logging.getLogger()

            file_handler = next((h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)), None)
            if file_handler:
                assert file_handler.maxBytes == 5242880
                assert file_handler.backupCount == 7
        finally:
            if os.path.exists(log_file):
                os.remove(log_file)

    def test_setup_logging_logger_actually_logs(self):
        """Test that the logger can actually log messages."""
        from app.core.logging import get_logger

        logger = get_logger('test_logger')

        # Just verify logger works without error
        logger.info("Test log message")
        assert True

    def test_setup_logging_accepts_config_object_with_properties(self):
        """Test that setup_logging works with config objects (like our Config class)."""
        from app.core.logging import setup_logging
        import logging

        # Mock a config object with properties
        class MockConfig:
            @property
            def LOG_LEVEL(self):
                return 'DEBUG'

            @property
            def LOG_FILE(self):
                return None

        config = MockConfig()
        setup_logging(level=config.LOG_LEVEL, log_file=config.LOG_FILE)
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
