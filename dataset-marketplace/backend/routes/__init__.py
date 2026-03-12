# ============================================================================
# Dataset Marketplace - Routes Package
# Initialize and export route blueprints
# ============================================================================

from routes.auth_routes import auth_bp
from routes.dataset_routes import datasets_bp
from routes.analytics_routes import analytics_bp

# Export all blueprints
__all__ = [
    'auth_bp',
    'datasets_bp',
    'analytics_bp'
]
