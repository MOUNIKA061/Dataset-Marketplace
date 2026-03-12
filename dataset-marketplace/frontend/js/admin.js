/* =============================================================================
   Admin Dashboard JavaScript
   Handles analytics display and admin-only functionality
   ============================================================================= */

// -----------------------------------------------------------------------------
// Global Variables
// Store analytics data and chart instances
// -----------------------------------------------------------------------------
let analyticsData = null;           // Analytics data from API
let adminCharts = {};               // Chart.js instances

// -----------------------------------------------------------------------------
// DOM Ready Handler
// Executes when the page has fully loaded
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    // Check admin authentication
    if (!auth.requireAdmin()) {
        return;
    }
    
    // Update navbar with user info
    auth.updateNavbar();
    
    // Load analytics data
    loadAnalytics();
});

// -----------------------------------------------------------------------------
// loadAnalytics - Fetch Analytics Data
// Loads download stats and usage data from API
// -----------------------------------------------------------------------------
async function loadAnalytics() {
    // Show loading state
    showLoading('Loading analytics...');
    
    try {
        // Fetch analytics from API
        const response = await api.get('/analytics');
        
        // Store analytics data
        analyticsData = response;
        
        // Display summary stats
        displaySummaryStats();
        
        // Display charts
        renderAnalyticsCharts();
        
        // Display recent activity
        displayRecentActivity();
        
        // Display top datasets
        displayTopDatasets();
        
    } catch (error) {
        showAlert(`Failed to load analytics: ${error.message}`, 'error');
        
        // Show error in content
        const content = document.getElementById('analytics-content');
        if (content) {
            content.innerHTML = `
                <div class="alert alert-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <span>${escapeHtml(error.message)}</span>
                </div>
            `;
        }
    } finally {
        hideLoading();
    }
}

// -----------------------------------------------------------------------------
// displaySummaryStats - Show Overview Statistics
// Renders the top-level stat cards
// -----------------------------------------------------------------------------
function displaySummaryStats() {
    if (!analyticsData) return;
    
    // Get stats container
    const statsContainer = document.getElementById('summary-stats');
    
    if (statsContainer) {
        // Extract summary data
        const totalDownloads = analyticsData.total_downloads || 0;
        const totalDatasets = analyticsData.total_datasets || 0;
        const totalUsers = analyticsData.total_users || 0;
        const totalStorage = analyticsData.total_storage || 0;
        
        // Update stats cards
        statsContainer.innerHTML = `
            <div class="admin-stat-card downloads">
                <i class="fas fa-download"></i>
                <div class="stat-value">${formatNumber(totalDownloads)}</div>
                <div class="stat-label">Total Downloads</div>
            </div>
            <div class="admin-stat-card datasets">
                <i class="fas fa-database"></i>
                <div class="stat-value">${formatNumber(totalDatasets)}</div>
                <div class="stat-label">Total Datasets</div>
            </div>
            <div class="admin-stat-card users">
                <i class="fas fa-users"></i>
                <div class="stat-value">${formatNumber(totalUsers)}</div>
                <div class="stat-label">Registered Users</div>
            </div>
            <div class="admin-stat-card storage">
                <i class="fas fa-hdd"></i>
                <div class="stat-value">${formatFileSize(totalStorage)}</div>
                <div class="stat-label">Total Storage</div>
            </div>
        `;
    }
}

