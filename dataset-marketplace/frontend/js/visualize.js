/* =============================================================================
   Data Visualization JavaScript
   Handles dataset visualization with Chart.js
   ============================================================================= */

// -----------------------------------------------------------------------------
// Global Variables
// -----------------------------------------------------------------------------
let datasetData = [];
let headers = [];
let numericColumns = [];
let categoricalColumns = [];
let currentChart = null;

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
    
    // Get dataset ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const datasetId = urlParams.get('id');
    
    if (datasetId) {
        loadDataset(datasetId);
    } else {
        showError('No dataset ID provided');
    }
    
    // Event listeners
    document.getElementById('generate-chart')?.addEventListener('click', generateChart);
    document.getElementById('chart-type')?.addEventListener('change', updateColumnSelectors);
});

// -----------------------------------------------------------------------------
// Load Dataset
// -----------------------------------------------------------------------------
async function loadDataset(datasetId) {
    const loading = document.getElementById('loading');
    const errorState = document.getElementById('error-state');
    
    try {
        loading.style.display = 'flex';
        
        // Fetch dataset details
        const response = await api.get(`/dataset/${datasetId}`);
        const dataset = response.dataset;
        
        // Update page title
        document.getElementById('dataset-title').textContent = dataset.name;
        document.title = `Visualize: ${dataset.name}`;
        
        // Parse stored data
        if (dataset.preview_data) {
            datasetData = typeof dataset.preview_data === 'string' 
                ? JSON.parse(dataset.preview_data) 
                : dataset.preview_data;
        } else if (dataset.data) {
            datasetData = typeof dataset.data === 'string'
                ? JSON.parse(dataset.data)
                : dataset.data;
        }
        
        if (!datasetData || datasetData.length === 0) {
            throw new Error('No data available for visualization');
        }
        
        // Get headers
        headers = Object.keys(datasetData[0]);
        
        // Classify columns
        classifyColumns();
        
        // Update UI
        updateDatasetInfo();
        populateColumnSelectors();
        renderDataTable();
        calculateStatistics();
        
        // Hide loading, show content
        loading.style.display = 'none';
        document.getElementById('dataset-info').style.display = 'block';
        document.getElementById('viz-controls').style.display = 'flex';
        document.getElementById('chart-container').style.display = 'block';
        document.getElementById('stats-section').style.display = 'block';
        document.getElementById('preview-section').style.display = 'block';
        
        // Generate initial chart
        generateChart();
        
    } catch (error) {
        loading.style.display = 'none';
        showError(error.message);
    }
}

// -----------------------------------------------------------------------------
// Classify Columns
// -----------------------------------------------------------------------------
function classifyColumns() {
    numericColumns = [];
    categoricalColumns = [];
    
    headers.forEach(header => {
        // Check first 10 non-null values
        let numericCount = 0;
        let totalCount = 0;
        
        for (let i = 0; i < Math.min(datasetData.length, 10); i++) {
            const value = datasetData[i][header];
            if (value !== null && value !== undefined && value !== '') {
                totalCount++;
                if (!isNaN(parseFloat(value))) {
                    numericCount++;
                }
            }
        }
        
        // If more than 70% are numeric, classify as numeric
        if (totalCount > 0 && numericCount / totalCount > 0.7) {
            numericColumns.push(header);
        } else {
            categoricalColumns.push(header);
        }
    });
}

// -----------------------------------------------------------------------------
// Update Dataset Info
// -----------------------------------------------------------------------------
function updateDatasetInfo() {
    document.getElementById('total-rows').textContent = datasetData.length;
    document.getElementById('total-cols').textContent = headers.length;
    document.getElementById('numeric-cols').textContent = numericColumns.length;
    document.getElementById('categorical-cols').textContent = categoricalColumns.length;
}

