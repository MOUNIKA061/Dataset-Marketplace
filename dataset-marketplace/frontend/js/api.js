/* =============================================================================
   API Service - HTTP Request Handler
   Centralized service for making API calls to the Flask backend
   Handles authentication, error handling, and response parsing
   ============================================================================= */

// -----------------------------------------------------------------------------
// API Service Class
// Singleton pattern to ensure consistent request handling
// -----------------------------------------------------------------------------

class ApiService {
    // -------------------------------------------------------------------------
    // Constructor
    // Initialize the API service with base URL from config
    // -------------------------------------------------------------------------
    constructor() {
        // Get base URL from config, default to localhost if not set
        this.baseUrl = CONFIG?.API_BASE_URL || 'http://localhost:5000/api';
    }
    
    // -------------------------------------------------------------------------
    // getAuthToken - Retrieve JWT Token
    // Returns the stored authentication token or null
    // -------------------------------------------------------------------------
    getAuthToken() {
        // Get token from localStorage using the configured key
        return localStorage.getItem(CONFIG?.AUTH_TOKEN_KEY || 'auth_token');
    }
    
    // -------------------------------------------------------------------------
    // setAuthToken - Store JWT Token
    // Saves the authentication token to localStorage
    // @param {string} token - The JWT token to store
    // -------------------------------------------------------------------------
    setAuthToken(token) {
        // Store token in localStorage for persistence across page reloads
        localStorage.setItem(CONFIG?.AUTH_TOKEN_KEY || 'auth_token', token);
    }
    
    // -------------------------------------------------------------------------
    // clearAuthToken - Remove JWT Token
    // Clears the stored authentication token (for logout)
    // -------------------------------------------------------------------------
    clearAuthToken() {
        // Remove token from localStorage
        localStorage.removeItem(CONFIG?.AUTH_TOKEN_KEY || 'auth_token');
    }
    
    // -------------------------------------------------------------------------
    // getHeaders - Build Request Headers
    // Creates the headers object for API requests
    // @param {boolean} includeAuth - Whether to include the auth token
    // @param {boolean} isFormData - Whether the request is FormData (no Content-Type)
    // @returns {Object} Headers object
    // -------------------------------------------------------------------------
    getHeaders(includeAuth = true, isFormData = false) {
        // Initialize headers object
        const headers = {};
        
        // Add Content-Type for non-FormData requests
        // FormData sets its own Content-Type with boundary
        if (!isFormData) {
            headers['Content-Type'] = 'application/json';
        }
        
        // Add Authorization header if token exists and auth is required
        if (includeAuth) {
            const token = this.getAuthToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }
        
        return headers;
    }
    
    // -------------------------------------------------------------------------
    // handleResponse - Process API Response
    // Parses the response and handles errors
    // @param {Response} response - The fetch Response object
    // @returns {Promise} Resolved with data or rejected with error
    // -------------------------------------------------------------------------
    async handleResponse(response) {
        // Try to parse response as JSON
        let data;
        try {
            data = await response.json();
        } catch (e) {
            // If JSON parsing fails, create a generic response
            data = { message: 'Unknown error occurred' };
        }
        
        // Check if response was successful (status 200-299)
        if (response.ok) {
            return data;
        }
        
        // Handle specific error status codes
        if (response.status === 401) {
            // Unauthorized - token expired or invalid
            this.clearAuthToken();
            // Redirect to login page
            window.location.href = 'index.html';
        }
        
        // Throw error with message from response
        throw new Error(data.error || data.message || 'Request failed');
    }
    
    // -------------------------------------------------------------------------
    // get - HTTP GET Request
    // Fetches data from the specified endpoint
    // @param {string} endpoint - The API endpoint (without base URL)
    // @param {boolean} requireAuth - Whether authentication is required
    // @returns {Promise} Response data
    // -------------------------------------------------------------------------
    async get(endpoint, requireAuth = true) {
        try {
            // Make GET request to the endpoint
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'GET',                           // HTTP method
                headers: this.getHeaders(requireAuth)    // Request headers
            });
            