// -----------------------------------------------------------------------------
// renderAnalyticsCharts - Create Analytics Visualizations
// Renders download trends and distribution charts
// -----------------------------------------------------------------------------
function renderAnalyticsCharts() {
    if (!analyticsData) return;
    
    // Get charts container
    const chartsContainer = document.getElementById('analytics-charts');
    
    if (chartsContainer) {
        // Set up chart canvases
        chartsContainer.innerHTML = `
            <div class="row">
                <div class="col-8">
                    <div class="chart-container">
                        <h3 class="chart-title">
                            <i class="fas fa-chart-line"></i> Download Trends (Last 30 Days)
                        </h3>
                        <div class="chart-wrapper" style="height: 300px;">
                            <canvas id="downloads-trend-chart"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-4">
                    <div class="chart-container">
                        <h3 class="chart-title">
                            <i class="fas fa-chart-pie"></i> Downloads by Category
                        </h3>
                        <div class="chart-wrapper" style="height: 300px;">
                            <canvas id="category-pie-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Create charts after DOM update
        setTimeout(() => {
            createDownloadsTrendChart();
            createCategoryPieChart();
        }, 100);
    }
}

// -----------------------------------------------------------------------------
// createDownloadsTrendChart - Create Line Chart
// Renders download trend over time
// -----------------------------------------------------------------------------
function createDownloadsTrendChart() {
    const canvas = document.getElementById('downloads-trend-chart');
    
    if (!canvas) return;
    
    // Destroy existing chart
    if (adminCharts.trendChart) {
        adminCharts.trendChart.destroy();
    }
    
    // Get or generate trend data
    const trendData = analyticsData.download_trend || generateMockTrendData();
    
    // Create chart
    adminCharts.trendChart = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: trendData.labels,
            datasets: [{
                label: 'Downloads',
                data: trendData.values,
                borderColor: CONFIG.CHART_COLORS.primary,
                backgroundColor: `${CONFIG.CHART_COLORS.primary}20`,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#ecf0f1'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// -----------------------------------------------------------------------------
// createCategoryPieChart - Create Pie Chart
// Renders downloads distribution by category/tag
// -----------------------------------------------------------------------------
function createCategoryPieChart() {
    const canvas = document.getElementById('category-pie-chart');
    
    if (!canvas) return;
    
    // Destroy existing chart
    if (adminCharts.pieChart) {
        adminCharts.pieChart.destroy();
    }
    
    // Get or generate category data
    const categoryData = analyticsData.downloads_by_category || generateMockCategoryData();
    
    // Create chart
    adminCharts.pieChart = new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: categoryData.labels,
            datasets: [{
                data: categoryData.values,
                backgroundColor: getChartColors(categoryData.labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15
                    }
                }
            }
        }
    });
}

// -----------------------------------------------------------------------------
// displayRecentActivity - Show Recent Downloads
// Lists recent download activity
// -----------------------------------------------------------------------------
function displayRecentActivity() {
    if (!analyticsData) return;
    
    // Get activity container
    const activityContainer = document.getElementById('recent-activity');
    
    if (!activityContainer) return;
    
    // Get recent downloads
    const recentDownloads = analyticsData.recent_downloads || [];
    
    // Build activity list
    let activityHtml = `
        <div class="card static">
            <h3 class="card-title"><i class="fas fa-history"></i> Recent Downloads</h3>
    `;
    
    if (recentDownloads.length === 0) {
        activityHtml += `
            <div class="empty-state" style="padding: 20px;">
                <i class="fas fa-download" style="font-size: 2rem;"></i>
                <p>No recent downloads</p>
            </div>
        `;
    } else {
        activityHtml += `<div class="mt-2">`;
        
        recentDownloads.forEach(download => {
            activityHtml += `
                <div style="display: flex; align-items: center; padding: 12px 0; border-bottom: 1px solid #ecf0f1;">
                    <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #3498db, #2980b9); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                        <i class="fas fa-download" style="color: white;"></i>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600;">${escapeHtml(download.dataset_name || 'Unknown Dataset')}</div>
                        <div style="font-size: 12px; color: #95a5a6;">
                            Downloaded by ${escapeHtml(download.user_name || 'Anonymous')}
                        </div>
                    </div>
                    <div style="font-size: 12px; color: #95a5a6;">
                        ${formatDate(download.downloaded_at)}
                    </div>
                </div>
            `;
        });
        
        activityHtml += `</div>`;
    }
    
    activityHtml += `</div>`;
    
    // Update container
    activityContainer.innerHTML = activityHtml;
}

// -----------------------------------------------------------------------------
// displayTopDatasets - Show Most Popular Datasets
// Lists top downloaded datasets
// -----------------------------------------------------------------------------
function displayTopDatasets() {
    if (!analyticsData) return;
    
    // Get container
    const topContainer = document.getElementById('top-datasets');
    
    if (!topContainer) return;
    
    // Get top datasets
    const topDatasets = analyticsData.top_datasets || [];
    
    // Build table
    let tableHtml = `
        <div class="card static">
            <h3 class="card-title"><i class="fas fa-trophy"></i> Top Datasets</h3>
    `;
    
    if (topDatasets.length === 0) {
        tableHtml += `
            <div class="empty-state" style="padding: 20px;">
                <i class="fas fa-database" style="font-size: 2rem;"></i>
                <p>No datasets yet</p>
            </div>
        `;
    } else {
        tableHtml += `
            <div class="table-wrapper mt-2">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Dataset</th>
                            <th>Owner</th>
                            <th>Downloads</th>
                            <th>Size</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        topDatasets.forEach((dataset, index) => {
            // Rank badge colors
            const rankColors = ['#f1c40f', '#95a5a6', '#cd6133'];
            const rankColor = rankColors[index] || '#3498db';
            
            tableHtml += `
                <tr onclick="window.location.href='dataset.html?id=${dataset.id}'" style="cursor: pointer;">
                    <td>
                        <span style="display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; background: ${rankColor}; color: white; border-radius: 50%; font-weight: bold; font-size: 12px;">
                            ${index + 1}
                        </span>
                    </td>
                    <td><strong>${escapeHtml(dataset.name)}</strong></td>
                    <td>${escapeHtml(dataset.owner_name || 'Unknown')}</td>
                    <td>
                        <span style="color: #2ecc71; font-weight: 600;">
                            <i class="fas fa-download"></i> ${formatNumber(dataset.download_count || 0)}
                        </span>
                    </td>
                    <td>${formatFileSize(dataset.file_size || 0)}</td>
                </tr>
            `;
        });
        
        tableHtml += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    tableHtml += `</div>`;
    
    // Update container
    topContainer.innerHTML = tableHtml;
}

// -----------------------------------------------------------------------------
// generateMockTrendData - Generate Sample Trend Data
// Creates demo data for the trend chart
// @returns {Object} Trend data with labels and values
// -----------------------------------------------------------------------------
function generateMockTrendData() {
    // Generate last 30 days labels
    const labels = [];
    const values = [];
    const today = new Date();
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Generate random-ish values with upward trend
        values.push(Math.floor(Math.random() * 20) + 5 + Math.floor((30 - i) / 3));
    }
    
    return { labels, values };
}

