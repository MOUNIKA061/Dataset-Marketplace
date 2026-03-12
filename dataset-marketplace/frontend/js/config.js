/* =============================================================================
   Configuration - Frontend Application Settings
   Centralized configuration for API endpoints and application constants
   ============================================================================= */

// -----------------------------------------------------------------------------
// API Configuration
// Base URL for all backend API calls
// Change this when deploying to production
// -----------------------------------------------------------------------------

const CONFIG = {
    // Base URL for API endpoints
    // For local development, this points to Flask running on port 5000
    // For production, change to your deployed API URL (e.g., AWS API Gateway)
    API_BASE_URL: 'http://localhost:5000/api',
    
    // Authentication token key for localStorage
    // Used to store and retrieve the JWT token
    AUTH_TOKEN_KEY: 'auth_token',
    
    // User data key for localStorage
    // Stores the current user's information
    USER_DATA_KEY: 'user_data',
    
    // Maximum file size for uploads (5MB in bytes)
    // Keeping it small to stay within AWS free tier
    MAX_FILE_SIZE: 5 * 1024 * 1024,
    
    // Allowed file extensions for dataset uploads
    ALLOWED_EXTENSIONS: ['.csv', '.json'],
    
    // Default number of rows to show in preview
    PREVIEW_ROWS: 10,
    
    // Chart colors for visualizations
    CHART_COLORS: {
        primary: '#3498db',      // Blue - main color
        secondary: '#2ecc71',    // Green - success
        tertiary: '#f39c12',     // Orange - warning
        quaternary: '#e74c3c',   // Red - danger
        quinary: '#9b59b6',      // Purple - accent
        senary: '#1abc9c',       // Teal - accent
        septenary: '#34495e',    // Dark gray - neutral
        octonary: '#e67e22'      // Dark orange - accent
    },
    
    // Pagination settings
    ITEMS_PER_PAGE: 12,
    
    // Debounce delay for search (milliseconds)
    SEARCH_DEBOUNCE: 300
};

// Freeze config object to prevent accidental modifications
Object.freeze(CONFIG);
Object.freeze(CONFIG.CHART_COLORS);
