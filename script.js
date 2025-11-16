// Update slider values
document.getElementById('maxPrice').oninput = function() {
    document.getElementById('priceValue').textContent = '$' + parseInt(this.value).toLocaleString();
};

document.getElementById('minGrad').oninput = function() {
    document.getElementById('gradValue').textContent = this.value + '%';
};

document.getElementById('minRetention').oninput = function() {
    document.getElementById('retentionValue').textContent = this.value + '%';
};

document.getElementById('topN').oninput = function() {
    document.getElementById('topNValue').textContent = this.value;
};

// Load states
fetch('/api/states')
    .then(res => res.json())
    .then(states => {
        const select = document.getElementById('state');
        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            select.appendChild(option);
        });
    })
    .catch(err => console.error('Error loading states:', err));

// Handle form submission
document.getElementById('recommendForm').onsubmit = async function(e) {
    e.preventDefault();
    
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    loading.style.display = 'block';
    results.innerHTML = '';

    // Get MSI preferences
    const msiPreferences = Array.from(document.querySelectorAll('.checkbox-group input:checked'))
        .map(cb => cb.value);

    const data = {
        maxNetPrice: parseInt(document.getElementById('maxPrice').value),
        minGradRate: parseInt(document.getElementById('minGrad').value),
        minRetention: parseInt(document.getElementById('minRetention').value),
        topN: parseInt(document.getElementById('topN').value),
        msiPreferences: msiPreferences,
        preferredState: document.getElementById('state').value || null,
        focusPell: document.getElementById('focusPell').checked  // 🎯 MISSION-ALIGNED: Pell focus
    };

    // Show loading state on dashboards immediately
    showTableauLoading();
    
    try {
        // Fetch both API calls in parallel for faster loading
        console.log('🚀 Fetching recommendations...');
        
        const dataFor200 = {...data, topN: 200};
        
        // Add timeout wrapper for fetch
        const fetchWithTimeout = (url, options, timeout = 30000) => {
            return Promise.race([
                fetch(url, options),
                new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('Request timeout')), timeout)
                )
            ]);
        };
        
        const [response, response200] = await Promise.all([
            fetchWithTimeout('/api/recommend', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }, 30000),
            fetchWithTimeout('/api/recommend', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(dataFor200)
            }, 30000)
        ]);

        if (!response.ok || !response200.ok) {
            throw new Error(`Server returned error: ${response.status} / ${response200.status}`);
        }

        const [result, result200] = await Promise.all([
            response.json(),
            response200.json()
        ]);
        
        if (result.success) {
            // Display the top N in cards
            displayResults(result.results);
            loading.style.display = 'none';
            
            // Update Tableau dashboards immediately using iframe URL filtering
            if (result200.success) {
                console.log('✅ Updating Tableau dashboards now...');
                updateTableauDashboards(result.results, result200.results);
                hideTableauLoading();
                
                // Scroll to Tableau dashboard
                setTimeout(() => {
                    document.querySelector('.tableau-section').scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'start' 
                    });
                }, 500);
            } else {
                console.warn('⚠️ Tableau data fetch failed, but recommendations are shown');
                hideTableauLoading();
            }
        } else {
            loading.style.display = 'none';
            hideTableauLoading();
            results.innerHTML = '<p style="color: red;">Error: ' + result.error + '</p>';
        }
    } catch (error) {
        loading.style.display = 'none';
        hideTableauLoading();
        
        console.error('❌ Error details:', error);
        
        let errorMessage = 'Error connecting to server.';
        if (error.message === 'Request timeout') {
            errorMessage = 'Request timed out. The server is taking too long to respond. Try reducing the number of results or simplifying your search.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Cannot reach the server. Make sure Flask is running on port 5000. Check the terminal for errors.';
        } else {
            errorMessage = `Server error: ${error.message}. Check browser console (F12) for details.`;
        }
        
        results.innerHTML = `
            <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 1.5rem; color: #856404;">
                <strong>⚠️ ${errorMessage}</strong>
                <details style="margin-top: 1rem; cursor: pointer;">
                    <summary style="font-weight: 500;">Troubleshooting Tips</summary>
                    <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                        <li>Make sure Flask is running (check terminal)</li>
                        <li>Try refreshing the page (Ctrl + Shift + R)</li>
                        <li>Try reducing "Number of Results" slider</li>
                        <li>Check browser console (F12) for detailed errors</li>
                    </ul>
                </details>
            </div>
        `;
    }
};

