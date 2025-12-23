#!/usr/bin/env python3
"""
Development server entry point for WorldInsights.

Run this file to start the development server:
    python run.py

For production, use wsgi.py with gunicorn or another WSGI server.
"""
import os
from app.create_app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment or use defaults
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5050))
    debug = app.config.get('DEBUG', False)
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║        🌍 WorldInsights Development Server              ║
╚══════════════════════════════════════════════════════════╝

Environment: {app.config.get('FLASK_ENV', 'production')}
Debug Mode:  {debug}
Running on:  http://{host}:{port}

Available endpoints:
  - Health Check: http://{host}:{port}/health
  - API Info:     http://{host}:{port}/

Press CTRL+C to quit
""")
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )
