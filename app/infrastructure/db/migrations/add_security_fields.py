"""
Database migration: Add security tracking fields to User model.

This migration adds fields for account lockout and failed login tracking.
"""
from app.infrastructure.db import db, User
from app.core.logging import get_logger

logger = get_logger('migration')


def upgrade():
    """
    Add security tracking fields to User table.
    
    Fields added:
    - failed_login_attempts: Counter for failed login attempts
    - locked_until: Timestamp when account lockout expires
    - last_login_attempt: Timestamp of last login attempt
    - last_successful_login: Timestamp of last successful login
    """
    try:
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        # Add columns if they don't exist
        if 'failed_login_attempts' not in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    'ALTER TABLE user ADD COLUMN failed_login_attempts INTEGER DEFAULT 0 NOT NULL'
                ))
                conn.commit()
            logger.info("Added failed_login_attempts column to user table")
        
        if 'locked_until' not in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    'ALTER TABLE user ADD COLUMN locked_until DATETIME'
                ))
                conn.commit()
            logger.info("Added locked_until column to user table")
        
        if 'last_login_attempt' not in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    'ALTER TABLE user ADD COLUMN last_login_attempt DATETIME'
                ))
                conn.commit()
            logger.info("Added last_login_attempt column to user table")
        
        if 'last_successful_login' not in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    'ALTER TABLE user ADD COLUMN last_successful_login DATETIME'
                ))
                conn.commit()
            logger.info("Added last_successful_login column to user table")
        
        logger.info("Security tracking fields migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False


def downgrade():
    """
    Remove security tracking fields from User table.
    
    WARNING: This will delete data in these columns.
    """
    try:
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        # Remove columns if they exist
        if 'failed_login_attempts' in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE user DROP COLUMN failed_login_attempts'))
                conn.commit()
            logger.info("Removed failed_login_attempts column from user table")
        
        if 'locked_until' in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE user DROP COLUMN locked_until'))
                conn.commit()
            logger.info("Removed locked_until column from user table")
        
        if 'last_login_attempt' in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE user DROP COLUMN last_login_attempt'))
                conn.commit()
            logger.info("Removed last_login_attempt column from user table")
        
        if 'last_successful_login' in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE user DROP COLUMN last_successful_login'))
                conn.commit()
            logger.info("Removed last_successful_login column from user table")
        
        logger.info("Security tracking fields downgrade completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during downgrade: {e}")
        return False


if __name__ == '__main__':
    # Run migration
    print("Running security fields migration...")
    if upgrade():
        print("✓ Migration completed successfully")
    else:
        print("✗ Migration failed")
