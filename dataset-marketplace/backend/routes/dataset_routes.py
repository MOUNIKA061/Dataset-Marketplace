# ============================================================================
# Dataset Marketplace - Dataset Routes
# API endpoints for dataset operations (upload, search, download, visualize)
# ============================================================================

from flask import Blueprint, request, jsonify, current_app, Response, g
from models import db, Dataset, Download
from auth import token_required, owner_required, optional_token, get_current_user
from services.s3_service import s3_service
from services.recommendation_service import recommendation_service
from services.stats_service import stats_service
import json
from datetime import datetime

# Create Blueprint for dataset routes
# All routes will have /api/datasets prefix
datasets_bp = Blueprint('datasets', __name__, url_prefix='/api/datasets')


def allowed_file(filename):
    """
    Check if file extension is allowed.
    
    Args:
        filename: Original filename with extension
    
    Returns:
        bool: True if extension is in allowed list
    """
    # Get allowed extensions from config
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'csv', 'json', 'xlsx'})
    
    # Check if file has extension and it's allowed
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def get_file_extension(filename):
    """
    Extract file extension from filename.
    
    Args:
        filename: Original filename
    
    Returns:
        str: Lowercase file extension without dot
    """
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


@datasets_bp.route('/upload', methods=['POST'])
@token_required
@owner_required
def upload_dataset():
    """
    Upload new dataset file to S3 and store metadata in MySQL.
    
    Headers:
        Authorization: Bearer <token>
    
    Form Data:
        file: Dataset file (CSV, JSON, XLSX)
        title: Dataset title
        description: Dataset description (optional)
        tags: Comma-separated tags (optional)
        is_public: "true" or "false" (optional, default: true)
    
    Response:
        Success (201):
            {
                "success": true,
                "message": "Dataset uploaded successfully",
                "dataset": {...}
            }
        
        Error (400):
            {
                "success": false,
                "message": "Error description"
            }
    """
    # Get current authenticated user
    user = get_current_user()
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No file provided'
        }), 400
    
    # Get file from request
    file = request.files['file']
    
    # Check if filename is present
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No file selected'
        }), 400
    
    # Validate file extension
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'message': 'File type not allowed. Use CSV, JSON, or XLSX'
        }), 400
    
    # Get form data
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    tags = request.form.get('tags', '').strip()
    is_public = request.form.get('is_public', 'true').lower() == 'true'
    
    # Validate title
    if not title:
        return jsonify({
            'success': False,
            'message': 'Title is required'
        }), 400
    
    try:
        # Read file data
        file_data = file.read()
        file_size = len(file_data)
        
        # Check file size limit (5MB for free-tier)
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024)
        if file_size > max_size:
            return jsonify({
                'success': False,
                'message': f'File too large. Maximum size is {max_size // (1024*1024)}MB'
            }), 400
        
        # Get file type
        file_type = get_file_extension(file.filename)
        
        # Parse file to get metadata
        df = stats_service.parse_file(file_data, file_type)
        
        if df is None:
            return jsonify({
                'success': False,
                'message': 'Failed to parse file. Check file format.'
            }), 400
        
        # Get dataset stats
        row_count = len(df)
        column_count = len(df.columns)
        column_info = stats_service.get_column_info(df)
        
        # Generate JSON snippet (first 100 rows)
        preview_rows = current_app.config.get('PREVIEW_ROW_COUNT', 100)
        json_snippet = stats_service.generate_snippet(df, max_rows=preview_rows)
        
        # Generate S3 key and upload file
        s3_key = s3_service.generate_s3_key(user.id, file.filename)
        
        # Determine content type
        content_type_map = {
            'csv': 'text/csv',
            'json': 'application/json',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel'
        }
        content_type = content_type_map.get(file_type, 'application/octet-stream')
        
        # Upload to S3
        upload_result = s3_service.upload_file(file_data, s3_key, content_type)
        
        if not upload_result['success']:
            return jsonify({
                'success': False,
                'message': f'S3 upload failed: {upload_result.get("error", "Unknown error")}'
            }), 500
        
        # Create dataset record in MySQL
        dataset = Dataset(
            owner_id=user.id,
            title=title,
            description=description,
            tags=tags,
            file_type=file_type,
            file_size=file_size,
            row_count=row_count,
            column_count=column_count,
            s3_key=s3_key,
            json_snippet=json_snippet,
            column_info=column_info,
            is_public=is_public
        )
        
        # Save to database
        db.session.add(dataset)
        db.session.commit()
        
        # Return success response
        return jsonify({
            'success': True,
            'message': 'Dataset uploaded successfully',
            'dataset': dataset.to_dict(include_snippet=False)
        }), 201
    
    except Exception as e:
        # Rollback database changes
        db.session.rollback()
        
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500


