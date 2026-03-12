# Dataset Marketplace MVP

A cloud-based dataset marketplace application that allows users to upload, search, download, and visualize datasets with AI-powered recommendations.

## Features

- **User Authentication**: Register, login with role-based access (admin, owner, user)
- **Dataset Upload**: Upload CSV/JSON files with automatic preview generation
- **Search & Filter**: Search datasets by keywords and tags
- **AI Recommendations**: Tag-similarity based dataset recommendations
- **Data Visualization**: Interactive charts using Chart.js for dataset statistics
- **Admin Dashboard**: Analytics and download statistics for administrators
- **Cloud Storage**: AWS S3 integration for secure dataset storage

## Project Structure

```
dataset-marketplace/
├── backend/                    # Flask API backend
│   ├── app.py                 # Main Flask application
│   ├── auth.py                # JWT authentication helpers
│   ├── config.py              # Configuration settings
│   ├── models.py              # Database models
│   ├── requirements.txt       # Python dependencies
│   ├── routes/                # API route handlers
│   │   ├── __init__.py
│   │   ├── analytics_routes.py
│   │   ├── auth_routes.py
│   │   └── dataset_routes.py
│   └── services/              # Business logic services
│       ├── __init__.py
│       ├── recommendation_service.py
│       ├── s3_service.py
│       └── stats_service.py
├── database/
│   └── schema.sql             # MySQL database schema
├── frontend/                   # HTML/CSS/JS frontend
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── admin.js
│   │   ├── api.js
│   │   ├── auth.js
│   │   ├── config.js
│   │   ├── dataset.js
│   │   ├── login.js
│   │   ├── register.js
│   │   ├── search.js
│   │   ├── upload.js
│   │   └── utils.js
│   ├── admin.html
│   ├── dataset.html
│   ├── index.html
│   ├── register.html
│   ├── search.html
│   └── upload.html
└── README.md
```

## Prerequisites

- Python 3.8+
- MySQL 5.7+ or AWS RDS MySQL
- AWS Account (for S3 storage) - Optional for local testing
- Node.js (optional, for serving frontend)

## Local Development Setup

### 1. Clone/Download the Project

```bash
cd dataset-marketplace
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Set Up MySQL Database

#### Option A: Local MySQL

1. Install MySQL Server locally
2. Create the database:

```bash
mysql -u root -p
```

```sql
CREATE DATABASE dataset_marketplace;
USE dataset_marketplace;
SOURCE database/schema.sql;
```

#### Option B: AWS RDS (Free Tier)

1. Go to AWS Console → RDS → Create database
2. Choose MySQL, Free tier
3. Configure:
   - DB instance identifier: `dataset-marketplace`
   - Master username: `admin`
   - Master password: (choose strong password)
4. Make it publicly accessible (for development)
5. Create database and note the endpoint

### 4. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this

# Database Configuration (Local)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_NAME=dataset_marketplace

# Database Configuration (AWS RDS - uncomment if using RDS)
# DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
# DB_USER=admin
# DB_PASSWORD=your-rds-password
# DB_NAME=dataset_marketplace

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-dataset-bucket-name

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
```

### 5. Set Up AWS S3 Bucket (Required for file storage)

1. Go to AWS Console → S3 → Create bucket
2. Bucket name: `your-dataset-bucket-name` (must be globally unique)
3. Region: Same as your preference (e.g., `us-east-1`)
4. Block public access: Keep enabled (access via signed URLs)
5. Create bucket

#### Configure CORS for S3 (if needed):

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST"],
        "AllowedOrigins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "ExposeHeaders": []
    }
]
```

### 6. Create AWS IAM User (for programmatic access)

1. Go to AWS Console → IAM → Users → Create user
2. User name: `dataset-marketplace-api`
3. Attach policy: `AmazonS3FullAccess` (or create a custom policy for your bucket only)
4. Create access key and save the credentials

### 7. Run the Backend

```bash
cd backend
python app.py
```

The API will be available at `http://localhost:5000`

