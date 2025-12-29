"""
Authentication service for WorldInsights Backend.
"""
from src.models import User
from src.extensions import db, mail
from src.core.security import (
    hash_password, verify_password, generate_verification_token,
    validate_email, validate_password_strength, verify_token,
    generate_password_reset_token
)
from src.core.config import Config
from flask_mail import Message
from typing import Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def register_user(username: str, email: str, password: str, terms_accepted: bool = False) -> Tuple[Optional[User], Optional[str]]:
    try:
        if not validate_email(email):
            return None, "Invalid email address"
        
        is_valid, error_msg = validate_password_strength(password, username=username, email=email)
        if not is_valid:
            return None, error_msg
        
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        
        if User.query.filter_by(email=email).first():
            return None, "Email already registered"
        
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_verified=False,
            role='user',
            subscription_tier='free',
            subscription_status='active',
            subscription_started_at=datetime.utcnow(),
            terms_accepted_at=datetime.utcnow() if terms_accepted else None
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
    try:
        token = generate_verification_token(user.id)
        # Note: In a real SPA, this URL should point to the Frontend (e.g. localhost:3000/verify?token=...)
        # For now we'll format it as an API link or Frontend link. 
        # Let's assume the frontend handles the verification via an API call.
        verification_url = f"{base_url}/verify-email?token={token}"
        
        msg = Message(
            subject="Verify Your WorldInsights Account",
            recipients=[user.email],
            html=f"Please verify your email: <a href='{verification_url}'>Verify Link</a>"
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def authenticate_user(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    try:
        config = Config()
        max_attempts = config.MAX_LOGIN_ATTEMPTS
        lockout_duration = config.LOCKOUT_DURATION
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return None, "Invalid email or password"
        
        if user.locked_until and datetime.utcnow() < user.locked_until:
             return None, "Account is locked"

        user.last_login_attempt = datetime.utcnow()
        
        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= max_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=lockout_duration)
            db.session.commit()
            return None, "Invalid email or password"
        
        if not user.is_verified:
            return None, "Email not verified"
            
        user.failed_login_attempts = 0
        user.last_successful_login = datetime.utcnow()
        db.session.commit()
        
        return user, None
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return None, "An error occurred"
