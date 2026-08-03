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

    function accessClass(mode) {
        if (mode === 'owner') {
            return 'access-owner';
        }
        if (mode === 'collaborator') {
            return 'access-collaborator';
        }
        if (mode === 'admin') {
            return 'access-admin';
        }
        return 'access-read-only';
    }

    function accessLabel(mode) {
        if (!mode) {
            return 'Read only';
        }
        return String(mode).replaceAll('_', ' ');
    }

    function formatIso(value) {
        if (!value) {
            return 'N/A';
        }
        const dt = new Date(value);
        if (Number.isNaN(dt.getTime())) {
            return String(value);
        }
        return dt.toLocaleString('en-GB', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
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
                <td>${escapeHtml(report.owner_name || '')}</td>
                <td>${escapeHtml(formatIso(report.created_at))}</td>
                <td>${escapeHtml(report.last_edited_by_name || '')}</td>
                <td>${escapeHtml(formatIso(report.last_edited_at))}</td>
                <td><span class="access-pill ${accessClass(report.access_mode)}">${escapeHtml(accessLabel(report.access_mode || 'read_only'))}</span></td>
                <td>${escapeHtml(report.updated_at || '')}</td>
                <td><a class="open-link" href="${escapeHtml(report.open_url || '#')}">Open</a></td>
            </tr>
        `).join('');
    }

    const ctx = window.ENERLYTIX_SAVED_REPORTS_CONTEXT || {};
    renderRows(Array.isArray(ctx.reports) ? ctx.reports : []);
}());
