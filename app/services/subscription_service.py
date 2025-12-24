"""
Subscription service for WorldInsights.

Handles subscription management, pricing tiers, and mock payment processing.
"""
from app.infrastructure.db import db, User, Subscription
from app.core.logging import get_logger
from typing import Optional, Tuple, Dict, List
from datetime import datetime, timedelta
import secrets

logger = get_logger('subscription_service')

# Pricing tier definitions
PRICING_TIERS = {
    'free': {
        'name': 'Free',
        'price': 0.00,
        'currency': 'USD',
        'interval': 'month',
        'features': [
            'Access to basic datasets',
            'Limited visualizations (5 per month)',
            'Community support',
            'Export data (CSV only)',
            'Basic analytics'
        ],
        'limits': {
            'datasets': 10,
            'visualizations_per_month': 5,
            'api_calls_per_day': 100
        }
    },
    'researcher': {
        'name': 'Researcher',
        'price': 29.00,
        'currency': 'USD',
        'interval': 'month',
        'features': [
            'Access to all datasets',
            'Unlimited visualizations',
            'Advanced analytics & correlations',
            'Machine learning features',
            'Priority support',
            'Export data (CSV, JSON, Excel)',
            '3D globe visualization',
            'Custom data queries',
            'API access'
        ],
        'limits': {
            'datasets': 'unlimited',
            'visualizations_per_month': 'unlimited',
            'api_calls_per_day': 10000
        }
    },
    'admin': {
        'name': 'Admin',
        'price': None,  # Contact for pricing
        'currency': 'USD',
        'interval': 'month',
        'features': [
            'All Researcher features',
            'User management',
            'System administration',
            'Analytics dashboard',
            'Subscription management',
            'Platform configuration',
            'Audit logs',
            'Dedicated support'
        ],
        'limits': {
            'datasets': 'unlimited',
            'visualizations_per_month': 'unlimited',
            'api_calls_per_day': 'unlimited'
        }
    }
}


def get_pricing_tiers() -> Dict:
    """
    Get all pricing tier information.
    
    Returns:
        Dictionary of pricing tiers with details
    """
    return PRICING_TIERS


def get_tier_price(tier: str) -> float:
    """
    Get price for a specific tier.
    
    Args:
        tier: Tier name (free, researcher, admin)
    
    Returns:
        Price in USD
    """
    if tier not in PRICING_TIERS:
        return 0.00
    return PRICING_TIERS[tier]['price'] or 0.00


def subscribe_user(user: User, tier: str, payment_method: str = 'mock_card') -> Tuple[bool, Optional[str]]:
    """
    Subscribe user to a tier (mock payment in dev mode).
    
    Args:
        user: User object
        tier: Subscription tier (free, researcher, admin)
        payment_method: Payment method (mock in dev mode)
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Validate tier
        if tier not in PRICING_TIERS:
            return False, "Invalid subscription tier"
        
        # Don't allow subscribing to admin tier via this method
        if tier == 'admin':
            return False, "Admin tier requires manual approval. Please contact support."
        
        # Get tier price
        amount = get_tier_price(tier)
        
        # Mock Stripe customer ID
        if not user.stripe_customer_id:
            user.stripe_customer_id = f"cus_mock_{secrets.token_hex(12)}"
        
        # Update user subscription (keep role unchanged)
        user.subscription_tier = tier
        user.subscription_status = 'active'
        user.subscription_started_at = datetime.utcnow()
        user.subscription_expires_at = None  # No expiry for active subscriptions
        
        # Create subscription record
        subscription = Subscription(
            user_id=user.id,
            tier=tier,
            status='active',
            amount=amount,
            currency='USD',
            payment_method=payment_method,
            started_at=datetime.utcnow(),
            expires_at=None
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        logger.info(f"User {user.username} subscribed to {tier} tier (mock payment: ${amount})")
        return True, None
        
    except Exception as e:
        logger.error(f"Error subscribing user: {e}")
        db.session.rollback()
        return False, "An error occurred while processing your subscription"


def cancel_subscription(user: User) -> Tuple[bool, Optional[str]]:
    """
    Cancel user subscription.
    
    Args:
        user: User object
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Don't allow cancelling free tier
        if user.subscription_tier == 'free':
            return False, "Cannot cancel free tier subscription"
        
        # Don't allow cancelling admin tier
        if user.subscription_tier == 'admin':
            return False, "Admin subscriptions cannot be cancelled. Please contact support."
        
        # Update user subscription status (keep role unchanged)
        user.subscription_status = 'cancelled'
        user.subscription_expires_at = datetime.utcnow() + timedelta(days=30)  # Grace period
        user.subscription_tier = 'free'
        
        # Mark current subscription as cancelled
        current_subscription = Subscription.query.filter_by(
            user_id=user.id,
            status='active'
        ).order_by(Subscription.created_at.desc()).first()
        
        if current_subscription:
            current_subscription.status = 'cancelled'
            current_subscription.cancelled_at = datetime.utcnow()
            current_subscription.expires_at = user.subscription_expires_at
        
        db.session.commit()
        
        logger.info(f"User {user.username} cancelled subscription")
        return True, None
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        db.session.rollback()
        return False, "An error occurred while cancelling your subscription"


