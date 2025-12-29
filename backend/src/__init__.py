from flask import Flask, jsonify
from src.core.config import Config
from src.extensions import db, migrate, login_manager, mail, cors, limiter

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Load Config
    if isinstance(config_class, type):
        config = config_class()
    else:
        config = config_class
        
    app.config.update(config.to_dict())

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)
    with app.app_context():
        # Import models so they are registered
        from src.models import User
        from src.models import User
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        from src.models import User
        return User.query.get(int(user_id))

    # Register Blueprints
    from src.api.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

    from src.api.data import bp as data_bp
    app.register_blueprint(data_bp, url_prefix='/api/v1/data')

    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "service": "backend-api"})

    return app