// -----------------------------------------------------------------------------
// Populate Column Selectors
// -----------------------------------------------------------------------------
function populateColumnSelectors() {
    const xSelect = document.getElementById('x-column');
    const ySelect = document.getElementById('y-column');
    
    // Clear existing options
    xSelect.innerHTML = '';
    ySelect.innerHTML = '';
    
    // Add all columns to X
    headers.forEach(header => {
        const option = document.createElement('option');
        option.value = header;
        option.textContent = header;
        xSelect.appendChild(option);
    });
    
    // Add numeric columns to Y, or all if none numeric
    const yColumns = numericColumns.length > 0 ? numericColumns : headers;
    yColumns.forEach(header => {
        const option = document.createElement('option');
        option.value = header;
        option.textContent = header;
        ySelect.appendChild(option);
    });
    
    // Select defaults
    if (categoricalColumns.length > 0) {
        xSelect.value = categoricalColumns[0];
    }
    if (numericColumns.length > 0) {
        ySelect.value = numericColumns[0];
    }
}

// -----------------------------------------------------------------------------
// Update Column Selectors Based on Chart Type
// -----------------------------------------------------------------------------
function updateColumnSelectors() {
    const chartType = document.getElementById('chart-type').value;
    const aggregation = document.getElementById('aggregation');
    
    // Scatter plots don't need aggregation
    if (chartType === 'scatter') {
        aggregation.value = 'none';
        aggregation.disabled = true;
    } else {
        aggregation.disabled = false;
    }
}

// -----------------------------------------------------------------------------
// Generate Chart
// -----------------------------------------------------------------------------
function generateChart() {
    const chartType = document.getElementById('chart-type').value;
    const xColumn = document.getElementById('x-column').value;
    const yColumn = document.getElementById('y-column').value;
    const aggregation = document.getElementById('aggregation').value;
    
    // Destroy existing chart
    if (currentChart) {
        currentChart.destroy();
    }
    
    // Prepare data
    let chartData;
    
    if (aggregation !== 'none' && chartType !== 'scatter') {
        chartData = aggregateData(xColumn, yColumn, aggregation);
    } else {
        chartData = prepareRawData(xColumn, yColumn, chartType);
    }
    
    // Create chart
    const ctx = document.getElementById('data-chart').getContext('2d');
    
    const config = {
        type: chartType,
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: `${yColumn} by ${xColumn}`,
                    font: { size: 16, weight: 'bold' }
                }
            }
        }
    };
    
    // Special options for different chart types
    if (chartType === 'scatter') {
        config.options.scales = {
            x: { title: { display: true, text: xColumn } },
            y: { title: { display: true, text: yColumn } }
        };
    } else if (chartType === 'bar' || chartType === 'line') {
        config.options.scales = {
            y: { beginAtZero: true }
        };
    }
    
    currentChart = new Chart(ctx, config);
}

// -----------------------------------------------------------------------------
// Aggregate Data
// -----------------------------------------------------------------------------
function aggregateData(xColumn, yColumn, aggregation) {
    const grouped = {};
    
    datasetData.forEach(row => {
        const key = String(row[xColumn] || 'Unknown');
        const value = parseFloat(row[yColumn]) || 0;
        
        if (!grouped[key]) {
            grouped[key] = [];
        }
        grouped[key].push(value);
    });
    
    const labels = Object.keys(grouped);
    const values = labels.map(key => {
        const arr = grouped[key];
        switch (aggregation) {
            case 'sum': return arr.reduce((a, b) => a + b, 0);
            case 'avg': return arr.reduce((a, b) => a + b, 0) / arr.length;
            case 'count': return arr.length;
            case 'min': return Math.min(...arr);
            case 'max': return Math.max(...arr);
            default: return arr[0];
        }
    });
    
    return {
        labels: labels.slice(0, 20), // Limit to 20 categories
        datasets: [{
            label: `${aggregation.toUpperCase()} of ${yColumn}`,
            data: values.slice(0, 20),
            backgroundColor: generateColors(Math.min(labels.length, 20)),
            borderColor: generateColors(Math.min(labels.length, 20), 1),
            borderWidth: 1
        }]
    };
}

