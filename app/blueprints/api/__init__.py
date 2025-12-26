"""
API Blueprint initialization.

Registers the API blueprint with Flask application.
"""
from flask import Flask
from app.blueprints.api.routes import api_bp


def init_app(app: Flask) -> None:
    """
    Initialize API blueprint with Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(api_bp)