function displayResults(colleges) {
    const resultsDiv = document.getElementById('results');
    
    if (colleges.length === 0) {
        resultsDiv.innerHTML = '<p>No colleges found matching your criteria.</p>';
        return;
    }

    // Calculate min and max scores for percentage scaling (1-100%)
    const scores = colleges.map(c => c.HybridScore);
    const minScore = Math.min(...scores);
    const maxScore = Math.max(...scores);
    const scoreRange = maxScore - minScore;
    
    // Function to convert score to percentage (1-100%)
    const toPercentage = (score) => {
        if (scoreRange === 0) return 100; // If all scores are the same, show 100%
        // Scale to 1-100% range, with top score = 100%, lowest = 1%
        return Math.round(((score - minScore) / scoreRange) * 99 + 1);
    };

    let html = '';
    
    // Add scroll hint if more than 3 results
    if (colleges.length > 3) {
        html += '<div style="background: #f0f7ff; border: 1px solid #007aff33; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1rem; text-align: center; color: #007aff; font-size: 0.9rem;">';
        html += `📋 Showing ${colleges.length} recommendations — Scroll down to see all`;
        html += '</div>';
    }
    
    html += colleges.map((college, index) => `
        <div class="college-card">
            <h3>#${index + 1} - ${college['Institution Name']}</h3>
            <p class="college-info">📍 ${college.City || 'N/A'}, ${college['State Abbreviation']} - ${college.Region}</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-label">Net Price</div>
                    <div class="stat-value">$${Math.round(college['Net Price']).toLocaleString()}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">🎯 Affordability Gap</div>
                    <div class="stat-value" style="color: ${college['Affordability Gap (net price minus income earned working 10 hrs at min wage)'] < 0 ? '#28a745' : '#dc3545'};">
                        $${Math.round(college['Affordability Gap (net price minus income earned working 10 hrs at min wage)']).toLocaleString()}
                    </div>
                </div>
                <div class="stat">
                    <div class="stat-label">Graduation Rate</div>
                    <div class="stat-value">${(college["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"] || 0).toFixed(1)}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">🎯 Pell Grad Rate (6yr)</div>
                    <div class="stat-value">${(college["Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"] || 0).toFixed(1)}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Retention Rate</div>
                    <div class="stat-value">${(college['First-Time, Full-Time Retention Rate'] || 0).toFixed(1)}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">🎯 % Pell Students</div>
                    <div class="stat-value">${(college['Percent of First-Time, Full-Time Undergraduates Awarded Pell Grants'] || 0).toFixed(1)}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Match Score</div>
                    <div class="stat-value" style="color: #007aff;">${toPercentage(college.HybridScore)}%</div>
                </div>
            </div>
        </div>
    `).join('');
    
    resultsDiv.innerHTML = html;
    
    // Scroll to top of results
    resultsDiv.scrollTop = 0;
}

// Tableau dashboard iframes and base URLs
const tableauDashboard1 = () => document.getElementById('tableau-dashboard-1');
const tableauDashboard2 = () => document.getElementById('tableau-dashboard-2');
const baseDashboard1Url = 'https://public.tableau.com/views/ProccessedBook/Dashboard1';
const baseDashboard2Url = 'https://public.tableau.com/views/ProccessedBook/Dashboard2';

