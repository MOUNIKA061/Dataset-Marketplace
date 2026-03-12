/* =============================================================================
   Authentication Module - User Authentication Handler
   Manages user login, registration, logout, and session state
   ============================================================================= */

// -----------------------------------------------------------------------------
// Auth Service Class
// Handles all authentication-related operations
// -----------------------------------------------------------------------------

class AuthService {
    // -------------------------------------------------------------------------
    // Constructor
    // Initialize auth service and set up event listeners
    // -------------------------------------------------------------------------
    constructor() {
        // Reference to the API service for making requests
        this.api = api;
        
        // Initialize user state from localStorage if available
        this.currentUser = this.loadUserFromStorage();
    }
    
    // -------------------------------------------------------------------------
    // loadUserFromStorage - Load User Data
    // Retrieves stored user data from localStorage
    // @returns {Object|null} User data or null if not found
    // -------------------------------------------------------------------------
    loadUserFromStorage() {
        try {
            // Get user data from localStorage
            const userData = localStorage.getItem(CONFIG?.USER_DATA_KEY || 'user_data');
            
            // Parse and return if exists
            return userData ? JSON.parse(userData) : null;
        } catch (error) {
            // Handle JSON parse errors
            console.error('Error loading user from storage:', error);
            return null;
        }
    }
    
    // -------------------------------------------------------------------------
    // saveUserToStorage - Save User Data
    // Stores user data in localStorage for persistence
    // @param {Object} user - User data to store
    // -------------------------------------------------------------------------
    saveUserToStorage(user) {
        // Convert user object to JSON string and store
        localStorage.setItem(CONFIG?.USER_DATA_KEY || 'user_data', JSON.stringify(user));
    }
    
    // -------------------------------------------------------------------------
    // clearUserFromStorage - Clear User Data
    // Removes user data from localStorage (for logout)
    // -------------------------------------------------------------------------
    clearUserFromStorage() {
        // Remove user data from localStorage
        localStorage.removeItem(CONFIG?.USER_DATA_KEY || 'user_data');
    }
    
    // -------------------------------------------------------------------------
    // register - Register New User
    // Creates a new user account
    // @param {string} username - Desired username
    // @param {string} email - User's email address
    // @param {string} password - User's password
    // @returns {Promise} Registration result
    // -------------------------------------------------------------------------
    async register(username, email, password) {
        try {
            // Make registration API call
            const response = await this.api.post('/register', {
                username,    // Username for the new account
                email,       // Email address (must be unique)
                password     // Password (will be hashed on backend)
            }, false);      // No auth required for registration
            
            // Return success response
            return response;
        } catch (error) {
            // Re-throw error for handling by caller
            throw error;
        }
    }
    
    // -------------------------------------------------------------------------
    // login - User Login
    // Authenticates user and stores session
    // @param {string} email - User's email address
    // @param {string} password - User's password
    // @returns {Promise} Login result with user data and token
    // -------------------------------------------------------------------------
    async login(email, password) {
        try {
            // Make login API call
            const response = await this.api.post('/login', {
                email,       // Email for authentication
                password     // Password to verify
            }, false);      // No auth required for login
            
            // If login successful, store token and user data
            if (response.token) {
                // Store JWT token
                this.api.setAuthToken(response.token);
                
                // Store user data
                this.currentUser = response.user;
                this.saveUserToStorage(response.user);
            }
            
            // Return success response
            return response;
        } catch (error) {
            // Re-throw error for handling by caller
            throw error;
        }
    }
    
    // -------------------------------------------------------------------------
    // logout - User Logout
    // Clears session and redirects to login
    // -------------------------------------------------------------------------
    logout() {
        // Clear authentication token
        this.api.clearAuthToken();
        
        // Clear stored user data
        this.clearUserFromStorage();
        
        // Clear current user reference
        this.currentUser = null;
        
        // Redirect to login page
        window.location.href = 'index.html';
    }
    
    // -------------------------------------------------------------------------
    // isAuthenticated - Check Authentication Status
    // Determines if user is currently logged in
    // @returns {boolean} True if authenticated
    // -------------------------------------------------------------------------
    isAuthenticated() {
        // Check if both token and user data exist
        const hasToken = !!this.api.getAuthToken();
        const hasUser = !!this.currentUser;
        
        return hasToken && hasUser;
    }
    
