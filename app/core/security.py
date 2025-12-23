"""
Core security module for WorldInsights.

This module provides security functions for password hashing, token generation,
and email validation. It is framework-agnostic and has no Flask dependencies.

Functions:
    - hash_password: Hash a password using bcrypt
    - verify_password: Verify a password against its hash
    - generate_verification_token: Generate email verification token
    - generate_password_reset_token: Generate password reset token
    - verify_token: Verify and decode a token
    - validate_email: Validate email address format
"""
import bcrypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from email_validator import validate_email as email_validate, EmailNotValidError
from typing import Optional
import os


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
    
    Returns:
        Hashed password as string
    
    Example:
        >>> hashed = hash_password("MySecurePassword123")
        >>> isinstance(hashed, str)
        True
    """
    # Convert password to bytes and hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    
    Example:
        >>> hashed = hash_password("MyPassword")
        >>> verify_password("MyPassword", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def _get_serializer() -> URLSafeTimedSerializer:
    """
    Get URLSafeTimedSerializer instance with secret key.
    
    Returns:
        Configured serializer
    """
    # Get secret key from environment or use default (should be set in production)
    secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    return URLSafeTimedSerializer(secret_key)


def generate_verification_token(user_id: int, expiration: int = 3600) -> str:
    """
    Generate email verification token for user.
    
    Args:
        user_id: User ID to encode in token
        expiration: Token expiration time in seconds (default: 1 hour)
    
    Returns:
        Signed token as string
    
    Example:
        >>> token = generate_verification_token(123)
        >>> isinstance(token, str)
        True
    """
    serializer = _get_serializer()
    return serializer.dumps(user_id, salt='email-verification')


def generate_password_reset_token(user_id: int, expiration: int = 3600) -> str:
    """
    Generate password reset token for user.
    
    Args:
        user_id: User ID to encode in token
        expiration: Token expiration time in seconds (default: 1 hour)
    
    Returns:
        Signed token as string
    
    Example:
        >>> token = generate_password_reset_token(123)
        >>> isinstance(token, str)
        True
    """
    serializer = _get_serializer()
    return serializer.dumps(user_id, salt='password-reset')


def verify_token(token: str, max_age: int = 3600) -> Optional[int]:
    """
    Verify and decode a token.
    
    Args:
        token: Token string to verify
        max_age: Maximum age of token in seconds (default: 1 hour)
    
    Returns:
        User ID if token valid, None otherwise
    
    Example:
        >>> token = generate_verification_token(123)
        >>> user_id = verify_token(token)
        >>> user_id == 123
        True
    """
    serializer = _get_serializer()
    
    try:
        # Try email verification salt first
        user_id = serializer.loads(
            token,
            salt='email-verification',
            max_age=max_age
        )
        return user_id
    except (SignatureExpired, BadSignature):
        # Try password reset salt
        try:
            user_id = serializer.loads(
                token,
                salt='password-reset',
                max_age=max_age
            )
            return user_id
        except (SignatureExpired, BadSignature):
            return None


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    
    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    try:
        # Validate email format
        email_validate(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


# Convenience function for generating secure random tokens
def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length: Length of token in bytes (default: 32)
    
    Returns:
        Secure random token as hex string
    """
    import secrets
    return secrets.token_urlsafe(length)
