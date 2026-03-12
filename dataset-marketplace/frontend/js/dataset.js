/* =============================================================================
   Dataset Details Page - View and Download with Visualizations
   ============================================================================= */

let currentDataset = null;
let previewData = [];
let statsData = {};
let charts = {};

// Colors for charts with named mapping
const chartColorPalette = {
    colors: [
        { name: 'Indigo', value: 'rgba(99, 102, 241, 0.8)', border: 'rgb(99, 102, 241)' },
        { name: 'Pink', value: 'rgba(236, 72, 153, 0.8)', border: 'rgb(236, 72, 153)' },
        { name: 'Green', value: 'rgba(34, 197, 94, 0.8)', border: 'rgb(34, 197, 94)' },
        { name: 'Orange', value: 'rgba(251, 146, 60, 0.8)', border: 'rgb(251, 146, 60)' },
        { name: 'Blue', value: 'rgba(59, 130, 246, 0.8)', border: 'rgb(59, 130, 246)' },
        { name: 'Purple', value: 'rgba(168, 85, 247, 0.8)', border: 'rgb(168, 85, 247)' },
        { name: 'Teal', value: 'rgba(20, 184, 166, 0.8)', border: 'rgb(20, 184, 166)' },
        { name: 'Red', value: 'rgba(239, 68, 68, 0.8)', border: 'rgb(239, 68, 68)' },
        { name: 'Yellow', value: 'rgba(234, 179, 8, 0.8)', border: 'rgb(234, 179, 8)' },
        { name: 'Gray', value: 'rgba(107, 114, 128, 0.8)', border: 'rgb(107, 114, 128)' }
    ],
    getColor: function(index) { return this.colors[index % this.colors.length].value; },
    getBorder: function(index) { return this.colors[index % this.colors.length].border; },
    getColors: function(count) { return this.colors.slice(0, count).map(c => c.value); },
    getBorders: function(count) { return this.colors.slice(0, count).map(c => c.border); }
};

// =============================================================================
// Initialize Page
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!auth.requireAuth()) return;
    auth.updateNavbar();
    
    // Get dataset ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const datasetId = urlParams.get('id');
    
    if (!datasetId) {
        alert('No dataset ID provided');
        window.location.href = 'search.html';
        return;
    }
    
    // Load the dataset
    loadDataset(datasetId);
});

