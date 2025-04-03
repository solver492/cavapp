import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Secret key from environment variable
    app.secret_key = os.environ.get("SESSION_SECRET", "cavalier_demenagement_secret")
    
    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///cavalier.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Fix for handling proxies
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'
    
    with app.app_context():
        # Import models here to avoid circular imports
        from models import User
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        
        # Create database tables
        db.create_all()
        
        # Register blueprints
        from routes import (
            auth_bp, dashboard_bp, client_bp, 
            prestation_bp, facture_bp, stockage_bp, user_bp
        )
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(client_bp)
        app.register_blueprint(prestation_bp)
        app.register_blueprint(facture_bp)
        app.register_blueprint(stockage_bp)
        app.register_blueprint(user_bp)
        
        # Create default admin user if it doesn't exist
        from utils import create_default_admin
        create_default_admin()
        
        return app
