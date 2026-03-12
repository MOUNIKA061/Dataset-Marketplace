/* =============================================================================
   Search Page JavaScript
   Handles dataset search, filtering, and recommendations display
   ============================================================================= */

// -----------------------------------------------------------------------------
// Global Variables
// Store search state and results
// -----------------------------------------------------------------------------
let currentSearchQuery = '';        // Current search query
let currentTags = [];               // Selected filter tags
let allDatasets = [];               // All loaded datasets
let recommendations = [];           // AI recommendations

// -----------------------------------------------------------------------------
// DOM Ready Handler
// Executes when the page has fully loaded
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication - redirect if not logged in
    if (!auth.requireAuth()) {
        return;
    }
    
    // Update navbar with user info
    auth.updateNavbar();
    
    // Initialize search functionality
    initializeSearch();
    
    // Load initial datasets
    loadDatasets();
    
    // Load AI recommendations
    loadRecommendations();
});

// -----------------------------------------------------------------------------
// initializeSearch - Set Up Search Functionality
// Configures search input and filter tags
// -----------------------------------------------------------------------------
function initializeSearch() {
    // Get search form
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', (event) => {
            event.preventDefault();
            currentSearchQuery = document.getElementById('search-query')?.value.trim() || '';
            performSearch();
        });
    }

    // Get search input element
    const searchInput = document.getElementById('search-query');
    
    if (searchInput) {
        // Add input event listener with debounce
        searchInput.addEventListener('input', debounce((event) => {
            currentSearchQuery = event.target.value.trim();
            performSearch();
        }, CONFIG?.SEARCH_DEBOUNCE || 300));
        
        // Handle Enter key
        searchInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                currentSearchQuery = searchInput.value.trim();
                performSearch();
            }
        });
    }
    
    // Get search button
    const searchBtn = searchForm?.querySelector('button[type="submit"]');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const searchInput = document.getElementById('search-query');
            if (searchInput) {
                currentSearchQuery = searchInput.value.trim();
                performSearch();
            }
        });
    }
}

// -----------------------------------------------------------------------------
// loadDatasets - Fetch Datasets from API
// Loads all available datasets
// -----------------------------------------------------------------------------
async function loadDatasets() {
    const datasetGrid = document.getElementById('results-grid');
    
    try {
        // Fetch datasets from API
        const response = await api.get('/search-datasets');
        
        // Store datasets
        allDatasets = response.datasets || [];
        
        // Display datasets
        displayDatasets(allDatasets);
        
        // Extract and display filter tags
        updateFilterTags();
        
    } catch (error) {
        // Show error
        if (datasetGrid) {
            datasetGrid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-error">
                        <i class="fas fa-exclamation-circle"></i>
                        <span>Failed to load datasets: ${escapeHtml(error.message)}</span>
                    </div>
                </div>
            `;
        }
    }
}

// -----------------------------------------------------------------------------
// performSearch - Execute Search Query
// Searches datasets by query and tags
// -----------------------------------------------------------------------------
async function performSearch() {
    const datasetGrid = document.getElementById('results-grid');
    
    try {
        // Build query parameters
        const params = new URLSearchParams();
        
        // Add search query if present
        if (currentSearchQuery) {
            params.append('q', currentSearchQuery);
        }
        
        // Add tags if selected
        if (currentTags.length > 0) {
            params.append('tags', currentTags.join(','));
        }
        
        // Fetch search results from API
        const queryString = params.toString();
        const endpoint = queryString 
            ? `/search-datasets?${queryString}` 
            : '/search-datasets';
        
        const response = await api.get(endpoint);
        
        // Display results
        displayDatasets(response.datasets || []);
        
    } catch (error) {
        // Show error
        if (datasetGrid) {
            datasetGrid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-error">
                        <i class="fas fa-exclamation-circle"></i>
                        <span>Search failed: ${escapeHtml(error.message)}</span>
                    </div>
                </div>
            `;
        }
    }
}

