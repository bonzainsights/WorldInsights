"""
WSGI entry point for WorldInsights production deployment.

This file is used by WSGI servers like gunicorn, uWSGI, or mod_wsgi.

Usage with gunicorn:
    gunicorn wsgi:app

Usage with gunicorn (with workers):
    gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app

Usage with gunicorn (from command line with config):
    gunicorn --config gunicorn_config.py wsgi:app
"""
from app.create_app import create_app

# Create the Flask application
# This will be imported by WSGI servers
app = create_app()

if __name__ == '__main__':
    # This won't be called by WSGI servers but allows testing
    print("Warning: Use 'python run.py' for development or 'gunicorn wsgi:app' for production")
    app.run()