### 8. Serve the Frontend

#### Option A: Use Python's HTTP Server

```bash
cd frontend
python -m http.server 8080
```

Access at `http://localhost:8080`

#### Option B: Open directly in browser

Simply open `frontend/index.html` in your web browser.

**Note**: When running locally, update `frontend/js/config.js`:

```javascript
API_BASE_URL: 'http://localhost:5000/api'
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register new user |
| POST | `/api/login` | User login |

### Datasets

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload-dataset` | Upload new dataset |
| GET | `/api/search-datasets` | Search/list datasets |
| GET | `/api/download/<id>` | Download dataset file |
| GET | `/api/visualize/<id>` | Get dataset stats |

### Recommendations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recommendations` | Get AI recommendations |

### Analytics (Admin only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics` | Get platform analytics |

## AWS Free Tier Deployment

### Backend Deployment Options

#### Option 1: AWS Lambda + API Gateway (Serverless)

1. Package the Flask app using Zappa or AWS SAM
2. Deploy to Lambda
3. Configure API Gateway as trigger

#### Option 2: AWS EC2 (t2.micro - Free Tier)

1. Launch EC2 instance (Amazon Linux 2)
2. Install Python, MySQL client
3. Clone project and configure
4. Use Gunicorn + Nginx for production
5. Configure security groups for ports 80, 443

```bash
# On EC2 instance
sudo yum update -y
sudo yum install python3 python3-pip nginx -y

# Clone and setup
git clone <your-repo>
cd dataset-marketplace/backend
pip3 install -r requirements.txt

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend Deployment

#### AWS S3 Static Website Hosting

1. Create S3 bucket for frontend
2. Enable static website hosting
3. Upload frontend files
4. Update `config.js` with production API URL
5. (Optional) Add CloudFront for HTTPS

```bash
# Upload frontend to S3
aws s3 sync frontend/ s3://your-frontend-bucket/ --exclude "*.git*"
```

## Default Admin Account

After running the schema, create an admin user:

```sql
INSERT INTO users (username, email, password_hash, role)
VALUES ('admin', 'admin@example.com', 
        '$2b$12$your-hashed-password', 'admin');
```

Or register through the app and update the role:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
```

## Free Tier Limits

To stay within AWS Free Tier:

- **S3**: 5GB storage, 20,000 GET requests, 2,000 PUT requests/month
- **RDS**: 750 hours t2.micro/month, 20GB storage
- **EC2**: 750 hours t2.micro/month

Recommendations:
- Keep dataset files under 5MB each
- Limit total storage to under 5GB
- Use efficient queries to minimize RDS usage

## Development Notes

### Adding New Features

1. **New API Route**: Add to `routes/` directory
2. **New Service**: Add to `services/` directory
3. **New Frontend Page**: Add HTML, CSS, and JS files

### Database Migrations

For schema changes, create migration scripts:

```sql
-- migrations/001_add_column.sql
ALTER TABLE datasets ADD COLUMN new_column VARCHAR(255);
```

### Testing

```bash
# Run backend tests (if implemented)
cd backend
python -m pytest tests/

# Test API endpoints
curl http://localhost:5000/api/search-datasets
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Check Flask CORS configuration and S3 CORS settings
2. **Database Connection**: Verify MySQL is running and credentials are correct
3. **S3 Access Denied**: Check IAM permissions and bucket policy
4. **JWT Errors**: Ensure SECRET_KEY is set consistently

### Logs

```bash
# Flask logs (development)
tail -f backend/app.log

# Check MySQL logs
sudo tail -f /var/log/mysql/error.log
```

## Security Considerations

1. Never commit `.env` files to version control
2. Use strong passwords for database and JWT secrets
3. Enable HTTPS in production
4. Implement rate limiting for API endpoints
5. Validate and sanitize all user inputs
6. Use parameterized queries (already implemented)

## License

MIT License - Feel free to use for personal or commercial projects.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review AWS documentation for cloud-specific issues
3. Check Flask documentation for backend issues
