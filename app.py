import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
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
csrf = CSRFProtect()

def create_app():
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Ajouter les options de pool pour PostgreSQL en production
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Fix for handling proxies
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
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
        
        # Register blueprints
        from routes import (
            auth_bp, dashboard_bp, client_bp, 
            prestation_bp, facture_bp, stockage_bp, user_bp, vehicule_bp,
            calendrier_bp
        )
        from routes.transporteur import transporteur_bp
        from healthcheck import healthcheck as healthcheck_blueprint
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(client_bp)
        app.register_blueprint(prestation_bp)
        app.register_blueprint(facture_bp)
        app.register_blueprint(stockage_bp)
        app.register_blueprint(user_bp)
        app.register_blueprint(vehicule_bp, url_prefix='/vehicules')
        app.register_blueprint(transporteur_bp)
        app.register_blueprint(calendrier_bp)
        app.register_blueprint(healthcheck_blueprint)
        
        # Create database tables
        db.create_all()
        
        # Create default admin user if it doesn't exist
        from utils import create_default_admin
        create_default_admin()
        
        return app