@datasets_bp.route('/search', methods=['GET'])
@optional_token
def search_datasets():
    """
    Search datasets by tags, title, or description.
    
    Query Parameters:
        q: Search query string (optional)
        tags: Comma-separated tags to filter (optional)
        page: Page number for pagination (default: 1)
        per_page: Results per page (default: 10, max: 50)
        sort: Sort field (created_at, downloads, title) (default: created_at)
        order: Sort order (asc, desc) (default: desc)
    
    Response:
        Success (200):
            {
                "success": true,
                "datasets": [...],
                "total": N,
                "page": 1,
                "per_page": 10,
                "pages": N
            }
    """
    # Get query parameters
    query = request.args.get('q', '').strip()
    tags_filter = request.args.get('tags', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(50, max(1, int(request.args.get('per_page', 10))))
    sort_field = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    # Start query builder
    query_builder = Dataset.query.filter(Dataset.is_public == True)
    
    # Apply text search if query provided
    if query:
        # Search in title, description, and tags
        search_pattern = f'%{query}%'
        query_builder = query_builder.filter(
            (Dataset.title.ilike(search_pattern)) |
            (Dataset.description.ilike(search_pattern)) |
            (Dataset.tags.ilike(search_pattern))
        )
    
    # Apply tags filter if provided
    if tags_filter:
        tag_list = [t.strip().lower() for t in tags_filter.split(',') if t.strip()]
        for tag in tag_list:
            query_builder = query_builder.filter(Dataset.tags.ilike(f'%{tag}%'))
    
    # Apply sorting
    sort_map = {
        'created_at': Dataset.created_at,
        'downloads': Dataset.download_count,
        'title': Dataset.title
    }
    sort_column = sort_map.get(sort_field, Dataset.created_at)
    
    if sort_order.lower() == 'asc':
        query_builder = query_builder.order_by(sort_column.asc())
    else:
        query_builder = query_builder.order_by(sort_column.desc())
    
    # Execute paginated query
    pagination = query_builder.paginate(page=page, per_page=per_page, error_out=False)
    
    # Build response
    datasets = [d.to_dict(include_snippet=True) for d in pagination.items]
    
    return jsonify({
        'success': True,
        'datasets': datasets,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }), 200


@datasets_bp.route('/recommendations', methods=['GET'])
@optional_token
def get_recommendations():
    """
    Get AI-powered dataset recommendations.
    
    Query Parameters:
        tags: Comma-separated tags for similarity matching (optional)
        dataset_id: Get similar datasets to this one (optional)
        limit: Number of recommendations (default: 5, max: 10)
    
    For authenticated users, recommendations are personalized based
    on download history if no tags/dataset_id provided.
    
    Response:
        Success (200):
            {
                "success": true,
                "recommendations": [...],
                "method": "tag_similarity" | "personalized" | "popular"
            }
    """
    # Get query parameters
    tags = request.args.get('tags', '').strip()
    dataset_id = request.args.get('dataset_id', type=int)
    limit = min(10, max(1, int(request.args.get('limit', 5))))
    
    # Get all public datasets
    all_datasets = Dataset.query.filter(Dataset.is_public == True).all()
    
    # Get current user if authenticated
    user = get_current_user()
    
    recommendations = []
    method = 'popular'
    
    try:
        if dataset_id:
            # Get similar datasets to specified one
            similar = recommendation_service.get_similar_datasets(
                dataset_id, all_datasets, top_n=limit
            )
            recommendations = similar
            method = 'similar_datasets'
        
        elif tags:
            # Get recommendations based on provided tags
            tag_recs = recommendation_service.get_recommendations_for_tags(
                tags, all_datasets, top_n=limit
            )
            recommendations = tag_recs
            method = 'tag_similarity'
        
        elif user:
            # Get personalized recommendations based on user's downloads
            user_downloads = Download.query.filter_by(user_id=user.id).all()
            
            if user_downloads:
                personalized = recommendation_service.get_user_recommendations(
                    user_downloads, all_datasets, top_n=limit
                )
                recommendations = personalized
                method = 'personalized'
            else:
                # Fall back to popular if no download history
                popular = recommendation_service.get_popular_datasets(
                    all_datasets, exclude_ids=set(), top_n=limit
                )
                recommendations = popular
                method = 'popular'
        else:
            # Anonymous user - return popular datasets
            popular = recommendation_service.get_popular_datasets(
                all_datasets, exclude_ids=set(), top_n=limit
            )
            recommendations = popular
            method = 'popular'
        
        # Fetch full dataset info for recommendations
        result_datasets = []
        for dataset_id, score in recommendations:
            dataset = Dataset.query.get(dataset_id)
            if dataset:
                dataset_dict = dataset.to_dict(include_snippet=False)
                dataset_dict['relevance_score'] = round(score, 4)
                result_datasets.append(dataset_dict)
        
        return jsonify({
            'success': True,
            'recommendations': result_datasets,
            'method': method
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get recommendations: {str(e)}'
        }), 500


@datasets_bp.route('/<int:dataset_id>', methods=['GET'])
@optional_token
def get_dataset(dataset_id):
    """
    Get single dataset details including preview data.
    
    Path Parameters:
        dataset_id: ID of dataset to retrieve
    
    Response:
        Success (200):
            {
                "success": true,
                "dataset": {...}  // includes json_snippet
            }
        
        Error (404):
            {
                "success": false,
                "message": "Dataset not found"
            }
    """
    # Query dataset by ID
    dataset = Dataset.query.get(dataset_id)
    
    # Check if dataset exists
    if not dataset:
        return jsonify({
            'success': False,
            'message': 'Dataset not found'
        }), 404
    
    # Check visibility permissions
    user = get_current_user()
    
    if not dataset.is_public:
        # Private dataset - only owner and admin can view
        if not user or (user.id != dataset.owner_id and not user.is_admin()):
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
    
    # Return dataset with snippet
    return jsonify({
        'success': True,
        'dataset': dataset.to_dict(include_snippet=True)
    }), 200


@datasets_bp.route('/download/<int:dataset_id>', methods=['GET'])
@token_required
def download_dataset(dataset_id):
    """
    Download dataset file from S3 and log the download.
    
    Path Parameters:
        dataset_id: ID of dataset to download
    
    Headers:
        Authorization: Bearer <token>
    
    Query Parameters:
        presigned: If "true", return presigned URL instead of file (optional)
    
    Response:
        Success (200): File stream or presigned URL
        
        Error (404):
            {
                "success": false,
                "message": "Dataset not found"
            }
    """
    # Get current user
    user = get_current_user()
    
    # Query dataset
    dataset = Dataset.query.get(dataset_id)
    
    # Check if dataset exists
    if not dataset:
        return jsonify({
            'success': False,
            'message': 'Dataset not found'
        }), 404
    
    # Check access permissions
    if not dataset.is_public:
        if user.id != dataset.owner_id and not user.is_admin():
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
    
    # Check if presigned URL requested
    use_presigned = request.args.get('presigned', 'false').lower() == 'true'
    
    try:
        # Log download in database
        download_record = Download(
            dataset_id=dataset.id,
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string[:500] if request.user_agent else None
        )
        db.session.add(download_record)
        
        # Increment download count
        dataset.increment_download()
        
        # Commit download log
        db.session.commit()
        
        if use_presigned:
            # Generate presigned URL for direct S3 download
            url_result = s3_service.generate_presigned_url(dataset.s3_key, expiration=3600)
            
            if url_result['success']:
                return jsonify({
                    'success': True,
                    'download_url': url_result['url'],
                    'expires_in': url_result['expires_in']
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': url_result.get('error', 'Failed to generate download URL')
                }), 500
        
        else:
            # Stream file directly from S3
            download_result = s3_service.download_file(dataset.s3_key)
            
            if not download_result['success']:
                return jsonify({
                    'success': False,
                    'message': download_result.get('error', 'Download failed')
                }), 500
            
            # Prepare filename
            filename = f"{dataset.title.replace(' ', '_')}.{dataset.file_type}"
            
            # Return file as response
            return Response(
                download_result['data'],
                mimetype=download_result['content_type'],
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Length': download_result['content_length']
                }
            )
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Download failed: {str(e)}'
        }), 500