            // Process and return the response
            return await this.handleResponse(response);
        } catch (error) {
            // Log error for debugging
            console.error(`GET ${endpoint} failed:`, error);
            throw error;
        }
    }
    
    // -------------------------------------------------------------------------
    // post - HTTP POST Request
    // Sends data to the specified endpoint
    // @param {string} endpoint - The API endpoint
    // @param {Object} data - The data to send
    // @param {boolean} requireAuth - Whether authentication is required
    // @returns {Promise} Response data
    // -------------------------------------------------------------------------
    async post(endpoint, data, requireAuth = true) {
        try {
            // Make POST request with JSON body
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',                          // HTTP method
                headers: this.getHeaders(requireAuth),   // Request headers
                body: JSON.stringify(data)               // Convert data to JSON string
            });
            
            // Process and return the response
            return await this.handleResponse(response);
        } catch (error) {
            // Log error for debugging
            console.error(`POST ${endpoint} failed:`, error);
            throw error;
        }
    }
    
    // -------------------------------------------------------------------------
    // postFormData - HTTP POST with FormData
    // Sends file uploads and form data
    // @param {string} endpoint - The API endpoint
    // @param {FormData} formData - The FormData object
    // @param {boolean} requireAuth - Whether authentication is required
    // @returns {Promise} Response data
    // -------------------------------------------------------------------------
    async postFormData(endpoint, formData, requireAuth = true) {
        try {
            // Make POST request with FormData body
            // Note: Don't set Content-Type header - browser sets it with boundary
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',                                  // HTTP method
                headers: this.getHeaders(requireAuth, true),     // Headers without Content-Type
                body: formData                                   // FormData body (not stringified)
            });
            
            // Process and return the response
            return await this.handleResponse(response);
        } catch (error) {
            // Log error for debugging
            console.error(`POST FormData ${endpoint} failed:`, error);
            throw error;
        }
    }
    
    // -------------------------------------------------------------------------
    // put - HTTP PUT Request
    // Updates data at the specified endpoint
    // @param {string} endpoint - The API endpoint
    // @param {Object} data - The data to update
    // @param {boolean} requireAuth - Whether authentication is required
    // @returns {Promise} Response data
    // -------------------------------------------------------------------------
    async put(endpoint, data, requireAuth = true) {
        try {
            // Make PUT request with JSON body
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'PUT',                           // HTTP method
                headers: this.getHeaders(requireAuth),   // Request headers
                body: JSON.stringify(data)               // Convert data to JSON string
            });
            
            // Process and return the response
            return await this.handleResponse(response);
        } catch (error) {
            // Log error for debugging
            console.error(`PUT ${endpoint} failed:`, error);
            throw error;
        }
    }
    
    // -------------------------------------------------------------------------
    // delete - HTTP DELETE Request
    // Removes data at the specified endpoint
    // @param {string} endpoint - The API endpoint
    // @param {boolean} requireAuth - Whether authentication is required
    // @returns {Promise} Response data
    // -------------------------------------------------------------------------
    async delete(endpoint, requireAuth = true) {
        try {
            // Make DELETE request
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'DELETE',                        // HTTP method
                headers: this.getHeaders(requireAuth)    // Request headers
            });
            
            // Process and return the response
            return await this.handleResponse(response);
        } catch (error) {
            // Log error for debugging
            console.error(`DELETE ${endpoint} failed:`, error);
            throw error;
        }
    }
    
    // -------------------------------------------------------------------------
    // downloadFile - Download File from API
    // Handles file downloads with proper blob handling
    // @param {string} endpoint - The API endpoint
    // @param {string} filename - The filename for the download
    // -------------------------------------------------------------------------
    async downloadFile(endpoint, filename) {
        try {
            // Make GET request for file
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'GET',
                headers: this.getHeaders(true)
            });
            
            // Check for errors
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Download failed');
            }
            
            // Get the response as a blob
            const blob = await response.blob();
            
            // Create a temporary URL for the blob
            const url = window.URL.createObjectURL(blob);
            
            // Create a temporary anchor element for download
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;                       // Set download filename
            document.body.appendChild(a);                // Add to DOM
            a.click();                                   // Trigger download
            
            // Clean up
            window.URL.revokeObjectURL(url);             // Release blob URL
            document.body.removeChild(a);                // Remove anchor element
            
            return { success: true };
        } catch (error) {
            console.error(`Download ${endpoint} failed:`, error);
            throw error;
        }
    }
}

// -----------------------------------------------------------------------------
// Create and export singleton instance
// Use this instance throughout the application
// -----------------------------------------------------------------------------
const api = new ApiService();
