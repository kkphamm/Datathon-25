// Update slider values and fill track
function updateSlider(slider, valueDisplay, format = (val) => val) {
    const value = slider.value;
    const min = slider.min;
    const max = slider.max;
    const percentage = ((value - min) / (max - min)) * 100;
    
    // Update value display
    valueDisplay.textContent = format(value);
    
    // Update slider track fill
    slider.style.setProperty('--value', `${percentage}%`);
}

// Initialize sliders with formatted values and filled tracks
document.getElementById('maxPrice').oninput = function() {
    updateSlider(this, document.getElementById('priceValue'), 
        (val) => '$' + parseInt(val).toLocaleString());
};

document.getElementById('minGrad').oninput = function() {
    updateSlider(this, document.getElementById('gradValue'), 
        (val) => val + '%');
};

document.getElementById('minRetention').oninput = function() {
    updateSlider(this, document.getElementById('retentionValue'), 
        (val) => val + '%');
};

document.getElementById('topN').oninput = function() {
    updateSlider(this, document.getElementById('topNValue'));
};

// Initialize slider fills on page load
window.addEventListener('DOMContentLoaded', () => {
    updateSlider(document.getElementById('maxPrice'), document.getElementById('priceValue'), 
        (val) => '$' + parseInt(val).toLocaleString());
    updateSlider(document.getElementById('minGrad'), document.getElementById('gradValue'), 
        (val) => val + '%');
    updateSlider(document.getElementById('minRetention'), document.getElementById('retentionValue'), 
        (val) => val + '%');
    updateSlider(document.getElementById('topN'), document.getElementById('topNValue'));
});

// Scroll reveal animation
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

// Observe scroll reveal elements
document.querySelectorAll('.scroll-reveal').forEach(el => {
    scrollObserver.observe(el);
});

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

// Handle form submission with loading state
document.getElementById('recommendForm').onsubmit = async function(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    // Enable button loading state
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    submitBtn.querySelector('.button-text').innerHTML = `
        <span class="button-spinner"></span>
        Searching...
    `;
    
    loading.classList.add('active');
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
        focusPell: document.getElementById('focusPell').checked
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
            // Display the top N in cards with staggered animation
            displayResults(result.results);
            loading.classList.remove('active');
            
            // Update Tableau dashboards immediately using iframe URL filtering
            if (result200.success) {
                console.log('✅ Updating Tableau dashboards now...');
                updateTableauDashboards(result.results, result200.results);
                hideTableauLoading();
                
                // Scroll to Tableau dashboard
                setTimeout(() => {
                    document.querySelector('.tableau-wrapper').scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'start' 
                    });
                }, 500);
            } else {
                console.warn('⚠️ Tableau data fetch failed, but recommendations are shown');
                hideTableauLoading();
            }
        } else {
            loading.classList.remove('active');
            hideTableauLoading();
            results.innerHTML = '<p style="color: red;">Error: ' + result.error + '</p>';
        }
    } catch (error) {
        loading.classList.remove('active');
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
            <div style="background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 12px; padding: 1.5rem; color: #92400E;">
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
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
        submitBtn.querySelector('.button-text').innerHTML = 'Get Recommendations';
    }
};

