"""
Authentication routes for WorldInsights.

Handles login, registration, email verification, profile, and admin functions.
"""
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.services.auth_service import (
    register_user, send_verification_email, verify_user_email,
    authenticate_user, change_user_role, delete_user_account, get_all_users
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
    Shows admin dashboard if user is admin.
    """
    # Get all users if admin
    all_users = None
    if current_user.is_admin():
        all_users = get_all_users()
    
    return render_template('auth/profile.html', user=current_user, all_users=all_users)


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
