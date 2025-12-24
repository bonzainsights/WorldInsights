"""
Database models for WorldInsights.

Defines SQLAlchemy models for DuckDB database.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # user, researcher, admin
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_verified': self.is_verified,
            'role': self.role,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == 'admin'
    
    def is_researcher(self):
        """Check if user is a researcher or admin."""
        return self.role in ('researcher', 'admin')
    
    def is_deleted(self):
        """Check if user account is marked for deletion."""
        return self.deleted_at is not None