// Display results with staggered fade-in animation
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
        if (scoreRange === 0) return 100;
        return Math.round(((score - minScore) / scoreRange) * 99 + 1);
    };

    let html = '';
    
    // Add scroll hint if more than 3 results
    if (colleges.length > 3) {
        html += '<div style="background: var(--primary-light); border: 1px solid var(--primary); border-radius: 10px; padding: 0.875rem 1.25rem; margin-bottom: 1.5rem; text-align: center; color: var(--primary); font-size: 0.9rem; font-weight: 600;">';
        html += `📋 Showing ${colleges.length} recommendations — Scroll down to see all`;
        html += '</div>';
    }
    
    html += colleges.map((college, index) => `
        <div class="college-card" style="animation-delay: ${index * 0.08}s">
            <h3>#${index + 1} - ${college['Institution Name']}</h3>
            <p class="college-info">📍 ${college.City || 'N/A'}, ${college['State Abbreviation']} - ${college.Region}</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-label">Net Price</div>
                    <div class="stat-value">$${Math.round(college['Net Price']).toLocaleString()}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Affordability Gap</div>
                    <div class="stat-value" style="color: ${college['Affordability Gap (net price minus income earned working 10 hrs at min wage)'] < 0 ? 'var(--success)' : 'var(--danger)'};">
                        $${Math.round(college['Affordability Gap (net price minus income earned working 10 hrs at min wage)']).toLocaleString()}
                    </div>
                </div>
                <div class="stat">
                    <div class="stat-label">Graduation Rate</div>
                    <div class="stat-value">${(college["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"] || 0).toFixed(1)}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Pell Grad Rate</div>
                    <div class="stat-value">${(college["Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"] || 0).toFixed(1)}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Retention Rate</div>
                    <div class="stat-value">${(college['First-Time, Full-Time Retention Rate'] || 0).toFixed(1)}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">% Pell Students</div>
                    <div class="stat-value">${(college['Percent of First-Time, Full-Time Undergraduates Awarded Pell Grants'] || 0).toFixed(1)}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">
                        Match Score
                        <span class="tooltip-container">
                            <span class="info-icon">i</span>
                            <span class="tooltip">Personalized match based on your preferences (100% = best fit)</span>
                        </span>
                    </div>
                    <div class="stat-value" style="color: var(--primary);">${toPercentage(college.HybridScore)}%</div>
                </div>
            </div>
        </div>
    `).join('');
    
    resultsDiv.innerHTML = html;
    
    // Trigger staggered animation
    setTimeout(() => {
        const cards = resultsDiv.querySelectorAll('.college-card');
        cards.forEach(card => {
            card.classList.add('fade-in');
        });
    }, 50);
    
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
    
    let overlay = document.getElementById('tableau-loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'tableau-loading-overlay';
        overlay.style.cssText = `
            position: relative;
            background: linear-gradient(135deg, var(--primary-light) 0%, #E0E7FF 100%);
            padding: 2.5rem;
            margin: 1.5rem 0;
            border-radius: 16px;
            text-align: center;
            border: 2px solid var(--primary);
        `;
        overlay.innerHTML = `
            <div style="color: var(--primary); font-size: 1.15rem; font-weight: 600; margin-bottom: 0.5rem;">
                🔄 Updating dashboards with your recommendations...
            </div>
            <div style="margin-top: 0.5rem; color: var(--text-secondary); font-size: 0.95rem;">
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
 */
function updateTableauDashboards(topColleges, allColleges) {
    if (!topColleges) {
        console.log('⚠️ No colleges to display');
        return;
    }
    
    console.log('🔄 Refreshing Tableau dashboards...');
    console.log(`  → Your results: ${topColleges.length} colleges`);
    console.log(`  → Extended data: ${allColleges.length} colleges`);
    
    const dashboard1BaseUrl = `${baseDashboard1Url}?:language=en-US&:embed=y&:display_count=n&:showVizHome=no&:refresh=yes`;
    const dashboard2BaseUrl = `${baseDashboard2Url}?:language=en-US&:embed=y&:display_count=n&:showVizHome=no&:refresh=yes`;
    let finalUrl1 = dashboard1BaseUrl;
    let finalUrl2 = dashboard2BaseUrl;
    
    if (topColleges.length > 0 && topColleges.length <= 20) {
        try {
            const topNNames = topColleges.map(c => c['Institution Name']);
            const filterValue = topNNames.join(',');
            
            const filterUrl1 = `${baseDashboard1Url}?Institution%20Name=${encodeURIComponent(filterValue)}&:language=en-US&:embed=y&:display_count=n&:showVizHome=no`;
            const filterUrl2 = `${baseDashboard2Url}?Institution%20Name=${encodeURIComponent(filterValue)}&:language=en-US&:embed=y&:display_count=n&:showVizHome=no`;
            
            if (filterUrl1.length < 2000 && filterUrl2.length < 2000) {
                console.log(`  ✓ Applying URL filter for ${topColleges.length} colleges to BOTH dashboards.`);
                finalUrl1 = filterUrl1;
                finalUrl2 = filterUrl2;
            } else {
                console.log(`  ⚠️ URL too long (${filterUrl1.length} chars), loading base dashboards.`);
            }
        } catch (error) {
            console.error('  ✗ Error building dashboard URLs, loading base dashboards:', error);
        }
    } else if (topColleges.length === 0) {
        console.log('  ℹ️ No results to filter on, loading base dashboards.');
    } else {
        console.log(`  ℹ️ Too many colleges (${topColleges.length}) for URL filtering, loading base dashboards.`);
    }
    
    if (tableauDashboard1()) {
        tableauDashboard1().src = finalUrl1;
    }
    
    if (tableauDashboard2()) {
        tableauDashboard2().src = finalUrl2;
    }
    
    console.log('✅ Tableau dashboards refreshed!');
    console.log('💡 Tip: Use the Tableau filters within each dashboard to explore your recommendations');
}
