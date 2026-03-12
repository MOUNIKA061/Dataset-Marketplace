# ============================================================================
# Dataset Marketplace - Services Package
# Initialize and export service modules
# ============================================================================

from services.s3_service import S3Service, s3_service
from services.recommendation_service import RecommendationService, recommendation_service
from services.stats_service import StatsService, stats_service

# Export all services
__all__ = [
    'S3Service',
    's3_service',
    'RecommendationService',
    'recommendation_service',
    'StatsService',
    'stats_service'
]
