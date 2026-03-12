# ============================================================================
# Dataset Marketplace - Main Application
# Flask application entry point with all configurations and routes
# ============================================================================

import os
import sys

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import get_config
from models import db, init_db
from services.s3_service import s3_service
from routes.auth_routes import auth_bp
from routes.dataset_routes import datasets_bp
from routes.analytics_routes import analytics_bp


def create_app(config_class=None):
    """
    Application factory function to create and configure Flask app.
    
    Args:
        config_class: Configuration class to use (optional)
                      If not provided, uses FLASK_ENV environment variable
    
    Returns:
        Flask: Configured Flask application instance
    
    This factory pattern allows:
    - Easy testing with different configurations
    - Multiple app instances if needed
    - Delayed initialization of extensions
    """
    # Create Flask application instance
    # Static folder points to frontend for serving HTML/CSS/JS
    app = Flask(
        __name__,
        static_folder='../frontend',
        static_url_path=''
    )
    
    # Load configuration
    # Use provided config class or detect from environment
    if config_class is None:
        config_class = get_config()
    
    # Apply configuration to app
    app.config.from_object(config_class)
    
    # --------------------------------------------------------------------
    # Initialize Extensions
    # --------------------------------------------------------------------
    
    # Enable CORS for API routes
    # This allows frontend (possibly on different port) to call backend
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # In production, restrict to specific domains
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize SQLAlchemy database
    db.init_app(app)
    
    # Initialize S3 service with app config
    s3_service.init_app(app)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # --------------------------------------------------------------------
    # Register Blueprints (Route groups)
    # --------------------------------------------------------------------
    
    # Authentication routes: /api/auth/*
    app.register_blueprint(auth_bp)
    
    # Dataset routes: /api/datasets/*
    app.register_blueprint(datasets_bp)
    
    # Analytics routes: /api/analytics/*
    app.register_blueprint(analytics_bp)
    
    # --------------------------------------------------------------------
    # Frontend Serving Routes
    # --------------------------------------------------------------------
    
    @app.route('/')
    def serve_index():
        """
        Serve main index page (login page).
        Redirects root URL to login.html
        """
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        """
        Serve static files from frontend folder.
        This handles HTML, CSS, JS, and other assets.
        
        Args:
            path: Requested file path
        
        Returns:
            File content or 404 error
        """
        # Check if file exists in static folder
        file_path = os.path.join(app.static_folder, path)
        
        if os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
        
        # For SPA-style routing, return index.html for unknown paths
        # This allows frontend routing to work
        return send_from_directory(app.static_folder, 'index.html')
    
    # --------------------------------------------------------------------
    # Error Handlers
    # --------------------------------------------------------------------
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            'success': False,
            'message': 'Bad request',
            'error': str(error)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return jsonify({
            'success': False,
            'message': 'Unauthorized',
            'error': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        return jsonify({
            'success': False,
            'message': 'Forbidden',
            'error': 'Access denied'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            'success': False,
            'message': 'Not found',
            'error': 'Resource not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        # Rollback any failed database transactions
        db.session.rollback()
        
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(error)
        }), 500
    
    # --------------------------------------------------------------------
    # Health Check Endpoint
    # --------------------------------------------------------------------
    
    @app.route('/api/health')
    def health_check():
        """
        Health check endpoint for monitoring and load balancers.
        
        Returns:
            JSON with status and database connection status
        """
        try:
            # Test database connection
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'version': '1.0.0'
        }), 200
    
    return app


# Create application instance
app = create_app()


if __name__ == '__main__':
    """
    Run development server when script is executed directly.
    
    For production, use:
    - gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 app:app (Linux/Mac)
    - waitress: waitress-serve --port=5000 app:app (Windows)
    """
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Get debug mode from config
    debug = app.config.get('DEBUG', True)
    
    # Print startup message
    print(f"""
    ============================================
    Dataset Marketplace Backend
    ============================================
    * Running on: http://localhost:{port}
    * Debug mode: {debug}
    * Environment: {os.environ.get('FLASK_ENV', 'development')}
    
    API Endpoints:
    * POST /api/auth/register - Register new user
    * POST /api/auth/login - Login and get token
    * GET  /api/auth/me - Get current user profile
    * POST /api/datasets/upload - Upload dataset
    * GET  /api/datasets/search - Search datasets
    * GET  /api/datasets/recommendations - Get AI recommendations
    * GET  /api/datasets/<id> - Get dataset details
    * GET  /api/datasets/download/<id> - Download dataset
    * GET  /api/datasets/visualize/<id> - Get visualization data
    * GET  /api/analytics/overview - Admin dashboard stats
    * GET  /api/health - Health check
    ============================================
    """)
    
    # Run development server
    # Host 0.0.0.0 allows external connections
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
