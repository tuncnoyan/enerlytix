(function () {
  const body = document.getElementById('records-body');
  const summary = document.getElementById('summary');
  const querySummary = document.getElementById('query-summary');
  const startHeader = document.getElementById('col-start');
  const endHeader = document.getElementById('col-end');
  const valueHeader = document.getElementById('col-value');

  function applyColumnLabels(dataType) {
    if (!startHeader || !endHeader || !valueHeader) {
      return;
    }

    if (dataType === 'invoice') {
      startHeader.textContent = 'startDate \u25bc';
      startHeader.title = 'Sorted: newest first';
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
        var ta = a.source_period_start ? new Date(a.source_period_start).getTime() : 0;
        var tb = b.source_period_start ? new Date(b.source_period_start).getTime() : 0;
        return tb - ta; // newest first
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
      let msg = 'Loaded ' + payload.total_records + ' records from ' + selectedSupplyIds.length + ' selected supplies.';
      if (dataType === 'invoice' && payload.total_records > 0 && payload.in_window === false) {
        msg += ' \u26a0\ufe0f No invoice data found for the selected period \u2014 showing all available historical records instead. '
          + 'If recent invoices exist in Etainabl, try \u201cRefresh data\u201d to re-import.';
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
    const reportingMonth = urlParams.get('reporting_month') || '';
    const dataType = urlParams.get('data_type') || 'monthly';
    const supplyIdsRaw = urlParams.get('supply_ids') || '';
    const selectedSupplyIds = supplyIdsRaw.split(',').map((item) => item.trim()).filter(Boolean);

    applyColumnLabels(dataType);

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