    // -------------------------------------------------------------------------
    // getCurrentUser - Get Current User
    // Returns the currently logged in user's data
    // @returns {Object|null} User data or null
    // -------------------------------------------------------------------------
    getCurrentUser() {
        return this.currentUser;
    }
    
    // -------------------------------------------------------------------------
    // isAdmin - Check Admin Status
    // Determines if current user has admin role
    // @returns {boolean} True if user is admin
    // -------------------------------------------------------------------------
    isAdmin() {
        // Check if user exists and has admin role
        return this.currentUser?.role === 'admin';
    }
    
    // -------------------------------------------------------------------------
    // isOwner - Check Owner Status
    // Determines if current user has owner role
    // @returns {boolean} True if user is owner
    // -------------------------------------------------------------------------
    isOwner() {
        // Owner role can also do owner things
        return this.currentUser?.role === 'owner' || this.isAdmin();
    }
    
    // -------------------------------------------------------------------------
    // requireAuth - Require Authentication
    // Redirects to login if not authenticated
    // Call this at the start of protected pages
    // -------------------------------------------------------------------------
    requireAuth() {
        // If not authenticated, redirect to login
        if (!this.isAuthenticated()) {
            window.location.href = 'index.html';
            return false;
        }
        return true;
    }
    
    // -------------------------------------------------------------------------
    // requireAdmin - Require Admin Role
    // Redirects if user is not an admin
    // Call this at the start of admin-only pages
    // -------------------------------------------------------------------------
    requireAdmin() {
        // First check authentication
        if (!this.requireAuth()) {
            return false;
        }
        
        // Then check admin role
        if (!this.isAdmin()) {
            window.location.href = 'search.html';
            return false;
        }
        
        return true;
    }
    
    // -------------------------------------------------------------------------
    // updateNavbar - Update Navigation Bar
    // Updates the navbar to show user info and logout button
    // Call this after page load on authenticated pages
    // -------------------------------------------------------------------------
    updateNavbar() {
        // Update user greeting
        const userGreeting = document.getElementById('user-greeting');
        if (userGreeting && this.currentUser) {
            userGreeting.textContent = `Hi, ${this.currentUser.username}`;
            userGreeting.style.display = 'inline-block';
        }
        
        // Hide login link when authenticated
        const loginLink = document.getElementById('login-link');
        if (loginLink) {
            loginLink.style.display = this.isAuthenticated() ? 'none' : 'inline-block';
        }
        
        // Show logout button when authenticated
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.style.display = this.isAuthenticated() ? 'inline-block' : 'none';
            logoutBtn.onclick = () => this.logout();
        }
        
        // Show upload link for owners and admins
        const uploadLink = document.getElementById('upload-link');
        if (uploadLink) {
            const canUpload = this.currentUser && 
                (this.currentUser.role === 'owner' || this.currentUser.role === 'admin');
            uploadLink.style.display = canUpload ? 'inline-block' : 'none';
        }
        
        // Show admin link only for admins
        const adminLink = document.getElementById('admin-link');
        if (adminLink) {
            adminLink.style.display = this.isAdmin() ? 'inline-block' : 'none';
        }
        
        // Legacy support for user-info container
        const userInfoContainer = document.getElementById('user-info');
        if (userInfoContainer && this.currentUser) {
            const roleBadge = this.currentUser.role === 'admin' 
                ? '<span class="badge badge-admin">Admin</span>'
                : this.currentUser.role === 'owner'
                    ? '<span class="badge badge-owner">Owner</span>'
                    : '<span class="badge badge-user">User</span>';
            
            userInfoContainer.innerHTML = `
                <span class="user-name">${this.currentUser.username} ${roleBadge}</span>
                <button class="logout-btn" onclick="auth.logout()">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </button>
            `;
        }
    }
}

// -----------------------------------------------------------------------------
// Create and export singleton instance
// Use this instance throughout the application
// -----------------------------------------------------------------------------
const auth = new AuthService();
