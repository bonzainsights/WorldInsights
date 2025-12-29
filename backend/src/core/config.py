"""
Core configuration module for WorldInsights Backend.
"""
import os
from typing import Any, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
# We look for .env in the backend root or project root
load_dotenv()

def _get_env(key: str, default: Any = None, cast_type: type = str) -> Any:
    value = os.getenv(key, default)
    if value is None:
        return None
    if cast_type == bool:
        if isinstance(value, bool): return value
        return str(value).lower() in ('true', '1', 'yes', 'on')
    if cast_type != str and value is not None:
        try:
            return cast_type(value)
        except (ValueError, TypeError):
            return default
    return value

class Config:
    def __init__(self):
        self._SECRET_KEY = _get_env('SECRET_KEY')
        if not self._SECRET_KEY:
            # Fallback for dev if not set, but warn in logs (simulated)
            self._SECRET_KEY = "dev-key-change-me"
        
        self._FLASK_ENV = _get_env('FLASK_ENV', 'production')
        self._DEBUG = _get_env('FLASK_DEBUG', False, bool)

        # Paths - Pointing to the PARENT directory's data/logs to share state
        # Assuming backend is running from /backend
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        project_root = os.path.dirname(backend_root) # if backend is in src/core/backend, wait. 
        # file is in backend/src/core/config.py
        # abspath = /.../backend/src/core/config.py
        # dirname = /.../backend/src/core
        # dirname = /.../backend/src
        # dirname = /.../backend
        # dirname = /.../WorldInsights
        
        # Let's simple use relative paths from the execution point (backend/)
        # If we run `python run.py` from `backend/`, then `../data` is valid.
        
        self._DUCKDB_PATH = _get_env('DUCKDB_PATH', '../data/worldinsights.duckdb')
        self._DATABASE_URL = _get_env('DATABASE_URL', f'duckdb:///{self._DUCKDB_PATH}')
        
        abs_db_path = os.path.abspath('../data/worldinsights.db')
        self._SQLALCHEMY_DATABASE_URI = _get_env('SQLALCHEMY_DATABASE_URI', f'sqlite:///{abs_db_path}')
        self._SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        # Mail
        self._MAIL_SERVER = _get_env('MAIL_SERVER', 'smtp.gmail.com')
        self._MAIL_PORT = _get_env('MAIL_PORT', 587, int)
        self._MAIL_USE_TLS = _get_env('MAIL_USE_TLS', True, bool)
        self._MAIL_USE_SSL = _get_env('MAIL_USE_SSL', False, bool)
        self._MAIL_USERNAME = _get_env('MAIL_USERNAME')
        self._MAIL_PASSWORD = _get_env('MAIL_PASSWORD')
        self._MAIL_DEFAULT_SENDER = _get_env('MAIL_DEFAULT_SENDER', 'noreply@worldinsights.bonzainsights.com')
        
        # Session Security
        self._SESSION_COOKIE_HTTPONLY = True
        self._SESSION_COOKIE_SAMESITE = 'Lax'
        self._SESSION_COOKIE_SECURE = False # Request True in prod, False for dev
        self._SESSION_PERMANENT = True
        
        # Security / API
        self._API_RATE_LIMIT = _get_env('API_RATE_LIMIT', 100, int)
        self._WTF_CSRF_ENABLED = False # Disable CSRF for API, we use JWT/Tokens usually
        self._WTF_CSRF_ENABLED = False # Disable CSRF for API, we use JWT/Tokens usually
        self._CORS_ORIGINS = _get_env('CORS_ORIGINS', '*')
        
        self._MAX_LOGIN_ATTEMPTS = _get_env('MAX_LOGIN_ATTEMPTS', 5, int)
        self._LOCKOUT_DURATION = _get_env('LOCKOUT_DURATION', 15, int) # minutes

    @property
    def MAX_LOGIN_ATTEMPTS(self): return self._MAX_LOGIN_ATTEMPTS
    @property
    def LOCKOUT_DURATION(self): return self._LOCKOUT_DURATION 
    
    @property
    def SESSION_COOKIE_HTTPONLY(self): return self._SESSION_COOKIE_HTTPONLY
    @property
    def SESSION_COOKIE_SAMESITE(self): return self._SESSION_COOKIE_SAMESITE
    @property
    def SESSION_COOKIE_SECURE(self): return self._SESSION_COOKIE_SECURE
    @property
    def SESSION_PERMANENT(self): return self._SESSION_PERMANENT

    @property
    def SECRET_KEY(self): return self._SECRET_KEY
    @property
    def SQLALCHEMY_DATABASE_URI(self): return self._SQLALCHEMY_DATABASE_URI
    @property
    def SQLALCHEMY_TRACK_MODIFICATIONS(self): return self._SQLALCHEMY_TRACK_MODIFICATIONS
    
    def to_dict(self):
        return {
            'SECRET_KEY': self._SECRET_KEY,
            'SQLALCHEMY_DATABASE_URI': self._SQLALCHEMY_DATABASE_URI,
            'SQLALCHEMY_TRACK_MODIFICATIONS': self._SQLALCHEMY_TRACK_MODIFICATIONS,
            'MAIL_SERVER': self._MAIL_SERVER,
            'MAIL_PORT': self._MAIL_PORT,
            'MAIL_USERNAME': self._MAIL_USERNAME,
            'MAIL_PASSWORD': self._MAIL_PASSWORD,
            'MAIL_USE_TLS': self._MAIL_USE_TLS,
            'MAIL_USE_SSL': self._MAIL_USE_SSL,
            'MAIL_DEFAULT_SENDER': self._MAIL_DEFAULT_SENDER,
            'SESSION_COOKIE_HTTPONLY': self._SESSION_COOKIE_HTTPONLY,
            'SESSION_COOKIE_SAMESITE': self._SESSION_COOKIE_SAMESITE,
        }
