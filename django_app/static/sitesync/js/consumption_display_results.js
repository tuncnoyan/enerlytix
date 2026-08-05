// Data-import results page logic.
(function () {
  const context = document.getElementById('results-context');
  if (!context) {
    return;
  }

  const body = document.getElementById('records-body');
  const summary = document.getElementById('summary');
  const querySummary = document.getElementById('query-summary');
  const startHeader = document.getElementById('col-start');
  const endHeader = document.getElementById('col-end');
  const valueHeader = document.getElementById('col-value');
  const csvExportLink = document.getElementById('export-csv-link');
  const xlsxExportLink = document.getElementById('export-xlsx-link');
  const backToImportLink = document.getElementById('back-to-import-link');

  function parseSupplyIds(rawValue) {
    return String(rawValue || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function applyColumnLabels(dataType) {
    if (!startHeader || !endHeader || !valueHeader) {
      return;
    }

    if (dataType === 'invoice') {
      startHeader.textContent = 'startDate';
      endHeader.textContent = 'endDate';
      valueHeader.textContent = 'netTotalCost';
      return;
    }

    startHeader.textContent = 'Source Start';
    endHeader.textContent = 'Source End';
    valueHeader.textContent = 'Value';
  }

  function clearRows() {
    if (body) {
      body.innerHTML = '';
    }
  }

  function sortRecords(records, dataType) {
    if (dataType === 'invoice') {
      return [...records].sort(function (a, b) {
        const ta = a.source_period_start ? new Date(a.source_period_start).getTime() : 0;
        const tb = b.source_period_start ? new Date(b.source_period_start).getTime() : 0;
        return tb - ta;
      });
    }
    return records;
  }

  function renderRows(records, dataType) {
    clearRows();
    records = sortRecords(records, dataType || 'monthly');
    if (!records.length) {
      if (summary) {
        summary.textContent = 'No records found for the selected filters.';
      }
      return;
    }

    records.forEach((row) => {
      const tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + (row.supply_name || row.supply_external_id || '') + '</td>' +
        '<td>' + (row.source_period_start || '') + '</td>' +
        '<td>' + (row.source_period_end || '') + '</td>' +
        '<td>' + (row.canonical_month_key || '') + '</td>' +
        '<td>' + (row.value || '0') + '</td>' +
        '<td>' + (row.data_type || '') + '</td>';
      body.appendChild(tr);
    });
  }

  function setExportLinks(params) {
    if (!csvExportLink || !xlsxExportLink) {
      return;
    }

    const query = params.toString();
    if (!query) {
      csvExportLink.classList.add('disabled');
      xlsxExportLink.classList.add('disabled');
      csvExportLink.href = '#';
      xlsxExportLink.href = '#';
      return;
    }

    csvExportLink.classList.remove('disabled');
    xlsxExportLink.classList.remove('disabled');
    csvExportLink.href = '/panel/imports/export.csv?' + query;
    xlsxExportLink.href = '/panel/imports/export.xlsx?' + query;
  }

  function updateQuerySummary(reportingMonth, dataType, siteIds, selectedSupplyIds) {
    if (!querySummary) {
      return;
    }

    const siteCount = siteIds
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean)
      .length;

    querySummary.textContent =
      'Month: ' + (reportingMonth || '-')
      + ' | Data Type: ' + (dataType || 'monthly')
      + ' | Sites: ' + siteCount
      + ' | Supplies: ' + selectedSupplyIds.length;
  }

  async function fetchAndRender(reportingMonth, dataType, siteIds, selectedSupplyIds) {
    const params = new URLSearchParams({
      reporting_month: reportingMonth,
      data_type: dataType,
      site_ids: siteIds,
      supply_ids: selectedSupplyIds.join(','),
    });

    setExportLinks(params);
    updateQuerySummary(reportingMonth, dataType, siteIds, selectedSupplyIds);
    applyColumnLabels(dataType);

    if (backToImportLink) {
      backToImportLink.href = '/panel/imports/?' + params.toString();
    }

    const response = await fetch('/api/consumption-display/?' + params.toString(), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      if (summary) {
        summary.textContent = 'Failed to load records.';
      }
      clearRows();
      return;
    }

    const payload = await response.json();
    if (summary) {
      let msg = 'Loaded ' + payload.total_records + ' records from ' + selectedSupplyIds.length + ' selected supplies.';
      if (dataType === 'invoice' && payload.total_records > 0 && payload.in_window === false) {
        msg += ' No invoice data found for the selected period - showing all available historical records instead.';
        summary.style.color = '#b45309';
      } else {
        summary.style.color = '';
      }
      summary.textContent = msg;
    }
    renderRows(payload.records || [], dataType);
  }

  document.addEventListener('DOMContentLoaded', function () {
    const urlParams = new URLSearchParams(window.location.search);
    const reportingMonth = urlParams.get('reporting_month') || context.dataset.reportingMonth || '';
    const dataType = urlParams.get('data_type') || context.dataset.dataType || 'monthly';
    const siteIds = urlParams.get('site_ids') || context.dataset.siteIds || '';
    const supplyId = urlParams.get('supply_id') || '';
    const supplyIdsRaw = urlParams.get('supply_ids') || context.dataset.supplyIds || '';

    const selectedSupplyIds = parseSupplyIds(supplyIdsRaw);
    if (!selectedSupplyIds.length && supplyId) {
      selectedSupplyIds.push(supplyId);
    }

    if (!reportingMonth || !selectedSupplyIds.length) {
      setExportLinks(new URLSearchParams());
      updateQuerySummary(reportingMonth, dataType, siteIds, selectedSupplyIds);
      applyColumnLabels(dataType);
      if (summary) {
        summary.textContent = 'Missing report filters. Go back to Data Import and select sites and supplies.';
      }
      return;
    }

    fetchAndRender(reportingMonth, dataType, siteIds, selectedSupplyIds);
  });
})();