// -----------------------------------------------------------------------------
// Prepare Raw Data
// -----------------------------------------------------------------------------
function prepareRawData(xColumn, yColumn, chartType) {
    const limit = 50; // Limit data points for performance
    const slicedData = datasetData.slice(0, limit);
    
    if (chartType === 'scatter') {
        return {
            datasets: [{
                label: `${xColumn} vs ${yColumn}`,
                data: slicedData.map(row => ({
                    x: parseFloat(row[xColumn]) || 0,
                    y: parseFloat(row[yColumn]) || 0
                })),
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: 'rgba(102, 126, 234, 1)',
                pointRadius: 5
            }]
        };
    }
    
    return {
        labels: slicedData.map(row => String(row[xColumn] || '')),
        datasets: [{
            label: yColumn,
            data: slicedData.map(row => parseFloat(row[yColumn]) || 0),
            backgroundColor: generateColors(slicedData.length),
            borderColor: generateColors(slicedData.length, 1),
            borderWidth: 1
        }]
    };
}

// -----------------------------------------------------------------------------
// Generate Colors
// -----------------------------------------------------------------------------
function generateColors(count, alpha = 0.6) {
    const baseColors = [
        `rgba(102, 126, 234, ${alpha})`,
        `rgba(118, 75, 162, ${alpha})`,
        `rgba(240, 147, 251, ${alpha})`,
        `rgba(46, 204, 113, ${alpha})`,
        `rgba(241, 196, 15, ${alpha})`,
        `rgba(231, 76, 60, ${alpha})`,
        `rgba(52, 152, 219, ${alpha})`,
        `rgba(155, 89, 182, ${alpha})`,
        `rgba(26, 188, 156, ${alpha})`,
        `rgba(230, 126, 34, ${alpha})`
    ];
    
    const colors = [];
    for (let i = 0; i < count; i++) {
        colors.push(baseColors[i % baseColors.length]);
    }
    return colors;
}

// -----------------------------------------------------------------------------
// Calculate Statistics
// -----------------------------------------------------------------------------
function calculateStatistics() {
    const statsGrid = document.getElementById('stats-grid');
    statsGrid.innerHTML = '';
    
    numericColumns.forEach(column => {
        const values = datasetData
            .map(row => parseFloat(row[column]))
            .filter(v => !isNaN(v));
        
        if (values.length === 0) return;
        
        const sum = values.reduce((a, b) => a + b, 0);
        const avg = sum / values.length;
        const min = Math.min(...values);
        const max = Math.max(...values);
        const sorted = [...values].sort((a, b) => a - b);
        const median = sorted.length % 2 === 0
            ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
            : sorted[Math.floor(sorted.length / 2)];
        
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = `
            <h4>${escapeHtml(column)}</h4>
            <div class="stat-row"><span>Min:</span><strong>${min.toFixed(2)}</strong></div>
            <div class="stat-row"><span>Max:</span><strong>${max.toFixed(2)}</strong></div>
            <div class="stat-row"><span>Average:</span><strong>${avg.toFixed(2)}</strong></div>
            <div class="stat-row"><span>Median:</span><strong>${median.toFixed(2)}</strong></div>
            <div class="stat-row"><span>Sum:</span><strong>${sum.toFixed(2)}</strong></div>
        `;
        statsGrid.appendChild(card);
    });
}

// -----------------------------------------------------------------------------
// Render Data Table
// -----------------------------------------------------------------------------
function renderDataTable() {
    const thead = document.getElementById('table-head');
    const tbody = document.getElementById('table-body');
    
    // Render header
    thead.innerHTML = `<tr>${headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}</tr>`;
    
    // Render first 20 rows
    const displayData = datasetData.slice(0, 20);
    tbody.innerHTML = displayData.map(row =>
        `<tr>${headers.map(h => `<td>${escapeHtml(String(row[h] ?? ''))}</td>`).join('')}</tr>`
    ).join('');
}

// -----------------------------------------------------------------------------
// Show Error
// -----------------------------------------------------------------------------
function showError(message) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error-state').style.display = 'block';
    document.getElementById('error-message').textContent = message;
}

// -----------------------------------------------------------------------------
// Utility Functions
// -----------------------------------------------------------------------------
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
