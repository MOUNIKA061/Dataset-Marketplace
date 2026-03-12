# ============================================================================
# Dataset Marketplace - Analytics Routes
# API endpoints for admin analytics and statistics
# ============================================================================

from flask import Blueprint, request, jsonify
from models import db, Dataset, Download, User
from auth import token_required, admin_required, get_current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta

# Create Blueprint for analytics routes
# All routes have /api/analytics prefix
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@analytics_bp.route('/overview', methods=['GET'])
@token_required
@admin_required
def get_overview():
    """
    Get high-level platform statistics for admin dashboard.
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        Success (200):
            {
                "success": true,
                "stats": {
                    "total_users": N,
                    "total_datasets": N,
                    "total_downloads": N,
                    "datasets_this_week": N,
                    "downloads_this_week": N,
                    "new_users_this_week": N
                }
            }
    
    Requires admin role.
    """
    try:
        # Calculate date range for "this week"
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Total counts
        total_users = User.query.count()
        total_datasets = Dataset.query.count()
        total_downloads = Download.query.count()
        
        # This week counts
        datasets_this_week = Dataset.query.filter(
            Dataset.created_at >= week_ago
        ).count()
        
        downloads_this_week = Download.query.filter(
            Download.downloaded_at >= week_ago
        ).count()
        
        new_users_this_week = User.query.filter(
            User.created_at >= week_ago
        ).count()
        
        # Calculate total download count from datasets table
        total_download_count = db.session.query(
            func.sum(Dataset.download_count)
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_datasets': total_datasets,
                'total_downloads': total_downloads,
                'total_download_count': int(total_download_count),
                'datasets_this_week': datasets_this_week,
                'downloads_this_week': downloads_this_week,
                'new_users_this_week': new_users_this_week
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get overview: {str(e)}'
        }), 500


@analytics_bp.route('/popular-datasets', methods=['GET'])
@token_required
@admin_required
def get_popular_datasets():
    """
    Get most popular datasets by download count.
    
    Query Parameters:
        limit: Number of results (default: 10, max: 50)
        days: Time range in days (optional, all-time if not specified)
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        Success (200):
            {
                "success": true,
                "datasets": [
                    {
                        "id": N,
                        "title": "...",
                        "download_count": N,
                        "owner_username": "..."
                    }
                ]
            }
    """
    try:
        # Get query parameters
        limit = min(50, max(1, int(request.args.get('limit', 10))))
        days = request.args.get('days', type=int)
        
        if days:
            # Filter by time range
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Count downloads in time range per dataset
            popular = db.session.query(
                Dataset.id,
                Dataset.title,
                Dataset.owner_id,
                User.username.label('owner_username'),
                func.count(Download.id).label('recent_downloads')
            ).join(
                Download, Download.dataset_id == Dataset.id
            ).join(
                User, User.id == Dataset.owner_id
            ).filter(
                Download.downloaded_at >= cutoff_date
            ).group_by(
                Dataset.id
            ).order_by(
                desc('recent_downloads')
            ).limit(limit).all()
            
            results = [{
                'id': d.id,
                'title': d.title,
                'download_count': d.recent_downloads,
                'owner_username': d.owner_username
            } for d in popular]
        
        else:
            # All-time popularity (using download_count column)
            popular = Dataset.query.join(
                User, User.id == Dataset.owner_id
            ).add_columns(
                User.username.label('owner_username')
            ).order_by(
                Dataset.download_count.desc()
            ).limit(limit).all()
            
            results = [{
                'id': d.Dataset.id,
                'title': d.Dataset.title,
                'download_count': d.Dataset.download_count,
                'owner_username': d.owner_username
            } for d in popular]
        
        return jsonify({
            'success': True,
            'datasets': results
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get popular datasets: {str(e)}'
        }), 500


@analytics_bp.route('/downloads-timeline', methods=['GET'])
@token_required
@admin_required
def get_downloads_timeline():
    """
    Get downloads aggregated by day for chart display.
    
    Query Parameters:
        days: Number of days to include (default: 30, max: 90)
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        Success (200):
            {
                "success": true,
                "timeline": [
                    {"date": "2024-01-01", "count": N},
                    ...
                ]
            }
    """
    try:
        # Get parameters
        days = min(90, max(1, int(request.args.get('days', 30))))
        
        # Calculate start date
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query downloads grouped by day
        results = db.session.query(
            func.date(Download.downloaded_at).label('date'),
            func.count(Download.id).label('count')
        ).filter(
            Download.downloaded_at >= start_date
        ).group_by(
            func.date(Download.downloaded_at)
        ).order_by(
            'date'
        ).all()
        
        # Build timeline with all days (fill zeros for missing days)
        timeline = []
        current_date = start_date.date()
        end_date = datetime.utcnow().date()
        
        # Create lookup dict from results
        downloads_by_date = {str(r.date): r.count for r in results}
        
        # Fill in all days
        while current_date <= end_date:
            date_str = str(current_date)
            timeline.append({
                'date': date_str,
                'count': downloads_by_date.get(date_str, 0)
            })
            current_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'timeline': timeline
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get timeline: {str(e)}'
        }), 500


