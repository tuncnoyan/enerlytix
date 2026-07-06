/**
 * JavaScript for handling site selection and supply list loading.
 */

let selectedSiteId = null;

const currentSupplyFilters = {
    utilityType: 'all',
    meterType: 'fiscal',  // default: exclude submeters until the checkbox is ticked
};

function getCsrfToken() {
    "use strict";

    const match = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}

function setReportStatus(message, isWarning) {
    "use strict";

    const statusNode = document.getElementById('report-status');
    if (!statusNode) {
        return;
    }
    statusNode.textContent = message || '';
    statusNode.style.color = isWarning ? '#b91c1c' : '#0f766e';
}

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
    const includeSubmetersCheckbox = document.getElementById('supply-filter-include-submeters');

    currentSupplyFilters.utilityType = utilitySelect ? utilitySelect.value : 'all';
    if (includeSubmetersCheckbox) {
        currentSupplyFilters.meterType = includeSubmetersCheckbox.checked ? 'all' : 'fiscal';
    } else if (meterSelect) {
        currentSupplyFilters.meterType = meterSelect.value;
    } else {
        currentSupplyFilters.meterType = 'fiscal';
    }

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
        updateReportButtonState();
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
    updateReportButtonState();
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

function getSelectedSupplyIds() {
    "use strict";

    return Array.from(document.querySelectorAll('.supply-selector:checked'))
        .map((checkbox) => checkbox.getAttribute('data-supply-id'))
        .filter(Boolean);
}

function getReportingMonthValue() {
    "use strict";

    const input = document.getElementById('import-reporting-month');
    return input ? input.value : '';
}

function getImportDataTypeValue() {
    "use strict";

    const input = document.getElementById('import-data-type');
    return input ? input.value : 'monthly';
}

function getReportMonthValue() {
    "use strict";

    const input = document.getElementById('report-reporting-month');
    return input ? input.value : '';
}

function updateReportButtonState() {
    "use strict";

    const button = document.getElementById('trigger-report-button');
    if (!button) {
        return;
    }

    const checkedSiteIds = getCheckedSiteIds();
    const reportMonth = getReportMonthValue();
    const isEnabled = checkedSiteIds.length === 1 && Boolean(reportMonth);

    button.disabled = !isEnabled;
    if (checkedSiteIds.length === 0) {
        button.title = 'Select a site first';
        setReportStatus('Select a site first.', true);
    } else if (checkedSiteIds.length > 1) {
        button.title = 'Select only one site to create a report';
        setReportStatus('Select only one site to create a report.', true);
    } else if (!reportMonth) {
        button.title = 'Select a reporting month';
        setReportStatus('Select a reporting month.', true);
    } else {
        button.title = 'Create a report for the selected site';
        setReportStatus('', false);
    }
}

function triggerReportView() {
    "use strict";

    const checkedSiteIds = getCheckedSiteIds();
    const reportMonth = getReportMonthValue();
    if (checkedSiteIds.length !== 1) {
        updateReportButtonState();
        return;
    }

    if (!reportMonth) {
        updateReportButtonState();
        return;
    }

    const params = new URLSearchParams({
        site_id: checkedSiteIds[0],
        end_month: reportMonth,
    });

    // Pass the currently checked supply external IDs so the report only
    // renders sections for supplies the user actually selected.
    const selectedSupplyIds = getSelectedSupplyIds();
    if (selectedSupplyIds.length > 0) {
        params.set('supply_ids', selectedSupplyIds.join(','));
    }

    window.location.href = '/report/?' + params.toString();
}

function getRefreshModeValue() {
    "use strict";

    const input = document.getElementById('import-refresh-mode');
    return input ? input.checked : false;
}

function setImportStatus(message, isError) {
    "use strict";

    const statusNode = document.getElementById('import-status');
    if (!statusNode) {
        return;
    }
    statusNode.textContent = message || '';
    statusNode.style.color = isError ? '#b91c1c' : '#0f766e';
}

function triggerConsumptionImport() {
    "use strict";

    const supplyIds = getSelectedSupplyIds();
    const reportingMonth = getReportingMonthValue();
    const dataType = getImportDataTypeValue();
    const refreshMode = getRefreshModeValue();
    const button = document.getElementById('trigger-import-button');

    if (!reportingMonth) {
        setImportStatus('Reporting month is required.', true);
        return;
    }
    if (!supplyIds.length) {
        setImportStatus('Select at least one supply to load data.', true);
        return;
    }

    setImportStatus('Import is running. Please wait...', false);
    if (button) {
        button.disabled = true;
    }

    fetch('/api/consumption-import/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
            supply_ids: supplyIds,
            reporting_month: reportingMonth,
            refresh_mode: refreshMode,
        }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error('Import request failed.');
            }
            return response.json();
        })
        .then(() => {
            const params = new URLSearchParams({
                reporting_month: reportingMonth,
                data_type: dataType,
                supply_ids: supplyIds.join(','),
            });
            window.location.href = '/consumption-display/?' + params.toString();
        })
        .catch((error) => {
            console.error(error);
            setImportStatus('Unable to run import. Please try again.', true);
        })
        .finally(() => {
            if (button) {
                button.disabled = false;
            }
        });
}

document.addEventListener('DOMContentLoaded', function() {
    "use strict";
    updateTopStatsFromCheckedSites();

    const now = new Date();
    const currentMonth = now.toISOString().slice(0, 7);
    const reportingMonthInput = document.getElementById('import-reporting-month');
    if (reportingMonthInput && !reportingMonthInput.value) {
        reportingMonthInput.value = currentMonth;
    }

    const reportMonthInput = document.getElementById('report-reporting-month');
    if (reportMonthInput && !reportMonthInput.value) {
        reportMonthInput.value = currentMonth;
    }

    const importButton = document.getElementById('trigger-import-button');
    if (importButton) {
        importButton.addEventListener('click', triggerConsumptionImport);
    }

    const reportButton = document.getElementById('trigger-report-button');
    if (reportButton) {
        reportButton.addEventListener('click', triggerReportView);
    }

    if (reportMonthInput) {
        reportMonthInput.addEventListener('change', updateReportButtonState);
    }

    renderNoSelectedSites();
    updateReportButtonState();
});
