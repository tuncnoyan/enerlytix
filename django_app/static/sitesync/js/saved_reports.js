(function () {
    'use strict';

    function escapeHtml(text) {
        return String(text)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    function statusClass(status) {
        return status === 'final' ? 'status-final' : 'status-draft';
    }

    function renderRows(reports) {
        const tbody = document.getElementById('saved-reports-body');
        const empty = document.getElementById('saved-reports-empty');
        if (!tbody || !empty) {
            return;
        }

        if (!reports || !reports.length) {
            tbody.innerHTML = '';
            empty.style.display = 'block';
            return;
        }

        empty.style.display = 'none';
        tbody.innerHTML = reports.map((report) => `
            <tr>
                <td>${escapeHtml(report.site_name || '')}</td>
                <td>${escapeHtml(report.reporting_month || '')}</td>
                <td><span class="status-pill ${statusClass(report.status)}">${escapeHtml(report.status || 'draft')}</span></td>
                <td>${escapeHtml(report.updated_at || '')}</td>
                <td><a class="open-link" href="${escapeHtml(report.open_url || '#')}">Open</a></td>
            </tr>
        `).join('');
    }

    const ctx = window.ENERLYTIX_SAVED_REPORTS_CONTEXT || {};
    renderRows(Array.isArray(ctx.reports) ? ctx.reports : []);
}());