@datasets_bp.route('/visualize/<int:dataset_id>', methods=['GET'])
@optional_token
def visualize_dataset(dataset_id):
    """
    Get visualization data for dataset charts.
    
    Path Parameters:
        dataset_id: ID of dataset
    
    Query Parameters:
        column: Specific column to analyze (optional)
    
    Response:
        Success (200):
            {
                "success": true,
                "stats": {...},      // Basic statistics
                "histograms": {...}, // Histogram data for charts
                "value_counts": {...} // Category distributions
            }
    """
    # Query dataset
    dataset = Dataset.query.get(dataset_id)
    
    # Check if dataset exists
    if not dataset:
        return jsonify({
            'success': False,
            'message': 'Dataset not found'
        }), 404
    
    # Check visibility
    user = get_current_user()
    if not dataset.is_public:
        if not user or (user.id != dataset.owner_id and not user.is_admin()):
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
    
    try:
        # Parse the JSON snippet to create DataFrame
        snippet_data = dataset.get_snippet_data()
        
        if not snippet_data:
            return jsonify({
                'success': False,
                'message': 'No preview data available'
            }), 404
        
        # Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(snippet_data)
        
        # Get specific column if requested
        column = request.args.get('column', '').strip()
        
        if column:
            # Return stats for specific column
            column_stats = stats_service.get_column_stats(df, column)
            return jsonify({
                'success': True,
                'column_stats': column_stats
            }), 200
        
        # Get full visualization data
        viz_data = stats_service.get_visualization_data(df)
        
        return jsonify({
            'success': True,
            'dataset_id': dataset_id,
            'title': dataset.title,
            'numeric_stats': viz_data['numeric_stats'],
            'histograms': viz_data['histograms'],
            'value_counts': viz_data['value_counts'],
            'summary': viz_data['summary']
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Visualization failed: {str(e)}'
        }), 500


