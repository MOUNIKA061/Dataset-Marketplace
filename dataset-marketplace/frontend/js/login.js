/* =============================================================================
   Login Page JavaScript
   Handles user authentication and login form submission
   ============================================================================= */

// -----------------------------------------------------------------------------
// DOM Ready Handler
// Executes when the page has fully loaded
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in
    // If so, redirect to search page
    if (auth.isAuthenticated()) {
        window.location.href = 'search.html';
        return;
    }
    
    // Get form element reference
    const loginForm = document.getElementById('login-form');
    
    // Attach form submission handler
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
});

// -----------------------------------------------------------------------------
// handleLogin - Process Login Form Submission
// Validates input and authenticates user with backend
// @param {Event} event - Form submission event
// -----------------------------------------------------------------------------
async function handleLogin(event) {
    // Prevent default form submission (page reload)
    event.preventDefault();
    
    // Get form input values
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    
    // Clear any existing error messages
    clearFormErrors();
    
    // Validate email format
    if (!email) {
        showFormError('email', 'Email is required');
        return;
    }
    
    if (!validateEmail(email)) {
        showFormError('email', 'Please enter a valid email address');
        return;
    }
    
    // Validate password is provided
    if (!password) {
        showFormError('password', 'Password is required');
        return;
    }
    
    try {
        // Show loading state on button
        const submitBtn = document.querySelector('#login-form button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
        
        // Attempt to log in via auth service
        const response = await auth.login(email, password);
        
        // Show success message
        showAlert('Login successful! Redirecting...', 'success', 2000);
        
        // Redirect to search page after brief delay
        setTimeout(() => {
            window.location.href = 'search.html';
        }, 1000);
        
    } catch (error) {
        // Show error message
        showAlert(error.message || 'Login failed. Please check your credentials.', 'error');
        
        // Reset button state
        const submitBtn = document.querySelector('#login-form button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
    }
}

// -----------------------------------------------------------------------------
// showFormError - Display Field-Level Error
// Shows error message below specific form field
// @param {string} fieldId - ID of the form field
// @param {string} message - Error message to display
// -----------------------------------------------------------------------------
function showFormError(fieldId, message) {
    // Get the input field
    const field = document.getElementById(fieldId);
    
    if (field) {
        // Add error class to field
        field.classList.add('error');
        
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.textContent = message;
        
        // Insert after the field
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    }
}

// -----------------------------------------------------------------------------
// clearFormErrors - Remove All Form Errors
// Clears all error messages and styling from the form
// -----------------------------------------------------------------------------
function clearFormErrors() {
    // Remove all error messages
    const errors = document.querySelectorAll('.form-error');
    errors.forEach(error => error.remove());
    
    // Remove error class from fields
    const fields = document.querySelectorAll('.form-control.error');
    fields.forEach(field => field.classList.remove('error'));
}
