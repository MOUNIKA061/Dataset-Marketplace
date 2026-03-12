# ============================================================================
# Dataset Marketplace - Database Models
# SQLAlchemy ORM models for Users, Datasets, and Downloads tables
# ============================================================================

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Initialize SQLAlchemy instance
# This will be bound to Flask app in app.py using db.init_app(app)
db = SQLAlchemy()


class User(db.Model):
    """
    User model representing application users.
    
    Supports three roles:
    - 'admin': Full access to all features including analytics
    - 'owner': Can upload and manage their own datasets
    - 'user': Can search, view, and download datasets
    
    Attributes:
        id: Unique identifier (primary key)
        username: Unique username for login
        email: Unique email address
        password_hash: Securely hashed password
        role: User role (admin/owner/user)
        created_at: Account creation timestamp
        updated_at: Last modification timestamp
    """
    
    # Table name in MySQL database
    __tablename__ = 'users'
    
    # Primary key: auto-incremented integer
    id = db.Column(db.Integer, primary_key=True)
    
    # Username: required, unique, max 80 chars
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    
    # Email: required, unique, max 120 chars
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    # Password hash: never store plain text passwords
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Role: enum with default 'user'
    role = db.Column(db.Enum('admin', 'owner', 'user'), default='user')
    
    # Timestamps for auditing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to datasets owned by this user
    # backref creates 'owner' attribute on Dataset model
    datasets = db.relationship('Dataset', backref='owner', lazy='dynamic', 
                               cascade='all, delete-orphan')
    
    # Relationship to downloads made by this user
    downloads = db.relationship('Download', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """
        Hash and store password securely using Werkzeug's PBKDF2.
        
        Args:
            password: Plain text password from user input
        
        The password is hashed using PBKDF2-SHA256 with random salt.
        Original password is never stored.
        """
        # Generate secure hash with salt using PBKDF2 algorithm
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
        
        Returns:
            bool: True if password matches, False otherwise
        """
        # Compare provided password with stored hash
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """
        Check if user has admin privileges.
        
        Returns:
            bool: True if user role is 'admin'
        """
        return self.role == 'admin'
    
    def can_upload(self):
        """
        Check if user can upload datasets.
        
        Returns:
            bool: True if user is admin or owner
        """
        # Both admin and owner roles can upload datasets
        return self.role in ['admin', 'owner']
    
    def to_dict(self):
        """
        Convert user object to dictionary for JSON serialization.
        Excludes sensitive data like password hash.
        
        Returns:
            dict: User data safe for API response
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        """String representation for debugging."""
        return f'<User {self.username}>'


class Dataset(db.Model):
    """
    Dataset model representing uploaded data files.
    
    Full files are stored in AWS S3, metadata and preview stored in MySQL.
    Includes JSON snippet (first 100 rows) for quick preview without S3 access.
    
    Attributes:
        id: Unique identifier (primary key)
        owner_id: Foreign key to user who uploaded
        title: Human-readable dataset name
        description: Detailed description
        tags: Comma-separated keywords for search
        file_type: Original file format (csv/json/xlsx)
        file_size: Size in bytes
        row_count: Number of data rows
        column_count: Number of columns
        s3_key: AWS S3 object key for file retrieval
        json_snippet: First 100 rows as JSON for preview
        column_info: JSON with column names and types
        download_count: Popularity metric
        is_public: Visibility flag
    """
    
    __tablename__ = 'datasets'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Dataset metadata
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(db.String(500))  # Comma-separated tags
    
    # File information
    file_type = db.Column(db.String(20), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    row_count = db.Column(db.Integer, default=0)
    column_count = db.Column(db.Integer, default=0)
    
    # S3 storage reference
    s3_key = db.Column(db.String(500), nullable=False)
    
    # Preview data (first 100 rows as JSON)
    json_snippet = db.Column(db.Text(16777215))  # MEDIUMTEXT
    
    # Column schema information as JSON
    column_info = db.Column(db.JSON)
    
    # Analytics
    download_count = db.Column(db.Integer, default=0, index=True)
    
    # Visibility
    is_public = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to download records
    downloads = db.relationship('Download', backref='dataset', lazy='dynamic',
                                cascade='all, delete-orphan')
    
    def get_tags_list(self):
        """
        Parse tags string into list.
        
        Returns:
            list: List of individual tags, empty list if no tags
        """
        # Split comma-separated tags and strip whitespace
        if self.tags:
            return [tag.strip().lower() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def set_tags_from_list(self, tags_list):
        """
        Convert list of tags to comma-separated string.
        
        Args:
            tags_list: List of tag strings
        """
        # Join tags with comma, converting to lowercase
        self.tags = ','.join([tag.strip().lower() for tag in tags_list])
    
    def get_snippet_data(self):
        """
        Parse JSON snippet string to Python object.
        
        Returns:
            list: List of dictionaries representing rows, empty list on error
        """
        if self.json_snippet:
            try:
                # Parse JSON string to Python list
                return json.loads(self.json_snippet)
            except json.JSONDecodeError:
                # Return empty list if JSON is malformed
                return []
        return []
    
    def increment_download(self):
        """
        Increment download counter by 1.
        Call db.session.commit() after this to persist.
        """
        self.download_count = (self.download_count or 0) + 1
    
    def to_dict(self, include_snippet=False):
        """
        Convert dataset to dictionary for JSON serialization.
        
        Args:
            include_snippet: Whether to include full JSON preview data
        
        Returns:
            dict: Dataset data for API response
        """
        data = {
            'id': self.id,
            'owner_id': self.owner_id,
            'owner_username': self.owner.username if self.owner else None,
            'title': self.title,
            'description': self.description,
            'tags': self.get_tags_list(),
            'file_type': self.file_type,
            'file_size': self.file_size,
            'row_count': self.row_count,
            'column_count': self.column_count,
            'column_info': self.column_info,
            'download_count': self.download_count,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Only include snippet if requested (can be large)
        if include_snippet:
            data['json_snippet'] = self.get_snippet_data()
        
        return data
    
    def __repr__(self):
        """String representation for debugging."""
        return f'<Dataset {self.title}>'


class Download(db.Model):
    """
    Download model tracking all file download events.
    
    Used for:
    - Analytics and popularity metrics
    - User download history
    - Rate limiting and abuse prevention
    
    Attributes:
        id: Unique identifier (primary key)
        dataset_id: Foreign key to downloaded dataset
        user_id: Foreign key to downloading user (nullable)
        ip_address: Client IP for analytics
        user_agent: Browser/client information
        downloaded_at: Timestamp of download
    """
    
    __tablename__ = 'downloads'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to datasets table
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    
    # Foreign key to users table (can be NULL for anonymous)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Request metadata for analytics
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    
    # Download timestamp
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """
        Convert download record to dictionary.
        
        Returns:
            dict: Download data for API response
        """
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'dataset_title': self.dataset.title if self.dataset else None,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Anonymous',
            'downloaded_at': self.downloaded_at.isoformat() if self.downloaded_at else None
        }
    
    def __repr__(self):
        """String representation for debugging."""
        return f'<Download {self.id} - Dataset {self.dataset_id}>'


def init_db(app):
    """
    Initialize database with Flask application.
    
    Args:
        app: Flask application instance
    
    This function:
    1. Binds SQLAlchemy to Flask app
    2. Creates all tables if they don't exist
    """
    # Bind SQLAlchemy instance to Flask app
    db.init_app(app)
    
    # Create tables within app context
    with app.app_context():
        # Create all tables defined by models
        # This is idempotent - won't recreate existing tables
        db.create_all()
