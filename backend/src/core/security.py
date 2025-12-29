"""
Core security module for WorldInsights.
"""
import bcrypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from email_validator import validate_email as email_validate, EmailNotValidError
from typing import Optional, Tuple, List
import os
import re
from zxcvbn import zxcvbn

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False

def _get_serializer() -> URLSafeTimedSerializer:
    secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    return URLSafeTimedSerializer(secret_key)

def generate_verification_token(user_id: int, expiration: int = 3600) -> str:
    serializer = _get_serializer()
    return serializer.dumps(user_id, salt='email-verification')

def generate_password_reset_token(user_id: int, expiration: int = 3600) -> str:
    serializer = _get_serializer()
    return serializer.dumps(user_id, salt='password-reset')

def verify_token(token: str, max_age: int = 3600) -> Optional[int]:
    serializer = _get_serializer()
    try:
        return serializer.loads(token, salt='email-verification', max_age=max_age)
    except (SignatureExpired, BadSignature):
        try:
            return serializer.loads(token, salt='password-reset', max_age=max_age)
        except (SignatureExpired, BadSignature):
            return None

def validate_email(email: str) -> bool:
    try:
        email_validate(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

def generate_secure_token(length: int = 32) -> str:
    import secrets
    return secrets.token_urlsafe(length)

COMMON_PASSWORDS = {
    'password', 'password123', '123456', '12345678', 'qwerty', 'abc123',
    'monkey', '1234567', 'letmein', 'trustno1', 'dragon', 'baseball',
    'iloveyou', 'master', 'sunshine', 'ashley', 'bailey', 'passw0rd',
    'shadow', '123123', '654321', 'superman', 'qazwsx', 'michael',
    'football', 'welcome', 'jesus', 'ninja', 'mustang', 'password1'
}

def validate_password_strength(password: str, username: Optional[str] = None, email: Optional[str] = None, min_length: int = 10) -> Tuple[bool, Optional[str]]:
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'/`~]', password):
        return False, "Password must contain at least one special character"
    if password.lower() in COMMON_PASSWORDS:
        return False, "This password is too common"
    if username and username.lower() in password.lower():
        return False, "Password cannot contain your username"
    if email:
        email_local = email.split('@')[0].lower()
        if email_local in password.lower():
            return False, "Password cannot contain your email address"
            
    # zxcvbn check
    user_inputs = []
    if username: user_inputs.append(username)
    if email: user_inputs.extend(email.split('@'))
    result = zxcvbn(password, user_inputs=user_inputs)
    if result['score'] < 3:
        return False, "Password is too weak (zxcvbn score < 3)"
        
    return True, None

def get_password_requirements() -> List[str]:
    return [
        "At least 12 characters long",
        "Contains uppercase, lowercase, number, and special char",
        "Not common or personal info"
    ]
