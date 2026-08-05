/**
 * JavaScript for handling site selection and supply list loading.
 */

let selectedSiteId = null;
const dashboardMode = (document.body && document.body.dataset && document.body.dataset.dashboardMode) || 'home';

const currentSupplyFilters = {
    utilityType: 'all',
    meterType: 'fiscal',  // default: exclude submeters until the checkbox is ticked
    supplyQuery: '',
    includeInactive: false,
};

function getCsrfToken() {
    "use strict";

    const match = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
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
    updateCreateReportControls();
    
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
        supply_q: currentSupplyFilters.supplyQuery,
        include_inactive: currentSupplyFilters.includeInactive ? '1' : '0',
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
    const supplySearchInput = document.getElementById('supply-filter-query');
    const includeInactiveCheckbox = document.getElementById('supply-filter-include-inactive');

    currentSupplyFilters.utilityType = utilitySelect ? utilitySelect.value : 'all';
    if (includeSubmetersCheckbox) {
        currentSupplyFilters.meterType = includeSubmetersCheckbox.checked ? 'all' : 'fiscal';
    } else if (meterSelect) {
        currentSupplyFilters.meterType = meterSelect.value;
    } else {
        currentSupplyFilters.meterType = 'fiscal';
    }
    currentSupplyFilters.supplyQuery = supplySearchInput ? supplySearchInput.value.trim() : '';
    currentSupplyFilters.includeInactive = Boolean(includeInactiveCheckbox && includeInactiveCheckbox.checked);

    updateTopStatsFromCheckedSites();
    loadSupplies(selectedSiteId);
}

