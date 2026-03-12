# ============================================================================
# Dataset Marketplace - Authentication Routes
# API endpoints for user registration and login
# ============================================================================

from flask import Blueprint, request, jsonify
from models import db, User
from auth import generate_token, token_required, get_current_user
import re

# Create Blueprint for authentication routes
# All routes in this blueprint will have /api/auth prefix
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def validate_email(email):
    """
    Validate email format using regex.
    
    Args:
        email: Email string to validate
    
    Returns:
        bool: True if email format is valid
    """
    # Simple email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Validate password strength.
    
    Args:
        password: Password string to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    
    Requirements:
        - Minimum 6 characters
    """
    # Check minimum length
    if len(password) < 6:
        return False, 'Password must be at least 6 characters'
    
    return True, None


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register new user account.
    
    Request JSON:
        {
            "username": "string",  # Required, 3-80 chars, unique
            "email": "string",     # Required, valid email format, unique
            "password": "string",  # Required, min 6 chars
            "role": "string"       # Optional, defaults to 'user'
        }
    
    Response:
        Success (201):
            {
                "success": true,
                "message": "User registered successfully",
                "user": {...}
            }
        
        Error (400):
            {
                "success": false,
                "message": "Error description"
            }
    """
    # Parse JSON request body
    data = request.get_json()
    
    # Validate required fields are present
    if not data:
        return jsonify({
            'success': False,
            'message': 'Request body is required'
        }), 400
    
    # Extract fields from request
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'user')
    
    # Validate username
    if not username:
        return jsonify({
            'success': False,
            'message': 'Username is required'
        }), 400
    
    if len(username) < 3 or len(username) > 80:
        return jsonify({
            'success': False,
            'message': 'Username must be between 3 and 80 characters'
        }), 400
    
    # Validate email
    if not email:
        return jsonify({
            'success': False,
            'message': 'Email is required'
        }), 400
    
    if not validate_email(email):
        return jsonify({
            'success': False,
            'message': 'Invalid email format'
        }), 400
    
    # Validate password
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({
            'success': False,
            'message': error_msg
        }), 400
    
    # Validate role (only allow 'user' for self-registration)
    # Admin can upgrade users later
    if role not in ['user', 'owner']:
        role = 'user'
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({
            'success': False,
            'message': 'Username already exists'
        }), 400
    
    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({
            'success': False,
            'message': 'Email already registered'
        }), 400
    
    try:
        # Create new user instance
        user = User(
            username=username,
            email=email,
            role=role
        )
        
        # Hash and set password
        user.set_password(password)
        
        # Add user to database session
        db.session.add(user)
        
        # Commit transaction to save user
        db.session.commit()
        
        # Generate JWT token for immediate login
        token = generate_token(user)
        
        # Return success response
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'token': token
        }), 201
    
    except Exception as e:
        # Rollback transaction on error
        db.session.rollback()
        
        return jsonify({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token.
    
    Request JSON:
        {
            "username": "string",  # Can be username or email
            "password": "string"
        }
    
    Response:
        Success (200):
            {
                "success": true,
                "message": "Login successful",
                "user": {...},
                "token": "jwt_token_string"
            }
        
        Error (401):
            {
                "success": false,
                "message": "Invalid credentials"
            }
    """
    # Parse JSON request body
    data = request.get_json()
    
    # Validate request body
    if not data:
        return jsonify({
            'success': False,
            'message': 'Request body is required'
        }), 400
    
    # Extract credentials
    username_or_email = data.get('username', '').strip()
    password = data.get('password', '')
    
    # Validate fields are present
    if not username_or_email:
        return jsonify({
            'success': False,
            'message': 'Username or email is required'
        }), 400
    
    if not password:
        return jsonify({
            'success': False,
            'message': 'Password is required'
        }), 400
    
    # Find user by username or email
    user = User.query.filter(
        (User.username == username_or_email) | 
        (User.email == username_or_email.lower())
    ).first()
    
    # Check if user exists and password is correct
    if not user or not user.check_password(password):
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        }), 401
    
    # Generate JWT token
    token = generate_token(user)
    
    # Return success response with token
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': user.to_dict(),
        'token': token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_profile():
    """
    Get current authenticated user's profile.
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        Success (200):
            {
                "success": true,
                "user": {...}
            }
    """
    # Get current user from g (set by token_required)
    user = get_current_user()
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/update-profile', methods=['PUT'])
@token_required
def update_profile():
    """
    Update current user's profile.
    
    Headers:
        Authorization: Bearer <token>
    
    Request JSON:
        {
            "email": "string",     # Optional, new email
            "password": "string"   # Optional, new password
        }
    
    Response:
        Success (200):
            {
                "success": true,
                "message": "Profile updated",
                "user": {...}
            }
    """
    # Get current user
    user = get_current_user()
    
    # Parse request body
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'Request body is required'
        }), 400
    
    try:
        # Update email if provided
        if 'email' in data:
            new_email = data['email'].strip().lower()
            
            if not validate_email(new_email):
                return jsonify({
                    'success': False,
                    'message': 'Invalid email format'
                }), 400
            
            # Check if email is taken by another user
            existing = User.query.filter(
                User.email == new_email,
                User.id != user.id
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'Email already in use'
                }), 400
            
            user.email = new_email
        
        # Update password if provided
        if 'password' in data:
            is_valid, error_msg = validate_password(data['password'])
            if not is_valid:
                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 400
            
            user.set_password(data['password'])
        
        # Commit changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Update failed: {str(e)}'
        }), 500


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token():
    """
    Verify if JWT token is still valid.
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        Success (200):
            {
                "success": true,
                "valid": true,
                "user": {...}
            }
    
    If token is invalid, @token_required will return 401
    """
    user = get_current_user()
    
    return jsonify({
        'success': True,
        'valid': True,
        'user': user.to_dict()
    }), 200
