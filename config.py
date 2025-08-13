import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for Assessment Validator"""
    
    # API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    RTO_API_BASE_URL = os.getenv('RTO_API_BASE_URL', 'https://training.gov.au/api/v1')
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Microsoft Entra External ID Authentication Configuration
    AZURE_OAUTH_CLIENT_ID = os.getenv('AZURE_CLIENT_ID', '')
    AZURE_OAUTH_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET', '')
    AZURE_TENANT_NAME = os.getenv('AZURE_TENANT_NAME', '')
    AZURE_POLICY_NAME = os.getenv('AZURE_POLICY_NAME', 'B2C_1_signupsignin')
    AZURE_DOMAIN_SUFFIX = os.getenv('AZURE_DOMAIN_SUFFIX', 'ciamlogin.com')
    
    # Email Configuration for Invitations
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.office365.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    FROM_EMAIL = os.getenv('FROM_EMAIL', '')
    FROM_NAME = os.getenv('FROM_NAME', 'RTO Assessment Validation System')
    
    # Application URLs
    APP_URL = os.getenv('APP_URL', 'http://localhost:5001')
    APP_NAME = os.getenv('APP_NAME', 'RTO Assessment Validation Tool')
    
    # File Storage
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'storage/uploads')
    VALIDATOR_STORAGE = os.getenv('VALIDATOR_STORAGE', 'storage/validators')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Supported file types
    ALLOWED_EXTENSIONS = {'docx', 'pdf', 'doc'}
    
    # Testing Configuration
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create upload directory if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        # Create validator storage directory
        os.makedirs(Config.VALIDATOR_STORAGE, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Secure cookie settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 