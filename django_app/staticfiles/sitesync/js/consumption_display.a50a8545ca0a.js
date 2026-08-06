// Data-import selection page logic.
(function () {
  const context = document.getElementById('import-selection-context');
  if (!context) {
    return;
  }

  const reportingMonthInput = document.getElementById('import-reporting-month');
  const dataTypeInput = document.getElementById('import-data-type');
  const refreshModeInput = document.getElementById('import-refresh-mode');
  const importButton = document.getElementById('trigger-import-button');
  const importStatus = document.getElementById('import-status');

  const siteSearchInput = document.getElementById('import-site-search');
  const siteListNode = document.getElementById('import-site-list');
  const selectedSiteCountNode = document.getElementById('selected-site-count');
  const selectAllSitesBtn = document.getElementById('select-all-sites-btn');
  const clearSiteSelectionBtn = document.getElementById('clear-site-selection-btn');

  const supplySearchInput = document.getElementById('import-supply-search');
  const utilityTypeInput = document.getElementById('import-utility-type');
  const includeSubmetersInput = document.getElementById('import-include-submeters');
  const includeInactiveInput = document.getElementById('import-include-inactive');
  const supplyListNode = document.getElementById('import-supply-list');
  const selectedSupplyCountNode = document.getElementById('selected-supply-count');
  const selectAllSuppliesBtn = document.getElementById('select-all-supplies-btn');
  const clearSupplySelectionBtn = document.getElementById('clear-supply-selection-btn');

  const state = {
    sites: [],
    supplies: [],
    selectedSiteIds: new Set(),
    selectedSupplyIds: new Set(),
  };

  function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function setImportStatus(message, isError) {
    if (!importStatus) {
      return;
    }
    importStatus.textContent = message || '';
    importStatus.classList.toggle('text-danger', Boolean(isError));
    importStatus.classList.toggle('text-muted', !isError);
  }

  function parseSupplyIds(rawValue) {
    return String(rawValue || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function parseSiteIds(rawValue) {
    return String(rawValue || '')
      .split(',')
      .map((item) => Number(item.trim()))
      .filter((item) => Number.isInteger(item) && item > 0);
  }

  function escapeHtml(value) {
    return String(value || '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function updateSelectionCounters() {
    if (selectedSiteCountNode) {
      selectedSiteCountNode.textContent = 'Selected: ' + state.selectedSiteIds.size;
    }
    if (selectedSupplyCountNode) {
      selectedSupplyCountNode.textContent = 'Selected: ' + state.selectedSupplyIds.size;
    }
  }

  function getCurrentUtilityType() {
    return utilityTypeInput ? String(utilityTypeInput.value || 'all').toLowerCase() : 'all';
  }

  function includeSubmeters() {
    return Boolean(includeSubmetersInput && includeSubmetersInput.checked);
  }

  function getFilteredSites() {
    const siteQuery = (siteSearchInput && siteSearchInput.value ? siteSearchInput.value : '').trim().toLowerCase();
    if (!siteQuery) {
      return state.sites;
    }
    return state.sites.filter((site) => {
      return (site.name || '').toLowerCase().includes(siteQuery)
        || (site.external_id || '').toLowerCase().includes(siteQuery);
    });
  }

  function getVisibleSupplies() {
    const supplyQuery = (supplySearchInput && supplySearchInput.value ? supplySearchInput.value : '').trim().toLowerCase();
    if (!supplyQuery) {
      return state.supplies;
    }
    return state.supplies.filter((supply) => {
      return (supply.name || '').toLowerCase().includes(supplyQuery)
        || (supply.external_id || '').toLowerCase().includes(supplyQuery)
        || (supply.site_name || '').toLowerCase().includes(supplyQuery)
        || (supply.utility_label || '').toLowerCase().includes(supplyQuery);
    });
  }

  function renderSiteList() {
    if (!siteListNode) {
      return;
    }

    const sites = getFilteredSites();
    if (!sites.length) {
      siteListNode.innerHTML = '<div class="list-group-item text-muted small">No sites match the current filter.</div>';
      updateSelectionCounters();
      return;
    }

    siteListNode.innerHTML = sites.map((site) => {
      const checked = state.selectedSiteIds.has(site.id) ? 'checked' : '';
      const name = escapeHtml(site.name || 'Unnamed site');
      const externalId = escapeHtml(site.external_id || '');
      const supplyCount = Number(site.supply_count || 0);
      return (
        '<label class="list-group-item d-flex justify-content-between align-items-start gap-2">'
        + '<span class="d-flex align-items-start gap-2">'
        + '<input class="form-check-input mt-1 import-site-selector" type="checkbox" value="' + site.id + '" ' + checked + '>'
        + '<span><strong>' + name + '</strong><br><small class="text-muted">' + externalId + '</small></span>'
        + '</span>'
        + '<small class="text-muted">Supplies: ' + supplyCount + '</small>'
        + '</label>'
      );
    }).join('');

    siteListNode.querySelectorAll('.import-site-selector').forEach((checkbox) => {
      checkbox.addEventListener('change', async function () {
        const siteId = Number(this.value);
        if (this.checked) {
          state.selectedSiteIds.add(siteId);
        } else {
          state.selectedSiteIds.delete(siteId);
        }
        updateSelectionCounters();
        await fetchSupplyOptions();
      });
    });

    updateSelectionCounters();
  }

  function renderSupplyList() {
    if (!supplyListNode) {
      return;
    }

    if (!state.selectedSiteIds.size) {
      supplyListNode.innerHTML = '<div class="list-group-item text-muted small">Select one or more sites to load supplies.</div>';
      updateSelectionCounters();
      return;
    }

    const supplies = getVisibleSupplies();
    if (!supplies.length) {
      supplyListNode.innerHTML = '<div class="list-group-item text-muted small">No supplies found for the selected sites and filters.</div>';
      updateSelectionCounters();
      return;
    }

    supplyListNode.innerHTML = supplies.map((supply) => {
      const checked = state.selectedSupplyIds.has(supply.external_id) ? 'checked' : '';
      const status = (supply.status || 'unknown').toLowerCase();
      const inactiveBadge = status === 'inactive'
        ? '<span class="badge text-bg-danger ms-2">inactive</span>'
        : '';
      return (
        '<label class="list-group-item d-flex justify-content-between align-items-start gap-2">'
        + '<span class="d-flex align-items-start gap-2">'
        + '<input class="form-check-input mt-1 import-supply-selector" type="checkbox" value="' + escapeHtml(supply.external_id) + '" ' + checked + '>'
        + '<span>'
        + '<strong>' + escapeHtml(supply.name || supply.external_id) + '</strong>' + inactiveBadge + '<br>'
        + '<small class="text-muted">' + escapeHtml(supply.site_name || '') + ' | ' + escapeHtml(supply.utility_label || '') + ' | ' + escapeHtml(supply.meter_type || '') + '</small><br>'
        + '<small class="text-muted">ID: ' + escapeHtml(supply.external_id) + '</small>'
        + '</span>'
        + '</span>'
        + '</label>'
      );
    }).join('');

    supplyListNode.querySelectorAll('.import-supply-selector').forEach((checkbox) => {
      checkbox.addEventListener('change', function () {
        const supplyId = this.value;
        if (this.checked) {
          state.selectedSupplyIds.add(supplyId);
        } else {
          state.selectedSupplyIds.delete(supplyId);
        }
        updateSelectionCounters();
      });
    });

    updateSelectionCounters();
  }

  async function fetchSiteOptions() {
    const response = await fetch('/api/import-review-sites/', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error('Failed to load site options.');
    }
    const payload = await response.json();
    state.sites = Array.isArray(payload.sites) ? payload.sites : [];
    renderSiteList();
  }

  async function fetchSupplyOptions() {
    if (!state.selectedSiteIds.size) {
      state.supplies = [];
      state.selectedSupplyIds.clear();
      renderSupplyList();
      return;
    }

    const params = new URLSearchParams({
      site_ids: Array.from(state.selectedSiteIds).join(','),
      include_inactive: includeInactiveInput && includeInactiveInput.checked ? '1' : '0',
      include_submeters: includeSubmeters() ? '1' : '0',
      utility_type: getCurrentUtilityType(),
    });

    const response = await fetch('/api/import-review-supplies/?' + params.toString(), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error('Failed to load supply options.');
    }

    const payload = await response.json();
    state.supplies = Array.isArray(payload.supplies) ? payload.supplies : [];
    const visibleSupplyIds = new Set(state.supplies.map((supply) => supply.external_id));
    state.selectedSupplyIds = new Set(Array.from(state.selectedSupplyIds).filter((id) => visibleSupplyIds.has(id)));
    renderSupplyList();
  }

  async function hydrateSelectionsFromSupplyIds(supplyIds) {
    if (!supplyIds.length) {
      return;
    }

    const params = new URLSearchParams({
      supply_ids: supplyIds.join(','),
      include_inactive: '1',
    });
    const response = await fetch('/api/import-review-supplies/?' + params.toString(), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      return;
    }

    const payload = await response.json();
    const hydratedSupplies = Array.isArray(payload.supplies) ? payload.supplies : [];
    hydratedSupplies.forEach((supply) => {
      state.selectedSiteIds.add(Number(supply.site_id));
      state.selectedSupplyIds.add(String(supply.external_id));
    });
  }

  function getSelectedSupplyIds() {
    return Array.from(state.selectedSupplyIds);
  }

  async function triggerImportAndLoad() {
    const reportingMonth = reportingMonthInput ? reportingMonthInput.value : '';
    const dataType = dataTypeInput ? dataTypeInput.value : 'monthly';
    const selectedSupplyIds = getSelectedSupplyIds();
    const refreshMode = Boolean(refreshModeInput && refreshModeInput.checked);

    if (!reportingMonth) {
      setImportStatus('Reporting month is required.', true);
      return;
    }
    if (!selectedSupplyIds.length) {
      setImportStatus('Select at least one supply before loading data.', true);
      return;
    }

    if (importButton) {
      importButton.disabled = true;
    }
    setImportStatus('Import is running. Please wait...', false);

    try {
      const response = await fetch('/api/consumption-import/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
          supply_ids: selectedSupplyIds,
          reporting_month: reportingMonth,
          refresh_mode: refreshMode,
        }),
      });

      if (!response.ok) {
        throw new Error('Import request failed.');
      }

      const params = new URLSearchParams({
        reporting_month: reportingMonth,
        data_type: dataType,
        site_ids: Array.from(state.selectedSiteIds).join(','),
        supply_ids: selectedSupplyIds.join(','),
      });
      window.location.href = '/panel/imports/results/?' + params.toString();
    } catch (error) {
      console.error(error);
      setImportStatus('Unable to run import. Please try again.', true);
      if (importButton) {
        importButton.disabled = false;
      }
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    async function initialize() {
      const now = new Date();
      const currentMonth = now.toISOString().slice(0, 7);

      if (reportingMonthInput && !reportingMonthInput.value) {
        reportingMonthInput.value = currentMonth;
      }

      const urlParams = new URLSearchParams(window.location.search);
      const reportingMonth = urlParams.get('reporting_month') || context.dataset.reportingMonth || (reportingMonthInput ? reportingMonthInput.value : '');
      const dataType = urlParams.get('data_type') || context.dataset.dataType || (dataTypeInput ? dataTypeInput.value : 'monthly');
      const siteIdsRaw = urlParams.get('site_ids') || context.dataset.siteIds || '';
      const supplyId = urlParams.get('supply_id') || '';
      const supplyIdsRaw = urlParams.get('supply_ids') || context.dataset.supplyIds || '';
      const selectedSupplyIds = parseSupplyIds(supplyIdsRaw);
      if (!selectedSupplyIds.length && supplyId) {
        selectedSupplyIds.push(supplyId);
      }

      parseSiteIds(siteIdsRaw).forEach((siteId) => state.selectedSiteIds.add(siteId));
      selectedSupplyIds.forEach((supplyExternalId) => state.selectedSupplyIds.add(supplyExternalId));

      if (reportingMonthInput && reportingMonth) {
        reportingMonthInput.value = reportingMonth;
      }
      if (dataTypeInput && dataType) {
        dataTypeInput.value = dataType;
      }
      if (utilityTypeInput && context.dataset.utilityType) {
        utilityTypeInput.value = context.dataset.utilityType;
      }
      if (includeSubmetersInput) {
        includeSubmetersInput.checked = ['1', 'true', 'yes', 'on'].includes(String(context.dataset.includeSubmeters || '').toLowerCase());
      }
      if (includeInactiveInput) {
        includeInactiveInput.checked = ['1', 'true', 'yes', 'on'].includes(String(context.dataset.includeInactive || '').toLowerCase());
      }

      if (importButton) {
        importButton.addEventListener('click', triggerImportAndLoad);
      }

      if (siteSearchInput) {
        siteSearchInput.addEventListener('input', renderSiteList);
      }
      if (selectAllSitesBtn) {
        selectAllSitesBtn.addEventListener('click', async function () {
          getFilteredSites().forEach((site) => state.selectedSiteIds.add(site.id));
          renderSiteList();
          await fetchSupplyOptions();
        });
      }
      if (clearSiteSelectionBtn) {
        clearSiteSelectionBtn.addEventListener('click', async function () {
          state.selectedSiteIds.clear();
          state.selectedSupplyIds.clear();
          renderSiteList();
          await fetchSupplyOptions();
        });
      }

      if (supplySearchInput) {
        supplySearchInput.addEventListener('input', renderSupplyList);
      }
      if (utilityTypeInput) {
        utilityTypeInput.addEventListener('change', async function () {
          await fetchSupplyOptions();
        });
      }
      if (includeSubmetersInput) {
        includeSubmetersInput.addEventListener('change', async function () {
          await fetchSupplyOptions();
        });
      }
      if (includeInactiveInput) {
        includeInactiveInput.addEventListener('change', async function () {
          await fetchSupplyOptions();
        });
      }
      if (selectAllSuppliesBtn) {
        selectAllSuppliesBtn.addEventListener('click', function () {
          getVisibleSupplies().forEach((supply) => state.selectedSupplyIds.add(supply.external_id));
          renderSupplyList();
        });
      }
      if (clearSupplySelectionBtn) {
        clearSupplySelectionBtn.addEventListener('click', function () {
          state.selectedSupplyIds.clear();
          renderSupplyList();
        });
      }

      try {
        await fetchSiteOptions();
        if (!state.selectedSiteIds.size && selectedSupplyIds.length) {
          await hydrateSelectionsFromSupplyIds(selectedSupplyIds);
        }
        renderSiteList();
        await fetchSupplyOptions();
      } catch (error) {
        console.error(error);
        setImportStatus('Unable to load site/supply options. Please refresh the page.', true);
      }
    }

    initialize();
  });
})();
