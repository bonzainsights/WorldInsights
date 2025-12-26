"""
Frontend Blueprint initialization.
"""
from flask import Flask
from app.blueprints.frontend.routes import frontend_bp


def init_app(app: Flask) -> None:
    """
    Initialize frontend blueprint with Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(frontend_bp)
