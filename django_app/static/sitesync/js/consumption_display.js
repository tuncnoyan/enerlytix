(function () {
  const body = document.getElementById('records-body');
  const summary = document.getElementById('summary');
  const querySummary = document.getElementById('query-summary');

  function clearRows() {
    if (body) {
      body.innerHTML = '';
    }
  }

  function renderRows(records) {
    clearRows();
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

  async function fetchAndRender(reportingMonth, dataType, selectedSupplyIds) {
    const params = new URLSearchParams({
      reporting_month: reportingMonth,
      data_type: dataType,
      supply_ids: selectedSupplyIds.join(','),
    });

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
      summary.textContent = 'Loaded ' + payload.total_records + ' records from ' + selectedSupplyIds.length + ' selected supplies.';
    }
    renderRows(payload.records || []);
  }

  document.addEventListener('DOMContentLoaded', function () {
    const urlParams = new URLSearchParams(window.location.search);
    const reportingMonth = urlParams.get('reporting_month') || '';
    const dataType = urlParams.get('data_type') || 'monthly';
    const supplyIdsRaw = urlParams.get('supply_ids') || '';
    const selectedSupplyIds = supplyIdsRaw.split(',').map((item) => item.trim()).filter(Boolean);

    if (querySummary) {
      querySummary.textContent = 'Month: ' + (reportingMonth || '-') + ' | Data Type: ' + dataType + ' | Supplies: ' + selectedSupplyIds.length;
    }

    if (!reportingMonth || !selectedSupplyIds.length) {
      if (summary) {
        summary.textContent = 'Missing query parameters. Return to the dashboard and load data again.';
      }
      return;
    }

    fetchAndRender(reportingMonth, dataType, selectedSupplyIds);
  });
})();
