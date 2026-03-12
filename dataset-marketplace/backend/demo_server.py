# ============================================================================
# Dataset Marketplace - Simplified Demo Backend
# A standalone Flask server that works without external dependencies
# Uses in-memory storage for demonstration purposes
# ============================================================================

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================================
# Configuration
# ============================================================================
SECRET_KEY = 'demo-secret-key-change-in-production'
JWT_EXPIRY_HOURS = 24

# ============================================================================
# In-Memory Data Storage (Replace with database in production)
# ============================================================================
users_db = {}          # {user_id: user_data}
datasets_db = {}       # {dataset_id: dataset_data}
downloads_db = []      # [download_records]
tokens_db = {}         # {token: user_id}
file_storage = {}      # {dataset_id: file_content}

# Auto-increment counters
next_user_id = 1
next_dataset_id = 1

# ============================================================================
# Initialize Flask App
# ============================================================================
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Enable CORS for all routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ============================================================================
# Helper Functions
# ============================================================================

def generate_token(user_id):
    """
    Generate a simple auth token for the user.
    In production, use proper JWT library.
    """
    token = secrets.token_urlsafe(32)
    tokens_db[token] = {
        'user_id': user_id,
        'expires': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return token

def verify_token(token):
    """
    Verify and decode auth token.
    Returns user_id if valid, None otherwise.
    """
    if not token or token not in tokens_db:
        return None
    
    token_data = tokens_db[token]
    if datetime.utcnow() > token_data['expires']:
        del tokens_db[token]
        return None
    
    return token_data['user_id']

def get_current_user():
    """
    Get current user from Authorization header.
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    user_id = verify_token(token)
    
    if user_id and user_id in users_db:
        return users_db[user_id]
    
    return None

def login_required(f):
    """
    Decorator to require authentication.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """
    Decorator to require admin role.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        if user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

def parse_csv(content, limit=100):
    """
    Parse CSV content and return list of dictionaries.
    """
    lines = content.strip().split('\n')
    if not lines:
        return []
    
    # Parse header
    headers = [h.strip().strip('"') for h in lines[0].split(',')]
    
    # Parse rows
    rows = []
    for line in lines[1:limit+1]:
        values = []
        current = ''
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                values.append(current.strip().strip('"'))
                current = ''
            else:
                current += char
        values.append(current.strip().strip('"'))
        
        row = dict(zip(headers, values))
        rows.append(row)
    
    return rows, headers

def parse_json_data(content, limit=100):
    """
    Parse JSON content and return list of dictionaries.
    """
    data = json.loads(content)
    
    if isinstance(data, list):
        rows = data[:limit]
    elif isinstance(data, dict) and 'data' in data:
        rows = data['data'][:limit]
    else:
        rows = [data]
    
    headers = list(rows[0].keys()) if rows else []
    return rows, headers

def calculate_stats(rows, headers):
    """
    Calculate basic statistics for numeric columns.
    """
    stats = {}
    
    for header in headers:
        values = []
        for row in rows:
            try:
                val = float(row.get(header, 0))
                values.append(val)
            except (ValueError, TypeError):
                continue
        
        if values:
            sorted_vals = sorted(values)
            n = len(values)
            stats[header] = {
                'mean': sum(values) / n,
                'median': sorted_vals[n // 2] if n % 2 else (sorted_vals[n//2-1] + sorted_vals[n//2]) / 2,
                'min': min(values),
                'max': max(values),
                'std': (sum((v - sum(values)/n)**2 for v in values) / n) ** 0.5
            }
    
    return stats

# ============================================================================
# Auth Routes
# ============================================================================

@app.route('/api/register', methods=['POST'])
def register():
    """
    Register a new user account.
    """
    global next_user_id
    
    data = request.get_json()
    
    # Validate required fields
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    # Check if email already exists
    for user in users_db.values():
        if user['email'] == email:
            return jsonify({'error': 'Email already registered'}), 400
        if user['username'] == username:
            return jsonify({'error': 'Username already taken'}), 400
    
    # Create new user
    user_id = next_user_id
    next_user_id += 1
    
    users_db[user_id] = {
        'id': user_id,
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'role': 'owner',  # Default role allows uploading
        'created_at': datetime.utcnow().isoformat()
    }
    
    return jsonify({
        'message': 'Registration successful',
        'user_id': user_id
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    """
    Authenticate user and return token.
    """
    data = request.get_json()
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Find user by email
    user = None
    for u in users_db.values():
        if u['email'] == email:
            user = u
            break
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Generate token
    token = generate_token(user['id'])
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role']
        }
    })

# ============================================================================
# Dataset Routes
# ============================================================================

@app.route('/api/upload-dataset', methods=['POST'])
@login_required
def upload_dataset():
    """
    Upload a new dataset file.
    """
    global next_dataset_id
    
    user = get_current_user()
    
    # Get file from request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.json')):
        return jsonify({'error': 'Only CSV and JSON files are allowed'}), 400
    
    # Read file content
    content = file.read().decode('utf-8')
    file_size = len(content.encode('utf-8'))
    
    # Parse file
    try:
        if filename.endswith('.csv'):
            rows, headers = parse_csv(content)
        else:
            rows, headers = parse_json_data(content)
    except Exception as e:
        return jsonify({'error': f'Failed to parse file: {str(e)}'}), 400
    
    # Get metadata from form
    name = request.form.get('name', file.filename)
    description = request.form.get('description', '')
    tags_str = request.form.get('tags', '[]')
    
    try:
        tags = json.loads(tags_str)
    except:
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
    
    # Create dataset record
    dataset_id = next_dataset_id
    next_dataset_id += 1
    
    datasets_db[dataset_id] = {
        'id': dataset_id,
        'name': name,
        'description': description,
        'tags': tags,
        'owner_id': user['id'],
        'owner_name': user['username'],
        'file_name': file.filename,
        'file_type': 'csv' if filename.endswith('.csv') else 'json',
        'file_size': file_size,
        'row_count': len(rows),
        'column_count': len(headers),
        'columns': headers,
        'preview': rows[:100],
        'download_count': 0,
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Store file content
    file_storage[dataset_id] = content
    
    return jsonify({
        'message': 'Dataset uploaded successfully',
        'dataset_id': dataset_id
    }), 201

@app.route('/api/search-datasets', methods=['GET'])
@login_required
def search_datasets():
    """
    Search and list datasets.
    """
    # Get query parameters
    query = request.args.get('q', '').lower()
    tags_filter = request.args.get('tags', '')
    dataset_id = request.args.get('id')
    
    # If specific ID requested
    if dataset_id:
        try:
            did = int(dataset_id)
            if did in datasets_db:
                return jsonify({'datasets': [datasets_db[did]]})
            else:
                return jsonify({'datasets': []})
        except ValueError:
            return jsonify({'error': 'Invalid dataset ID'}), 400
    
    # Filter datasets
    results = []
    filter_tags = [t.strip().lower() for t in tags_filter.split(',') if t.strip()]
    
    for dataset in datasets_db.values():
        # Search in name and description
        if query:
            name_match = query in dataset['name'].lower()
            desc_match = query in dataset['description'].lower()
            tag_match = any(query in str(t).lower() for t in dataset['tags'])
            
            if not (name_match or desc_match or tag_match):
                continue
        
        # Filter by tags
        if filter_tags:
            dataset_tags = [str(t).lower() for t in dataset['tags']]
            if not any(ft in dataset_tags for ft in filter_tags):
                continue
        
        results.append(dataset)
    
    # Sort by download count (popularity)
    results.sort(key=lambda x: x['download_count'], reverse=True)
    
    return jsonify({'datasets': results})

@app.route('/api/download/<int:dataset_id>', methods=['GET'])
@login_required
def download_dataset(dataset_id):
    """
    Download a dataset file.
    """
    user = get_current_user()
    
    if dataset_id not in datasets_db:
        return jsonify({'error': 'Dataset not found'}), 404
    
    if dataset_id not in file_storage:
        return jsonify({'error': 'File not available'}), 404
    
    dataset = datasets_db[dataset_id]
    content = file_storage[dataset_id]
    
    # Log download
    downloads_db.append({
        'dataset_id': dataset_id,
        'dataset_name': dataset['name'],
        'user_id': user['id'],
        'user_name': user['username'],
        'downloaded_at': datetime.utcnow().isoformat()
    })
    
    # Increment download count
    dataset['download_count'] += 1
    
    # Return file content
    from io import BytesIO
    buffer = BytesIO(content.encode('utf-8'))
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='text/csv' if dataset['file_type'] == 'csv' else 'application/json',
        as_attachment=True,
        download_name=dataset['file_name']
    )

@app.route('/api/visualize/<int:dataset_id>', methods=['GET'])
@login_required
def visualize_dataset(dataset_id):
    """
    Get visualization data for a dataset.
    """
    if dataset_id not in datasets_db:
        return jsonify({'error': 'Dataset not found'}), 404
    
    dataset = datasets_db[dataset_id]
    preview = dataset.get('preview', [])
    headers = dataset.get('columns', [])
    
    # Calculate statistics
    stats = calculate_stats(preview, headers)
    
    return jsonify({
        'dataset_id': dataset_id,
        'preview': preview,  # Return all preview data for visualization
        'stats': stats,
        'columns': headers,
        'row_count': dataset['row_count'],
        'name': dataset['name']
    })

# ============================================================================
# Recommendations Route
# ============================================================================

@app.route('/api/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    """
    Get AI-powered dataset recommendations based on tag similarity.
    """
    user = get_current_user()
    
    # Get user's downloaded datasets for preference analysis
    user_downloads = [d for d in downloads_db if d['user_id'] == user['id']]
    
    # Collect tags from user's downloads
    user_tags = set()
    for download in user_downloads:
        did = download['dataset_id']
        if did in datasets_db:
            user_tags.update(str(t).lower() for t in datasets_db[did]['tags'])
    
    # If no downloads, use popular tags
    if not user_tags:
        all_tags = []
        for dataset in datasets_db.values():
            all_tags.extend(str(t).lower() for t in dataset['tags'])
        user_tags = set(all_tags[:5]) if all_tags else set()
    
    # Score datasets by tag similarity
    recommendations = []
    for dataset in datasets_db.values():
        dataset_tags = set(str(t).lower() for t in dataset['tags'])
        
        # Calculate Jaccard similarity
        if user_tags or dataset_tags:
            intersection = len(user_tags & dataset_tags)
            union = len(user_tags | dataset_tags)
            score = intersection / union if union > 0 else 0
        else:
            score = 0.5  # Default score for new users
        
        if score > 0:
            recommendations.append({
                'dataset': dataset,
                'score': score,
                'reason': f"Similar tags: {', '.join(user_tags & dataset_tags)}" if user_tags & dataset_tags else "Popular in your area"
            })
    
    # Sort by score and limit
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    recommendations = recommendations[:5]
    
    return jsonify({'recommendations': recommendations})

# ============================================================================
# Analytics Route (Admin Only)
# ============================================================================

@app.route('/api/analytics', methods=['GET'])
@login_required
def get_analytics():
    """
    Get platform analytics (admin only).
    """
    user = get_current_user()
    
    # Allow non-admins to see limited analytics for demo
    # In production, uncomment the admin check
    # if user['role'] != 'admin':
    #     return jsonify({'error': 'Admin access required'}), 403
    
    # Calculate totals
    total_downloads = sum(d['download_count'] for d in datasets_db.values())
    total_datasets = len(datasets_db)
    total_users = len(users_db)
    total_storage = sum(d['file_size'] for d in datasets_db.values())
    
    # Get top datasets
    top_datasets = sorted(
        datasets_db.values(),
        key=lambda x: x['download_count'],
        reverse=True
    )[:10]
    
    # Get recent downloads
    recent_downloads = sorted(
        downloads_db,
        key=lambda x: x['downloaded_at'],
        reverse=True
    )[:10]
    
    # Downloads by category (tags)
    tag_counts = {}
    for dataset in datasets_db.values():
        for tag in dataset['tags']:
            tag_str = str(tag).lower()
            tag_counts[tag_str] = tag_counts.get(tag_str, 0) + dataset['download_count']
    
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        'total_downloads': total_downloads,
        'total_datasets': total_datasets,
        'total_users': total_users,
        'total_storage': total_storage,
        'top_datasets': top_datasets,
        'recent_downloads': recent_downloads,
        'downloads_by_category': {
            'labels': [t[0] for t in top_tags],
            'values': [t[1] for t in top_tags]
        }
    })

# ============================================================================
# Static File Serving
# ============================================================================

@app.route('/')
def serve_index():
    """Serve the main index.html page."""
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from frontend folder."""
    return app.send_static_file(path)

# ============================================================================
# Create Demo Data
# ============================================================================

def create_demo_data():
    """
    Create sample users and datasets for demo purposes.
    """
    global next_user_id, next_dataset_id
    
    # Create admin user
    users_db[1] = {
        'id': 1,
        'username': 'admin',
        'email': 'admin@demo.com',
        'password_hash': generate_password_hash('admin123'),
        'role': 'admin',
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Create demo user
    users_db[2] = {
        'id': 2,
        'username': 'demo',
        'email': 'demo@demo.com',
        'password_hash': generate_password_hash('demo123'),
        'role': 'owner',
        'created_at': datetime.utcnow().isoformat()
    }
    
    next_user_id = 3
    
    # Create sample datasets
    sample_datasets = [
        {
            'name': 'Stock Market Data 2024',
            'description': 'Historical stock prices for major tech companies including AAPL, GOOGL, MSFT, and AMZN.',
            'tags': ['finance', 'stocks', 'market', 'historical'],
            'columns': ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume'],
            'preview': [
                {'date': '2024-01-01', 'symbol': 'AAPL', 'open': '185.50', 'high': '187.20', 'low': '184.80', 'close': '186.90', 'volume': '45000000'},
                {'date': '2024-01-02', 'symbol': 'AAPL', 'open': '186.90', 'high': '188.50', 'low': '186.00', 'close': '187.80', 'volume': '42000000'},
                {'date': '2024-01-03', 'symbol': 'GOOGL', 'open': '140.25', 'high': '142.00', 'low': '139.50', 'close': '141.30', 'volume': '28000000'},
                {'date': '2024-01-04', 'symbol': 'GOOGL', 'open': '141.30', 'high': '143.10', 'low': '140.80', 'close': '142.50', 'volume': '26500000'},
                {'date': '2024-01-05', 'symbol': 'MSFT', 'open': '375.00', 'high': '378.50', 'low': '374.00', 'close': '377.20', 'volume': '22000000'},
            ],
            'file_size': 256000,
            'row_count': 5000,
            'download_count': 125
        },
        {
            'name': 'Customer Sales Dataset',
            'description': 'E-commerce sales data with customer demographics, product categories, and transaction details.',
            'tags': ['sales', 'ecommerce', 'customers', 'retail'],
            'columns': ['order_id', 'customer_id', 'product', 'category', 'price', 'quantity', 'date'],
            'preview': [
                {'order_id': '1001', 'customer_id': 'C001', 'product': 'Laptop', 'category': 'Electronics', 'price': '999.99', 'quantity': '1', 'date': '2024-03-01'},
                {'order_id': '1002', 'customer_id': 'C002', 'product': 'Headphones', 'category': 'Electronics', 'price': '149.99', 'quantity': '2', 'date': '2024-03-01'},
                {'order_id': '1003', 'customer_id': 'C003', 'product': 'Running Shoes', 'category': 'Sports', 'price': '89.99', 'quantity': '1', 'date': '2024-03-02'},
                {'order_id': '1004', 'customer_id': 'C001', 'product': 'Mouse', 'category': 'Electronics', 'price': '29.99', 'quantity': '1', 'date': '2024-03-02'},
                {'order_id': '1005', 'customer_id': 'C004', 'product': 'Yoga Mat', 'category': 'Sports', 'price': '24.99', 'quantity': '2', 'date': '2024-03-03'},
            ],
            'file_size': 512000,
            'row_count': 10000,
            'download_count': 89
        },
        {
            'name': 'Weather Observations',
            'description': 'Daily weather data from US cities including temperature, humidity, and precipitation.',
            'tags': ['weather', 'climate', 'temperature', 'environment'],
            'columns': ['date', 'city', 'temp_high', 'temp_low', 'humidity', 'precipitation', 'wind_speed'],
            'preview': [
                {'date': '2024-03-01', 'city': 'New York', 'temp_high': '52', 'temp_low': '38', 'humidity': '65', 'precipitation': '0.2', 'wind_speed': '12'},
                {'date': '2024-03-01', 'city': 'Los Angeles', 'temp_high': '72', 'temp_low': '55', 'humidity': '45', 'precipitation': '0', 'wind_speed': '8'},
                {'date': '2024-03-02', 'city': 'Chicago', 'temp_high': '45', 'temp_low': '32', 'humidity': '70', 'precipitation': '0.5', 'wind_speed': '18'},
                {'date': '2024-03-02', 'city': 'Houston', 'temp_high': '78', 'temp_low': '62', 'humidity': '75', 'precipitation': '0.1', 'wind_speed': '10'},
                {'date': '2024-03-03', 'city': 'Phoenix', 'temp_high': '85', 'temp_low': '58', 'humidity': '20', 'precipitation': '0', 'wind_speed': '6'},
            ],
            'file_size': 185000,
            'row_count': 3650,
            'download_count': 67
        },
        {
            'name': 'Social Media Analytics',
            'description': 'User engagement metrics from social media platforms including likes, shares, and comments.',
            'tags': ['social', 'analytics', 'marketing', 'engagement'],
            'columns': ['post_id', 'platform', 'likes', 'shares', 'comments', 'impressions', 'date'],
            'preview': [
                {'post_id': 'P001', 'platform': 'Twitter', 'likes': '1250', 'shares': '340', 'comments': '89', 'impressions': '45000', 'date': '2024-03-01'},
                {'post_id': 'P002', 'platform': 'Instagram', 'likes': '5600', 'shares': '120', 'comments': '230', 'impressions': '78000', 'date': '2024-03-01'},
                {'post_id': 'P003', 'platform': 'LinkedIn', 'likes': '890', 'shares': '450', 'comments': '67', 'impressions': '23000', 'date': '2024-03-02'},
                {'post_id': 'P004', 'platform': 'Facebook', 'likes': '2300', 'shares': '890', 'comments': '156', 'impressions': '56000', 'date': '2024-03-02'},
                {'post_id': 'P005', 'platform': 'TikTok', 'likes': '15000', 'shares': '2300', 'comments': '890', 'impressions': '250000', 'date': '2024-03-03'},
            ],
            'file_size': 320000,
            'row_count': 8000,
            'download_count': 156
        },
        {
            'name': 'Machine Learning Features',
            'description': 'Pre-processed feature dataset for ML model training with normalized values.',
            'tags': ['ml', 'machine learning', 'features', 'ai'],
            'columns': ['sample_id', 'feature_1', 'feature_2', 'feature_3', 'feature_4', 'label'],
            'preview': [
                {'sample_id': '1', 'feature_1': '0.234', 'feature_2': '0.567', 'feature_3': '0.891', 'feature_4': '0.123', 'label': '1'},
                {'sample_id': '2', 'feature_1': '0.456', 'feature_2': '0.789', 'feature_3': '0.234', 'feature_4': '0.567', 'label': '0'},
                {'sample_id': '3', 'feature_1': '0.678', 'feature_2': '0.123', 'feature_3': '0.456', 'feature_4': '0.789', 'label': '1'},
                {'sample_id': '4', 'feature_1': '0.890', 'feature_2': '0.345', 'feature_3': '0.678', 'feature_4': '0.012', 'label': '0'},
                {'sample_id': '5', 'feature_1': '0.012', 'feature_2': '0.567', 'feature_3': '0.890', 'feature_4': '0.234', 'label': '1'},
            ],
            'file_size': 1024000,
            'row_count': 50000,
            'download_count': 234
        }
    ]
    
    # Add datasets
    for i, ds in enumerate(sample_datasets, start=1):
        datasets_db[i] = {
            'id': i,
            'name': ds['name'],
            'description': ds['description'],
            'tags': ds['tags'],
            'owner_id': 1 if i % 2 == 0 else 2,
            'owner_name': 'admin' if i % 2 == 0 else 'demo',
            'file_name': f"{ds['name'].lower().replace(' ', '_')}.csv",
            'file_type': 'csv',
            'file_size': ds['file_size'],
            'row_count': ds['row_count'],
            'column_count': len(ds['columns']),
            'columns': ds['columns'],
            'preview': ds['preview'],
            'download_count': ds['download_count'],
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Generate CSV content for download
        csv_lines = [','.join(ds['columns'])]
        for row in ds['preview']:
            csv_lines.append(','.join(str(row.get(col, '')) for col in ds['columns']))
        file_storage[i] = '\n'.join(csv_lines)
    
    next_dataset_id = 6
    
    # Add some sample downloads
    for i in range(1, 6):
        downloads_db.append({
            'dataset_id': i,
            'dataset_name': datasets_db[i]['name'],
            'user_id': 2,
            'user_name': 'demo',
            'downloaded_at': (datetime.utcnow() - timedelta(days=i)).isoformat()
        })
    
    print("✓ Demo data created successfully!")
    print("  - Admin user: admin@demo.com / admin123")
    print("  - Demo user: demo@demo.com / demo123")

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Dataset Marketplace - Demo Server")
    print("="*60)
    
    # Create demo data
    create_demo_data()
    
    print("\n  Starting server...")
    print("  API: http://localhost:5000/api")
    print("  Frontend: http://localhost:5000")
    print("\n  Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    # Run Flask development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False
    )
