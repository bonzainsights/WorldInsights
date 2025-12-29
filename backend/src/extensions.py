from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions (unbound)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
cors = CORS()

# Limiter requires a key_func, so we initialize it with one but no app yet
limiter = Limiter(key_func=get_remote_address)