@datasets_bp.route('/my-datasets', methods=['GET'])
@token_required
def get_my_datasets():
    """
    Get datasets owned by current user.
    
    Headers:
        Authorization: Bearer <token>
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Results per page (default: 10)
    
    Response:
        Success (200):
            {
                "success": true,
                "datasets": [...],
                "total": N
            }
    """
    user = get_current_user()
    
    # Get pagination parameters
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(50, max(1, int(request.args.get('per_page', 10))))
    
    # Query user's datasets
    pagination = Dataset.query.filter_by(owner_id=user.id)\
        .order_by(Dataset.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    datasets = [d.to_dict(include_snippet=False) for d in pagination.items]
    
    return jsonify({
        'success': True,
        'datasets': datasets,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }), 200


@datasets_bp.route('/<int:dataset_id>', methods=['DELETE'])
@token_required
def delete_dataset(dataset_id):
    """
    Delete a dataset (owner or admin only).
    
    Path Parameters:
        dataset_id: ID of dataset to delete
    
    Headers:
        Authorization: Bearer <token>
    
    Response:
        Success (200):
            {
                "success": true,
                "message": "Dataset deleted"
            }
    """
    user = get_current_user()
    
    # Query dataset
    dataset = Dataset.query.get(dataset_id)
    
    if not dataset:
        return jsonify({
            'success': False,
            'message': 'Dataset not found'
        }), 404
    
    # Check ownership or admin
    if dataset.owner_id != user.id and not user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Access denied'
        }), 403
    
    try:
        # Delete from S3
        s3_service.delete_file(dataset.s3_key)
        
        # Delete from database
        db.session.delete(dataset)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Dataset deleted successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Delete failed: {str(e)}'
        }), 500
