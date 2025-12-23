"""
Unit tests for core/security.py module.

Tests password hashing, verification, and token generation/verification.
All tests must pass before implementing the actual security module.
"""
import pytest
from datetime import datetime, timedelta


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        from app.core.security import hash_password
        
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_different_for_same_password(self):
        """Test that same password produces different hashes (salt)."""
        from app.core.security import hash_password
        
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different due to salt
    
    def test_verify_password_correct(self):
        """Test that correct password verifies successfully."""
        from app.core.security import hash_password, verify_password
        
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test that incorrect password fails verification."""
        from app.core.security import hash_password, verify_password
        
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_password_handles_special_characters(self):
        """Test that special characters in password are handled."""
        from app.core.security import hash_password, verify_password
        
        password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_hash_password_handles_unicode(self):
        """Test that unicode characters are handled."""
        from app.core.security import hash_password, verify_password
        
        password = "パスワード123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True


class TestTokenGeneration:
    """Test token generation and verification."""
    
    def test_generate_verification_token_returns_string(self):
        """Test that generate_verification_token returns a string."""
        from app.core.security import generate_verification_token
        
        user_id = 123
        token = generate_verification_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test that valid token is verified correctly."""
        from app.core.security import generate_verification_token, verify_token
        
        user_id = 123
        token = generate_verification_token(user_id)
        
        verified_id = verify_token(token)
        assert verified_id == user_id
    
    def test_verify_token_invalid(self):
        """Test that invalid token returns None."""
        from app.core.security import verify_token
        
        invalid_token = "invalid-token-string"
        
        verified_id = verify_token(invalid_token)
        assert verified_id is None
    
    def test_verify_token_expired(self):
        """Test that expired token returns None."""
        from app.core.security import generate_verification_token, verify_token
        import time
        
        user_id = 123
        # Generate token
        token = generate_verification_token(user_id)
        
        # Wait 2 seconds then verify with 1 second max_age (should be expired)
        time.sleep(2)
        verified_id = verify_token(token, max_age=1)
        assert verified_id is None
    
    def test_tokens_are_unique(self):
        """Test that different user IDs produce different tokens."""
        from app.core.security import generate_verification_token
        
        token1 = generate_verification_token(1)
        token2 = generate_verification_token(2)
        
        assert token1 != token2
    
    def test_generate_password_reset_token(self):
        """Test password reset token generation."""
        from app.core.security import generate_password_reset_token, verify_token
        
        user_id = 456
        token = generate_password_reset_token(user_id)
        
        assert isinstance(token, str)
        verified_id = verify_token(token)
        assert verified_id == user_id


class TestEmailValidation:
    """Test email validation."""
    
    def test_validate_email_valid(self):
        """Test that valid email passes validation."""
        from app.core.security import validate_email
        
        valid_emails = [
            "user@example.com",
            "admin@worldinsights.com",
            "test.user@domain.co.uk",
            "test+tag@domain.com"
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True
    
    def test_validate_email_invalid(self):
        """Test that invalid email fails validation."""
        from app.core.security import validate_email
        
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com"
        ]
        
        for email in invalid_emails:
            assert validate_email(email) is False


class TestSecurityModuleNoFlaskDependencies:
    """Test that security module has no Flask dependencies."""
    
    def test_no_flask_imports(self):
        """Test that security module doesn't import Flask."""
        import inspect
        from app.core import security as security_module
        
        source = inspect.getsource(security_module)
        
        # Should not have Flask imports
        assert 'from flask import' not in source
        assert 'import flask' not in source.lower()
