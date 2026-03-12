# ============================================================================
# Dataset Marketplace - Authentication Module
# JWT-based authentication with role-based access control
# ============================================================================

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app, g
from models import User


def generate_token(user):
    """
    Generate JWT access token for authenticated user.
    
    Args:
        user: User model instance
    
    Returns:
        str: Encoded JWT token string
    
    Token payload includes:
        - user_id: User's database ID
        - username: User's username
        - role: User's role (admin/owner/user)
        - exp: Expiration timestamp
        - iat: Issued at timestamp
    """
    # Get configuration from Flask app context
    secret_key = current_app.config['SECRET_KEY']
    expiration = current_app.config.get('JWT_EXPIRATION_DELTA', timedelta(hours=24))
    algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
    
    # Build JWT payload with user information and timestamps
    payload = {
        'user_id': user.id,           # User identifier for database lookups
        'username': user.username,     # Username for display purposes
        'role': user.role,             # Role for authorization checks
        'exp': datetime.utcnow() + expiration,  # Token expiration time
        'iat': datetime.utcnow()       # Token issue time
    }
    
    # Encode payload with secret key using configured algorithm
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    
    return token


def decode_token(token):
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        dict: Decoded payload if valid
        None: If token is invalid or expired
    
    Validates:
        - Token signature using secret key
        - Token expiration (exp claim)
    """
    # Get configuration from Flask app context
    secret_key = current_app.config['SECRET_KEY']
    algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
    
    try:
        # Decode and verify token signature and expiration
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    
    except jwt.ExpiredSignatureError:
        # Token has expired (exp claim in the past)
        return None
    
    except jwt.InvalidTokenError:
        # Token is malformed or signature verification failed
        return None


def get_token_from_header():
    """
    Extract JWT token from Authorization header.
    
    Returns:
        str: Token string if present and properly formatted
        None: If header is missing or malformed
    
    Expected format: "Bearer <token>"
    """
    # Get Authorization header from request
    auth_header = request.headers.get('Authorization', '')
    
    # Check if header follows Bearer token format
    if auth_header.startswith('Bearer '):
        # Extract token part after "Bearer "
        return auth_header[7:]  # Skip "Bearer " (7 characters)
    
    return None


def token_required(f):
    """
    Decorator to require valid JWT token for route access.
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route():
            user = g.current_user  # Access authenticated user
            return jsonify({'user': user.username})
    
    Sets g.current_user with authenticated User instance.
    Returns 401 error if token is missing or invalid.
    """
    @wraps(f)  # Preserve original function metadata
    def decorated(*args, **kwargs):
        # Extract token from Authorization header
        token = get_token_from_header()
        
        # Check if token is present
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication token is missing',
                'error': 'unauthorized'
            }), 401
        
        # Decode and validate token
        payload = decode_token(token)
        
        # Check if token is valid
        if not payload:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token',
                'error': 'unauthorized'
            }), 401
        
        # Fetch user from database using user_id from token
        user = User.query.get(payload['user_id'])
        
        # Verify user still exists (could have been deleted)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'error': 'unauthorized'
            }), 401
        
        # Store user in Flask g object for access in route function
        g.current_user = user
        
        # Call the decorated route function
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """
    Decorator to require admin role for route access.
    Must be used after @token_required decorator.
    
    Usage:
        @app.route('/admin-only')
        @token_required
        @admin_required
        def admin_route():
            return jsonify({'message': 'Admin access granted'})
    
    Returns 403 error if user is not an admin.
    """
    @wraps(f)  # Preserve original function metadata
    def decorated(*args, **kwargs):
        # Get current user from g (set by token_required)
        user = getattr(g, 'current_user', None)
        
        # Verify user exists (should always be true after token_required)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Authentication required',
                'error': 'unauthorized'
            }), 401
        
        # Check if user has admin role
        if not user.is_admin():
            return jsonify({
                'success': False,
                'message': 'Admin privileges required',
                'error': 'forbidden'
            }), 403
        
        # Call the decorated route function
        return f(*args, **kwargs)
    
    return decorated


def owner_required(f):
    """
    Decorator to require owner or admin role for route access.
    Used for routes that require upload capabilities.
    Must be used after @token_required decorator.
    
    Usage:
        @app.route('/upload')
        @token_required
        @owner_required
        def upload_route():
            return jsonify({'message': 'Upload access granted'})
    
    Returns 403 error if user cannot upload datasets.
    """
    @wraps(f)  # Preserve original function metadata
    def decorated(*args, **kwargs):
        # Get current user from g (set by token_required)
        user = getattr(g, 'current_user', None)
        
        # Verify user exists
        if not user:
            return jsonify({
                'success': False,
                'message': 'Authentication required',
                'error': 'unauthorized'
            }), 401
        
        # Check if user can upload (admin or owner)
        if not user.can_upload():
            return jsonify({
                'success': False,
                'message': 'Owner or admin privileges required for uploads',
                'error': 'forbidden'
            }), 403
        
        # Call the decorated route function
        return f(*args, **kwargs)
    
    return decorated


def optional_token(f):
    """
    Decorator to optionally authenticate user without requiring it.
    Useful for routes accessible to both authenticated and anonymous users.
    
    Usage:
        @app.route('/public')
        @optional_token
        def public_route():
            user = g.current_user  # May be None
            if user:
                return jsonify({'message': f'Hello {user.username}'})
            return jsonify({'message': 'Hello anonymous user'})
    
    Sets g.current_user to User instance or None.
    Never returns authentication errors.
    """
    @wraps(f)  # Preserve original function metadata
    def decorated(*args, **kwargs):
        # Initialize current_user as None
        g.current_user = None
        
        # Try to extract and validate token
        token = get_token_from_header()
        
        if token:
            # Attempt to decode token
            payload = decode_token(token)
            
            if payload:
                # Fetch user if token is valid
                user = User.query.get(payload['user_id'])
                if user:
                    g.current_user = user
        
        # Always call route function (even without valid auth)
        return f(*args, **kwargs)
    
    return decorated


def get_current_user():
    """
    Utility function to get current authenticated user.
    
    Returns:
        User: Current user instance if authenticated
        None: If no user is authenticated
    
    Usage in route functions:
        user = get_current_user()
        if user:
            print(f"Logged in as {user.username}")
    """
    return getattr(g, 'current_user', None)
