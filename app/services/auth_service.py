"""
Authentication service for WorldInsights.

Handles user registration, login, email verification, and role management.
"""
from app.infrastructure.db import db, User
from app.core.security import hash_password, verify_password, generate_verification_token, validate_email
from app.core.logging import get_logger
from flask_mail import Message, Mail
from typing import Optional, Tuple
from flask import url_for

logger = get_logger('auth_service')
mail = Mail()


def register_user(username: str, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """
    Register a new user.
    
    Args:
        username: Username
        email: Email address
        password: Password
    
    Returns:
        Tuple of (User, error_message)
        If successful: (User object, None)
        If error: (None, error message)
    """
    try:
        # Validate email
        if not validate_email(email):
            return None, "Invalid email address"
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return None, "Email already registered"
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_verified=False,
            role='user'
        )
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {username}")
        return user, None
        
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        db.session.rollback()
        return None, "An error occurred during registration"


def send_verification_email(user: User, base_url: str) -> bool:
    """
    Send verification email to user.
    
    Args:
        user: User object
        base_url: Base URL for verification link
    
    Returns:
        True if successful, False otherwise
    """
    try:
        token = generate_verification_token(user.id)
        verification_url = f"{base_url}/auth/verify/{token}"
        
        msg = Message(
            subject="Verify Your WorldInsights Account",
            recipients=[user.email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #3B82F6;">Welcome to WorldInsights!</h2>
                    <p>Hello {user.username},</p>
                    <p>Thank you for registering with WorldInsights. Please verify your email address by clicking the button below:</p>
                    <p style="margin: 30px 0;">
                        <a href="{verification_url}" style="background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%); color: white; padding: 12px 30px; text-decoration: none; Border-radius: 8px; display: inline-block;">
                            Verify Email Address
                        </a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="color: #666; font-size: 14px;">{verification_url}</p>
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px;">WorldInsights - Global Data Intelligence Platform</p>
                </body>
            </html>
            """
        )
        
        mail.send(msg)
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return False


def verify_user_email(token: str) -> Tuple[bool, Optional[str]]:
    """
    Verify user email with token.
    
    Args:
        token: Verification token
    
    Returns:
        Tuple of (success, error_message)
    """
    from app.core.security import verify_token
    
    try:
        user_id = verify_token(token)
        
        if not user_id:
            return False, "Invalid or expired verification link"
        
        user = User.query.get(user_id)
        if not user:
            return False, "User not found"
        
        if user.is_verified:
            return False, "Email already verified"
        
        user.is_verified = True
        db.session.commit()
        
        logger.info(f"User verified: {user.username}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error verifying user: {e}")
        db.session.rollback()
        return False, "An error occurred during verification"


def authenticate_user(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """
    Authenticate user with email and password.
    
    Args:
        email: Email address
        password: Password
    
    Returns:
        Tuple of (User, error_message)
    """
    try:
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return None, "Invalid email or password"
        
        if not verify_password(password, user.password_hash):
            return None, "Invalid email or password"
        
        if not user.is_verified:
            return None, "Please verify your email address before logging in"
        
        if user.is_deleted():
            return None, "This account has been deleted. Contact support to recover your account."
        
        logger.info(f"User authenticated: {user.username}")
        return user, None
        
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return None, "An error occurred during login"


def change_user_role(admin: User, target_user_id: int, new_role: str) -> Tuple[bool, Optional[str]]:
    """
    Change user role (admin only).
    
    Args:
        admin: Admin user performing the action
        target_user_id: ID of user to change
        new_role: New role (user, researcher, admin)
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Check if requester is admin
        if not admin.is_admin():
            return False, "Only administrators can change user roles"
        
        # Validate new role
        if new_role not in ('user', 'researcher', 'admin'):
            return False, "Invalid role specified"
        
        # Get target user
        target_user = User.query.get(target_user_id)
        if not target_user:
            return False, "User not found"
        
        # Don't allow changing own role
        if target_user.id == admin.id:
            return False, "You cannot change your own role"
        
        # Update role
        old_role = target_user.role
        target_user.role = new_role
        db.session.commit()
        
        logger.info(f"Admin {admin.username} changed {target_user.username} role from {old_role} to {new_role}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error changing user role: {e}")
        db.session.rollback()
        return False, "An error occurred while changing user role"


def delete_user_account(user: User, password: str) -> Tuple[bool, Optional[str]]:
    """
    Mark user account for deletion after password confirmation.
    Account will be recoverable for 30 days.
    
    Args:
        user: User to delete
        password: Password confirmation
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Verify password
        if not verify_password(password, user.password_hash):
            return False, "Incorrect password"
        
        # Don't allow deleting admin account
        if user.is_admin() and user.email == 'admin@worldinsights.com':
            return False, "Cannot delete the default admin account"
        
        # Soft delete - mark for deletion
        username = user.username
        user.deleted_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"User account marked for deletion: {username}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        db.session.rollback()
        return False, "An error occurred while deleting your account"


def get_all_users() -> list:
    """
    Get all users (admin only).
    
    Returns:
        List of all users
    """
    try:
        return User.query.all()
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return []


def toggle_user_verification(admin: User, target_user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Toggle user verification status (admin only).
    
    Args:
        admin: Admin user performing the action
        target_user_id: ID of user to toggle verification
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        if not admin.is_admin():
            return False, "Only administrators can change verification status"
        
        target_user = User.query.get(target_user_id)
        if not target_user:
            return False, "User not found"
        
        # Toggle verification
        target_user.is_verified = not target_user.is_verified
        db.session.commit()
        
        status = "verified" if target_user.is_verified else "unverified"
        logger.info(f"Admin {admin.username} set {target_user.username} as {status}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error toggling user verification: {e}")
        db.session.rollback()
        return False, "An error occurred while changing verification status"


def admin_delete_user(admin: User, target_user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Mark a user account for deletion (admin only).
    Account will be recoverable for 30 days.
    
    Args:
        admin: Admin user performing the action
        target_user_id: ID of user to delete
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        if not admin.is_admin():
            return False, "Only administrators can delete user accounts"
        
        target_user = User.query.get(target_user_id)
        if not target_user:
            return False, "User not found"
        
        # Don't allow deleting own account
        if target_user.id == admin.id:
            return False, "You cannot delete your own account"
        
        # Don't allow deleting the default admin
        if target_user.is_admin() and target_user.email == 'admin@worldinsights.com':
            return False, "Cannot delete the default admin account"
        
        # Soft delete - mark for deletion
        username = target_user.username
        target_user.deleted_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Admin {admin.username} marked user {username} for deletion")
        return True, None
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        db.session.rollback()
        return False, "An error occurred while deleting the user account"


def recover_user(admin: User, target_user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Recover a deleted user account (admin only).
    
    Args:
        admin: Admin user performing the action
        target_user_id: ID of user to recover
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        if not admin.is_admin():
            return False, "Only administrators can recover user accounts"
        
        target_user = User.query.get(target_user_id)
        if not target_user:
            return False, "User not found"
        
        if not target_user.is_deleted():
            return False, "User account is not deleted"
        
        # Recover account
        username = target_user.username
        target_user.deleted_at = None
        db.session.commit()
        
        logger.info(f"Admin {admin.username} recovered user {username}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error recovering user: {e}")
        db.session.rollback()
        return False, "An error occurred while recovering the user account"


def update_profile(user: User, first_name: str, last_name: str) -> Tuple[bool, Optional[str]]:
    """
    Update user profile information.
    
    Args:
        user: User to update
        first_name: First name
        last_name: Last name
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        user.first_name = first_name.strip() if first_name else None
        user.last_name = last_name.strip() if last_name else None
        db.session.commit()
        
        logger.info(f"User profile updated: {user.username}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        db.session.rollback()
        return False, "An error occurred while updating your profile"


def send_password_reset_email(user: User, base_url: str) -> bool:
    """
    Send password reset email to user.
    
    Args:
        user: User object
        base_url: Base URL for reset link
    
    Returns:
        True if successful, False otherwise
    """
    from app.core.security import generate_password_reset_token
    from datetime import datetime
    
    try:
        token = generate_password_reset_token(user.id)
        reset_url = f"{base_url}/auth/reset-password/{token}"
        
        msg = Message(
            subject="Reset Your WorldInsights Password",
            recipients=[user.email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #3B82F6;">Password Reset Request</h2>
                    <p>Hello {user.username},</p>
                    <p>We received a request to reset your password for your WorldInsights account. Click the button below to reset your password:</p>
                    <p style="margin: 30px 0;">
                        <a href="{reset_url}" style="background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">
                            Reset Password
                        </a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="color: #666; font-size: 14px;">{reset_url}</p>
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px;">WorldInsights - Global Data Intelligence Platform</p>
                </body>
            </html>
            """
        )
        
        mail.send(msg)
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
        return False


def reset_password(token: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Reset user password using token.
    
    Args:
        token: Password reset token
        new_password: New password
    
    Returns:
        Tuple of (success, error_message)
    """
    from app.core.security import verify_token
    from datetime import datetime
    
    try:
        # Verify token
        user_id = verify_token(token)
        
        if not user_id:
            return False, "Invalid or expired password reset link"
        
        user = User.query.get(user_id)
        if not user:
            return False, "User not found"
        
        if user.is_deleted():
            return False, "This account has been deleted"
        
        # Update password
        user.password_hash = hash_password(new_password)
        db.session.commit()
        
        logger.info(f"Password reset successful for user: {user.username}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        db.session.rollback()
        return False, "An error occurred while resetting your password"


def change_password(user: User, current_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Change user password after verifying current password.
    
    Args:
        user: User to update
        current_password: Current password for verification
        new_password: New password
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect"
        
        # Check if new password is different
        if verify_password(new_password, user.password_hash):
            return False, "New password must be different from current password"
        
        # Update password
        user.password_hash = hash_password(new_password)
        db.session.commit()
        
        logger.info(f"Password changed successfully for user: {user.username}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        db.session.rollback()
        return False, "An error occurred while changing your password"

