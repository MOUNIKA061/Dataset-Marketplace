/* =============================================================================
   Utility Functions - Common Helper Functions
   Reusable utility functions for DOM manipulation, formatting, and validation
   ============================================================================= */

// -----------------------------------------------------------------------------
// UI Utilities
// Functions for showing/hiding loading states and alerts
// -----------------------------------------------------------------------------

/**
 * showLoading - Display Loading Overlay
 * Shows a full-screen loading indicator with optional message
 * @param {string} message - Optional loading message to display
 */
function showLoading(message = 'Loading...') {
    // Check if loading overlay already exists
    let overlay = document.getElementById('loading-overlay');
    
    if (!overlay) {
        // Create loading overlay element
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="spinner"></div>
            <div class="loading-text">${message}</div>
        `;
        
        // Add to the document body
        document.body.appendChild(overlay);
    } else {
        // Update message if overlay exists
        const textEl = overlay.querySelector('.loading-text');
        if (textEl) {
            textEl.textContent = message;
        }
    }
}

/**
 * hideLoading - Hide Loading Overlay
 * Removes the loading overlay from the page
 */
function hideLoading() {
    // Find the loading overlay
    const overlay = document.getElementById('loading-overlay');
    
    // Remove if exists
    if (overlay) {
        overlay.remove();
    }
}

/**
 * showAlert - Display Alert Message
 * Shows a styled alert message to the user
 * @param {string} message - The message to display
 * @param {string} type - Alert type: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in ms before auto-hide (0 = no auto-hide)
 */
function showAlert(message, type = 'info', duration = 5000) {
    // Get or create alerts container
    let alertsContainer = document.getElementById('alerts-container');
    
    if (!alertsContainer) {
        // Create container for alerts
        alertsContainer = document.createElement('div');
        alertsContainer.id = 'alerts-container';
        alertsContainer.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 2000;
            max-width: 400px;
        `;
        document.body.appendChild(alertsContainer);
    }
    
    // Create unique ID for this alert
    const alertId = 'alert-' + Date.now();
    
    // Select icon based on type
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    // Create alert element
    const alert = document.createElement('div');
    alert.id = alertId;
    alert.className = `alert alert-${type} alert-dismissible`;
    alert.style.marginBottom = '10px';
    alert.innerHTML = `
        <i class="${icons[type] || icons.info}"></i>
        <span>${message}</span>
        <button class="alert-close" onclick="dismissAlert('${alertId}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to container
    alertsContainer.appendChild(alert);
    
    // Auto-dismiss after duration (if set)
    if (duration > 0) {
        setTimeout(() => {
            dismissAlert(alertId);
        }, duration);
    }
}

/**
 * dismissAlert - Remove Alert
 * Removes a specific alert from the page
 * @param {string} alertId - The ID of the alert to remove
 */
function dismissAlert(alertId) {
    // Find the alert element
    const alert = document.getElementById(alertId);
    
    if (alert) {
        // Add fade-out animation
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(100%)';
        alert.style.transition = 'all 0.3s ease';
        
        // Remove after animation
        setTimeout(() => {
            alert.remove();
        }, 300);
    }
}

// -----------------------------------------------------------------------------
// Data Formatting Utilities
// Functions for formatting data for display
// -----------------------------------------------------------------------------

/**
 * formatFileSize - Format Bytes to Human Readable
 * Converts bytes to KB, MB, GB with proper units
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size string
 */
function formatFileSize(bytes) {
    // Handle zero or invalid input
    if (!bytes || bytes === 0) return '0 Bytes';
    
    // Define size units
    const units = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    // Calculate the appropriate unit
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    // Format and return
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + units[i];
}

/**
 * formatDate - Format Date String
 * Converts ISO date string to readable format
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    // Handle missing date
    if (!dateString) return 'Unknown';
    
    // Parse the date
    const date = new Date(dateString);
    
    // Check for invalid date
    if (isNaN(date.getTime())) return 'Invalid date';
    
    // Format options
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    // Return formatted date
    return date.toLocaleDateString('en-US', options);
}

/**
 * formatNumber - Format Number with Commas
 * Adds thousand separators to numbers
 * @param {number} num - Number to format
 * @returns {string} Formatted number string
 */
function formatNumber(num) {
    // Handle invalid input
    if (num === null || num === undefined) return '0';
    
    // Convert to number if string
    const number = typeof num === 'string' ? parseFloat(num) : num;
    
    // Check for NaN
    if (isNaN(number)) return '0';
    
    // Format with locale
    return number.toLocaleString('en-US');
}

/**
 * truncateText - Truncate Long Text
 * Shortens text to specified length with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength = 100) {
    // Handle missing text
    if (!text) return '';
    
    // Return as-is if short enough
    if (text.length <= maxLength) return text;
    
    // Truncate and add ellipsis
    return text.substring(0, maxLength).trim() + '...';
}

// -----------------------------------------------------------------------------
// Validation Utilities
// Functions for validating user input
// -----------------------------------------------------------------------------

/**
 * validateEmail - Validate Email Format
 * Checks if email address has valid format
 * @param {string} email - Email to validate
 * @returns {boolean} True if valid
 */
function validateEmail(email) {
    // Email regex pattern
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    return emailRegex.test(email);
}

/**
 * validatePassword - Validate Password Strength
 * Checks if password meets minimum requirements
 * @param {string} password - Password to validate
 * @returns {Object} Validation result with status and message
 */
function validatePassword(password) {
    // Minimum length check
    if (password.length < 6) {
        return {
            valid: false,
            message: 'Password must be at least 6 characters long'
        };
    }
    
    // Password is valid
    return {
        valid: true,
        message: 'Password is valid'
    };
}

/**
 * validateFile - Validate File for Upload
 * Checks file size and extension
 * @param {File} file - File to validate
 * @returns {Object} Validation result
 */
function validateFile(file) {
    // Check if file exists
    if (!file) {
        return {
            valid: false,
            message: 'No file selected'
        };
    }
    
    // Get max file size from config
    const maxSize = CONFIG?.MAX_FILE_SIZE || 5 * 1024 * 1024;
    
    // Check file size
    if (file.size > maxSize) {
        return {
            valid: false,
            message: `File size exceeds ${formatFileSize(maxSize)} limit`
        };
    }
    
    // Get allowed extensions from config
    const allowedExt = CONFIG?.ALLOWED_EXTENSIONS || ['.csv', '.json'];
    
    // Get file extension
    const fileName = file.name.toLowerCase();
    const ext = '.' + fileName.split('.').pop();
    
    // Check extension
    if (!allowedExt.includes(ext)) {
        return {
            valid: false,
            message: `Only ${allowedExt.join(', ')} files are allowed`
        };
    }
    
    // File is valid
    return {
        valid: true,
        message: 'File is valid'
    };
}

// -----------------------------------------------------------------------------
// DOM Utilities
// Functions for DOM manipulation
// -----------------------------------------------------------------------------

/**
 * createElement - Create DOM Element
 * Helper to create element with classes and attributes
 * @param {string} tag - HTML tag name
 * @param {Object} options - Options (className, id, innerHTML, attributes)
 * @returns {HTMLElement} Created element
 */
function createElement(tag, options = {}) {
    // Create the element
    const element = document.createElement(tag);
    
    // Add class name if provided
    if (options.className) {
        element.className = options.className;
    }
    
    // Add ID if provided
    if (options.id) {
        element.id = options.id;
    }
    
    // Add innerHTML if provided
    if (options.innerHTML) {
        element.innerHTML = options.innerHTML;
    }
    
    // Add text content if provided
    if (options.textContent) {
        element.textContent = options.textContent;
    }
    
    // Add attributes if provided
    if (options.attributes) {
        Object.entries(options.attributes).forEach(([key, value]) => {
            element.setAttribute(key, value);
        });
    }
    
    // Add event listeners if provided
    if (options.events) {
        Object.entries(options.events).forEach(([event, handler]) => {
            element.addEventListener(event, handler);
        });
    }
    
    return element;
}

/**
 * debounce - Debounce Function Calls
 * Delays function execution until after specified wait time
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait = 300) {
    // Store timeout ID
    let timeoutId;
    
    // Return debounced function
    return function executedFunction(...args) {
        // Clear existing timeout
        clearTimeout(timeoutId);
        
        // Set new timeout
        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, wait);
    };
}

/**
 * escapeHtml - Escape HTML Characters
 * Prevents XSS by escaping special characters
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    // Handle non-string input
    if (typeof text !== 'string') return '';
    
    // Map of characters to escape
    const escapeMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    // Replace each character
    return text.replace(/[&<>"']/g, char => escapeMap[char]);
}

// -----------------------------------------------------------------------------
// URL Utilities
// Functions for URL manipulation
// -----------------------------------------------------------------------------

/**
 * getUrlParam - Get URL Parameter
 * Retrieves parameter value from URL query string
 * @param {string} param - Parameter name
 * @returns {string|null} Parameter value or null
 */
function getUrlParam(param) {
    // Parse URL search params
    const urlParams = new URLSearchParams(window.location.search);
    
    // Return parameter value
    return urlParams.get(param);
}

/**
 * setUrlParam - Set URL Parameter
 * Updates URL with new parameter without page reload
 * @param {string} param - Parameter name
 * @param {string} value - Parameter value
 */
function setUrlParam(param, value) {
    // Parse current URL params
    const urlParams = new URLSearchParams(window.location.search);
    
    // Set or delete parameter
    if (value) {
        urlParams.set(param, value);
    } else {
        urlParams.delete(param);
    }
    
    // Build new URL
    const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
    
    // Update URL without reload
    window.history.replaceState({}, '', newUrl);
}

// -----------------------------------------------------------------------------
// Data Parsing Utilities
// Functions for parsing and processing data
// -----------------------------------------------------------------------------

/**
 * parseCSV - Parse CSV String to Array
 * Converts CSV string to array of objects
 * @param {string} csvString - CSV content
 * @param {number} limit - Maximum rows to parse (0 = all)
 * @returns {Array} Array of row objects
 */
function parseCSV(csvString, limit = 0) {
    // Split into lines
    const lines = csvString.trim().split('\n');
    
    // Handle empty CSV
    if (lines.length === 0) return [];
    
    // Parse headers (first line)
    const headers = parseCSVLine(lines[0]);
    
    // Result array
    const result = [];
    
    // Determine how many rows to parse
    const rowCount = limit > 0 ? Math.min(limit + 1, lines.length) : lines.length;
    
    // Parse data rows
    for (let i = 1; i < rowCount; i++) {
        // Parse line values
        const values = parseCSVLine(lines[i]);
        
        // Create row object
        const row = {};
        headers.forEach((header, index) => {
            row[header] = values[index] || '';
        });
        
        result.push(row);
    }
    
    return result;
}

/**
 * parseCSVLine - Parse Single CSV Line
 * Handles quoted values and commas within quotes
 * @param {string} line - CSV line to parse
 * @returns {Array} Array of values
 */
function parseCSVLine(line) {
    // Result array
    const result = [];
    
    // Current value being built
    let current = '';
    
    // Whether we're inside quotes
    let inQuotes = false;
    
    // Iterate through characters
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        const nextChar = line[i + 1];
        
        if (char === '"') {
            if (inQuotes && nextChar === '"') {
                // Escaped quote
                current += '"';
                i++; // Skip next quote
            } else {
                // Toggle quotes mode
                inQuotes = !inQuotes;
            }
        } else if (char === ',' && !inQuotes) {
            // End of value
            result.push(current.trim());
            current = '';
        } else {
            // Regular character
            current += char;
        }
    }
    
    // Add last value
    result.push(current.trim());
    
    return result;
}

/**
 * parseJSON - Safe JSON Parse
 * Parses JSON with error handling
 * @param {string} jsonString - JSON string to parse
 * @returns {Object|null} Parsed object or null on error
 */
function parseJSON(jsonString) {
    try {
        return JSON.parse(jsonString);
    } catch (error) {
        console.error('JSON parse error:', error);
        return null;
    }
}

// -----------------------------------------------------------------------------
// Chart Utilities
// Functions for working with charts
// -----------------------------------------------------------------------------

/**
 * getChartColors - Get Array of Chart Colors
 * Returns an array of colors for chart data series
 * @param {number} count - Number of colors needed
 * @returns {Array} Array of color strings
 */
function getChartColors(count) {
    // Get colors from config
    const colors = CONFIG?.CHART_COLORS 
        ? Object.values(CONFIG.CHART_COLORS)
        : ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c'];
    
    // If we need more colors than available, cycle through
    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    
    return result;
}

/**
 * calculateStats - Calculate Basic Statistics
 * Computes mean, median, min, max for numeric array
 * @param {Array} values - Array of numbers
 * @returns {Object} Statistics object
 */
function calculateStats(values) {
    // Filter to only numbers
    const numbers = values
        .map(v => parseFloat(v))
        .filter(v => !isNaN(v));
    
    // Handle empty array
    if (numbers.length === 0) {
        return {
            count: 0,
            mean: 0,
            median: 0,
            min: 0,
            max: 0,
            sum: 0
        };
    }
    
    // Sort for median calculation
    const sorted = [...numbers].sort((a, b) => a - b);
    
    // Calculate statistics
    const sum = numbers.reduce((a, b) => a + b, 0);
    const mean = sum / numbers.length;
    const min = sorted[0];
    const max = sorted[sorted.length - 1];
    
    // Calculate median
    const mid = Math.floor(sorted.length / 2);
    const median = sorted.length % 2 !== 0
        ? sorted[mid]
        : (sorted[mid - 1] + sorted[mid]) / 2;
    
    return {
        count: numbers.length,
        mean: parseFloat(mean.toFixed(2)),
        median: parseFloat(median.toFixed(2)),
        min: parseFloat(min.toFixed(2)),
        max: parseFloat(max.toFixed(2)),
        sum: parseFloat(sum.toFixed(2))
    };
}
