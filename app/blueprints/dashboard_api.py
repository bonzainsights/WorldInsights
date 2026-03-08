"""
Dashboard API routes for WorldInsights.

Provides RESTful endpoints for dashboard CRUD operations:
- Create, Read, Update, Delete dashboards
- List user dashboards
- Share dashboards
- Public dashboard access
"""
from flask import Blueprint, request, jsonify, session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import secrets

from app.core.logging import get_logger
from app.infrastructure.db.models import db
from app.infrastructure.db.dashboard_models import Dashboard, DashboardShare

# Create blueprint
dashboard_api_bp = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboards')

logger = get_logger(__name__)


# ==========================================================================
# CRUD Operations
# ==========================================================================

@dashboard_api_bp.route('', methods=['POST'])
def create_dashboard():
    """
    Create a new dashboard.
    
    Request Body:
        title (str): Dashboard title
        description (str, optional): Dashboard description
        layout (dict): Canvas layout settings
        panels (list): Panel configurations
        is_public (bool): Whether dashboard is public
    
    Returns:
        JSON with created dashboard
    """
    data = request.get_json()
    
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    # Get user ID from session (if logged in)
    user_id = session.get('user_id')
    
    # Create dashboard
    dashboard = Dashboard(
        user_id=user_id,
        title=data['title'],
        description=data.get('description', ''),
        layout=data.get('layout', {}),
        panels=data.get('panels', []),
        is_public=data.get('is_public', False)
    )
    
    db.session.add(dashboard)
    db.session.commit()
    
    logger.info(f"Dashboard created: {dashboard.id} by user {user_id}")
    
    return jsonify(dashboard.to_dict()), 201


@dashboard_api_bp.route('/<dashboard_id>', methods=['GET'])
def get_dashboard(dashboard_id: str):
    """
    Get a specific dashboard by ID.
    
    Args:
        dashboard_id: Dashboard UUID
    
    Returns:
        JSON with dashboard data
    """
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    
    # Check permissions
    if not dashboard.is_public:
        user_id = session.get('user_id')
        if not user_id or dashboard.user_id != user_id:
            # Check if shared with user
            share = DashboardShare.query.filter_by(
                dashboard_id=dashboard_id,
                user_id=user_id
            ).first()
            
            if not share:
                return jsonify({'error': 'Dashboard not found or not accessible'}), 404
    
    return jsonify(dashboard.to_dict()), 200


@dashboard_api_bp.route('/<dashboard_id>', methods=['PUT'])
def update_dashboard(dashboard_id: str):
    """
    Update an existing dashboard.
    
    Args:
        dashboard_id: Dashboard UUID
    
    Request Body:
        title (str, optional): New title
        description (str, optional): New description
        layout (dict, optional): New layout
        panels (list, optional): New panels
        is_public (bool, optional): New visibility
    
    Returns:
        JSON with updated dashboard
    """
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    
    # Check ownership
    user_id = session.get('user_id')
    if not user_id or dashboard.user_id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    # Update fields
    for field in ['title', 'description', 'layout', 'panels', 'is_public']:
        if field in data:
            setattr(dashboard, field, data[field])
    
    dashboard.version += 1
    db.session.commit()
    
    logger.info(f"Dashboard updated: {dashboard_id}")
    
    return jsonify(dashboard.to_dict()), 200


@dashboard_api_bp.route('/<dashboard_id>', methods=['DELETE'])
def delete_dashboard(dashboard_id: str):
    """
    Delete a dashboard.
    
    Args:
        dashboard_id: Dashboard UUID
    
    Returns:
        JSON with success message
    """
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    
    # Check ownership
    user_id = session.get('user_id')
    if not user_id or dashboard.user_id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    db.session.delete(dashboard)
    db.session.commit()
    
    logger.info(f"Dashboard deleted: {dashboard_id}")
    
    return jsonify({'message': 'Dashboard deleted successfully'}), 200


# ==========================================================================
# List Operations
# ==========================================================================

