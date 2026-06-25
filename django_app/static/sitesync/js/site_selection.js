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
    const siteItem = event.target.closest('.site-item');
    siteItem.classList.add('selected');

    const checkbox = siteItem.querySelector('.site-selector');
    if (checkbox) {
        checkbox.checked = true;
    }
    updateTopStatsFromCheckedSites();
    
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
    
    const checkedSiteIds = getCheckedSiteIds();
    if (!checkedSiteIds.length) {
        renderNoSelectedSites();
        return;
    }

    const query = new URLSearchParams({
        site_ids: checkedSiteIds.join(','),
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
            updateTopStatsFromCheckedSites();
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

    updateTopStatsFromCheckedSites();
    loadSupplies(selectedSiteId);
}

function getCheckedSiteIds() {
    "use strict";

    return Array.from(document.querySelectorAll('.site-selector:checked'))
        .map((checkbox) => {
            const parent = checkbox.closest('.site-item');
            return parent ? parent.dataset.siteId : null;
        })
        .filter(Boolean);
}

function renderNoSelectedSites() {
    "use strict";

    const supplyPanel = document.getElementById('supply-panel');
    if (!supplyPanel) {
        return;
    }
    supplyPanel.innerHTML = '<h3>Supply Details</h3><div class="empty-state"><p>Select one or more sites to view supplies.</p></div>';
}

function getCountForSiteItem(siteItem) {
    "use strict";

    const utilityType = currentSupplyFilters.utilityType;
    const meterType = currentSupplyFilters.meterType;

    const totalFiscal = Number(siteItem.dataset.fiscalTotal || 0);
    const totalSubmeter = Number(siteItem.dataset.submeterTotal || 0);

    let fiscalCount = totalFiscal;
    let submeterCount = totalSubmeter;

    if (utilityType !== 'all') {
        fiscalCount = Number(siteItem.dataset['fiscal' + capitalizeFilterValue(utilityType)] || 0);
        submeterCount = Number(siteItem.dataset['submeter' + capitalizeFilterValue(utilityType)] || 0);
    }

    if (meterType === 'fiscal') {
        submeterCount = 0;
    } else if (meterType === 'sub') {
        fiscalCount = 0;
    }

    return {
        siteCount: Number(siteItem.dataset.siteCount || 1),
        fiscalCount,
        submeterCount,
    };
}

function capitalizeFilterValue(value) {
    "use strict";

    return value.charAt(0).toUpperCase() + value.slice(1);
}

function updateTopStatsFromCheckedSites() {
    "use strict";

    const siteCountNode = document.getElementById('stats-site-count');
    const fiscalCountNode = document.getElementById('stats-fiscal-count');
    const submeterCountNode = document.getElementById('stats-submeter-count');
    const selectedSitesCountNode = document.getElementById('selected-sites-count');
    const checkedSiteItems = Array.from(document.querySelectorAll('.site-selector:checked'))
        .map((checkbox) => checkbox.closest('.site-item'))
        .filter(Boolean);
    const visibleCheckedSiteItems = checkedSiteItems.filter((siteItem) => siteItem.style.display !== 'none');

    if (!siteCountNode || !fiscalCountNode || !submeterCountNode) {
        return;
    }

    if (selectedSitesCountNode) {
        selectedSitesCountNode.textContent = 'Selected Sites: '
            + String(checkedSiteItems.length)
            + ' (' + String(visibleCheckedSiteItems.length) + ' visible)';
    }

    if (!checkedSiteItems.length) {
        siteCountNode.textContent = siteCountNode.dataset.default || siteCountNode.textContent;
        fiscalCountNode.textContent = fiscalCountNode.dataset.default || fiscalCountNode.textContent;
        submeterCountNode.textContent = submeterCountNode.dataset.default || submeterCountNode.textContent;
        return;
    }

    const totals = checkedSiteItems.reduce((accumulator, siteItem) => {
        const counts = getCountForSiteItem(siteItem);
        accumulator.siteCount += counts.siteCount;
        accumulator.fiscalCount += counts.fiscalCount;
        accumulator.submeterCount += counts.submeterCount;
        return accumulator;
    }, {
        siteCount: 0,
        fiscalCount: 0,
        submeterCount: 0,
    });

    siteCountNode.textContent = String(totals.siteCount);
    fiscalCountNode.textContent = String(totals.fiscalCount);
    submeterCountNode.textContent = String(totals.submeterCount);
}

function toggleSiteSelection(event) {
    "use strict";

    if (event && event.target) {
        event.stopPropagation();
    }
    updateTopStatsFromCheckedSites();
    loadSupplies(selectedSiteId);
}

function selectAllSites() {
    "use strict";

    const siteItems = Array.from(document.querySelectorAll('.site-item'));
    siteItems.forEach((siteItem) => {
        if (siteItem.style.display === 'none') {
            return;
        }
        const checkbox = siteItem.querySelector('.site-selector');
        if (checkbox) {
            checkbox.checked = true;
        }
    });
    updateTopStatsFromCheckedSites();
    loadSupplies(selectedSiteId);
}

function deselectAllSites() {
    "use strict";

    document.querySelectorAll('.site-selector:checked').forEach((checkbox) => {
        checkbox.checked = false;
    });
    document.querySelectorAll('.site-item.selected').forEach((item) => {
        item.classList.remove('selected');
    });
    updateTopStatsFromCheckedSites();
    loadSupplies(selectedSiteId);
}

// Auto-select first site on page load if available
document.addEventListener('DOMContentLoaded', function() {
    "use strict";
    const firstSite = document.querySelector('.site-item');
    updateTopStatsFromCheckedSites();
    if (firstSite) {
        // Simulate click on first site
        const siteId = firstSite.getAttribute('data-site-id');
        firstSite.classList.add('selected');
        const checkbox = firstSite.querySelector('.site-selector');
        if (checkbox) {
            checkbox.checked = true;
        }
        if (siteId) {
            selectedSiteId = siteId;
            loadSupplies(siteId);
        }
    }
});
