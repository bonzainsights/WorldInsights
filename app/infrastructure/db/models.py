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
    
    # Subscription fields
    subscription_tier = db.Column(db.String(20), default='free', nullable=False)  # free, researcher, admin
    subscription_status = db.Column(db.String(20), default='active', nullable=False)  # active, cancelled, expired
    subscription_started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    subscription_expires_at = db.Column(db.DateTime, nullable=True)  # For trial/cancellation handling
    stripe_customer_id = db.Column(db.String(100), nullable=True)  # Mock ID in dev mode
    
    # Security tracking fields
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)  # Account lockout expiration
    last_login_attempt = db.Column(db.DateTime, nullable=True)  # Last login attempt timestamp
    last_successful_login = db.Column(db.DateTime, nullable=True)  # Last successful login
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to subscriptions
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')
    
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
            'subscription_tier': self.subscription_tier,
            'subscription_status': self.subscription_status,
            'subscription_started_at': self.subscription_started_at.isoformat() if self.subscription_started_at else None,
            'subscription_expires_at': self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
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
    
    def has_active_subscription(self):
        """Check if user has an active subscription."""
        return self.subscription_status == 'active'
    
    def is_free_tier(self):
        """Check if user is on free tier."""
        return self.subscription_tier == 'free'
    
    def can_access_premium_features(self):
        """Check if user can access premium features (researcher or admin)."""
        return self.subscription_tier in ('researcher', 'admin') and self.has_active_subscription()
    
    def is_account_locked(self):
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def reset_failed_attempts(self):
        """Reset failed login attempts counter."""
        self.failed_login_attempts = 0
        self.locked_until = None


class Subscription(db.Model):
    """Subscription model for tracking user subscription history."""
    
    __tablename__ = 'subscription'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    tier = db.Column(db.String(20), nullable=False)  # free, researcher, admin
    status = db.Column(db.String(20), nullable=False)  # active, cancelled, expired
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)  # Subscription amount
    currency = db.Column(db.String(3), nullable=False, default='USD')
    payment_method = db.Column(db.String(50), nullable=True)  # Mock in dev mode
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Subscription {self.tier} for User {self.user_id}>'
    
    def to_dict(self):
        """Convert subscription to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'tier': self.tier,
            'status': self.status,
            'amount': float(self.amount) if self.amount else 0.00,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def is_active(self):
        """Check if subscription is active."""
        return self.status == 'active' and (self.expires_at is None or self.expires_at > datetime.utcnow())
    
    def is_cancelled(self):
        """Check if subscription is cancelled."""
        return self.cancelled_at is not None
