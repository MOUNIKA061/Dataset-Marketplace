-- ============================================================================
-- Dataset Marketplace - Database Schema
-- MySQL Database Schema for Users, Datasets, and Downloads tables
-- ============================================================================

-- Create database if not exists
-- Uncomment the following lines if creating a new database
-- CREATE DATABASE IF NOT EXISTS dataset_marketplace;
-- USE dataset_marketplace;

-- ============================================================================
-- USERS TABLE
-- Stores user account information with role-based access control
-- Roles: 'admin' - full access, 'owner' - can upload datasets, 'user' - can download
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    -- Primary key: auto-incremented unique identifier for each user
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Username: unique identifier for login, max 80 characters
    username VARCHAR(80) NOT NULL UNIQUE,
    
    -- Email: unique email address for account recovery, max 120 characters
    email VARCHAR(120) NOT NULL UNIQUE,
    
    -- Password: hashed password using werkzeug security, max 255 characters
    password_hash VARCHAR(255) NOT NULL,
    
    -- Role: defines user permissions (admin, owner, user)
    -- Default is 'user' for new registrations
    role ENUM('admin', 'owner', 'user') DEFAULT 'user',
    
    -- Created timestamp: automatically set when record is inserted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Updated timestamp: automatically updated on record modification
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Index on username for faster login queries
    INDEX idx_username (username),
    
    -- Index on email for faster lookups
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- DATASETS TABLE
-- Stores metadata about uploaded datasets
-- Full files are stored in AWS S3, only metadata and preview stored here
-- ============================================================================
CREATE TABLE IF NOT EXISTS datasets (
    -- Primary key: auto-incremented unique identifier for each dataset
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Foreign key: references the user who uploaded this dataset
    owner_id INT NOT NULL,
    
    -- Title: human-readable name for the dataset, max 200 characters
    title VARCHAR(200) NOT NULL,
    
    -- Description: detailed description of the dataset contents
    description TEXT,
    
    -- Tags: comma-separated keywords for search and recommendations
    -- Example: "finance,stocks,market,historical"
    tags VARCHAR(500),
    
    -- File type: original file format (csv, json, xlsx, etc.)
    file_type VARCHAR(20) NOT NULL,
    
    -- File size: size in bytes of the original file
    file_size BIGINT NOT NULL,
    
    -- Row count: number of rows/records in the dataset
    row_count INT DEFAULT 0,
    
    -- Column count: number of columns/fields in the dataset
    column_count INT DEFAULT 0,
    
    -- S3 key: the object key/path in AWS S3 bucket
    -- Format: "datasets/{user_id}/{timestamp}_{filename}"
    s3_key VARCHAR(500) NOT NULL,
    
    -- JSON snippet: first 100 rows stored as JSON for preview
    -- Stored as MEDIUMTEXT to handle larger previews (up to 16MB)
    json_snippet MEDIUMTEXT,
    
    -- Column info: JSON containing column names and data types
    -- Example: [{"name": "price", "type": "float"}, {"name": "date", "type": "string"}]
    column_info JSON,
    
    -- Download count: tracks popularity, incremented on each download
    download_count INT DEFAULT 0,
    
    -- Is public: whether dataset is visible to all users
    is_public BOOLEAN DEFAULT TRUE,
    
    -- Created timestamp: when dataset was uploaded
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Updated timestamp: when metadata was last modified
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraint linking to users table
    CONSTRAINT fk_dataset_owner FOREIGN KEY (owner_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    
    -- Index on owner_id for faster queries by user
    INDEX idx_owner (owner_id),
    
    -- Full-text index on title, description, tags for search functionality
    FULLTEXT INDEX idx_search (title, description, tags),
    
    -- Index on download_count for popularity sorting
    INDEX idx_popularity (download_count DESC),
    
    -- Index on created_at for recent datasets
    INDEX idx_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- DOWNLOADS TABLE
-- Logs all download events for analytics and tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS downloads (
    -- Primary key: auto-incremented unique identifier for each download event
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Foreign key: references the dataset that was downloaded
    dataset_id INT NOT NULL,
    
    -- Foreign key: references the user who downloaded (NULL for anonymous)
    user_id INT,
    
    -- IP address: for rate limiting and analytics (IPv4 or IPv6)
    ip_address VARCHAR(45),
    
    -- User agent: browser/client information for analytics
    user_agent VARCHAR(500),
    
    -- Downloaded timestamp: when the download occurred
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint linking to datasets table
    CONSTRAINT fk_download_dataset FOREIGN KEY (dataset_id) 
        REFERENCES datasets(id) ON DELETE CASCADE,
    
    -- Foreign key constraint linking to users table
    CONSTRAINT fk_download_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE SET NULL,
    
    -- Index on dataset_id for download count queries
    INDEX idx_dataset (dataset_id),
    
    -- Index on user_id for user download history
    INDEX idx_user (user_id),
    
    -- Index on downloaded_at for time-based analytics
    INDEX idx_downloaded_at (downloaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- SAMPLE DATA (Optional - for testing)
-- Uncomment to insert sample admin user
-- ============================================================================
-- INSERT INTO users (username, email, password_hash, role) VALUES
-- ('admin', 'admin@example.com', 'pbkdf2:sha256:260000$...', 'admin');

-- ============================================================================
-- USEFUL QUERIES FOR TESTING
-- ============================================================================

-- View all users:
-- SELECT id, username, email, role, created_at FROM users;

-- View all datasets with owner info:
-- SELECT d.id, d.title, d.tags, d.download_count, u.username as owner
-- FROM datasets d JOIN users u ON d.owner_id = u.id;

-- View download statistics:
-- SELECT d.title, COUNT(dl.id) as downloads, MAX(dl.downloaded_at) as last_download
-- FROM datasets d LEFT JOIN downloads dl ON d.id = dl.dataset_id
-- GROUP BY d.id ORDER BY downloads DESC;

-- Search datasets by tag:
-- SELECT * FROM datasets WHERE MATCH(title, description, tags) AGAINST('finance');
