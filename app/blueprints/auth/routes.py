"""
Authentication routes for WorldInsights.

Handles login, registration, email verification, profile, and admin functions.
"""
from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.services.auth_service import (
    register_user, send_verification_email, verify_user_email,
    authenticate_user, change_user_role, delete_user_account, get_all_users,
    toggle_user_verification, admin_delete_user, recover_user, update_profile,
    send_password_reset_email, reset_password, change_password
)
from app.infrastructure.db import User


def get_limiter():
    """Get limiter instance from app extensions."""
    return current_app.extensions.get('limiter')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration page and handler.
    Rate limited to 3 attempts per minute to prevent abuse.
    """
    # Apply rate limiting if available
    limiter = get_limiter()
    if limiter:
        limiter.limit("3 per minute")(lambda: None)()
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        terms_accepted = request.form.get('terms_accepted') == 'on'
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        # Check terms acceptance
        if not terms_accepted:
            flash('You must accept the Terms of Service and Privacy Policy to create an account', 'error')
            return render_template('auth/register.html')
        
        # Password strength is now validated in register_user service
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        # Register user
        user, error = register_user(username, email, password, terms_accepted=terms_accepted)
        
        if error:
            flash(error, 'error')
            return render_template('auth/register.html')
        
        # Send verification email
        base_url = request.url_root.rstrip('/')
        if send_verification_email(user, base_url):
            flash('Registration successful! Please check your email to verify your account.', 'success')
        else:
            flash('Registration successful! However, we couldn\'t send the verification email. Please contact support.', 'warning')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/verify/<token>')
def verify_email(token):
    """
    Email verification handler.
    """
    success, error = verify_user_email(token)
    
    if success:
        flash('Email verified successfully! You can now log in.', 'success')
    else:
        flash(error or 'Verification failed', 'error')
    
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page and handler.
    Rate limited to 5 attempts per minute to prevent brute force attacks.
    """
    # Apply rate limiting if available
    limiter = get_limiter()
    if limiter:
        limiter.limit("5 per minute")(lambda: None)()
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
        # Authenticate user (includes account lockout logic)
        user, error = authenticate_user(email, password)
        
        if error:
            flash(error, 'error')
            return render_template('auth/login.html')
        
        # Log in user
        login_user(user, remember=remember)
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to next page or profile
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('auth.profile'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    User logout handler.
    """
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """
    User profile page.
    """
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """
    Admin dashboard page.
    Shows user management interface for admins only.
    """
    if not current_user.is_admin():
        flash('Unauthorized access', 'error')
        return redirect(url_for('auth.profile'))
    
    from app.services.subscription_service import get_subscription_stats
    from datetime import datetime
    
    all_users = get_all_users()
    subscription_stats = get_subscription_stats()
    
    return render_template('auth/admin_dashboard.html', 
                         all_users=all_users,
                         subscription_stats=subscription_stats,
                         now=datetime.now())


@auth_bp.route('/change-role', methods=['POST'])
@login_required
def change_role():
    """
    Change user role (admin only).
    """
    if not current_user.is_admin():
        flash('Unauthorized access', 'error')
        return redirect(url_for('auth.profile'))
    
    user_id = request.form.get('user_id', type=int)
    new_role = request.form.get('role', '').strip()
    
    if not user_id or not new_role:
        flash('Invalid request', 'error')
        return redirect(url_for('auth.profile'))
    
    success, error = change_user_role(current_user, user_id, new_role)
    
    if success:
        flash('User role updated successfully', 'success')
    else:
        flash(error or 'Failed to update user role', 'error')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """
    Delete user account.
    """
    password = request.form.get('password', '')
    
    if not password:
        flash('Password is required to delete account', 'error')
        return redirect(url_for('auth.profile'))
    
    success, error = delete_user_account(current_user, password)
    
    if success:
        logout_user()
        flash('Your account has been deleted successfully', 'success')
        return redirect(url_for('index'))
    else:
        flash(error or 'Failed to delete account', 'error')
        return redirect(url_for('auth.profile'))


@auth_bp.route('/toggle-verification', methods=['POST'])
@login_required
def toggle_verification():
    """
    Toggle user verification status (admin only).
    """
    if not current_user.is_admin():
        flash('Unauthorized access', 'error')
        return redirect(url_for('auth.profile'))
    
    user_id = request.form.get('user_id', type=int)
    
    if not user_id:
        flash('Invalid request', 'error')
        return redirect(url_for('auth.profile'))
    
    success, error = toggle_user_verification(current_user, user_id)
    
    if success:
        flash('User verification status updated successfully', 'success')
    else:
        flash(error or 'Failed to update verification status', 'error')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/admin-delete-user', methods=['POST'])
@login_required
def admin_delete_user_route():
    """
    Delete a user account (admin only).
    """
    if not current_user.is_admin():
        flash('Unauthorized access', 'error')
        return redirect(url_for('auth.profile'))
    
    user_id = request.form.get('user_id', type=int)
    
    if not user_id:
        flash('Invalid request', 'error')
        return redirect(url_for('auth.profile'))
    
    success, error = admin_delete_user(current_user, user_id)
    
    if success:
        flash('User account marked for deletion. Can be recovered within 30 days.', 'success')
    else:
        flash(error or 'Failed to delete user account', 'error')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/recover-user', methods=['POST'])
@login_required
def recover_user_route():
    """
    Recover a deleted user account (admin only).
    """
    if not current_user.is_admin():
        flash('Unauthorized access', 'error')
        return redirect(url_for('auth.profile'))
    
    user_id = request.form.get('user_id', type=int)
    
    if not user_id:
        flash('Invalid request', 'error')
        return redirect(url_for('auth.profile'))
    
    success, error = recover_user(current_user, user_id)
    
    if success:
        flash('User account recovered successfully', 'success')
    else:
        flash(error or 'Failed to recover user account', 'error')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile_route():
    """
    Update user profile information.
    """
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    
    success, error = update_profile(current_user, first_name, last_name)
    
    if success:
        flash('Profile updated successfully', 'success')
    else:
        flash(error or 'Failed to update profile', 'error')
    
    return redirect(url_for('auth.profile'))



@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Forgot password page and handler.
    Rate limited to 3 attempts per hour to prevent abuse.
    """
    # Apply rate limiting if available
    limiter = get_limiter()
    if limiter:
        limiter.limit("3 per hour")(lambda: None)()
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Email address is required', 'error')
            return render_template('auth/forgot_password.html')
        
        # Always show success message for security (don't reveal if email exists)
        user = User.query.filter_by(email=email).first()
        
        if user and not user.is_deleted():
            base_url = request.url_root.rstrip('/')
            if send_password_reset_email(user, base_url):
                flash('If an account exists with that email, you will receive password reset instructions.', 'success')
            else:
                flash('If an account exists with that email, you will receive password reset instructions.', 'success')
        else:
            # Show same message even if user doesn't exist (security)
            flash('If an account exists with that email, you will receive password reset instructions.', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_route(token):
    """
    Reset password page and handler.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Reset password
        success, error = reset_password(token, new_password)
        
        if success:
            flash('Your password has been reset successfully. You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(error or 'Failed to reset password', 'error')
            return render_template('auth/reset_password.html', token=token)
    
    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password_route():
    """
    Change password handler for logged-in users.
    """
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validation
    if not current_password or not new_password or not confirm_password:
        flash('All password fields are required', 'error')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 8:
        flash('New password must be at least 8 characters long', 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('auth.profile'))
    
    # Change password
    success, error = change_password(current_user, current_password, new_password)
    
    if success:
        flash('Password changed successfully', 'success')
    else:
        flash(error or 'Failed to change password', 'error')
    
    return redirect(url_for('auth.profile'))


# ============================================
# Pricing and Subscription Routes
# ============================================

from app.services.subscription_service import (
    get_pricing_tiers, subscribe_user, cancel_subscription,
    upgrade_subscription, downgrade_subscription, check_subscription_status,
    get_subscription_history
)
from app.core.config import Config
from datetime import datetime


@auth_bp.route('/subscribe/<tier>')
@login_required
def subscribe(tier):
    """
    Subscription checkout page.
    """
    # Validate tier
    tiers = get_pricing_tiers()
    if tier not in tiers:
        flash('Invalid subscription tier', 'error')
        return redirect(url_for('pricing'))
    
    # Don't allow subscribing to current tier
    if current_user.subscription_tier == tier:
        flash('You are already subscribed to this tier', 'warning')
        return redirect(url_for('auth.dashboard'))
    
    # Get tier information
    tier_info = tiers[tier]
    
    # Get developer mode setting
    config = Config()
    developer_mode = config.DEVELOPER_MODE
    
    return render_template('auth/checkout.html', 
                         tier=tier, 
                         tier_info=tier_info,
                         developer_mode=developer_mode)


@auth_bp.route('/subscribe/<tier>', methods=['POST'])
@login_required
def process_subscription(tier):
    """
    Process subscription (mock payment in dev mode).
    """
    # Validate tier
    tiers = get_pricing_tiers()
    if tier not in tiers:
        flash('Invalid subscription tier', 'error')
        return redirect(url_for('pricing'))
    
    # Subscribe user
    success, error = subscribe_user(current_user, tier, payment_method='mock_card')
    
    if success:
        # Redirect to success page
        return redirect(url_for('auth.checkout_success', tier=tier))
    else:
        flash(error or 'Failed to process subscription', 'error')
        return redirect(url_for('auth.subscribe', tier=tier))


@auth_bp.route('/checkout/success')
@login_required
def checkout_success():
    """
    Checkout success page.
    """
    tier = request.args.get('tier', current_user.subscription_tier)
    tiers = get_pricing_tiers()
    tier_info = tiers.get(tier, {})
    
    # Get developer mode setting
    config = Config()
    developer_mode = config.DEVELOPER_MODE
    
    return render_template('auth/checkout_success.html',
                         tier_name=tier_info.get('name', tier.capitalize()),
                         amount=tier_info.get('price', 0.00),
                         started_at=current_user.subscription_started_at.strftime('%B %d, %Y') if current_user.subscription_started_at else 'N/A',
                         developer_mode=developer_mode)


@auth_bp.route('/subscription/cancel', methods=['POST'])
@login_required
def cancel_subscription_route():
    """
    Cancel user subscription.
    """
    success, error = cancel_subscription(current_user)
    
    if success:
        flash('Your subscription has been cancelled. You will retain access until the end of your billing period.', 'success')
    else:
        flash(error or 'Failed to cancel subscription', 'error')
    
    return redirect(url_for('auth.dashboard'))


@auth_bp.route('/subscription/upgrade/<tier>', methods=['POST'])
@login_required
def upgrade_subscription_route(tier):
    """
    Upgrade subscription to higher tier.
    """
    success, error = upgrade_subscription(current_user, tier)
    
    if success:
        flash(f'Successfully upgraded to {tier.capitalize()} tier!', 'success')
    else:
        flash(error or 'Failed to upgrade subscription', 'error')
    
    return redirect(url_for('auth.dashboard'))


@auth_bp.route('/subscription/downgrade/<tier>', methods=['POST'])
@login_required
def downgrade_subscription_route(tier):
    """
    Downgrade subscription to lower tier.
    """
    success, error = downgrade_subscription(current_user, tier)
    
    if success:
        flash(f'Successfully downgraded to {tier.capitalize()} tier', 'success')
    else:
        flash(error or 'Failed to downgrade subscription', 'error')
    
    return redirect(url_for('auth.dashboard'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """
    User dashboard with subscription information.
    """
    # Get subscription status
    subscription_status = check_subscription_status(current_user)
    subscription_history = get_subscription_history(current_user)
    
    return render_template('auth/dashboard.html',
                         user=current_user,
                         subscription_status=subscription_status,
                         subscription_history=subscription_history)
