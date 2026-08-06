(function () {
    'use strict';

    const FILTER_DEBOUNCE_MS = 320;

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

    function validationStatusClass(status) {
        if (status === 'validated') {
            return 'status-final';
        }
        if (status === 'awaiting_validation') {
            return 'status-awaiting';
        }
        return 'status-draft';
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

    function hasActiveFilters(selectedFilters) {
        if (!selectedFilters || typeof selectedFilters !== 'object') {
            return false;
        }

        if (selectedFilters.site_query || selectedFilters.user_query || selectedFilters.start_month || selectedFilters.end_month) {
            return true;
        }

        if (selectedFilters.report_status_applied || selectedFilters.validation_status_applied) {
            return true;
        }

        return false;
    }

    function renderRows(reports, selectedFilters) {
        const tbody = document.getElementById('saved-reports-body');
        const empty = document.getElementById('saved-reports-empty');
        if (!tbody || !empty) {
            return;
        }

        if (!reports || !reports.length) {
            tbody.innerHTML = '';
            empty.textContent = hasActiveFilters(selectedFilters)
                ? 'No saved reports match the current filters.'
                : 'No saved reports found.';
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
                <td>${escapeHtml(report.validator_name || '—')}</td>
                <td>${escapeHtml(formatIso(report.validation_date))}</td>
                <td><span class="status-pill ${validationStatusClass(report.validation_status)}">${escapeHtml(report.validation_status || 'draft')}</span></td>
                <td><a class="open-link" href="${escapeHtml(report.open_url || '#')}">Open</a></td>
            </tr>
        `).join('');
    }

    function serializeFilterForm(form) {
        const params = new URLSearchParams();
        const formData = new FormData(form);

        formData.forEach((value, key) => {
            const normalized = String(value || '').trim();
            if (!normalized) {
                return;
            }
            params.append(key, normalized);
        });

        return params;
    }

    function navigateWithFilters(form) {
        const params = serializeFilterForm(form);
        const query = params.toString();
        const target = query ? `${form.action}?${query}` : form.action;
        window.location.assign(target);
    }

    function attachFilterFormBehavior(ctx) {
        const form = document.getElementById('saved-reports-filters');
        if (!form) {
            return;
        }

        form.addEventListener('submit', (event) => {
            event.preventDefault();
            navigateWithFilters(form);
        });

        const siteInput = form.querySelector('#site_query');
        const userInput = form.querySelector('#user_query');
        const instantSelectors = [
            '#start_month',
            '#end_month',
            'input[name="report_status"]',
            'input[name="validation_status"]',
        ];

        let searchTimer = null;
        function queueSearchSubmit() {
            if (searchTimer) {
                clearTimeout(searchTimer);
            }
            searchTimer = setTimeout(() => {
                navigateWithFilters(form);
            }, FILTER_DEBOUNCE_MS);
        }

        if (siteInput) {
            siteInput.addEventListener('input', queueSearchSubmit);
        }
        if (userInput) {
            userInput.addEventListener('input', queueSearchSubmit);
        }

        instantSelectors.forEach((selector) => {
            form.querySelectorAll(selector).forEach((node) => {
                node.addEventListener('change', () => navigateWithFilters(form));
            });
        });

        // Keep default checkbox state explicit in runtime context.
        if (!ctx.selectedFilters) {
            ctx.selectedFilters = {};
        }
    }

    const ctx = window.ENERLYTIX_SAVED_REPORTS_CONTEXT || {};
    renderRows(Array.isArray(ctx.reports) ? ctx.reports : [], ctx.selectedFilters || null);
    attachFilterFormBehavior(ctx);
}());