def upgrade_subscription(user: User, new_tier: str) -> Tuple[bool, Optional[str]]:
    """
    Upgrade subscription to higher tier.
    
    Args:
        user: User object
        new_tier: New subscription tier
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Validate tier
        if new_tier not in PRICING_TIERS:
            return False, "Invalid subscription tier"
        
        # Check if it's actually an upgrade
        tier_hierarchy = {'free': 0, 'researcher': 1, 'admin': 2}
        current_level = tier_hierarchy.get(user.subscription_tier, 0)
        new_level = tier_hierarchy.get(new_tier, 0)
        
        if new_level <= current_level:
            return False, "This is not an upgrade. Use downgrade or subscribe instead."
        
        # Use subscribe_user to handle the upgrade
        return subscribe_user(user, new_tier)
        
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        return False, "An error occurred while upgrading your subscription"


def downgrade_subscription(user: User, new_tier: str) -> Tuple[bool, Optional[str]]:
    """
    Downgrade subscription to lower tier.
    
    Args:
        user: User object
        new_tier: New subscription tier
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Validate tier
        if new_tier not in PRICING_TIERS:
            return False, "Invalid subscription tier"
        
        # Check if it's actually a downgrade
        tier_hierarchy = {'free': 0, 'researcher': 1, 'admin': 2}
        current_level = tier_hierarchy.get(user.subscription_tier, 0)
        new_level = tier_hierarchy.get(new_tier, 0)
        
        if new_level >= current_level:
            return False, "This is not a downgrade. Use upgrade or subscribe instead."
        
        # Cancel current subscription and subscribe to new tier
        if user.subscription_tier != 'free':
            # Mark current subscription as cancelled
            current_subscription = Subscription.query.filter_by(
                user_id=user.id,
                status='active'
            ).order_by(Subscription.created_at.desc()).first()
            
            if current_subscription:
                current_subscription.status = 'cancelled'
                current_subscription.cancelled_at = datetime.utcnow()
        
        # Subscribe to new tier
        return subscribe_user(user, new_tier)
        
    except Exception as e:
        logger.error(f"Error downgrading subscription: {e}")
        return False, "An error occurred while downgrading your subscription"


def check_subscription_status(user: User) -> Dict:
    """
    Check and return user's subscription status.
    
    Args:
        user: User object
    
    Returns:
        Dictionary with subscription status information
    """
    try:
        # Check if subscription has expired (keep role unchanged)
        if user.subscription_expires_at and user.subscription_expires_at < datetime.utcnow():
            user.subscription_status = 'expired'
            user.subscription_tier = 'free'
            db.session.commit()
        
        return {
            'tier': user.subscription_tier,
            'status': user.subscription_status,
            'started_at': user.subscription_started_at,
            'expires_at': user.subscription_expires_at,
            'is_active': user.has_active_subscription(),
            'can_access_premium': user.can_access_premium_features(),
            'tier_info': PRICING_TIERS.get(user.subscription_tier, {})
        }
        
    except Exception as e:
        logger.error(f"Error checking subscription status: {e}")
        return {
            'tier': 'free',
            'status': 'unknown',
            'is_active': False,
            'can_access_premium': False
        }


def get_subscription_history(user: User) -> List[Dict]:
    """
    Get user's subscription history.
    
    Args:
        user: User object
    
    Returns:
        List of subscription dictionaries
    """
    try:
        subscriptions = Subscription.query.filter_by(user_id=user.id).order_by(
            Subscription.created_at.desc()
        ).all()
        
        return [sub.to_dict() for sub in subscriptions]
        
    except Exception as e:
        logger.error(f"Error fetching subscription history: {e}")
        return []


def mock_stripe_checkout(user: User, tier: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Simulate Stripe checkout flow (developer mode).
    
    Args:
        user: User object
        tier: Subscription tier
    
    Returns:
        Tuple of (success, error_message, checkout_session_id)
    """
    try:
        # Validate tier
        if tier not in PRICING_TIERS:
            return False, "Invalid subscription tier", None
        
        # Generate mock checkout session ID
        checkout_session_id = f"cs_mock_{secrets.token_hex(16)}"
        
        logger.info(f"Mock Stripe checkout initiated for user {user.username}, tier: {tier}")
        
        return True, None, checkout_session_id
        
    except Exception as e:
        logger.error(f"Error in mock checkout: {e}")
        return False, "An error occurred during checkout", None


def get_subscription_stats() -> Dict:
    """
    Get subscription statistics (for admin dashboard).
    
    Returns:
        Dictionary with subscription statistics
    """
    try:
        total_users = User.query.count()
        free_users = User.query.filter_by(subscription_tier='free').count()
        researcher_users = User.query.filter_by(subscription_tier='researcher').count()
        admin_users = User.query.filter_by(subscription_tier='admin').count()
        
        active_subscriptions = User.query.filter_by(subscription_status='active').count()
        cancelled_subscriptions = User.query.filter_by(subscription_status='cancelled').count()
        
        # Calculate mock revenue (for display purposes)
        researcher_revenue = researcher_users * PRICING_TIERS['researcher']['price']
        
        # Get recent subscriptions
        recent_subscriptions = Subscription.query.order_by(
            Subscription.created_at.desc()
        ).limit(10).all()
        
        return {
            'total_users': total_users,
            'by_tier': {
                'free': free_users,
                'researcher': researcher_users,
                'admin': admin_users
            },
            'by_status': {
                'active': active_subscriptions,
                'cancelled': cancelled_subscriptions
            },
            'revenue': {
                'monthly': researcher_revenue,
                'currency': 'USD'
            },
            'recent_subscriptions': [sub.to_dict() for sub in recent_subscriptions]
        }
        
    except Exception as e:
        logger.error(f"Error fetching subscription stats: {e}")
        return {
            'total_users': 0,
            'by_tier': {'free': 0, 'researcher': 0, 'admin': 0},
            'by_status': {'active': 0, 'cancelled': 0},
            'revenue': {'monthly': 0, 'currency': 'USD'},
            'recent_subscriptions': []
        }
