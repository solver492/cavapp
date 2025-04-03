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
    
    # Ajouter des filtres personnalisés pour les templates
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        if not text:
            return ""
        return text.replace('\n', '<br>')
    
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
        from routes.api import api_bp
        from healthcheck import healthcheck as healthcheck_blueprint
        
        # Blueprint enregistrement avec préfixes cohérents
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp, url_prefix='/tableau-de-bord')
        app.register_blueprint(client_bp, url_prefix='/clients')
        app.register_blueprint(prestation_bp, url_prefix='/prestations')
        app.register_blueprint(facture_bp, url_prefix='/factures')
        app.register_blueprint(stockage_bp, url_prefix='/stockage')
        app.register_blueprint(user_bp, url_prefix='/utilisateurs')
        app.register_blueprint(vehicule_bp, url_prefix='/vehicules')
        app.register_blueprint(transporteur_bp, url_prefix='/transporteurs')
        app.register_blueprint(calendrier_bp, url_prefix='/calendrier')
        app.register_blueprint(api_bp, url_prefix='/api')  # Ajout du préfixe /api pour les routes API
        app.register_blueprint(healthcheck_blueprint)
        
        # Create database tables
        db.create_all()
        
        # Create default admin user if it doesn't exist
        from utils import create_default_admin
        create_default_admin()
        
        return app
