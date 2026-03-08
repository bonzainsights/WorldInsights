"""
Dashboard database models for WorldInsights.

This module defines the Dashboard model for storing user-created dashboards
with all their panels, configurations, and settings.
"""
from app.infrastructure.db.models import db
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid


class Dashboard(db.Model):
    """
    Dashboard model for storing user-created dashboards.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Owner's user ID (nullable for anonymous dashboards)
        title: Dashboard title
        description: Optional description
        layout: JSON storing canvas settings (zoom, grid, etc.)
        panels: JSON storing all panel configurations
        is_public: Whether dashboard is publicly accessible
        created_at: Creation timestamp
        updated_at: Last update timestamp
        version: Version number for optimistic locking
    """
    
    __tablename__ = 'dashboards'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    layout = db.Column(db.JSON, nullable=False, default=dict)
    panels = db.Column(db.JSON, nullable=False, default=list)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.Integer, default=1)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('dashboards', lazy='dynamic', cascade='all, delete-orphan'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'layout': self.layout,
            'panels': self.panels,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version,
            'owner_username': self.user.username if self.user else 'Anonymous'
        }
    
    def from_dict(self, data: Dict[str, Any]) -> 'Dashboard':
        """Load dashboard from dictionary."""
        for key in ['title', 'description', 'layout', 'panels', 'is_public']:
            if key in data:
                setattr(self, key, data[key])
        return self
    
    def __repr__(self) -> str:
        return f'<Dashboard {self.title}>'


class DashboardTag(db.Model):
    """
    Tags for organizing dashboards.
    
    Attributes:
        id: Unique identifier
        name: Tag name
        dashboards: Many-to-many relationship with dashboards
    """
    
    __tablename__ = 'dashboard_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    dashboards = db.relationship('Dashboard', secondary='dashboard_dashboard_tags', backref='tags')
    
    def __repr__(self) -> str:
        return f'<DashboardTag {self.name}>'


# Association table for many-to-many relationship
dashboard_dashboard_tags = db.Table(
    'dashboard_dashboard_tags',
    db.Column('dashboard_id', db.String(36), db.ForeignKey('dashboards.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('dashboard_tags.id'), primary_key=True)
)


class DashboardShare(db.Model):
    """
    Dashboard sharing permissions.
    
    Attributes:
        id: Unique identifier
        dashboard_id: Dashboard being shared
        user_id: User with access (nullable for public links)
        share_token: Unique token for link sharing
        can_edit: Whether user can edit or just view
        expires_at: Optional expiration date
        created_at: Creation timestamp
    """
    
    __tablename__ = 'dashboard_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    dashboard_id = db.Column(db.String(36), db.ForeignKey('dashboards.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    share_token = db.Column(db.String(64), unique=True, nullable=True)
    can_edit = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    dashboard = db.relationship('Dashboard', backref=db.backref('shares', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('shared_dashboards', lazy='dynamic'))
    
    def __repr__(self) -> str:
        return f'<DashboardShare {self.dashboard_id} -> User {self.user_id}>'
