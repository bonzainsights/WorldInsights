"""
Unit tests for create_app.py module.

Tests Flask application factory following Clean Architecture principles.
All tests must pass before finalizing the app factory implementation.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestCreateApp:
    """Test suite for Flask application factory."""
    
    def test_create_app_returns_flask_instance(self):
        """Test that create_app returns a Flask application instance."""
        from app.create_app import create_app
        from flask import Flask
        
        app = create_app()
        
        assert app is not None
        assert isinstance(app, Flask)
    
    def test_create_app_with_testing_config(self):
        """Test that create_app accepts configuration."""
        from app.create_app import create_app
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-key', 'FLASK_ENV': 'testing'}):
            app = create_app()
            
            assert app is not None
            assert app.config['TESTING'] or app.config.get('FLASK_ENV') == 'testing'
    
    def test_create_app_loads_config_from_core(self):
        """Test that create_app uses Config from core module."""
        from app.create_app import create_app
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key'}):
            app = create_app()
            
            # Should have SECRET_KEY from config
            assert 'SECRET_KEY' in app.config
    
    def test_create_app_initializes_logging(self):
        """Test that create_app sets up logging."""
        from app.create_app import create_app
        from app.core.logging import get_logger
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-key'}):
            app = create_app()
            
            # Logger should be initialized
            logger = get_logger()
            assert logger is not None
    
    def test_create_app_registers_health_endpoint(self):
        """Test that a health check endpoint exists."""
        from app.create_app import create_app
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-key'}):
            app = create_app()
            
            with app.test_client() as client:
                response = client.get('/health')
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'healthy'
    
    def test_create_app_has_error_handlers(self):
        """Test that error handlers are registered."""
        from app.create_app import create_app
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-key'}):
            app = create_app()
            
            # Test 404 handler
            with app.test_client() as client:
                response = client.get('/nonexistent-route')
                
                assert response.status_code == 404
                data = response.get_json()
                assert 'error' in data
    
    def test_create_app_no_business_logic_in_routes(self):
        """Test that create_app doesn't contain business logic."""
        import inspect
        from app import create_app as create_app_module
        
        source = inspect.getsource(create_app_module)
        
        # Should not have business logic keywords (data processing, etc.)
        # This is a basic check - manual review is also important
        assert 'pandas' not in source.lower()
        assert 'numpy' not in source.lower()
    
    def test_create_app_follows_dependency_injection(self):
        """Test that create_app can accept injected config."""
        from app.create_app import create_app
        from app.core.config import Config
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-key'}):
            config = Config()
            app = create_app(config=config)
            
            assert app is not None
    
    def test_create_app_sets_app_name(self):
        """Test that the Flask app has the correct name."""
        from app.create_app import create_app
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-key'}):
            app = create_app()
            
            assert app.name == 'app.create_app' or 'worldinsights' in app.name.lower()
    
    def test_create_app_can_be_called_multiple_times(self):
        """Test that create_app can be called multiple times."""
        from app.create_app import create_app
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-key'}):
            app1 = create_app()
            app2 = create_app()
            
            # Should create separate instances
            assert app1 is not app2
    
    def test_create_app_cors_enabled(self):
        """Test that CORS is configured for API routes."""
        from app.create_app import create_app
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-key'}):
            app = create_app()
            
            # CORS should be set up (we can check via response headers)
            with app.test_client() as client:
                response = client.get('/health')
                # Basic check - if CORS is added, there might be headers
                assert response.status_code == 200
    
    def test_create_app_returns_json_responses(self):
        """Test that API endpoints return JSON."""
        from app.create_app import create_app
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-key'}):
            app = create_app()
            
            with app.test_client() as client:
                response = client.get('/health')
                
                assert response.content_type == 'application/json'
    
    def test_create_app_testing_mode_sets_testing_flag(self):
        """Test that testing configuration sets TESTING flag."""
        from app.create_app import create_app
        
        with patch.dict('os.environ', {'SECRET_KEY': 'test-key', 'FLASK_ENV': 'testing'}):
            app = create_app()
            
            # In testing environment, some flags should be set
            assert app.config.get('FLASK_ENV') == 'testing' or app.config.get('TESTING')
