/**
 * JavaScript for handling site selection and supply list loading.
 */

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
    
    // Fetch supplies
    fetch('/supplies/?site_id=' + encodeURIComponent(siteId))
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load supplies');
            }
            return response.text();
        })
        .then(html => {
            // Replace panel content with fetched HTML
            supplyPanel.innerHTML = '<h3>Supply Details</h3>' + html;
        })
        .catch(error => {
            console.error('Error loading supplies:', error);
            supplyPanel.innerHTML = '<h3>Supply Details</h3><div class="empty-state"><p>Error loading supplies. Please try again.</p></div>';
        });
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
            loadSupplies(siteId);
        }
    }
});