// -----------------------------------------------------------------------------
// displayDatasets - Render Dataset Cards
// Creates grid of dataset cards from results
// @param {Array} datasets - Array of dataset objects
// -----------------------------------------------------------------------------
function displayDatasets(datasets) {
    const datasetGrid = document.getElementById('results-grid');
    
    if (!datasetGrid) return;
    
    // Handle empty results
    if (!datasets || datasets.length === 0) {
        datasetGrid.innerHTML = `
            <div class="col-12">
                <div class="empty-state">
                    <i class="fas fa-database"></i>
                    <h3>No datasets found</h3>
                    <p>Try adjusting your search or filters</p>
                    ${currentSearchQuery || currentTags.length > 0 
                        ? '<button class="btn btn-primary" onclick="clearFilters()">Clear Filters</button>'
                        : '<a href="upload.html" class="btn btn-primary">Upload First Dataset</a>'
                    }
                </div>
            </div>
        `;
        return;
    }
    
    // Build cards HTML
    let cardsHtml = '';
    
    datasets.forEach(dataset => {
        // Parse tags (handle JSON string or array)
        let tags = [];
        if (typeof dataset.tags === 'string') {
            try {
                tags = JSON.parse(dataset.tags);
            } catch {
                tags = dataset.tags.split(',').map(t => t.trim());
            }
        } else if (Array.isArray(dataset.tags)) {
            tags = dataset.tags;
        }
        
        // Build tags HTML
        const tagsHtml = tags
            .slice(0, 3)
            .map(tag => `<span class="tag tag-primary">${escapeHtml(tag)}</span>`)
            .join('');
        
        // Additional tags indicator
        const moreTagsHtml = tags.length > 3 
            ? `<span class="tag">+${tags.length - 3}</span>` 
            : '';
        
        // Create card
        cardsHtml += `
            <div class="dataset-card" onclick="viewDataset(${dataset.id})">
                <div class="dataset-card-header">
                    <h3>${escapeHtml(dataset.name)}</h3>
                    <div class="dataset-owner">by ${escapeHtml(dataset.owner_name || 'Unknown')}</div>
                </div>
                <div class="dataset-card-body">
                    <p class="dataset-card-description">${escapeHtml(dataset.description || 'No description')}</p>
                    <div class="dataset-tags">
                        ${tagsHtml}
                        ${moreTagsHtml}
                    </div>
                    <div class="dataset-meta">
                        <div class="dataset-meta-item">
                            <i class="fas fa-file"></i>
                            <span>${formatFileSize(dataset.file_size || 0)}</span>
                        </div>
                        <div class="dataset-meta-item">
                            <i class="fas fa-download"></i>
                            <span>${formatNumber(dataset.download_count || 0)}</span>
                        </div>
                        <div class="dataset-meta-item">
                            <i class="fas fa-calendar"></i>
                            <span>${formatDate(dataset.created_at).split(',')[0]}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    // Update grid
    datasetGrid.innerHTML = cardsHtml;
}

// -----------------------------------------------------------------------------
// updateFilterTags - Build Filter Tags List
// Extracts unique tags from datasets for filtering
// -----------------------------------------------------------------------------
function updateFilterTags() {
    // Get all unique tags from datasets
    const tagSet = new Set();
    
    allDatasets.forEach(dataset => {
        let tags = [];
        if (typeof dataset.tags === 'string') {
            try {
                tags = JSON.parse(dataset.tags);
            } catch {
                tags = dataset.tags.split(',').map(t => t.trim());
            }
        } else if (Array.isArray(dataset.tags)) {
            tags = dataset.tags;
        }
        
        tags.forEach(tag => tagSet.add(tag.toLowerCase()));
    });
    
    // Convert to array and sort
    const allTags = Array.from(tagSet).sort();
    
    // Get filter container
    const filterTags = document.getElementById('filter-tags');
    
    if (filterTags && allTags.length > 0) {
        // Build filter tags HTML
        filterTags.innerHTML = allTags
            .slice(0, 10)  // Show max 10 tags
            .map(tag => {
                const isActive = currentTags.includes(tag);
                return `
                    <span class="filter-tag ${isActive ? 'active' : ''}" 
                          onclick="toggleFilterTag('${escapeHtml(tag)}')">
                        ${escapeHtml(tag)}
                    </span>
                `;
            })
            .join('');
    }
}

// -----------------------------------------------------------------------------
// toggleFilterTag - Toggle Tag Filter
// Adds or removes tag from filter selection
// @param {string} tag - Tag to toggle
// -----------------------------------------------------------------------------
function toggleFilterTag(tag) {
    // Check if tag is already selected
    const index = currentTags.indexOf(tag);
    
    if (index > -1) {
        // Remove tag from selection
        currentTags.splice(index, 1);
    } else {
        // Add tag to selection
        currentTags.push(tag);
    }
    
    // Update filter tag buttons
    updateFilterTags();
    
    // Perform search with new filters
    performSearch();
}

// -----------------------------------------------------------------------------
// clearFilters - Clear All Filters
// Resets search query and tags
// -----------------------------------------------------------------------------
function clearFilters() {
    // Clear search query
    currentSearchQuery = '';
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.value = '';
    }
    
    // Clear tags
    currentTags = [];
    
    // Update filter display
    updateFilterTags();
    
    // Reload all datasets
    displayDatasets(allDatasets);
}

// -----------------------------------------------------------------------------
// loadRecommendations - Fetch AI Recommendations
// Loads personalized dataset recommendations
// -----------------------------------------------------------------------------
async function loadRecommendations() {
    const recommendationsContainer = document.getElementById('recommendations-list');
    
    try {
        // Fetch recommendations from API
        const response = await api.get('/recommendations');
        
        // Store recommendations
        recommendations = response.recommendations || [];
        
        // Display recommendations
        displayRecommendations(recommendations);
        
        // Load popular tags
        loadPopularTags();
        
    } catch (error) {
        // Show error or default message
        if (recommendationsContainer) {
            recommendationsContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.875rem; text-align: center;">Unable to load recommendations</p>';
        }
        
        // Still try to load popular tags
        loadPopularTags();
    }
}

// -----------------------------------------------------------------------------
// displayRecommendations - Render Recommendations
// Creates recommendation cards
// @param {Array} recommendations - Array of recommended datasets
// -----------------------------------------------------------------------------
function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations-list');
    
    if (!container) return;
    
    // Handle empty recommendations
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.875rem; text-align: center;">No recommendations yet</p>';
        return;
    }
    
    // Build recommendation items HTML (compact sidebar style)
    let itemsHtml = '';
    
    recommendations.slice(0, 5).forEach((item, index) => {
        const dataset = item.dataset || item;
        const score = item.score || item.similarity_score || 0.8;
        
        itemsHtml += `
            <a href="dataset.html?id=${dataset.id}" class="rec-item">
                <div class="rec-icon">${(dataset.name || 'D').charAt(0).toUpperCase()}</div>
                <div class="rec-info">
                    <div class="rec-title">${escapeHtml(dataset.name || 'Dataset')}</div>
                    <div class="rec-meta">${Math.round(score * 100)}% match · ${formatNumber(dataset.download_count || 0)} downloads</div>
                </div>
            </a>
        `;
    });
    
    container.innerHTML = itemsHtml;
}

// -----------------------------------------------------------------------------
// loadPopularTags - Display Popular Tags in Sidebar
// Extracts and shows most common tags
// -----------------------------------------------------------------------------
function loadPopularTags() {
    const tagsContainer = document.getElementById('popular-tags');
    if (!tagsContainer) return;
    
    // Get all tags from datasets
    const tagCounts = {};
    
    allDatasets.forEach(dataset => {
        let tags = [];
        if (typeof dataset.tags === 'string') {
            try {
                tags = JSON.parse(dataset.tags);
            } catch {
                tags = dataset.tags.split(',').map(t => t.trim());
            }
        } else if (Array.isArray(dataset.tags)) {
            tags = dataset.tags;
        }
        
        tags.forEach(tag => {
            const normalizedTag = tag.toLowerCase().trim();
            tagCounts[normalizedTag] = (tagCounts[normalizedTag] || 0) + 1;
        });
    });
    
    // Sort by count and take top 10
    const sortedTags = Object.entries(tagCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    if (sortedTags.length === 0) {
        tagsContainer.innerHTML = '<span style="color: var(--text-muted); font-size: 0.875rem;">No tags yet</span>';
        return;
    }
    
    // Build tags HTML
    const tagsHtml = sortedTags.map(([tag, count], index) => {
        const isPopular = index < 3;
        return `<span class="tag ${isPopular ? 'popular' : ''}" onclick="searchByTag('${escapeHtml(tag)}')">${escapeHtml(tag)}</span>`;
    }).join('');
    
    tagsContainer.innerHTML = tagsHtml;
}

// -----------------------------------------------------------------------------
// searchByTag - Search datasets by tag
// @param {string} tag - Tag to search for
// -----------------------------------------------------------------------------
function searchByTag(tag) {
    const tagsInput = document.getElementById('tags-filter');
    if (tagsInput) {
        tagsInput.value = tag;
    }
    currentTags = [tag];
    performSearch();
}

// -----------------------------------------------------------------------------
// viewDataset - Navigate to Dataset Details
// Redirects to dataset detail page
// @param {number} datasetId - ID of dataset to view
// -----------------------------------------------------------------------------
function viewDataset(datasetId) {
    window.location.href = `dataset.html?id=${datasetId}`;
}
