"""
Flask application factory for WorldInsights.

This module implements the application factory pattern, providing
a clean way to create and configure Flask applications with dependency injection.

Following Clean Architecture:
- This is the delivery layer (Flask-specific)
- Depends on core modules (config, logging)
- Does NOT contain business logic
- Registers blueprints and middleware
"""
from flask import Flask, jsonify, render_template, request, url_for, flash, redirect
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from typing import Optional, Union, Dict, Any

from app.core.config import Config
from app.core.logging import setup_logging, get_logger
from app.infrastructure.db import init_db, User
from app.services.auth_service import mail as service_mail


def create_app(config: Optional[Union[Config, Dict[str, Any]]] = None) -> Flask:
    """
    Create and configure the Flask application.
    
    This factory function follows the application factory pattern,
    allowing for dependency injection and easier testing.
    
    Args:
        config: Optional configuration object or dict.
                If None, creates a new Config from environment variables.
    
    Returns:
        Configured Flask application instance
    
    Example:
        >>> app = create_app()
        >>> app.run()
    
    Example with custom config:
        >>> from app.core.config import Config
        >>> config = Config()
        >>> app = create_app(config=config)
    """
    # ============================================
    # Create Flask application
    # ============================================
    app = Flask(__name__)
    
    # ============================================
    # Load configuration
    # ============================================
    if config is None:
        config = Config()
    
    # Convert Config object to dict for Flask config
    if hasattr(config, 'to_dict'):
        # It's our Config class
        config_dict = config.to_dict(redact_secrets=False)
        app.config.update(config_dict)
    elif isinstance(config, dict):
        # It's already a dict
        app.config.update(config)
    else:
        # It's an object with attributes
        for key in dir(config):
            if key.isupper():
                app.config[key] = getattr(config, key)
    
    # Set testing flag if in testing environment
    if app.config.get('FLASK_ENV') == 'testing':
        app.config['TESTING'] = True
    
    # ============================================
    # Initialize logging
    # ============================================
    logger = setup_logging(config)
    logger.info(f"WorldInsights application starting in {app.config.get('FLASK_ENV', 'production')} mode")
    
    # ============================================
    # Initialize Database
    # ============================================
    init_db(app)
    
    # ============================================
    # Initialize Flask-Login
    # ============================================
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # ============================================
    # Initialize Flask-Mail
    # ============================================
    mail = Mail()
    mail.init_app(app)
    # Update service mail instance
    service_mail.init_app(app)
    
    # ============================================
    # Initialize Flask-Limiter (Rate Limiting)
    # ============================================
    if app.config.get('RATE_LIMIT_ENABLED', True):
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=app.config.get('RATE_LIMIT_STORAGE_URL', 'memory://'),
            default_limits=["200 per day", "50 per hour"],
            storage_options={}
        )
        logger.info("Rate limiting enabled")
        # Store limiter in app extensions for access in blueprints
        app.extensions['limiter'] = limiter
    else:
        logger.warning("Rate limiting is DISABLED")
    
    # ============================================
    # Initialize Flask-Talisman (HTTPS & Security Headers)
    # ============================================
    if app.config.get('REQUIRE_HTTPS', False) and not app.config.get('TESTING', False):
        # Content Security Policy
        csp = {
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", "https://cdn.plot.ly", "https://cdn.jsdelivr.net"],
            'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            'font-src': ["'self'", "https://fonts.gstatic.com"],
            'img-src': ["'self'", "data:", "https:"],
            'connect-src': ["'self'"],
        }
        
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,  # 1 year
            content_security_policy=csp,
            content_security_policy_nonce_in=['script-src'],
            referrer_policy='strict-origin-when-cross-origin',
            feature_policy={
                'geolocation': "'none'",
                'microphone': "'none'",
                'camera': "'none'"
            }
        )
        logger.info("HTTPS enforcement and security headers enabled")
    else:
        logger.warning("HTTPS enforcement is DISABLED (development mode)")
    
    # ============================================
    # Register error handlers
    # ============================================
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status': 500
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors."""
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request was malformed or invalid',
            'status': 400
        }), 400
    
    # ============================================
    # Register basic routes
    # ============================================
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint.
        
        Returns:
            JSON response with health status
        """
        return jsonify({
            'status': 'healthy',
            'service': 'worldinsights',
            'environment': app.config.get('FLASK_ENV', 'production')
        }), 200
    
    @app.route('/', methods=['GET'])
    def index():
        """
        Homepage route.
        
        Returns:
            Rendered homepage template
        """
        return render_template('index.html')
    
    @app.route('/pricing', methods=['GET'])
    def pricing():
        """
        Pricing page showing subscription tiers.
        
        Returns:
            Rendered pricing template
        """
        return render_template('auth/pricing.html')
    
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """
        Contact page and form handler.
        
        Returns:
            Rendered contact template or redirect after submission
        """
        from app.services.auth_service import send_contact_email
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            issue_type = request.form.get('issue_type', '').strip()
            message = request.form.get('message', '').strip()
            
            # Validation
            if not name or not email or not issue_type or not message:
                flash('All fields are required', 'error')
                return render_template('contact.html')
            
            # Send email
            if send_contact_email(name, email, issue_type, message):
                flash('Thank you for contacting us! We will get back to you soon.', 'success')
            else:
                flash('There was an error sending your message. Please try again later.', 'error')
            
            return redirect(url_for('contact'))
        
        return render_template('contact.html')
    
    @app.route('/privacy', methods=['GET'])
    def privacy():
        """
        Privacy Policy page.
        
        Returns:
            Rendered privacy policy template
        """
        return render_template('privacy.html')
    
    @app.route('/terms', methods=['GET'])
    def terms():
        """
        Terms of Service page.
        
        Returns:
            Rendered terms of service template
        """
        return render_template('terms.html')
    
    @app.route('/data-usage', methods=['GET'])
    def data_usage():
        """
        Data Usage Policy page.
        
        Returns:
            Rendered data usage policy template
        """
        return render_template('data_usage.html')
    
    @app.route('/about', methods=['GET'])
    def about():
        """
        About Us page.
        
        Returns:
            Rendered about page template
        """
        return render_template('about.html')
    
    
    # ============================================
    # CORS Configuration (for API routes)
    # ============================================
    @app.after_request
    def after_request(response):
        """Add CORS headers to all responses."""
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # ============================================
    # Register blueprints
    # ============================================
    from app.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from app.blueprints.api import api_bp
    app.register_blueprint(api_bp)
    
    from app.blueprints.frontend import frontend_bp
    app.register_blueprint(frontend_bp)
    
    logger.info("WorldInsights application initialized successfully")
    
    return app


# ============================================
# Application entry point for development
# ============================================
if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('DEBUG', False)
    )