// =============================================================================
// Load Dataset
// =============================================================================
async function loadDataset(datasetId) {
    try {
        // Fetch dataset details
        const response = await api.get(`/search-datasets?id=${datasetId}`);
        currentDataset = response.datasets?.[0] || response.dataset;
        
        if (!currentDataset) {
            throw new Error('Dataset not found');
        }
        
        // Display dataset info
        displayDatasetInfo();
        
        // Load visualization data
        await loadVisualizationData(datasetId);
        
        // Render statistics cards
        renderStatsCards();
        
        // Render charts
        renderAllCharts();
        
        // Render data preview
        renderDataPreview();
        
        // Show content, hide loading
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('dataset-content').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading dataset:', error);
        document.getElementById('loading-state').innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <h2>❌ Error Loading Dataset</h2>
                <p>${error.message}</p>
                <a href="search.html" class="btn btn-primary">Back to Search</a>
            </div>
        `;
    }
}

// =============================================================================
// Display Dataset Info
// =============================================================================
function displayDatasetInfo() {
    const d = currentDataset;
    
    document.getElementById('dataset-title').textContent = d.name || 'Untitled Dataset';
    document.getElementById('dataset-desc').textContent = d.description || 'No description provided';
    document.getElementById('owner-name').textContent = d.owner_name || 'Unknown';
    document.getElementById('upload-date').textContent = formatDate(d.created_at);
    document.getElementById('row-count').textContent = formatNumber(d.row_count || 0);
    document.getElementById('col-count').textContent = formatNumber(d.column_count || d.columns?.length || 0);
    document.getElementById('download-count').textContent = formatNumber(d.download_count || 0);
    document.getElementById('file-type').textContent = (d.file_type || 'csv').toUpperCase();
    document.getElementById('file-size').textContent = formatFileSize(d.file_size || 0);
    
    // Render tags
    let tags = [];
    if (typeof d.tags === 'string') {
        try { tags = JSON.parse(d.tags); } catch { tags = d.tags.split(','); }
    } else if (Array.isArray(d.tags)) {
        tags = d.tags;
    }
    
    const tagsContainer = document.getElementById('dataset-tags');
    tagsContainer.innerHTML = tags.map(t => 
        `<span class="tag tag-primary">${escapeHtml(t.trim())}</span>`
    ).join('');
    
    document.title = `${d.name} - Dataset Marketplace`;
}

// =============================================================================
// Load Visualization Data
// =============================================================================
async function loadVisualizationData(datasetId) {
    try {
        const response = await api.get(`/visualize/${datasetId}`);
        previewData = response.preview || [];
        statsData = response.stats || {};
    } catch (error) {
        console.error('Failed to load visualization data:', error);
        previewData = currentDataset.preview || [];
    }
}

// =============================================================================
// Render Statistics Cards with Color Mapping
// =============================================================================
function renderStatsCards() {
    const container = document.getElementById('stats-cards');
    if (!container) return;
    
    const numericColumns = Object.keys(statsData).filter(col => 
        statsData[col] && typeof statsData[col].mean === 'number'
    );
    
    if (numericColumns.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted); text-align: center; width: 100%;">No numeric columns for statistics</p>';
        return;
    }
    
    let html = '';
    
    // Show stats for each numeric column with its assigned color
    numericColumns.slice(0, 6).forEach((col, idx) => {
        const stats = statsData[col];
        const color = chartColorPalette.colors[idx];
        html += `
            <div class="stat-card-item" style="border-left: 4px solid ${color.border};">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <div style="width: 12px; height: 12px; background: ${color.value}; border-radius: 2px;"></div>
                    <span style="font-size: 0.75rem; color: #6b7280;">${color.name}</span>
                </div>
                <div class="stat-value">${formatNumber(stats.mean, 2)}</div>
                <div class="stat-label">${escapeHtml(col)}</div>
                <div style="font-size: 0.7rem; color: #9ca3af; margin-top: 0.25rem;">
                    Min: ${formatNumber(stats.min, 1)} | Max: ${formatNumber(stats.max, 1)}
                </div>
            </div>
        `;
    });
    
    // Add total rows and columns
    html += `
        <div class="stat-card-item">
            <div class="stat-value">${formatNumber(currentDataset.row_count || previewData.length)}</div>
            <div class="stat-label">Total Rows</div>
        </div>
        <div class="stat-card-item">
            <div class="stat-value">${formatNumber(currentDataset.column_count || currentDataset.columns?.length || 0)}</div>
            <div class="stat-label">Total Columns</div>
        </div>
    `;
    
    container.innerHTML = html;
}

// =============================================================================
// Render All Charts
// =============================================================================
function renderAllCharts() {
    renderBarChart();
    renderPieChart();
    renderLineChart();
    renderDoughnutChart();
    
    // Add color legend at the bottom
    addColorLegend();
}

// =============================================================================
// Add Color Legend - Shows which color maps to which parameter
// =============================================================================
function addColorLegend() {
    const columns = currentDataset.columns || [];
    const numericCols = Object.keys(statsData).filter(col => 
        statsData[col] && typeof statsData[col].mean === 'number'
    );
    
    // Find the charts section to add legend after it
    const chartsSection = document.querySelector('.charts-section');
    if (!chartsSection) return;
    
    // Check if legend already exists
    if (document.getElementById('color-legend')) return;
    
    let legendHtml = `
        <div id="color-legend" class="chart-card" style="grid-column: 1 / -1; margin-top: 1rem;">
            <h3>🎨 Color Legend - Parameter Mapping</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
    `;
    
    // Show column-to-color mapping for numeric columns
    numericCols.slice(0, 8).forEach((col, idx) => {
        const color = chartColorPalette.colors[idx];
        legendHtml += `
            <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem; background: #f9fafb; border-radius: 8px;">
                <div style="width: 24px; height: 24px; background: ${color.value}; border-radius: 4px; border: 2px solid ${color.border};"></div>
                <div>
                    <strong style="display: block; font-size: 0.9rem;">${escapeHtml(col)}</strong>
                    <span style="font-size: 0.75rem; color: #6b7280;">${color.name} - Numeric Column</span>
                </div>
            </div>
        `;
    });
    
    legendHtml += `
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: #f0f9ff; border-radius: 8px; border-left: 4px solid #3b82f6;">
                <strong>Chart Color Key:</strong>
                <ul style="margin: 0.5rem 0 0 1.5rem; font-size: 0.875rem; color: #374151;">
                    <li><span style="color: ${chartColorPalette.colors[0].border};">■</span> <strong>Indigo</strong> = Mean values / Primary metric</li>
                    <li><span style="color: ${chartColorPalette.colors[2].border};">■</span> <strong>Green</strong> = Minimum values</li>
                    <li><span style="color: ${chartColorPalette.colors[3].border};">■</span> <strong>Orange</strong> = Maximum values</li>
                </ul>
            </div>
        </div>
    `;
    
    chartsSection.parentElement.insertAdjacentHTML('beforeend', legendHtml);
}

// =============================================================================
// Bar Chart - Real Column Statistics from Dataset
// =============================================================================
function renderBarChart() {
    const ctx = document.getElementById('bar-chart');
    if (!ctx) return;
    
    const numericColumns = Object.keys(statsData).filter(col => 
        statsData[col] && typeof statsData[col].mean === 'number'
    ).slice(0, 8);
    
    if (numericColumns.length === 0) {
        ctx.parentElement.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No numeric data available for bar chart</p>';
        return;
    }
    
    // Extract REAL data from the dataset
    const labels = numericColumns.map(col => col.length > 15 ? col.substring(0, 15) + '...' : col);
    const means = numericColumns.map(col => statsData[col].mean);
    const mins = numericColumns.map(col => statsData[col].min);
    const maxs = numericColumns.map(col => statsData[col].max);
    
    if (charts.bar) charts.bar.destroy();
    
    charts.bar = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Mean Value',
                    data: means,
                    backgroundColor: chartColorPalette.getColor(0),
                    borderColor: chartColorPalette.getBorder(0),
                    borderWidth: 2,
                    borderRadius: 6
                },
                {
                    label: 'Min Value',
                    data: mins,
                    backgroundColor: chartColorPalette.getColor(2),
                    borderColor: chartColorPalette.getBorder(2),
                    borderWidth: 2,
                    borderRadius: 6
                },
                {
                    label: 'Max Value',
                    data: maxs,
                    backgroundColor: chartColorPalette.getColor(3),
                    borderColor: chartColorPalette.getBorder(3),
                    borderWidth: 2,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `Statistics for ${currentDataset.name}`,
                    font: { size: 14 }
                },
                legend: { 
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const col = numericColumns[context.dataIndex];
                            return `${context.dataset.label}: ${formatNumber(context.raw, 2)} (${col})`;
                        }
                    }
                }
            },
            scales: {
                y: { 
                    beginAtZero: true,
                    title: { display: true, text: 'Value' }
                },
                x: {
                    title: { display: true, text: 'Columns' }
                }
            }
        }
    });
}

// =============================================================================
// Pie Chart - Real Category Distribution from Dataset
// =============================================================================
function renderPieChart() {
    const ctx = document.getElementById('pie-chart');
    if (!ctx) return;
    
    const columns = currentDataset.columns || [];
    let categoryData = {};
    let selectedColumn = '';
    
    if (previewData.length > 0) {
        // Find the best categorical column (non-numeric, reasonable unique values)
        selectedColumn = columns.find(col => {
            const uniqueValues = new Set(previewData.map(row => row[col]));
            const isNumeric = statsData[col] && typeof statsData[col].mean === 'number';
            return !isNumeric && uniqueValues.size <= 10 && uniqueValues.size > 1;
        });
        
        // Fallback to first non-numeric column or first column
        if (!selectedColumn) {
            selectedColumn = columns.find(col => !(statsData[col] && typeof statsData[col].mean === 'number')) || columns[0];
        }
        
        // Count REAL occurrences from the dataset
        previewData.forEach(row => {
            const val = String(row[selectedColumn] || 'Unknown').substring(0, 20);
            categoryData[val] = (categoryData[val] || 0) + 1;
        });
    }
    
    const labels = Object.keys(categoryData).slice(0, 8);
    const values = labels.map(l => categoryData[l]);
    
    if (labels.length === 0) {
        ctx.parentElement.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No categorical data available for pie chart</p>';
        return;
    }
    
    if (charts.pie) charts.pie.destroy();
    
    charts.pie = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: chartColorPalette.getColors(labels.length),
                borderColor: chartColorPalette.getBorders(labels.length),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `Distribution by "${selectedColumn}"`,
                    font: { size: 14 }
                },
                legend: {
                    position: 'right',
                    labels: { 
                        boxWidth: 14,
                        padding: 10,
                        generateLabels: function(chart) {
                            const data = chart.data;
                            return data.labels.map((label, i) => ({
                                text: `${label}: ${values[i]} (${((values[i] / values.reduce((a,b) => a+b, 0)) * 100).toFixed(1)}%)`,
                                fillStyle: data.datasets[0].backgroundColor[i],
                                strokeStyle: data.datasets[0].borderColor[i],
                                lineWidth: 2,
                                index: i
                            }));
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a,b) => a+b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return `${context.label}: ${context.raw} records (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// =============================================================================
// Line Chart - Real Trend Data from Dataset
// =============================================================================
function renderLineChart() {
    const ctx = document.getElementById('line-chart');
    if (!ctx) return;
    
    const numericColumns = Object.keys(statsData).filter(col => 
        statsData[col] && typeof statsData[col].mean === 'number'
    ).slice(0, 4);
    
    if (numericColumns.length === 0 || previewData.length === 0) {
        ctx.parentElement.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No numeric data available for line chart</p>';
        return;
    }
    
    // Use REAL data from the dataset rows
    const rowCount = Math.min(previewData.length, 25);
    
    // Try to find a date/time column for X-axis, otherwise use row index
    const columns = currentDataset.columns || [];
    const dateCol = columns.find(col => 
        col.toLowerCase().includes('date') || 
        col.toLowerCase().includes('time') ||
        col.toLowerCase().includes('year') ||
        col.toLowerCase().includes('month')
    );
    
    const labels = previewData.slice(0, rowCount).map((row, i) => {
        if (dateCol && row[dateCol]) {
            const val = String(row[dateCol]);
            return val.length > 10 ? val.substring(0, 10) : val;
        }
        return `Row ${i + 1}`;
    });
    
    // Create datasets with REAL values from the dataset
    const datasets = numericColumns.map((col, idx) => ({
        label: col,
        data: previewData.slice(0, rowCount).map(row => parseFloat(row[col]) || 0),
        borderColor: chartColorPalette.getBorder(idx),
        backgroundColor: chartColorPalette.getColor(idx).replace('0.8', '0.2'),
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6
    }));
    
    if (charts.line) charts.line.destroy();
    
    charts.line = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `Trend Analysis - ${numericColumns.join(', ')}`,
                    font: { size: 14 }
                },
                legend: { 
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatNumber(context.raw, 2)}`;
                        }
                    }
                }
            },
            scales: {
                y: { 
                    title: { display: true, text: 'Value' }
                },
                x: {
                    title: { display: true, text: dateCol || 'Data Points' }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// =============================================================================
// Doughnut Chart - Another Real Category Distribution
// =============================================================================
function renderDoughnutChart() {
    const ctx = document.getElementById('doughnut-chart');
    if (!ctx) return;
    
    const columns = currentDataset.columns || [];
    let categoryData = {};
    let selectedColumn = '';
    
    if (previewData.length > 0 && columns.length > 1) {
        // Find a DIFFERENT categorical column than pie chart used
        const categoricalCols = columns.filter(col => {
            const uniqueValues = new Set(previewData.map(row => row[col]));
            const isNumeric = statsData[col] && typeof statsData[col].mean === 'number';
            return !isNumeric && uniqueValues.size <= 15 && uniqueValues.size > 1;
        });
        
        // Use second categorical column or a numeric column grouped
        if (categoricalCols.length > 1) {
            selectedColumn = categoricalCols[1];
        } else if (categoricalCols.length === 1) {
            // Use a numeric column and group into ranges
            const numCol = Object.keys(statsData).find(col => statsData[col]?.mean);
            if (numCol) {
                selectedColumn = numCol;
                const stats = statsData[numCol];
                const range = (stats.max - stats.min) / 4;
                previewData.forEach(row => {
                    const val = parseFloat(row[numCol]) || 0;
                    let group;
                    if (val <= stats.min + range) group = `${numCol}: Low`;
                    else if (val <= stats.min + range * 2) group = `${numCol}: Medium-Low`;
                    else if (val <= stats.min + range * 3) group = `${numCol}: Medium-High`;
                    else group = `${numCol}: High`;
                    categoryData[group] = (categoryData[group] || 0) + 1;
                });
            }
        } else {
            selectedColumn = columns[Math.min(1, columns.length - 1)];
        }
        
        // Count occurrences if not already done
        if (Object.keys(categoryData).length === 0) {
            previewData.forEach(row => {
                const val = String(row[selectedColumn] || 'Other').substring(0, 20);
                categoryData[val] = (categoryData[val] || 0) + 1;
            });
        }
    }
    
    const labels = Object.keys(categoryData).slice(0, 8);
    const values = labels.map(l => categoryData[l]);
    
    if (labels.length === 0) {
        ctx.parentElement.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No categorical data available for doughnut chart</p>';
        return;
    }
    
    if (charts.doughnut) charts.doughnut.destroy();
    
    charts.doughnut = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: chartColorPalette.getColors(labels.length),
                borderColor: chartColorPalette.getBorders(labels.length),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `Breakdown by "${selectedColumn}"`,
                    font: { size: 14 }
                },
                legend: {
                    position: 'right',
                    labels: { 
                        boxWidth: 14,
                        padding: 10,
                        generateLabels: function(chart) {
                            const data = chart.data;
                            return data.labels.map((label, i) => ({
                                text: `${label}: ${values[i]}`,
                                fillStyle: data.datasets[0].backgroundColor[i],
                                strokeStyle: data.datasets[0].borderColor[i],
                                lineWidth: 2,
                                index: i
                            }));
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a,b) => a+b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return `${context.label}: ${context.raw} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// =============================================================================
// Render Data Preview Table
// =============================================================================
function renderDataPreview() {
    const thead = document.getElementById('preview-thead');
    const tbody = document.getElementById('preview-tbody');
    
    if (!thead || !tbody) return;
    
    const columns = currentDataset.columns || [];
    const rows = previewData.slice(0, 20);
    
    if (columns.length === 0 || rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="100%" style="text-align: center; padding: 2rem;">No preview data available</td></tr>';
        return;
    }
    
    // Render header
    thead.innerHTML = '<tr>' + columns.map(col => 
        `<th>${escapeHtml(col)}</th>`
    ).join('') + '</tr>';
    
    // Render body
    tbody.innerHTML = rows.map(row => 
        '<tr>' + columns.map(col => 
            `<td>${escapeHtml(String(row[col] ?? ''))}</td>`
        ).join('') + '</tr>'
    ).join('');
}

// =============================================================================
// Download Dataset
// =============================================================================
async function downloadDataset() {
    if (!currentDataset) {
        alert('Dataset not loaded');
        return;
    }
    
    const btn = document.getElementById('download-btn');
    const originalText = btn.innerHTML;
    
    try {
        btn.innerHTML = '⏳ Downloading...';
        btn.disabled = true;
        
        // Get filename
        const filename = currentDataset.file_name || 
            `${currentDataset.name.replace(/[^a-z0-9]/gi, '_')}.csv`;
        
        // Download via API
        await api.downloadFile(`/download/${currentDataset.id}`, filename);
        
        // Update download count
        const countEl = document.getElementById('download-count');
        if (countEl) {
            const newCount = (currentDataset.download_count || 0) + 1;
            countEl.textContent = formatNumber(newCount);
            currentDataset.download_count = newCount;
        }
        
        btn.innerHTML = '✅ Downloaded!';
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 2000);
        
    } catch (error) {
        console.error('Download failed:', error);
        btn.innerHTML = '❌ Download Failed';
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 2000);
    }
}

// =============================================================================
// Utility Functions
// =============================================================================
function formatDate(dateStr) {
    if (!dateStr) return 'Unknown';
    try {
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        });
    } catch {
        return dateStr;
    }
}

function formatNumber(num, decimals = 0) {
    if (num === null || num === undefined) return '0';
    return Number(num).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatFileSize(bytes) {
    if (!bytes) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
