"""
Database initialization module for WorldInsights.

Handles database setup, initialization, and default data creation.
"""
from app.infrastructure.db.models import db, User
from app.core.security import hash_password
from app.core.logging import get_logger

logger = get_logger('database')


def init_db(app):
    """
    Initialize database with Flask app.
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Create default admin user if not exists
        create_default_admin()


def create_default_admin():
    """
    Create default admin user if it doesn't exist.
    
    Default credentials:
    - Username: admin
    - Email: admin@worldinsights.bonzainsights.com
    - Password: Tahaxaina@1
    - Role: admin
    - Verified: True
    """
    try:
        # Check if admin user already exists
        admin = User.query.filter_by(email='admin@worldinsights.bonzainsights.com').first()
        
        if not admin:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@worldinsights.bonzainsights.com',
                password_hash=hash_password('Tahaxaina@1'),
                is_verified=True,
                role='admin',
                subscription_tier='admin',
                subscription_status='active'
            )
            
            db.session.add(admin)
            db.session.commit()
            
            logger.info("Default admin user created successfully")
            logger.info("Admin credentials - Email: admin@worldinsights.bonzainsights.com, Password: Tahaxaina@1")
        else:
            logger.info("Admin user already exists")
            
    except Exception as e:
        logger.error(f"Error creating default admin user: {e}")
        db.session.rollback()


def get_db_session():
    """Get database session."""
    return db.session
