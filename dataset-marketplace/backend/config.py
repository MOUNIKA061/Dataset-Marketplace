# ============================================================================
# Dataset Marketplace - Configuration
# Application configuration settings for different environments
# ============================================================================

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file in parent directory
# This allows sensitive configuration to be kept out of version control
load_dotenv()


class Config:
    """
    Base configuration class containing default settings.
    All other configuration classes inherit from this base class.
    Settings are loaded from environment variables with fallback defaults.
    """
    
    # --------------------------------------------------------------------
    # Flask Core Settings
    # --------------------------------------------------------------------
    
    # SECRET_KEY: Used for session signing, CSRF protection, and JWT encoding
    # IMPORTANT: Change this to a random string in production!
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Debug mode: enables auto-reload and detailed error pages
    # Set to False in production for security
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # --------------------------------------------------------------------
    # Database Configuration (MySQL)
    # --------------------------------------------------------------------
    
    # MySQL connection parameters loaded from environment variables
    # These can point to local MySQL or AWS RDS instance
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'dataset_marketplace')
    
    # SQLAlchemy database URI constructed from MySQL parameters
    # Format: mysql+pymysql://user:password@host:port/database
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    
    # Disable SQLAlchemy event system to save resources
    # This emits deprecation warning if not set
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pool settings for better performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,           # Number of connections to keep open
        'pool_recycle': 3600,     # Recycle connections after 1 hour
        'pool_pre_ping': True     # Verify connections before using
    }
    
    # --------------------------------------------------------------------
    # AWS S3 Configuration
    # --------------------------------------------------------------------
    
    # AWS credentials - use IAM roles in production instead of keys
    # For local development, set these in .env file
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    
    # S3 bucket name for storing datasets
    # Create this bucket in AWS console before running
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'dataset-marketplace-files')
    
    # Maximum file size for uploads (5MB for free-tier compliance)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB in bytes
    
    # Allowed file extensions for dataset uploads
    ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls'}
    
    # --------------------------------------------------------------------
    # JWT Authentication Settings
    # --------------------------------------------------------------------
    
    # JWT token expiration time (24 hours)
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))
    JWT_EXPIRATION_DELTA = timedelta(hours=JWT_EXPIRATION_HOURS)
    
    # JWT algorithm for token signing
    JWT_ALGORITHM = 'HS256'
    
    # --------------------------------------------------------------------
    # Dataset Processing Settings
    # --------------------------------------------------------------------
    
    # Number of rows to store as JSON snippet for preview
    PREVIEW_ROW_COUNT = 100
    
    # Maximum columns to include in preview
    MAX_PREVIEW_COLUMNS = 50
    

class DevelopmentConfig(Config):
    """
    Development configuration with debug mode enabled.
    Used for local development and testing.
    """
    DEBUG = True
    
    # More verbose logging in development
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """
    Production configuration with security hardening.
    Used for deployment on AWS or other cloud providers.
    """
    DEBUG = False
    
    # Ensure secret key is set in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production!")
    
    # Disable SQLAlchemy query logging in production
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """
    Testing configuration for unit and integration tests.
    Uses separate test database to avoid data corruption.
    """
    TESTING = True
    DEBUG = True
    
    # Use separate test database
    MYSQL_DATABASE = 'dataset_marketplace_test'
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@"
        f"{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )


# Dictionary mapping environment names to configuration classes
# Used in app.py to load correct configuration based on FLASK_ENV
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Get configuration class based on FLASK_ENV environment variable.
    
    Returns:
        Config: Configuration class appropriate for current environment
    
    Usage:
        config = get_config()
        app.config.from_object(config)
    """
    # Read environment name from FLASK_ENV, default to 'development'
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Return corresponding configuration class, fallback to development
    return config_by_name.get(env, DevelopmentConfig)