@analytics_bp.route('/uploads-timeline', methods=['GET'])
@token_required
@admin_required
def get_uploads_timeline():
    """
    Get dataset uploads aggregated by day.
    
    Query Parameters:
        days: Number of days (default: 30, max: 90)
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        Success (200):
            {
                "success": true,
                "timeline": [
                    {"date": "2024-01-01", "count": N},
                    ...
                ]
            }
    """
    try:
        days = min(90, max(1, int(request.args.get('days', 30))))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query datasets grouped by day
        results = db.session.query(
            func.date(Dataset.created_at).label('date'),
            func.count(Dataset.id).label('count')
        ).filter(
            Dataset.created_at >= start_date
        ).group_by(
            func.date(Dataset.created_at)
        ).order_by(
            'date'
        ).all()
        
        # Build timeline
        timeline = []
        current_date = start_date.date()
        end_date = datetime.utcnow().date()
        
        uploads_by_date = {str(r.date): r.count for r in results}
        
        while current_date <= end_date:
            date_str = str(current_date)
            timeline.append({
                'date': date_str,
                'count': uploads_by_date.get(date_str, 0)
            })
            current_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'timeline': timeline
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get uploads timeline: {str(e)}'
        }), 500


@analytics_bp.route('/user-stats', methods=['GET'])
@token_required
@admin_required
def get_user_stats():
    """
    Get user statistics including role distribution.
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        Success (200):
            {
                "success": true,
                "stats": {
                    "by_role": {"admin": N, "owner": N, "user": N},
                    "top_uploaders": [...],
                    "top_downloaders": [...]
                }
            }
    """
    try:
        # Users by role
        role_counts = db.session.query(
            User.role,
            func.count(User.id)
        ).group_by(User.role).all()
        
        by_role = {role: count for role, count in role_counts}
        
        # Top uploaders (by dataset count)
        top_uploaders = db.session.query(
            User.id,
            User.username,
            func.count(Dataset.id).label('dataset_count')
        ).join(
            Dataset, Dataset.owner_id == User.id
        ).group_by(
            User.id
        ).order_by(
            desc('dataset_count')
        ).limit(10).all()
        
        uploaders = [{
            'user_id': u.id,
            'username': u.username,
            'dataset_count': u.dataset_count
        } for u in top_uploaders]
        
        # Top downloaders (by download count)
        top_downloaders = db.session.query(
            User.id,
            User.username,
            func.count(Download.id).label('download_count')
        ).join(
            Download, Download.user_id == User.id
        ).group_by(
            User.id
        ).order_by(
            desc('download_count')
        ).limit(10).all()
        
        downloaders = [{
            'user_id': u.id,
            'username': u.username,
            'download_count': u.download_count
        } for u in top_downloaders]
        
        return jsonify({
            'success': True,
            'stats': {
                'by_role': by_role,
                'top_uploaders': uploaders,
                'top_downloaders': downloaders
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get user stats: {str(e)}'
        }), 500


@analytics_bp.route('/tag-distribution', methods=['GET'])
@token_required
@admin_required
def get_tag_distribution():
    """
    Get distribution of tags across all datasets.
    
    Query Parameters:
        limit: Number of top tags to return (default: 20)
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        Success (200):
            {
                "success": true,
                "tags": [
                    {"tag": "finance", "count": N},
                    ...
                ]
            }
    """
    try:
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        
        # Get all datasets with tags
        datasets = Dataset.query.filter(Dataset.tags.isnot(None)).all()
        
        # Count tag frequencies
        from collections import Counter
        tag_counter = Counter()
        
        for dataset in datasets:
            tags = dataset.get_tags_list()
            tag_counter.update(tags)
        
        # Get top tags
        top_tags = tag_counter.most_common(limit)
        
        tags_list = [{'tag': tag, 'count': count} for tag, count in top_tags]
        
        return jsonify({
            'success': True,
            'tags': tags_list
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get tag distribution: {str(e)}'
        }), 500


@analytics_bp.route('/recent-activity', methods=['GET'])
@token_required
@admin_required
def get_recent_activity():
    """
    Get recent platform activity (uploads and downloads).
    
    Query Parameters:
        limit: Number of activities to return (default: 20)
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        Success (200):
            {
                "success": true,
                "activity": [
                    {
                        "type": "upload" | "download",
                        "timestamp": "ISO date",
                        "user": "username",
                        "dataset": "title"
                    }
                ]
            }
    """
    try:
        limit = min(50, max(1, int(request.args.get('limit', 20))))
        
        # Get recent uploads
        recent_uploads = db.session.query(
            Dataset.title.label('dataset_title'),
            Dataset.created_at.label('timestamp'),
            User.username
        ).join(
            User, User.id == Dataset.owner_id
        ).order_by(
            Dataset.created_at.desc()
        ).limit(limit // 2).all()
        
        # Get recent downloads
        recent_downloads = db.session.query(
            Dataset.title.label('dataset_title'),
            Download.downloaded_at.label('timestamp'),
            User.username
        ).join(
            Dataset, Dataset.id == Download.dataset_id
        ).join(
            User, User.id == Download.user_id
        ).order_by(
            Download.downloaded_at.desc()
        ).limit(limit // 2).all()
        
        # Combine and sort
        activity = []
        
        for upload in recent_uploads:
            activity.append({
                'type': 'upload',
                'timestamp': upload.timestamp.isoformat() if upload.timestamp else None,
                'user': upload.username,
                'dataset': upload.dataset_title
            })
        
        for download in recent_downloads:
            activity.append({
                'type': 'download',
                'timestamp': download.timestamp.isoformat() if download.timestamp else None,
                'user': download.username,
                'dataset': download.dataset_title
            })
        
        # Sort by timestamp descending
        activity.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        return jsonify({
            'success': True,
            'activity': activity[:limit]
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get recent activity: {str(e)}'
        }), 500