function clearSupplySearch() {
    "use strict";

    const supplySearchInput = document.getElementById('supply-filter-query');
    if (supplySearchInput) {
        supplySearchInput.value = '';
    }
    currentSupplyFilters.supplyQuery = '';
    applySupplyFilters();
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

    if (selectedSitesCountNode) {
        selectedSitesCountNode.textContent = 'Selected Sites: '
            + String(checkedSiteItems.length)
            + ' (' + String(visibleCheckedSiteItems.length) + ' visible)';
    }

    if (!siteCountNode || !fiscalCountNode || !submeterCountNode) {
        return;
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
    updateCreateReportControls();
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
    updateCreateReportControls();
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
    updateCreateReportControls();
    setCreateReportStatus('', false);
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

function setCreateReportStatus(message, isError) {
    "use strict";

    const statusNode = document.getElementById('create-report-status');
    if (!statusNode) {
        return;
    }
    statusNode.textContent = message || '';
    statusNode.style.color = isError ? '#b91c1c' : '#5b7080';
}

function getReportMonthValue() {
    "use strict";

    const input = document.getElementById('report-end-month');
    return input ? input.value : '';
}

function getReportRefreshModeValue() {
    "use strict";

    const input = document.getElementById('report-refresh-mode');
    return input ? input.checked : true;
}

function updateCreateReportControls() {
    "use strict";

    const button = document.getElementById('trigger-create-report-button');
    if (!button) {
        return;
    }

    const checkedSiteIds = getCheckedSiteIds();
    if (checkedSiteIds.length === 1) {
        button.disabled = false;
        button.title = 'Create report for selected site';
        return;
    }

    button.disabled = true;
    button.title = checkedSiteIds.length
        ? 'Select only one site to create a report'
        : 'Select one site to create a report';
}

function buildReportQuery(siteId, endMonth, selectedSupplyIds) {
    "use strict";

    const params = new URLSearchParams({
        site_id: String(siteId),
        end_month: endMonth,
    });
    if (selectedSupplyIds && selectedSupplyIds.length) {
        params.set('supply_ids', selectedSupplyIds.join(','));
    }
    return params.toString();
}

function getSuppliesForReportRefresh() {
    "use strict";

    const selected = getSelectedSupplyIds();
    if (selected.length) {
        return selected;
    }

    return Array.from(document.querySelectorAll('.supply-selector'))
        .map((checkbox) => checkbox.getAttribute('data-supply-id'))
        .filter(Boolean);
}

function triggerCreateReport() {
    "use strict";

    const checkedSiteIds = getCheckedSiteIds();
    const endMonth = getReportMonthValue();
    const refreshMode = getReportRefreshModeValue();
    const button = document.getElementById('trigger-create-report-button');

    if (!checkedSiteIds.length) {
        setCreateReportStatus('Select one site to create a report.', true);
        return;
    }

    if (checkedSiteIds.length > 1) {
        setCreateReportStatus('Select only one site to create a report.', true);
        return;
    }

    if (!endMonth) {
        setCreateReportStatus('Reporting month is required.', true);
        return;
    }

    const selectedSiteIdForReport = checkedSiteIds[0];
    const selectedSupplyIds = getSelectedSupplyIds();
    const reportUrl = '/report/?' + buildReportQuery(selectedSiteIdForReport, endMonth, selectedSupplyIds);

    const reportSupplyIds = getSuppliesForReportRefresh();
    if (!reportSupplyIds.length) {
        setCreateReportStatus('No supplies available for data checks. Opening report.', false);
        window.location.href = reportUrl;
        return;
    }

    if (refreshMode) {
        setCreateReportStatus('Refreshing selected supply data before opening report...', false);
    } else {
        setCreateReportStatus('Checking data availability for selected supplies...', false);
    }
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
            supply_ids: reportSupplyIds,
            reporting_month: endMonth,
            refresh_mode: refreshMode,
        }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error('Report pre-refresh failed.');
            }
            return response.json();
        })
        .then((payload) => {
            const recordsFailed = Number(payload && payload.records_failed ? payload.records_failed : 0);
            const recordsImported = Number(payload && payload.records_imported ? payload.records_imported : 0);

            if (recordsFailed > 0) {
                setCreateReportStatus('Data preparation failed for one or more supplies. Please retry import before opening report.', true);
                return;
            }

            if (refreshMode) {
                if (recordsImported > 0) {
                    setCreateReportStatus('Data refresh completed. Opening report...', false);
                } else {
                    setCreateReportStatus('Refresh completed with no new records. Opening report...', false);
                }
            } else if (recordsImported > 0) {
                setCreateReportStatus('Missing data detected and downloaded. Opening report...', false);
            } else {
                setCreateReportStatus('All required data is already available. Opening report...', false);
            }

            window.location.href = reportUrl;
        })
        .catch((error) => {
            console.error(error);
            setCreateReportStatus('Unable to prepare data before report. Please try again.', true);
        })
        .finally(() => {
            updateCreateReportControls();
        });
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
            const importReviewUrl = (document.body && document.body.dataset && document.body.dataset.importReviewUrl)
                || '/panel/imports/';
            const params = new URLSearchParams({
                reporting_month: reportingMonth,
                data_type: dataType,
                supply_ids: supplyIds.join(','),
            });
            window.location.href = importReviewUrl + '?' + params.toString();
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
    updateCreateReportControls();

    const now = new Date();
    const currentMonth = now.toISOString().slice(0, 7);
    const reportMonthInput = document.getElementById('report-end-month');
    if (reportMonthInput && !reportMonthInput.value) {
        reportMonthInput.value = currentMonth;
    }

    const createReportButton = document.getElementById('trigger-create-report-button');
    if (createReportButton) {
        createReportButton.addEventListener('click', triggerCreateReport);
    }

    const reportingMonthInput = document.getElementById('import-reporting-month');
    if (reportingMonthInput && !reportingMonthInput.value) {
        reportingMonthInput.value = currentMonth;
    }

    const importButton = document.getElementById('trigger-import-button');
    if (importButton) {
        importButton.addEventListener('click', triggerConsumptionImport);
    }

    const supplySearchInput = document.getElementById('supply-filter-query');
    if (supplySearchInput) {
        supplySearchInput.addEventListener('input', applySupplyFilters);
    }

    renderNoSelectedSites();
});
