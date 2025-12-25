"""
Run database migrations for WorldInsights.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.create_app import create_app
from app.infrastructure.db.migrations.add_security_fields import upgrade

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        print("Running security fields migration...")
        if upgrade():
            print("✓ Migration completed successfully")
        else:
            print("✗ Migration failed")
