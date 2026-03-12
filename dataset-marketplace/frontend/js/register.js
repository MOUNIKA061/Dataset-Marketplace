/* =============================================================================
   Register Page JavaScript
   Handles user registration and form validation
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
    const registerForm = document.getElementById('register-form');
    
    // Attach form submission handler
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Add real-time password strength indicator
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', updatePasswordStrength);
    }
    
    // Add confirm password validation
    const confirmInput = document.getElementById('confirm-password');
    if (confirmInput) {
        confirmInput.addEventListener('input', validatePasswordMatch);
    }
});

// -----------------------------------------------------------------------------
// handleRegister - Process Registration Form Submission
// Validates input and creates new user account
// @param {Event} event - Form submission event
// -----------------------------------------------------------------------------
async function handleRegister(event) {
    // Prevent default form submission
    event.preventDefault();
    
    // Get form input values
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    // Clear any existing error messages
    clearFormErrors();
    
    // Validate username
    if (!username) {
        showFormError('username', 'Username is required');
        return;
    }
    
    if (username.length < 3) {
        showFormError('username', 'Username must be at least 3 characters');
        return;
    }
    
    // Validate email
    if (!email) {
        showFormError('email', 'Email is required');
        return;
    }
    
    if (!validateEmail(email)) {
        showFormError('email', 'Please enter a valid email address');
        return;
    }
    
    // Validate password
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.valid) {
        showFormError('password', passwordValidation.message);
        return;
    }
    
    // Validate password confirmation
    if (password !== confirmPassword) {
        showFormError('confirm-password', 'Passwords do not match');
        return;
    }
    
    try {
        // Show loading state on button
        const submitBtn = document.querySelector('#register-form button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';
        
        // Attempt to register via auth service
        const response = await auth.register(username, email, password);
        
        // Show success message
        showAlert('Account created successfully! Please log in.', 'success', 3000);
        
        // Redirect to login page after brief delay
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 2000);
        
    } catch (error) {
        // Show error message
        showAlert(error.message || 'Registration failed. Please try again.', 'error');
        
        // Reset button state
        const submitBtn = document.querySelector('#register-form button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
    }
}

// -----------------------------------------------------------------------------
// updatePasswordStrength - Show Password Strength Indicator
// Real-time feedback on password quality
// -----------------------------------------------------------------------------
function updatePasswordStrength() {
    // Get password value
    const password = document.getElementById('password').value;
    
    // Find or create strength indicator
    let strengthIndicator = document.getElementById('password-strength');
    
    if (!strengthIndicator) {
        // Create strength indicator element
        strengthIndicator = document.createElement('div');
        strengthIndicator.id = 'password-strength';
        strengthIndicator.className = 'password-strength';
        strengthIndicator.style.cssText = `
            margin-top: 8px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        `;
        
        // Insert after password field
        const passwordField = document.getElementById('password');
        passwordField.parentNode.insertBefore(strengthIndicator, passwordField.nextSibling);
    }
    
    // Calculate password strength
    let strength = 0;
    let label = 'Weak';
    let color = '#e74c3c';
    
    // Length check
    if (password.length >= 6) strength++;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // Complexity checks
    if (/[a-z]/.test(password)) strength++; // Has lowercase
    if (/[A-Z]/.test(password)) strength++; // Has uppercase
    if (/[0-9]/.test(password)) strength++; // Has number
    if (/[^a-zA-Z0-9]/.test(password)) strength++; // Has special char
    
    // Determine label and color based on strength
    if (strength <= 2) {
        label = 'Weak';
        color = '#e74c3c';
    } else if (strength <= 4) {
        label = 'Fair';
        color = '#f39c12';
    } else if (strength <= 5) {
        label = 'Good';
        color = '#3498db';
    } else {
        label = 'Strong';
        color = '#2ecc71';
    }
    
    // Update indicator
    const barWidth = Math.min((strength / 7) * 100, 100);
    strengthIndicator.innerHTML = `
        <div style="flex: 1; height: 4px; background: #ecf0f1; border-radius: 2px;">
            <div style="width: ${barWidth}%; height: 100%; background: ${color}; border-radius: 2px; transition: all 0.3s;"></div>
        </div>
        <span style="color: ${color}; font-weight: 500;">${label}</span>
    `;
}

// -----------------------------------------------------------------------------
// validatePasswordMatch - Check Password Confirmation
// Validates that confirm password matches password
// -----------------------------------------------------------------------------
function validatePasswordMatch() {
    // Get password values
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    // Get confirm field
    const confirmField = document.getElementById('confirm-password');
    
    // Remove existing match indicator
    const existingIndicator = document.getElementById('password-match');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    // Only show indicator if confirm field has value
    if (!confirmPassword) return;
    
    // Create match indicator
    const matchIndicator = document.createElement('div');
    matchIndicator.id = 'password-match';
    matchIndicator.style.cssText = `
        margin-top: 8px;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    `;
    
    // Check if passwords match
    if (password === confirmPassword) {
        matchIndicator.innerHTML = `
            <i class="fas fa-check-circle" style="color: #2ecc71;"></i>
            <span style="color: #2ecc71;">Passwords match</span>
        `;
    } else {
        matchIndicator.innerHTML = `
            <i class="fas fa-times-circle" style="color: #e74c3c;"></i>
            <span style="color: #e74c3c;">Passwords do not match</span>
        `;
    }
    
    // Insert after confirm field
    confirmField.parentNode.insertBefore(matchIndicator, confirmField.nextSibling);
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
        field.style.borderColor = '#e74c3c';
        
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.textContent = message;
        
        // Insert after the field (and any existing indicators)
        const parent = field.parentNode;
        const nextElement = field.nextSibling;
        
        // Skip past any existing indicators
        let insertPoint = nextElement;
        while (insertPoint && (insertPoint.id === 'password-strength' || insertPoint.id === 'password-match')) {
            insertPoint = insertPoint.nextSibling;
        }
        
        parent.insertBefore(errorDiv, insertPoint);
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
    
    // Remove error styling from fields
    const fields = document.querySelectorAll('.form-control');
    fields.forEach(field => {
        field.classList.remove('error');
        field.style.borderColor = '';
    });
}
