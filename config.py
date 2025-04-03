import os

class Config:
    # Basic configuration
    DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    TESTING = False
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Application settings
    APP_NAME = "Cavalier Déménagement"
    COMPANY_FULL_NAME = "Cavalier Déménagement"
    COMPANY_ADDRESS = "123 Rue du Transport, 75000 Paris"
    COMPANY_PHONE = "+33 1 23 45 67 89"
    COMPANY_EMAIL = "contact@cavalier-demenagement.fr"
    COMPANY_WEBSITE = "www.cavalier-demenagement.fr"
    COMPANY_SIRET = "123 456 789 00012"
    
    # Invoice settings
    INVOICE_PREFIX = "FAC"
    VAT_RATE = 20.0  # Default VAT rate (%)
