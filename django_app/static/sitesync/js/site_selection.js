/**
 * JavaScript for handling site selection and supply list loading.
 */

let selectedSiteId = null;

const currentSupplyFilters = {
    utilityType: 'all',
    meterType: 'all',
};

function selectSite(siteId, event) {
    "use strict";
    
    // Prevent event bubbling
    if (event) {
        event.preventDefault();
    }
    
    // Update UI: mark selected site
    const siteItems = document.querySelectorAll('.site-item');
    siteItems.forEach(item => {
        item.classList.remove('selected');
    });
    event.target.closest('.site-item').classList.add('selected');
    
    // Load supplies for the selected site
    selectedSiteId = siteId;
    loadSupplies(siteId);
}

function loadSupplies(siteId) {
    "use strict";
    
    const supplyPanel = document.getElementById('supply-panel');
    if (!supplyPanel) {
        console.error('Supply panel not found');
        return;
    }
    
    // Show loading state
    supplyPanel.innerHTML = '<h3>Supply Details</h3><div class="empty-state"><p>Loading supplies...</p></div>';
    
    const query = new URLSearchParams({
        site_id: String(siteId),
        utility_type: currentSupplyFilters.utilityType,
        meter_type: currentSupplyFilters.meterType,
    });

    // Fetch supplies
    fetch('/supplies/?' + query.toString())
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load supplies');
            }
            return response.text();
        })
        .then(html => {
            // Replace panel content with fetched HTML
            supplyPanel.innerHTML = '<h3>Supply Details</h3>' + html;
            syncTopStatsWithSelection();
        })
        .catch(error => {
            console.error('Error loading supplies:', error);
            supplyPanel.innerHTML = '<h3>Supply Details</h3><div class="empty-state"><p>Error loading supplies. Please try again.</p></div>';
        });
}

function applySupplyFilters() {
    "use strict";

    const utilitySelect = document.getElementById('supply-filter-utility');
    const meterSelect = document.getElementById('supply-filter-meter');

    currentSupplyFilters.utilityType = utilitySelect ? utilitySelect.value : 'all';
    currentSupplyFilters.meterType = meterSelect ? meterSelect.value : 'all';

    if (selectedSiteId) {
        loadSupplies(selectedSiteId);
    }
}

function syncTopStatsWithSelection() {
    "use strict";

    const statsPayload = document.getElementById('supply-filter-stats');
    const siteCountNode = document.getElementById('stats-site-count');
    const fiscalCountNode = document.getElementById('stats-fiscal-count');
    const submeterCountNode = document.getElementById('stats-submeter-count');

    if (!siteCountNode || !fiscalCountNode || !submeterCountNode) {
        return;
    }

    if (!statsPayload) {
        siteCountNode.textContent = siteCountNode.dataset.default || siteCountNode.textContent;
        fiscalCountNode.textContent = fiscalCountNode.dataset.default || fiscalCountNode.textContent;
        submeterCountNode.textContent = submeterCountNode.dataset.default || submeterCountNode.textContent;
        return;
    }

    siteCountNode.textContent = statsPayload.dataset.siteCount || '0';
    fiscalCountNode.textContent = statsPayload.dataset.fiscalCount || '0';
    submeterCountNode.textContent = statsPayload.dataset.submeterCount || '0';
}

// Auto-select first site on page load if available
document.addEventListener('DOMContentLoaded', function() {
    "use strict";
    const firstSite = document.querySelector('.site-item');
    if (firstSite) {
        // Simulate click on first site
        const siteId = firstSite.getAttribute('data-site-id');
        firstSite.classList.add('selected');
        if (siteId) {
            selectedSiteId = siteId;
            loadSupplies(siteId);
        }
    }
});