@dashboard_api_bp.route('', methods=['GET'])
def list_dashboards():
    """
    List dashboards for current user.
    
    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20)
        search (str): Search in title/description
        sort (str): Sort field (created_at, updated_at, title)
        order (str): Sort order (asc, desc)
    
    Returns:
        JSON with paginated dashboard list
    """
    user_id = session.get('user_id')
    
    # Query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'updated_at')
    order = request.args.get('order', 'desc')
    
    # Build query
    query = Dashboard.query
    
    if user_id:
        # User's dashboards
        query = query.filter_by(user_id=user_id)
    else:
        # No user - return empty list
        return jsonify({
            'dashboards': [],
            'total': 0,
            'page': page,
            'per_page': per_page,
            'pages': 0
        }), 200
    
    # Search filter
    if search:
        query = query.filter(
            db.or_(
                Dashboard.title.ilike(f'%{search}%'),
                Dashboard.description.ilike(f'%{search}%')
            )
        )
    
    # Sorting
    if hasattr(Dashboard, sort):
        sort_column = getattr(Dashboard, sort)
        if order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(Dashboard.updated_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    dashboards = [d.to_dict() for d in pagination.items]
    
    return jsonify({
        'dashboards': dashboards,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@dashboard_api_bp.route('/public', methods=['GET'])
def list_public_dashboards():
    """
    List all public dashboards.
    
    Query Parameters:
        page (int): Page number
        per_page (int): Items per page
    
    Returns:
        JSON with paginated public dashboard list
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Dashboard.query.filter_by(is_public=True)\
        .order_by(Dashboard.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    dashboards = [d.to_dict() for d in pagination.items]
    
    return jsonify({
        'dashboards': dashboards,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


# ==========================================================================
# Sharing Operations
# ==========================================================================

@dashboard_api_bp.route('/<dashboard_id>/share', methods=['POST'])
def share_dashboard(dashboard_id: str):
    """
    Create a share link for a dashboard.
    
    Request Body:
        can_edit (bool): Whether share allows editing
        expires_days (int, optional): Days until link expires
    
    Returns:
        JSON with share token
    """
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    
    # Check ownership
    user_id = session.get('user_id')
    if not user_id or dashboard.user_id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    # Generate share token
    share_token = secrets.token_urlsafe(32)
    
    # Calculate expiration
    expires_at = None
    if data.get('expires_days'):
        expires_at = datetime.utcnow() + timedelta(days=data['expires_days'])
    
    # Create share record
    share = DashboardShare(
        dashboard_id=dashboard_id,
        share_token=share_token,
        can_edit=data.get('can_edit', False),
        expires_at=expires_at
    )
    
    db.session.add(share)
    db.session.commit()
    
    logger.info(f"Dashboard {dashboard_id} shared with token {share_token[:8]}...")
    
    return jsonify({
        'share_token': share_token,
        'share_url': f'/dashboard/shared/{share_token}',
        'can_edit': share.can_edit,
        'expires_at': share.expires_at.isoformat() if share.expires_at else None
    }), 201


@dashboard_api_bp.route('/shared/<share_token>', methods=['GET'])
def get_shared_dashboard(share_token: str):
    """
    Access dashboard via share token.
    
    Args:
        share_token: Share access token
    
    Returns:
        JSON with dashboard data
    """
    share = DashboardShare.query.filter_by(share_token=share_token).first_or_404()
    
    # Check expiration
    if share.expires_at and datetime.utcnow() > share.expires_at:
        return jsonify({'error': 'Share link has expired'}), 410
    
    return jsonify(share.dashboard.to_dict()), 200


@dashboard_api_bp.route('/<dashboard_id>/share', methods=['DELETE'])
def revoke_share(dashboard_id: str):
    """
    Revoke all share links for a dashboard.
    
    Returns:
        JSON with success message
    """
    dashboard = Dashboard.query.get_or_404(dashboard_id)
    
    # Check ownership
    user_id = session.get('user_id')
    if not user_id or dashboard.user_id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    # Delete all shares
    DashboardShare.query.filter_by(dashboard_id=dashboard_id).delete()
    db.session.commit()
    
    logger.info(f"All shares revoked for dashboard {dashboard_id}")
    
    return jsonify({'message': 'All share links revoked'}), 200
