/* =============================================================================
   Upload Page JavaScript
   Handles dataset file upload, preview, and form submission
   ============================================================================= */

// -----------------------------------------------------------------------------
// Global Variables
// -----------------------------------------------------------------------------
let selectedFile = null;
let previewData = [];
let previewHeaders = [];

// -----------------------------------------------------------------------------
// DOM Ready Handler
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!auth.requireAuth()) {
        return;
    }
    
    // Update navbar
    auth.updateNavbar();
    
    // Initialize file upload
    initializeFileUpload();
    
    // Form submission
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUpload);
    }
    
    // Remove file button
    const removeBtn = document.getElementById('remove-file');
    if (removeBtn) {
        removeBtn.addEventListener('click', removeSelectedFile);
    }
});

// -----------------------------------------------------------------------------
// Initialize File Upload
// -----------------------------------------------------------------------------
function initializeFileUpload() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    
    if (!dropZone || !fileInput) return;
    
    // Click to select
    dropZone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'INPUT') {
            fileInput.click();
        }
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            handleFileSelection(e.target.files[0]);
        }
    });
    
    // Drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.add('dragover'));
    });
    
    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.remove('dragover'));
    });
    
    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// -----------------------------------------------------------------------------
// Handle File Selection
// -----------------------------------------------------------------------------
async function handleFileSelection(file) {
    // Validate file
    const ext = file.name.split('.').pop().toLowerCase();
    const validExts = ['csv', 'json'];
    
    if (!validExts.includes(ext)) {
        showAlert('Please select a CSV or JSON file', 'error');
        return;
    }
    
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showAlert('File size must be under 10MB', 'error');
        return;
    }
    
    // Store file
    selectedFile = file;
    
    // Update UI
    document.getElementById('drop-zone').style.display = 'none';
    document.getElementById('file-info').style.display = 'flex';
    document.getElementById('selected-file-name').textContent = file.name;
    document.getElementById('selected-file-size').textContent = formatFileSize(file.size);
    
    // Generate preview
    await generatePreview(file);
}

// -----------------------------------------------------------------------------
// Remove Selected File
// -----------------------------------------------------------------------------
function removeSelectedFile() {
    selectedFile = null;
    previewData = [];
    previewHeaders = [];
    
    document.getElementById('drop-zone').style.display = 'block';
    document.getElementById('file-info').style.display = 'none';
    document.getElementById('preview-section').style.display = 'none';
    document.getElementById('file-input').value = '';
}

// -----------------------------------------------------------------------------
// Generate Preview
// -----------------------------------------------------------------------------
async function generatePreview(file) {
    const previewSection = document.getElementById('preview-section');
    const previewThead = document.getElementById('preview-thead');
    const previewTbody = document.getElementById('preview-tbody');
    const previewRows = document.getElementById('preview-rows');
    const previewCols = document.getElementById('preview-cols');
    
    try {
        const content = await readFileAsText(file);
        const ext = file.name.split('.').pop().toLowerCase();
        
        let data = [];
        
        if (ext === 'csv') {
            data = parseCSV(content);
        } else if (ext === 'json') {
            const json = JSON.parse(content);
            data = Array.isArray(json) ? json : (json.data || [json]);
        }
        
        if (data.length === 0) {
            showAlert('No data found in file', 'warning');
            return;
        }
        
        // Store data
        previewData = data;
        previewHeaders = Object.keys(data[0]);
        
        // Update stats
        previewRows.textContent = `Rows: ${data.length}`;
        previewCols.textContent = `Columns: ${previewHeaders.length}`;
        
        // Build table header
        previewThead.innerHTML = `<tr>${previewHeaders.map(h => `<th>${escapeHtml(h)}</th>`).join('')}</tr>`;
        
        // Build table body (first 10 rows)
        const displayData = data.slice(0, 10);
        previewTbody.innerHTML = displayData.map(row => 
            `<tr>${previewHeaders.map(h => `<td>${escapeHtml(String(row[h] ?? ''))}</td>`).join('')}</tr>`
        ).join('');
        
        // Show preview
        previewSection.style.display = 'block';
        
    } catch (error) {
        showAlert('Error parsing file: ' + error.message, 'error');
    }
}

// -----------------------------------------------------------------------------
// Parse CSV
// -----------------------------------------------------------------------------
function parseCSV(content) {
    const lines = content.trim().split('\n');
    if (lines.length < 2) return [];
    
    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim().replace(/^"|"$/g, ''));
        const row = {};
        headers.forEach((h, idx) => {
            row[h] = values[idx] || '';
        });
        data.push(row);
    }
    
    return data;
}

// -----------------------------------------------------------------------------
// Read File as Text
// -----------------------------------------------------------------------------
function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

// -----------------------------------------------------------------------------
// Handle Upload
// -----------------------------------------------------------------------------
async function handleUpload(event) {
    event.preventDefault();
    
    if (!selectedFile) {
        showAlert('Please select a file to upload', 'error');
        return;
    }
    
    // Get form values (using correct IDs from HTML)
    const title = document.getElementById('title')?.value.trim();
    const description = document.getElementById('description')?.value.trim();
    const tagsInput = document.getElementById('tags')?.value.trim();
    const isPublic = document.getElementById('is-public')?.checked ?? true;
    
    // Parse tags
    const tags = tagsInput
        ? tagsInput.split(/[,\s]+/).map(t => t.trim().toLowerCase()).filter(t => t)
        : [];
    
    // Validate
    if (!title) {
        showAlert('Please enter a dataset title', 'error');
        return;
    }
    
    if (!description) {
        showAlert('Please enter a description', 'error');
        return;
    }
    
    try {
        // Show loading
        const submitBtn = document.querySelector('#upload-form button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner small"></span> Uploading...';
        
        // Create FormData
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('name', title);
        formData.append('description', description);
        formData.append('tags', JSON.stringify(tags));
        formData.append('is_public', isPublic);
        
        // Upload
        const response = await api.postFormData('/upload-dataset', formData);
        
        showAlert('Dataset uploaded successfully!', 'success');
        
        // Redirect to dataset page
        setTimeout(() => {
            window.location.href = `dataset.html?id=${response.dataset_id}`;
        }, 1500);
        
    } catch (error) {
        showAlert(error.message || 'Upload failed', 'error');
        
        const submitBtn = document.querySelector('#upload-form button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Upload Dataset';
    }
}

// -----------------------------------------------------------------------------
// Utility Functions
// -----------------------------------------------------------------------------
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showAlert(message, type, duration = 5000) {
    // Check if showAlert exists in utils.js
    if (typeof window.showAlert === 'function' && window.showAlert !== showAlert) {
        window.showAlert(message, type, duration);
        return;
    }
    
    // Fallback alert
    let alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;';
        document.body.appendChild(alertContainer);
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.cssText = 'padding:15px 20px;margin-bottom:10px;border-radius:8px;color:white;font-weight:500;animation:fadeIn 0.3s;';
    alert.style.background = type === 'success' ? '#2ecc71' : type === 'error' ? '#e74c3c' : '#f39c12';
    alert.textContent = message;
    
    alertContainer.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, duration);
}
