/**
 * AI Summary for Prediction Page
 * Displays concise news analysis with bullet points
 */

function loadAISummary(symbol) {
    // Show loading
    const summaryContainer = document.getElementById('ai-summary-container');
    if (!summaryContainer) return;
    
    summaryContainer.innerHTML = `
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">📰 Latest News & AI Analysis</h5>
            </div>
            <div class="card-body">
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <p class="mt-2">Loading AI analysis...</p>
                </div>
            </div>
        </div>
    `;
    
    // Fetch AI summary
    fetch(`/api/ai-summary/${symbol}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayAISummary(data.summary, data.news_count);
            } else {
                showError(data.message || 'Failed to load AI summary');
            }
        })
        .catch(error => {
            console.error('Error loading AI summary:', error);
            showError('Failed to load AI summary');
        });
}

function displayAISummary(summary, newsCount) {
    const summaryContainer = document.getElementById('ai-summary-container');
    if (!summaryContainer) return;
    
    // Format the summary with proper HTML
    const formattedSummary = formatSummaryText(summary);
    
    summaryContainer.innerHTML = `
        <div class="card shadow-sm">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="fas fa-newspaper"></i> Latest News & AI Analysis
                </h5>
            </div>
            <div class="card-body">
                <div class="ai-summary-content">
                    ${formattedSummary}
                </div>
                <small class="text-muted mt-2 d-block">Based on ${newsCount} recent articles</small>
            </div>
        </div>
    `;
}

function formatSummaryText(text) {
    // Convert bullet points to HTML
    let formatted = text
        .replace(/^• (.+)$/gm, '<div class="summary-point"><strong>• $1</strong></div>')
        .replace(/^  - (.+)$/gm, '<div class="summary-subpoint">- $1</div>')
        .replace(/\n\n/g, '<br>');
    
    return formatted;
}

function showError(message) {
    const summaryContainer = document.getElementById('ai-summary-container');
    if (!summaryContainer) return;
    
    summaryContainer.innerHTML = `
        <div class="card">
            <div class="card-header bg-warning text-dark">
                <h5 class="mb-0">📰 Latest News & AI Analysis</h5>
            </div>
            <div class="card-body">
                <div class="alert alert-warning mb-0">
                    <i class="fas fa-exclamation-triangle"></i> ${message}
                </div>
            </div>
        </div>
    `;
}

// Auto-load when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Get symbol from page (adjust selector as needed)
    const symbolElement = document.querySelector('[data-stock-symbol]');
    if (symbolElement) {
        const symbol = symbolElement.getAttribute('data-stock-symbol');
        loadAISummary(symbol);
    }
});
