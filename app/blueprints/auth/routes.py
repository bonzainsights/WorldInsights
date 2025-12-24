"""
Authentication routes for WorldInsights.

Handles login, registration, email verification, profile, and admin functions.
"""
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.services.auth_service import (
    register_user, send_verification_email, verify_user_email,
    authenticate_user, change_user_role, delete_user_account, get_all_users,
    toggle_user_verification, admin_delete_user, recover_user, update_profile,
    send_password_reset_email, reset_password, change_password
)
from app.infrastructure.db import User


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration page and handler.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        # Register user
        user, error = register_user(username, email, password)
        
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
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
        # Authenticate user
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
    
    all_users = get_all_users()
    return render_template('auth/admin_dashboard.html', all_users=all_users)


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
    """
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