// -----------------------------------------------------------------------------
// generateMockCategoryData - Generate Sample Category Data
// Creates demo data for the pie chart
// @returns {Object} Category data with labels and values
// -----------------------------------------------------------------------------
function generateMockCategoryData() {
    return {
        labels: ['Machine Learning', 'Finance', 'Healthcare', 'Sports', 'Other'],
        values: [35, 25, 20, 12, 8]
    };
}

// -----------------------------------------------------------------------------
// refreshAnalytics - Reload Analytics Data
// Refreshes all analytics data and charts
// -----------------------------------------------------------------------------
function refreshAnalytics() {
    // Destroy existing charts
    Object.values(adminCharts).forEach(chart => {
        if (chart) chart.destroy();
    });
    adminCharts = {};
    
    // Reload data
    loadAnalytics();
}

// -----------------------------------------------------------------------------
// exportAnalytics - Export Analytics Report
// Downloads analytics data as CSV
// -----------------------------------------------------------------------------
function exportAnalytics() {
    if (!analyticsData) {
        showAlert('No analytics data to export', 'warning');
        return;
    }
    
    // Build CSV content
    let csvContent = 'Dataset Analytics Report\n';
    csvContent += `Generated: ${new Date().toLocaleString()}\n\n`;
    
    // Summary stats
    csvContent += 'Summary Statistics\n';
    csvContent += `Total Downloads,${analyticsData.total_downloads || 0}\n`;
    csvContent += `Total Datasets,${analyticsData.total_datasets || 0}\n`;
    csvContent += `Total Users,${analyticsData.total_users || 0}\n`;
    csvContent += `Total Storage (bytes),${analyticsData.total_storage || 0}\n\n`;
    
    // Top datasets
    if (analyticsData.top_datasets?.length > 0) {
        csvContent += 'Top Datasets\n';
        csvContent += 'Rank,Name,Owner,Downloads,Size\n';
        analyticsData.top_datasets.forEach((dataset, index) => {
            csvContent += `${index + 1},${dataset.name},${dataset.owner_name || 'Unknown'},${dataset.download_count || 0},${dataset.file_size || 0}\n`;
        });
    }
    
    // Create and download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics_report_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    showAlert('Analytics report exported', 'success', 2000);
}
