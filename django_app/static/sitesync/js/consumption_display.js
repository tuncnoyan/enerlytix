(function () {
  const monthInput = document.getElementById('reporting-month');
  const supplyInput = document.getElementById('supply-id');
  const typeInput = document.getElementById('data-type');
  const loadButton = document.getElementById('load-data');
  const body = document.getElementById('records-body');
  const emptyState = document.getElementById('empty-state');
  const summary = document.getElementById('summary');

  function normalizeMonth(value) {
    if (!value) return '';
    return value;
  }

  function clearRows() {
    body.innerHTML = '';
  }

  function renderRows(records) {
    clearRows();
    if (!records.length) {
      emptyState.textContent = 'No records found for the selected filters.';
      return;
    }

    emptyState.textContent = '';
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

  async function loadData() {
    const reportingMonth = normalizeMonth(monthInput.value);
    if (!reportingMonth) {
      summary.textContent = 'Reporting month is required.';
      clearRows();
      emptyState.textContent = 'No records loaded.';
      return;
    }

    const params = new URLSearchParams({
      reporting_month: reportingMonth,
      data_type: typeInput.value,
    });

    if (supplyInput.value) {
      params.set('supply_id', supplyInput.value);
    }

    const response = await fetch('/api/consumption-display/?' + params.toString(), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      summary.textContent = 'Failed to load records.';
      clearRows();
      emptyState.textContent = 'Unable to fetch data.';
      return;
    }

    const payload = await response.json();
    summary.textContent = 'Loaded ' + payload.total_records + ' records.';
    renderRows(payload.records || []);
  }

  if (loadButton) {
    loadButton.addEventListener('click', loadData);
  }
})();