// Show loading state on Tableau dashboards
function showTableauLoading() {
    const tableauSection = document.querySelector('.tableau-section');
    if (!tableauSection) return;
    
    // Add loading overlay
    let overlay = document.getElementById('tableau-loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'tableau-loading-overlay';
        overlay.style.cssText = `
            position: relative;
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            margin: 1rem 0;
            border-radius: 8px;
            text-align: center;
            border: 2px dashed #007aff;
        `;
        overlay.innerHTML = `
            <div style="color: #007aff; font-size: 1.1rem; font-weight: 500;">
                🔄 Updating dashboards with your recommendations...
            </div>
            <div style="margin-top: 0.5rem; color: #666; font-size: 0.9rem;">
                Please wait a moment
            </div>
        `;
        tableauSection.appendChild(overlay);
    }
    overlay.style.display = 'block';
}

// Hide loading state on Tableau dashboards
function hideTableauLoading() {
    const overlay = document.getElementById('tableau-loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

/**
 * Update Tableau dashboards using iframe URL filtering
 * Note: URL length limits (~2000 chars) mean we can't filter with too many colleges
 * So we'll just reload the dashboards and let them show all data
 */
function updateTableauDashboards(topColleges, allColleges) {
    if (!topColleges) {
        console.log('⚠️ No colleges to display');
        return;
    }
    
    console.log('🔄 Refreshing Tableau dashboards...');
    console.log(`  → Your results: ${topColleges.length} colleges`);
    console.log(`  → Extended data: ${allColleges.length} colleges`);
    
    // Define the base URLs with refresh parameters
    const dashboard1BaseUrl = `${baseDashboard1Url}?:language=en-US&:embed=y&:display_count=n&:showVizHome=no&:refresh=yes`;
    const dashboard2BaseUrl = `${baseDashboard2Url}?:language=en-US&:embed=y&:display_count=n&:showVizHome=no&:refresh=yes`;
    let finalUrl1 = dashboard1BaseUrl;
    let finalUrl2 = dashboard2BaseUrl;
    // Check if we can and should apply a URL filter (e.g., <= 20 colleges is safe)
    if (topColleges.length > 0 && topColleges.length <= 20) {
        try {
            const topNNames = topColleges.map(c => c['Institution Name']);
            const filterValue = topNNames.join(',');
            
            // Create filter URLs for *both* dashboards
            const filterUrl1 = `${baseDashboard1Url}?Institution%20Name=${encodeURIComponent(filterValue)}&:language=en-US&:embed=y&:display_count=n&:showVizHome=no`;
            const filterUrl2 = `${baseDashboard2Url}?Institution%20Name=${encodeURIComponent(filterValue)}&:language=en-US&:embed=y&:display_count=n&:showVizHome=no`;
            // Check URL length (most browsers support ~2000 chars)
            if (filterUrl1.length < 2000 && filterUrl2.length < 2000) {
                console.log(`  ✓ Applying URL filter for ${topColleges.length} colleges to BOTH dashboards.`);
                finalUrl1 = filterUrl1;
                finalUrl2 = filterUrl2;
            } else {
                console.log(`  ⚠️ URL too long (${filterUrl1.length} chars), loading base dashboards.`);
                // finalUrl1 and finalUrl2 are already set to base URLs
            }
        } catch (error) {
            console.error('  ✗ Error building dashboard URLs, loading base dashboards:', error);
            // finalUrl1 and finalUrl2 are already set to base URLs
        }
    } else if (topColleges.length === 0) {
        console.log('  ℹ️ No results to filter on, loading base dashboards.');
        // finalUrl1 and finalUrl2 are already set to base URLs
    } else {
        // Too many colleges for URL filtering
        console.log(`  ℹ️ Too many colleges (${topColleges.length}) for URL filtering, loading base dashboards.`);
        // finalUrl1 and finalUrl2 are already set to base URLs
    }
    
    // Set the .src property for both iframes
    if (tableauDashboard1()) {
        tableauDashboard1().src = finalUrl1;
    }
    
    if (tableauDashboard2()) {
        tableauDashboard2().src = finalUrl2;
    }
    
    console.log('✅ Tableau dashboards refreshed!');
    console.log('💡 Tip: Use the Tableau filters within each dashboard to explore your recommendations');
}

// Note: We now use iframe URL filtering instead of the Tableau JavaScript API
// The updateTableauDashboards() function above handles all filtering by changing the iframe src

