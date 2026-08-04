/* global Chart, html2canvas */

(function () {
    'use strict';

    const palette = {
        electricity: '#7AB800',
        gas: '#7C878E',
        water: '#333F48',
        benchmark: '#F5C400',
        muted: '#C6D0D7',
        greenDark: '#00693C',
    };

    // 20-colour palette for multi-line day-comparison charts
    const multiLineColours = [
        '#333F48', '#7C878E', '#7AB800', '#F5C400', '#00693C',
        '#9B59B6', '#E67E22', '#1ABC9C', '#3498DB', '#E74C3C',
        '#2ECC71', '#F39C12', '#16A085', '#8E44AD', '#2980B9',
        '#D35400', '#27AE60', '#C0392B', '#2C3E50', '#95A5A6',
    ];

    const state = {
        reportData: null,
        comments: new Map(),
        validationComments: new Map(),
        validationCommentThreads: new Map(),
        validationPages: new Map(),
        referenceCommentKeys: new Set(),
        charts: new Map(),
        cover: null,
        coverEditorBound: false,
    };

    const COVER_DEFAULT_BACKGROUND_CANDIDATES = [
        '/static/sitesync/images/Green%20and%20Leafy%20Office.jpg',
        '/static/sitesync/images/cover-front-default.svg',
    ];
    const COVER_BACK_STATIC_CANDIDATES = [
        '/static/sitesync/images/Report%20Back%20Cover%20Page.jpg',
        '/static/sitesync/images/cover-back-static.svg',
    ];
    const COVER_SCOPE_TEMPLATE = 'This monthly energy report provides a consolidated overview of utility performance at [SITE_NAME]. It summarises electricity and water consumption using monthly invoice data, half-hourly electricity profiles, and daily usage comparisons. The report aims to highlight key trends, seasonal changes, and anomalies in consumption to support ongoing energy-performance management and cost-efficiency planning.';
    const ALLOWED_BACKGROUND_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);
    const ALLOWED_BACKGROUND_EXTENSIONS = new Set(['jpg', 'jpeg', 'png', 'webp']);
    const ALLOWED_LOGO_TYPES = new Set(['image/png', 'image/jpeg', 'image/svg+xml']);
    const ALLOWED_LOGO_EXTENSIONS = new Set(['png', 'jpg', 'jpeg', 'svg']);
    const MAX_BACKGROUND_BYTES = 10 * 1024 * 1024;
    const MAX_LOGO_BYTES = 2 * 1024 * 1024;

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(';').shift();
        }
        return '';
    }

    function getScrollRestoreKey() {
        const ctx = getContext();
        return `enerlytix-report-scroll::${ctx.reportId || ''}::${ctx.siteId || ''}::${ctx.endMonth || ''}`;
    }

    function getValidationCommentsRestoreKey() {
        const ctx = getContext();
        return `enerlytix-validation-comments::${ctx.reportId || ''}::${ctx.siteId || ''}::${ctx.endMonth || ''}`;
    }

    function persistScrollForReload() {
        try {
            const y = window.scrollY || window.pageYOffset || 0;
            window.sessionStorage.setItem(getScrollRestoreKey(), String(y));
        } catch (_e) {
            // Ignore storage failures and continue.
        }
    }

    function restoreScrollAfterReload() {
        try {
            const key = getScrollRestoreKey();
            const raw = window.sessionStorage.getItem(key);
            if (!raw) { return; }
            window.sessionStorage.removeItem(key);
            const y = Number(raw);
            if (!Number.isFinite(y)) { return; }
            window.requestAnimationFrame(() => window.scrollTo(0, y));
            // Some browsers need a second pass after async layout work.
            window.setTimeout(() => window.scrollTo(0, y), 80);
        } catch (_e) {
            // Ignore storage failures and continue.
        }
    }

    function persistValidationCommentsForReload() {
        try {
            const snapshot = Object.fromEntries(state.validationComments.entries());
            window.sessionStorage.setItem(getValidationCommentsRestoreKey(), JSON.stringify(snapshot));
        } catch (_e) {
            // Ignore storage failures and continue.
        }
    }

    function restoreValidationCommentsAfterReload() {
        try {
            const key = getValidationCommentsRestoreKey();
            const raw = window.sessionStorage.getItem(key);
            if (!raw) { return; }
            window.sessionStorage.removeItem(key);
            const parsed = JSON.parse(raw);
            if (!parsed || typeof parsed !== 'object') { return; }
            Object.entries(parsed).forEach(([pageKey, text]) => {
                state.validationComments.set(String(pageKey), String(text || ''));
            });
        } catch (_e) {
            // Ignore storage failures and continue.
        }
    }

    // ─── Formatters ──────────────────────────────────────────────────────────

    function formatCurrency(value) {
        if (value === null || value === undefined || Number.isNaN(Number(value))) {
            return 'N/A';
        }
        return new Intl.NumberFormat('en-GB', {
            style: 'currency',
            currency: 'GBP',
            maximumFractionDigits: 2,
        }).format(Number(value));
    }

    function formatNumber(value, fractionDigits) {
        if (value === null || value === undefined || Number.isNaN(Number(value))) {
            return 'N/A';
        }
        return new Intl.NumberFormat('en-GB', {
            maximumFractionDigits: fractionDigits ?? 2,
        }).format(Number(value));
    }

    function escapeHtml(text) {
        return String(text)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    /** Convert "YYYY-MM-DD..." to "DD/MM/YYYY" */
    function ddMmYyyy(isoStr) {
        if (!isoStr) { return ''; }
        const parts = isoStr.slice(0, 10).split('-');
        return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : isoStr;
    }

    function formatDateDdMmmmYyyy(dateObj) {
        if (!(dateObj instanceof Date) || Number.isNaN(dateObj.getTime())) {
            return '';
        }
        return dateObj.toLocaleDateString('en-GB', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
        });
    }

    function formatMonthYear(endMonth) {
        if (!endMonth || !/^\d{4}-\d{2}$/.test(endMonth)) {
            return endMonth || '';
        }
        const [year, month] = endMonth.split('-').map(Number);
        const dt = new Date(Date.UTC(year, month - 1, 1));
        return dt.toLocaleDateString('en-GB', { month: 'long', year: 'numeric', timeZone: 'UTC' });
    }

    function getCoverSessionKey() {
        const ctx = getContext();
        return `enerlytix-cover::${ctx.siteId || ''}::${ctx.endMonth || ''}`;
    }

    function inferExtension(fileName) {
        const name = String(fileName || '');
        const idx = name.lastIndexOf('.');
        return idx >= 0 ? name.slice(idx + 1).toLowerCase() : '';
    }

    function validateUpload(file, allowedTypes, allowedExtensions, maxBytes) {
        if (!file) {
            return { ok: false, message: 'No file selected.' };
        }
        const ext = inferExtension(file.name);
        const typeAllowed = allowedTypes.has(String(file.type || '').toLowerCase());
        const extAllowed = allowedExtensions.has(ext);
        if (!typeAllowed && !extAllowed) {
            return { ok: false, message: 'Unsupported file type.' };
        }
        if (Number(file.size || 0) > maxBytes) {
            return { ok: false, message: `File exceeds ${Math.round(maxBytes / (1024 * 1024))} MB limit.` };
        }
        return { ok: true, message: '' };
    }

    function fileToDataUrl(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(String(reader.result || ''));
            reader.onerror = () => reject(new Error('Unable to read file.'));
            reader.readAsDataURL(file);
        });
    }

    function buildDefaultContentsLines(reportData) {
        const lines = ['Total Utility Usage (\u00a3)'];
        (reportData.supplies || []).forEach((supply) => {
            const utility = String(supply.utility_type_display || supply.utility_type || 'Utility').trim();
            const utilityLower = utility.toLowerCase();
            const meter = String(supply.meter_number || '').trim();
            const withMeter = (title) => (meter ? `${title} (${meter})` : title);
            lines.push(withMeter(`Monthly ${utilityLower} usage overview`));
            lines.push(withMeter(`Monthly ${utilityLower} consumption analysis`));
            if (utilityLower === 'electricity') {
                lines.push(withMeter('Electricity load factor and demand performance'));
                lines.push(withMeter('Half-hourly electricity usage comparison'));
                lines.push(withMeter('Daily electricity usage comparison - weekdays'));
                lines.push(withMeter('Daily electricity usage comparison - weekends'));
            }
        });
        return [...new Set(lines)];
    }

    async function resolveFirstAvailableAsset(candidates) {
        const seen = new Set();
        const list = (candidates || []).filter((asset) => {
            const key = String(asset || '').trim();
            if (!key || seen.has(key)) {
                return false;
            }
            seen.add(key);
            return true;
        });

        for (const asset of list) {
            if (/^data:/i.test(asset)) {
                return asset;
            }
            try {
                const response = await fetch(asset, { method: 'GET', cache: 'no-store' });
                if (response.ok) {
                    return asset;
                }
            } catch (_error) {
                // Try next candidate.
            }
        }

        return list[list.length - 1] || '';
    }

    async function resolveCoverDefaultAssets(reportData) {
        const coverDefaults = reportData.cover_defaults || {};
        const apiFront = coverDefaults.front_cover_1?.background_asset;
        const apiBack = coverDefaults.back_cover?.image_asset;

        const frontBackground = await resolveFirstAvailableAsset([
            apiFront,
            ...COVER_DEFAULT_BACKGROUND_CANDIDATES,
        ]);

        const backCover = await resolveFirstAvailableAsset([
            apiBack,
            ...COVER_BACK_STATIC_CANDIDATES,
        ]);

        return { frontBackground, backCover };
    }

    function buildDefaultCoverState(reportData, resolvedAssets) {
        const coverDefaults = reportData.cover_defaults || {};
        const fc1 = coverDefaults.front_cover_1 || {};
        const fc2 = coverDefaults.front_cover_2 || {};
        const monthTitle = fc1.report_month_title || `${formatMonthYear(reportData.reporting_period?.end_month)} Energy Report`.trim();
        const scopeBody = fc2.scope_body || COVER_SCOPE_TEMPLATE.replace('[SITE_NAME]', reportData.site?.name || 'the selected site');
        const defaultContentsLines = (fc2.contents_entries || []).length
            ? fc2.contents_entries.map((entry) => entry.display_line || entry.title).filter(Boolean)
            : buildDefaultContentsLines(reportData);

        return {
            siteTitle: fc1.site_title || reportData.site?.name || '',
            monthTitle,
            dateText: fc1.report_date || formatDateDdMmmmYyyy(new Date()),
            scopeTitle: fc2.scope_title || 'SCOPE',
            scopeBody,
            contentsTitle: fc2.contents_title || 'CONTENTS',
            contentsText: fc2.contents_text || defaultContentsLines.join('\n'),
            backgroundDataUrl: resolvedAssets?.frontBackground || fc1.background_asset || COVER_DEFAULT_BACKGROUND_CANDIDATES[0],
            logoDataUrl: fc1.client_logo_asset || '',
            backCoverDataUrl: resolvedAssets?.backCover || (coverDefaults.back_cover || {}).image_asset || COVER_BACK_STATIC_CANDIDATES[0],
        };
    }

    function loadCoverState(reportData, resolvedAssets) {
        const defaults = buildDefaultCoverState(reportData, resolvedAssets);
        let restored = {};
        try {
            restored = JSON.parse(sessionStorage.getItem(getCoverSessionKey()) || '{}');
        } catch (_err) {
            restored = {};
        }

        const restoredBackground = String(restored.backgroundDataUrl || '');
        const keepRestoredBackground = /^data:image\//i.test(restoredBackground);

        state.cover = {
            ...defaults,
            ...(restored || {}),
            backgroundDataUrl: keepRestoredBackground ? restoredBackground : defaults.backgroundDataUrl,
            backCoverDataUrl: defaults.backCoverDataUrl,
        };
    }

    function persistCoverState() {
        if (!state.cover) { return; }
        sessionStorage.setItem(getCoverSessionKey(), JSON.stringify(state.cover));
    }

    // ─── Subtitle builders ────────────────────────────────────────────────────

    /**
     * Build a subtitle for yearly (12-month) charts.
     * Format: "Site – Meter – (DD/MM/YYYY – DD/MM/YYYY)"
     */
    function yearlySubtitle(meterNumber) {
        const rd = state.reportData;
        if (!rd) { return ''; }
        const siteName = rd.site?.name || '';
        const period = rd.reporting_period;
        if (!period) { return siteName; }
        const startStr = ddMmYyyy(period.report_start);
        const [y, m] = period.end_month.split('-').map(Number);
        const lastDay = new Date(y, m, 0); // trick: day 0 of month m+1 = last day of month m
        const endStr = `${String(lastDay.getDate()).padStart(2, '0')}/${String(m).padStart(2, '0')}/${y}`;
        const parts = [siteName, meterNumber].filter(Boolean);
        return `${parts.join(' \u2013 ')} \u2013 (${startStr} \u2013 ${endStr})`;
    }

    /**
     * Build a subtitle for single-month (HH) charts.
     * Format: "Site – Meter – (01/MM/YYYY – DD/MM/YYYY)"
     */
    function monthlySubtitle(meterNumber) {
        const rd = state.reportData;
        if (!rd) { return ''; }
        const siteName = rd.site?.name || '';
        const period = rd.reporting_period;
        if (!period) { return siteName; }
        const [y, m] = period.end_month.split('-').map(Number);
        const lastDay = new Date(y, m, 0);
        const startStr = `01/${String(m).padStart(2, '0')}/${y}`;
        const endStr = `${String(lastDay.getDate()).padStart(2, '0')}/${String(m).padStart(2, '0')}/${y}`;
        const parts = [siteName, meterNumber].filter(Boolean);
        return `${parts.join(' \u2013 ')} \u2013 (${startStr} \u2013 ${endStr})`;
    }

    /**
     * Subtitle for weekday/weekend charts whose date range is the actual
     * first-to-last day across the day records.
     */
    function dayRangeSubtitle(meterNumber, days) {
        const rd = state.reportData;
        if (!rd || !days || !days.length) { return monthlySubtitle(meterNumber); }
        const sorted = [...days].sort((a, b) => (a.date > b.date ? 1 : -1));
        const start = ddMmYyyy(sorted[0]?.date);
        const end = ddMmYyyy(sorted[sorted.length - 1]?.date);
        const siteName = rd.site?.name || '';
        const parts = [siteName, meterNumber].filter(Boolean);
        return `${parts.join(' \u2013 ')} \u2013 (${start} \u2013 ${end})`;
    }

    // ─── Page state ───────────────────────────────────────────────────────────

    function getContext() { return window.ENERLYTIX_REPORT_CONTEXT || {}; }

    function getPageValidationState(pageKey) {
        const pages = getContext().validationSummary?.pages_validation || {};
        return pages[pageKey] || {};
    }

    function isCurrentValidator() {
        const ctx = getContext();
        const validatorId = ctx.validationSummary?.validator_user_id;
        const currentUserId = ctx.currentUserId;
        if (!validatorId || !currentUserId) {
            return false;
        }
        return String(validatorId) === String(currentUserId);
    }

    function canAssignValidator() {
        return Boolean(getContext().canAssignValidator);
    }

    function updateValidationSummaryPanel() {
        const ctx = getContext();
        const summary = ctx.validationSummary || {};
        const panel = document.querySelector('.validation-summary-panel');
        if (!panel) { return; }

        const statusPill = panel.querySelector('.validation-summary-item:nth-child(1) .validation-status-pill');
        if (statusPill) {
            const status = String(summary.validation_status || 'draft');
            statusPill.className = `validation-status-pill validation-status-${status}`;
            statusPill.textContent = status;
        }

        const validatorText = panel.querySelector('.validation-summary-item:nth-child(2) span');
        if (validatorText) {
            validatorText.textContent = summary.validator_user_name || '\u2014';
        }

        const validatedByText = panel.querySelector('.validation-summary-item:nth-child(3) span');
        if (validatedByText) {
            validatedByText.textContent = summary.validated_by_user_name || '\u2014';
        }

        const pagesText = panel.querySelector('.validation-summary-item:nth-child(4) span');
        if (pagesText) {
            pagesText.textContent = `${Number(summary.validated_page_count || 0)} / ${Number(summary.total_page_count || 0)}`;
        }
    }

    function updateValidationPillsAcrossSections() {
        const ctx = getContext();
        const summaryStatus = String(ctx.validationSummary?.validation_status || 'draft');
        const uncheckedStatus = summaryStatus === 'validated' ? 'awaiting_validation' : summaryStatus;
        document.querySelectorAll('.validation-panel').forEach((panel) => {
            const checkbox = panel.querySelector('.validation-toggle');
            const pill = panel.querySelector('.validation-status-pill');
            if (!checkbox || !pill) { return; }
            const pageKey = checkbox.dataset.pageKey;
            const pageState = getPageValidationState(pageKey);
            const status = pageState.is_validated ? 'validated' : uncheckedStatus;
            pill.className = `validation-status-pill validation-status-${status}`;
            pill.textContent = status;
        });
    }

    function isReportReadOnly() {
        const mode = String(getContext().accessMode || 'read_only').toLowerCase();
        return mode !== 'owner' && mode !== 'collaborator' && mode !== 'validator' && mode !== 'admin';
    }

    function setReadOnlyHeroLabel() {
        const label = document.getElementById('report-readonly-label');
        const help = document.getElementById('report-readonly-help');
        if (!label) {
            return;
        }
        if (isReportReadOnly()) {
            label.style.display = 'inline-flex';
            if (help) {
                help.style.display = 'inline-flex';
            }
        } else {
            label.style.display = 'none';
            if (help) {
                help.style.display = 'none';
            }
        }
    }

    function setAccessBanner() {
        const banner = document.getElementById('report-access-banner');
        if (!banner) {
            return;
        }

        const ctx = getContext();
        const mode = String(ctx.accessMode || 'read_only').toLowerCase();
        if (mode === 'owner' || mode === 'collaborator' || mode === 'validator' || mode === 'admin') {
            banner.style.display = 'block';
            banner.textContent = `Access mode: ${mode.replaceAll('_', ' ')} (editable)`;
            return;
        }

        const isFinalValidatedLocked = (
            String(ctx.reportStatus || '').toLowerCase() === 'final'
            && String(ctx.validationSummary?.validation_status || '').toLowerCase() === 'validated'
        );

        if (isFinalValidatedLocked) {
            banner.style.display = 'block';
            banner.textContent = 'Access mode: read only. This report is final and validated. Owner/contributor edits require superior-chain regrant (team lead, manager, or admin).';
            return;
        }

        banner.style.display = 'block';
        banner.textContent = 'Access mode: read only. You can view this report, but cannot save edits.';
    }

    function applyReadOnlyToCoverEditor() {
        if (!isReportReadOnly()) {
            return;
        }
        const root = document.getElementById('cover-editor');
        if (!root) {
            return;
        }
        root.querySelectorAll('input, textarea, button, select').forEach((el) => {
            el.disabled = true;
            el.setAttribute('aria-disabled', 'true');
        });
    }

    (function initializeCommentState() {
        const ctx = getContext();
        const initial = ctx.initialComments || {};
        Object.entries(initial).forEach(([key, value]) => {
            state.comments.set(String(key), String(value || ''));
        });
        const validationComments = ctx.validationComments || {};
        Object.entries(validationComments).forEach(([key, value]) => {
            state.validationComments.set(String(key), String(value || ''));
        });
        const validationThreads = ctx.validationCommentThreads || {};
        Object.entries(validationThreads).forEach(([key, value]) => {
            state.validationCommentThreads.set(String(key), Array.isArray(value) ? value : []);
        });
        const validationPages = ctx.validationSummary?.pages_validation || {};
        Object.entries(validationPages).forEach(([key, value]) => {
            state.validationPages.set(String(key), value || {});
        });
        restoreValidationCommentsAfterReload();
        const refKeys = Array.isArray(ctx.referenceCommentKeys) ? ctx.referenceCommentKeys : [];
        refKeys.forEach((key) => state.referenceCommentKeys.add(String(key)));
    }());

    async function saveDraftReport() {
        if (isReportReadOnly()) {
            window.alert('You have read-only access to this report.');
            return;
        }
        const ctx = getContext();
        if (!ctx.siteId || !ctx.endMonth) {
            window.alert('Site and reporting month are required before saving a draft.');
            return;
        }

        const payload = new URLSearchParams();
        payload.set('site_id', String(ctx.siteId));
        payload.set('end_month', String(ctx.endMonth));
        payload.set('save_mode', 'draft');
        payload.set('comments', JSON.stringify(Object.fromEntries(state.comments.entries())));
        payload.set('validation_comments', JSON.stringify(Object.fromEntries(state.validationComments.entries())));

        const response = await fetch('/report/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: payload.toString(),
        });

        if (!response.ok) {
            window.alert('Unable to save draft report.');
            return;
        }

        window.alert('Draft saved.');
    }

    async function saveFinalReport(confirmFinalEdit = false) {
        if (isReportReadOnly()) {
            window.alert('You have read-only access to this report.');
            return;
        }
        const ctx = getContext();

        if (!confirmFinalEdit && Boolean(ctx.validationSummary?.can_finalize)) {
            const accepted = window.confirm(
                'Saving as final will lock this report as read-only. Further edits require superior-chain regrant (team lead, manager, or admin). Continue?'
            );
            if (!accepted) {
                return;
            }
        }
        if (!ctx.siteId || !ctx.endMonth) {
            window.alert('Site and reporting month are required before saving final.');
            return;
        }

        const payload = new URLSearchParams();
        payload.set('site_id', String(ctx.siteId));
        payload.set('end_month', String(ctx.endMonth));
        payload.set('save_mode', 'final');
        payload.set('confirm_final_edit', confirmFinalEdit ? 'true' : 'false');
        payload.set('comments', JSON.stringify(Object.fromEntries(state.comments.entries())));
        payload.set('validation_comments', JSON.stringify(Object.fromEntries(state.validationComments.entries())));

        const response = await fetch('/report/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: payload.toString(),
        });

        if (response.status === 409 && !confirmFinalEdit) {
            const accepted = window.confirm('This report is already final and may have been shared. Continue and save a replacement final version?');
            if (accepted) {
                await saveFinalReport(true);
            }
            return;
        }

        if (!response.ok) {
            window.alert('Unable to save final report.');
            return;
        }

        window.alert('Final report saved. The report is now read-only until re-granted by a superior.');
    }

    async function updateDelegation(action) {
        const ctx = getContext();
        if (!ctx.reportId) {
            return;
        }

        const isGrant = action === 'grant';
        const select = document.getElementById(isGrant ? 'delegation-grant-user' : 'delegation-revoke-user');
        const feedback = document.getElementById('delegation-feedback');
        const userId = select ? String(select.value || '').trim() : '';
        if (!userId) {
            if (feedback) {
                feedback.textContent = isGrant ? 'Select a user to grant.' : 'Select a delegate to revoke.';
            }
            return;
        }

        const route = isGrant
            ? `/reports/${encodeURIComponent(ctx.reportId)}/delegations/grant/`
            : `/reports/${encodeURIComponent(ctx.reportId)}/delegations/revoke/`;

        const payload = new URLSearchParams();
        payload.set('granted_user_id', userId);

        const response = await fetch(route, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: payload.toString(),
        });

        let message = isGrant ? 'Write access granted.' : 'Write access revoked.';
        try {
            const body = await response.json();
            if (body && body.detail) {
                message = String(body.detail);
            }
            if (body && body.errors) {
                message = JSON.stringify(body.errors);
            }
        } catch (_err) {
            // Keep fallback message.
        }

        if (!response.ok) {
            if (feedback) {
                feedback.textContent = message;
            }
            return;
        }

        if (feedback) {
            feedback.textContent = message;
        }
        window.location.reload();
    }

    function renderEmptyState(message) {
        const el = document.getElementById('report-empty');
        if (el) { el.textContent = message; el.style.display = 'block'; }
    }

    function clearEmptyState() {
        const el = document.getElementById('report-empty');
        if (el) { el.style.display = 'none'; }
    }

    const saveDraftButton = document.getElementById('save-draft-button');
    setAccessBanner();
    setReadOnlyHeroLabel();
    applyReadOnlyToCoverEditor();
    if (saveDraftButton) {
        if (isReportReadOnly()) {
            saveDraftButton.disabled = true;
            saveDraftButton.title = 'Read-only access';
        }
        saveDraftButton.addEventListener('click', () => {
            saveDraftReport().catch(() => window.alert('Unable to save draft report.'));
        });
    }

    const saveFinalButton = document.getElementById('save-final-button');
    if (saveFinalButton) {
        if (isReportReadOnly()) {
            saveFinalButton.disabled = true;
            saveFinalButton.title = 'Read-only access';
        }
        saveFinalButton.addEventListener('click', () => {
            saveFinalReport(false).catch(() => window.alert('Unable to save final report.'));
        });
    }

    const delegationGrantButton = document.getElementById('delegation-grant-button');
    if (delegationGrantButton) {
        delegationGrantButton.addEventListener('click', () => {
            updateDelegation('grant').catch(() => {
                const feedback = document.getElementById('delegation-feedback');
                if (feedback) {
                    feedback.textContent = 'Unable to grant write access right now.';
                }
            });
        });
    }

    const delegationRevokeButton = document.getElementById('delegation-revoke-button');
    if (delegationRevokeButton) {
        delegationRevokeButton.addEventListener('click', () => {
            updateDelegation('revoke').catch(() => {
                const feedback = document.getElementById('delegation-feedback');
                if (feedback) {
                    feedback.textContent = 'Unable to revoke write access right now.';
                }
            });
        });
    }

    function setSubtitle(text) {
        const el = document.getElementById('report-subtitle');
        if (el) { el.textContent = text; }
    }

    function setMeta(rd) {
        const meta = document.getElementById('report-meta');
        if (!meta) { return; }
        const months = rd.reporting_period?.months || [];
        meta.innerHTML = [
            `<span><strong>Site:</strong> ${escapeHtml(rd.site?.name || 'Unknown')}</span>`,
            `<span><strong>End month:</strong> ${escapeHtml(rd.reporting_period?.end_month || '')}</span>`,
            `<span><strong>Window:</strong> ${escapeHtml(months[0]?.label || '')} to ${escapeHtml(months[months.length - 1]?.label || '')}</span>`,
        ].join('');
    }

    function destroyCharts() {
        state.charts.forEach((chart) => chart.destroy());
        state.charts.clear();
    }

    // ─── HTML builders ────────────────────────────────────────────────────────

    function subtitleHtml(text) {
        return text
            ? `<div style="color:#7C878E;font-size:0.82rem;margin-bottom:0.7rem;">${escapeHtml(text)}</div>`
            : '';
    }

    /**
     * A chart slot whose parent uses `position:relative` so Chart.js can
     * measure it correctly with `responsive:true / maintainAspectRatio:false`.
     * (Using display:grid on the parent was the root cause of blank charts.)
     */
    function createChartSlot(chartId, height = '18rem') {
        return `
            <div class="chart-canvas-wrapper" style="position:relative;height:${height};background:linear-gradient(180deg,#fafcf8 0%,#eef5ea 100%);border:1px solid #dce7d7;border-radius:0.55rem;overflow:hidden;padding:0.3rem;margin-top:0.7rem;">
                <canvas id="${escapeHtml(chartId)}" style="display:block;"></canvas>
            </div>`;
    }

    function createPlaceholderSlot(message) {
        return `
            <div style="margin-top:0.7rem;min-height:8rem;display:flex;align-items:center;justify-content:center;background:linear-gradient(180deg,#fafcf8 0%,#eef5ea 100%);border:1px solid #dce7d7;border-radius:0.55rem;padding:1rem;text-align:center;color:#47604b;font-weight:700;">
                <span>${escapeHtml(message)}</span>
            </div>`;
    }

    function createCommentBox(id) {
        const warning = state.referenceCommentKeys.has(id)
            ? `<div class="comment-reference-warning" style="margin-top:0.6rem;color:#7c878e;font-size:0.78rem;font-weight:700;">Reference comment from previous month. Review and update as needed.</div>`
            : '';
        const validationState = getPageValidationState(id);
        const validationThreads = state.validationCommentThreads.get(id) || [];
        const threadHtml = validationThreads.length
            ? `<div class="validation-comment-thread" style="display:grid;gap:0.35rem;margin-top:0.55rem;">${validationThreads.map((entry) => `
                    <div style="border-left:3px solid #cbd5e1;padding-left:0.6rem;font-size:0.78rem;color:#475569;">
                        <div style="font-weight:700;">Note by ${escapeHtml(entry.authored_by_user_name || 'Unknown')} · ${escapeHtml(ddMmYyyy(entry.updated_at))}</div>
                        <div>${escapeHtml(entry.comment_text || '')}</div>
                    </div>
                `).join('')}</div>`
            : `<div class="validation-comment-thread" style="margin-top:0.55rem;color:#64748b;font-size:0.78rem;">No validation notes yet.</div>`;
        const canToggle = isCurrentValidator() && !isReportReadOnly();
        const toggleChecked = validationState.is_validated ? 'checked' : '';
        const toggleDisabled = canToggle ? '' : 'disabled aria-disabled="true"';
        const toggleHint = isCurrentValidator()
            ? 'You can mark this page as validated.'
            : 'Only the assigned validator can toggle this page.';
        const summaryStatus = String(getContext().validationSummary?.validation_status || 'draft');
        const uncheckedStatus = summaryStatus === 'validated' ? 'awaiting_validation' : summaryStatus;
        const panelStatus = validationState.is_validated ? 'validated' : uncheckedStatus;
        return `${warning}
            <textarea class="comment-box" data-section-id="${escapeHtml(id)}" placeholder="Add a comment..." style="margin-top:0.6rem;"></textarea>
            <div class="validation-panel" style="margin-top:0.55rem;padding:0.65rem;border:1px solid #d9e7d5;border-radius:0.5rem;background:#f8fbf6;">
                <div style="display:flex;justify-content:space-between;gap:0.5rem;align-items:center;flex-wrap:wrap;">
                    <label style="display:inline-flex;align-items:center;gap:0.45rem;font-size:0.8rem;font-weight:700;color:#334155;">
                        <input class="validation-toggle" data-page-key="${escapeHtml(id)}" type="checkbox" ${toggleChecked} ${toggleDisabled} />
                        Page validated
                    </label>
                    <span class="validation-status-pill validation-status-${escapeHtml(panelStatus)}">${escapeHtml(panelStatus)}</span>
                </div>
                <div style="margin-top:0.35rem;font-size:0.76rem;color:#64748b;">${escapeHtml(toggleHint)}</div>
                <div style="margin-top:0.35rem;font-size:0.76rem;color:#64748b;">Notes here are informational only and do not count as validation approval.</div>
                <textarea class="validation-comment-box" data-validation-page-key="${escapeHtml(id)}" placeholder="Add a validation note..." style="margin-top:0.55rem;width:100%;min-height:4rem;border-radius:0.45rem;border:1px solid var(--cxg-border);padding:0.65rem;font:inherit;resize:vertical;"></textarea>
                ${threadHtml}
            </div>`;
    }

    function registerCommentBoxes(root) {
        root.querySelectorAll('.comment-box').forEach((ta) => {
            const sid = ta.dataset.sectionId;
            if (sid && state.comments.has(sid)) { ta.value = state.comments.get(sid); }
            if (isReportReadOnly()) {
                ta.readOnly = true;
                ta.setAttribute('aria-readonly', 'true');
                ta.title = 'Read-only comment';
            }
            ta.addEventListener('input', () => state.comments.set(sid, ta.value));
        });
        root.querySelectorAll('.validation-comment-box').forEach((ta) => {
            const sid = ta.dataset.validationPageKey;
            if (sid && state.validationComments.has(sid)) { ta.value = state.validationComments.get(sid); }
            if (isReportReadOnly()) {
                ta.readOnly = true;
                ta.setAttribute('aria-readonly', 'true');
                ta.title = 'Read-only validation comment';
            }
            ta.addEventListener('input', () => state.validationComments.set(sid, ta.value));
        });
        root.querySelectorAll('.validation-toggle').forEach((cb) => {
            const pageKey = cb.dataset.pageKey;
            const stateRow = getPageValidationState(pageKey);
            cb.checked = Boolean(stateRow.is_validated);
            if (!isCurrentValidator() || isReportReadOnly()) {
                cb.disabled = true;
                cb.setAttribute('aria-disabled', 'true');
                return;
            }
            cb.addEventListener('change', () => {
                togglePageValidation(pageKey, cb.checked, cb).catch((error) => {
                    window.alert(error?.message || 'Unable to update page validation right now.');
                    cb.checked = !cb.checked;
                });
            });
        });
        const assignButton = document.querySelector('#validation-assign-button');
        const assignSelect = document.querySelector('#validation-validator-select');
        if (assignButton && assignSelect && canAssignValidator()) {
            if (assignButton.dataset.validationAssignBound === 'true') {
                return;
            }
            assignButton.dataset.validationAssignBound = 'true';
            assignButton.addEventListener('click', async () => {
                const validatorId = assignSelect.value;
                if (!validatorId) {
                    window.alert('Choose a validator first.');
                    return;
                }
                const feedback = document.querySelector('#validation-assign-feedback');
                try {
                    assignButton.disabled = true;
                    if (feedback) {
                        feedback.textContent = 'Assigning validator...';
                    }
                    const ctx = getContext();
                    if (!ctx.reportId) {
                        throw new Error('Save the report draft first, then assign a validator.');
                    }
                    const payload = new URLSearchParams();
                    payload.set('validator_user_id', validatorId);
                    const response = await fetch(`/reports/${encodeURIComponent(ctx.reportId)}/validation/assign/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRFToken': getCookie('csrftoken'),
                        },
                        body: payload.toString(),
                    });
                    const body = await response.json().catch(() => ({}));
                    if (!response.ok) {
                        throw new Error(body.detail || 'Unable to assign validator');
                    }
                    if (feedback) {
                        feedback.textContent = `Validator assigned to ${body.validator_user || 'selected user'}. Refreshing...`;
                    }
                    persistScrollForReload();
                    window.location.reload();
                } catch (error) {
                    if (feedback) {
                        feedback.textContent = error.message || 'Unable to assign validator right now.';
                    }
                    assignButton.disabled = false;
                }
            });
        }
    }

    async function togglePageValidation(pageKey, isValidated, checkboxEl) {
        const ctx = getContext();
        if (!ctx.reportId) {
            return;
        }

        const payload = new URLSearchParams();
        payload.set('is_validated', isValidated ? 'true' : 'false');
        const knownPageKeys = Array.from(document.querySelectorAll('.validation-toggle'))
            .map((el) => String(el.dataset.pageKey || '').trim())
            .filter((key) => key.length > 0);
        payload.set('known_page_keys', JSON.stringify(knownPageKeys));

        const response = await fetch(`/reports/${encodeURIComponent(ctx.reportId)}/validation/pages/${encodeURIComponent(pageKey)}/mark/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: payload.toString(),
        });

        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(body.detail || 'Unable to update validation');
        }

        const summary = body.validation_summary || {};
        ctx.validationSummary = {
            ...(ctx.validationSummary || {}),
            ...summary,
            validator_user_name: summary.validator_user_name ?? ctx.validationSummary?.validator_user_name,
            validated_by_user_name: summary.validated_by_user_name ?? ctx.validationSummary?.validated_by_user_name,
        };

        if (summary.pages_validation && typeof summary.pages_validation === 'object') {
            ctx.validationSummary.pages_validation = summary.pages_validation;
        } else {
            if (!ctx.validationSummary.pages_validation) {
                ctx.validationSummary.pages_validation = {};
            }
            ctx.validationSummary.pages_validation[pageKey] = {
                ...(ctx.validationSummary.pages_validation[pageKey] || {}),
                page_key: pageKey,
                is_validated: Boolean(body.is_validated),
                validated_by_user_name: body.validated_by_user || null,
                validated_at: body.validated_at || null,
            };
        }

        if (checkboxEl) {
            checkboxEl.checked = Boolean(body.is_validated);
        }

        updateValidationSummaryPanel();
        updateValidationPillsAcrossSections();
    }

    function renderNavEntry(label, targetId) {
        return `<a href="#${escapeHtml(targetId)}">${escapeHtml(label)}</a>`;
    }

    // ─── Monthly series normalisation ─────────────────────────────────────────

    function normaliseMonthlySeries(series, utilityType) {
        const isWater = utilityType === 'water';
        return {
            labels: (series?.months || []).map((item) => item.label),
            current: series?.[isWater ? 'current_m3' : 'current_kwh'] || [],
            previous: series?.[isWater ? 'previous_year_m3' : 'previous_year_kwh'] || [],
            benchmark: series?.[isWater ? 'benchmark_m3' : 'benchmark_kwh'] || [],
        };
    }

    // ─── HH label helper ──────────────────────────────────────────────────────

    function formatHhDateLabel(ts) {
        try {
            return new Date(ts).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
        } catch (_e) { return ts; }
    }

    // ─── Overview section ─────────────────────────────────────────────────────

    function renderOverviewSection(reportData) {
        const id = 'overview';
        const chartId = 'overview-chart';
        const allItems = reportData.overview?.by_utility || [];
        // Only show utilities that actually have cost data
        const items = allItems.filter((it) => Number(it.total_cost || 0) > 0);
        const perMeter = reportData.overview?.per_meter || [];
        const totalCost = reportData.overview?.total_cost || 0;
        const sub = yearlySubtitle(null);

        // Per-meter rows preferred; fall back to by-utility grouped rows.
        // Also filter out zero-cost rows so they don't clutter the table.
        const rowSrc = perMeter.length > 0
            ? perMeter.filter((r) => Number(r.total_cost || 0) > 0)
            : items.map((it) => ({
                label: it.label,
                meter_number: (it.meter_numbers || []).join(', '),
                total_cost: it.total_cost,
            }));

        let tableBody = rowSrc.map((row) => `
            <tr>
                <td>${escapeHtml(row.label)}</td>
                <td>${escapeHtml(row.meter_number || '')}</td>
                <td style="text-align:right;">${formatCurrency(row.total_cost)}</td>
            </tr>`).join('');

        if (tableBody) {
            tableBody += `
            <tr style="font-weight:800;border-top:2px solid #c6d0d7;">
                <td><strong>Total</strong></td>
                <td></td>
                <td style="text-align:right;"><strong>${formatCurrency(totalCost)}</strong></td>
            </tr>`;
        }

        const html = `
            <section class="section section-card" id="${id}" style="text-align:center;">
                <h2 style="margin:0 0 0.2rem;font-size:1.35rem;text-align:center;">Total Utility Usage (£)</h2>
                ${sub ? `<div style="color:#7C878E;font-size:0.84rem;margin-bottom:1rem;text-align:center;">${escapeHtml(sub)}</div>` : ''}
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem;align-items:start;text-align:left;">
                    <div>
                        <table>
                            <thead>
                                <tr>
                                    <th style="cursor:default;">Utility <span style="font-size:0.65rem;">▲</span></th>
                                    <th>Meter Numbers</th>
                                    <th style="text-align:right;">Total Cost</th>
                                </tr>
                            </thead>
                            <tbody>${tableBody || '<tr><td colspan="3">No cost data available.</td></tr>'}</tbody>
                        </table>
                        ${createCommentBox('overview-table')}
                    </div>
                    <div>
                        ${createChartSlot(chartId, '22rem')}
                        ${createCommentBox('overview-chart')}
                    </div>
                </div>
            </section>`;

        return {
            id,
            html,
            init() {
                const canvas = document.getElementById(chartId);
                if (!canvas || !items.length) { return; }
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'doughnut',
                    data: {
                        // Labels shown on the outside of each segment
                        labels: items.map((it) => `${it.label} ${formatNumber(it.percentage, 2)}%`),
                        datasets: [{
                            data: items.map((it) => Number(it.total_cost || 0)),
                            backgroundColor: items.map((it) => palette[it.utility_type] || palette.muted),
                            borderColor: '#FFFFFF',
                            borderWidth: 3,
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        layout: { padding: { top: 30, bottom: 30, left: 60, right: 60 } },
                        plugins: {
                            legend: { display: false },
                            // Use Chart.js datalabels-style approach via afterDraw, or use the
                            // built-in tooltip to show segment labels outside the arc.
                            // We replicate the PDF look via the afterDraw custom plugin below.
                        },
                    },
                    plugins: [{
                        id: 'outsideLabels',
                        afterDraw(chart) {
                            const { ctx, data, chartArea } = chart;
                            const meta = chart.getDatasetMeta(0);
                            ctx.save();
                            ctx.font = 'bold 11px Manrope, Segoe UI, sans-serif';
                            ctx.fillStyle = '#333F48';
                            meta.data.forEach((arc, index) => {
                                const label = data.labels[index];
                                if (!label) { return; }
                                // midAngle of arc
                                const startAngle = arc.startAngle;
                                const endAngle = arc.endAngle;
                                const midAngle = (startAngle + endAngle) / 2;
                                const outerRadius = arc.outerRadius;
                                const cx = arc.x;
                                const cy = arc.y;
                                const offsetR = outerRadius + 14;
                                const x = cx + Math.cos(midAngle) * offsetR;
                                const y = cy + Math.sin(midAngle) * offsetR;
                                ctx.textAlign = x < cx ? 'right' : 'left';
                                ctx.textBaseline = 'middle';
                                ctx.fillText(label, x, y);
                            });
                            ctx.restore();
                        },
                    }],
                }));
            },
        };
    }

    // ─── Monthly chart + table ────────────────────────────────────────────────

    function renderMonthlyChartCard(supply) {
        const sectionId = `monthly-${supply.id}`;
        const chartId = `monthly-chart-${supply.id}`;
        const series = normaliseMonthlySeries(supply.monthly, supply.utility_type);
        const unit = supply.utility_type === 'water' ? 'm³' : 'kWh';
        const hasData = series.labels.length > 0 &&
            (series.current.some((v) => v !== null) || series.previous.some((v) => v !== null));
        const sub = yearlySubtitle(supply.meter_number);
        const title = `Monthly ${supply.utility_type_display} Usage`;
        const hasBenchmark = series.benchmark.some((v) => v !== null);

        const monthlyRows = (supply.monthly?.table || []).map((row) => {
            const cur = row.current ?? row.current_kwh ?? row.current_m3;
            const prev = row.previous_year ?? row.previous_year_kwh ?? row.previous_year_m3;
            const gross = row.gross_variance ?? row.gross_variance_kwh ?? row.gross_variance_m3;
            const rel = row.relative_variance ?? row.relative_variance_pct;
            const label = row.date || row.month || row.label || '';
            return `<tr>
                <td>${escapeHtml(label)}</td>
                <td style="text-align:right;">${formatNumber(cur, 2)}</td>
                <td style="text-align:right;">${formatNumber(prev, 2)}</td>
                <td style="text-align:right;">${formatNumber(gross, 2)}</td>
                <td style="text-align:right;">${formatNumber(rel, 2)}</td>
            </tr>`;
        }).join('');

        // Chart and table are SEPARATE section-cards so each becomes its own PDF page.
        const chartCard = `
            <section class="section-card" style="margin-bottom:0.85rem;">
                <h3 class="card-title-screen" style="margin:0 0 0.25rem;">${escapeHtml(title)}</h3>
                <div class="card-subtitle-screen" style="color:#7C878E;font-size:0.82rem;margin-bottom:0.7rem;">${escapeHtml(sub)}</div>
                ${hasData ? createChartSlot(chartId, '26rem') : createPlaceholderSlot('No monthly data available')}
                ${createCommentBox(`monthly-chart-${sectionId}`)}
            </section>`;

        const tableCard = `
            <section class="section-card" style="margin-bottom:0.85rem;">
                <h3 style="margin:0 0 0.25rem;">${escapeHtml(title)}</h3>
                ${subtitleHtml(sub)}
                <table>
                    <thead><tr>
                        <th>Date</th>
                        <th style="text-align:right;">Last 12 Months (${escapeHtml(unit)})</th>
                        <th style="text-align:right;">Prev. 12 Months (${escapeHtml(unit)})</th>
                        <th style="text-align:right;">Gross Variance (${escapeHtml(unit)})</th>
                        <th style="text-align:right;">Relative Variance (%)</th>
                    </tr></thead>
                    <tbody>${monthlyRows || `<tr><td colspan="5">No data available.</td></tr>`}</tbody>
                </table>
                ${createCommentBox(`monthly-table-${sectionId}`)}
            </section>`;

        return {
            id: `${sectionId}-card`,
            html: chartCard + tableCard,
            init() {
                if (!hasData) { return; }
                const canvas = document.getElementById(chartId);
                if (!canvas) { return; }

                const datasets = [
                    {
                        label: 'Current Consumption',
                        data: series.current,
                        backgroundColor: palette.electricity,
                        borderColor: palette.electricity,
                        borderWidth: 1,
                        order: 2,
                    },
                    {
                        label: 'Previous Year the Same Month',
                        data: series.previous,
                        backgroundColor: palette.gas,
                        borderColor: palette.gas,
                        borderWidth: 1,
                        order: 3,
                    },
                ];
                if (hasBenchmark) {
                    // Render benchmark as a line so it matches the legacy report appearance.
                    datasets.push({
                        type: 'line',
                        label: `Benchmark (${unit})`,
                        data: series.benchmark,
                        borderColor: palette.benchmark,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [6, 4],
                        pointRadius: 0,
                        fill: false,
                        tension: 0,
                        order: 1,
                    });
                }

                state.charts.set(chartId, new Chart(canvas, {
                    type: 'bar',
                    data: { labels: series.labels, datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: { stacked: false, title: { display: true, text: 'Months' } },
                            y: {
                                beginAtZero: true,
                                title: { display: true, text: unit },
                                ticks: {
                                    callback(value) {
                                        return Math.abs(value) >= 1000
                                            ? `${formatNumber(value / 1000, 1)}K`
                                            : formatNumber(value, 0);
                                    },
                                },
                            },
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: title,
                                font: { size: 16, weight: 'bold', family: 'Manrope, Segoe UI, sans-serif' },
                                color: '#333F48',
                                padding: { top: 4, bottom: 2 },
                            },
                            subtitle: {
                                display: Boolean(sub),
                                text: sub,
                                font: { size: 11, family: 'Manrope, Segoe UI, sans-serif' },
                                color: '#7C878E',
                                padding: { bottom: 12 },
                            },
                            legend: { position: 'bottom' },
                        },
                    },
                }));
            },
        };
    }

    // ─── Load Factor ─────────────────────────────────────────────────────────

    function renderLoadFactorCard(supply) {
        const sectionId = `load-factor-${supply.id}`;
        const chartId = `load-factor-chart-${supply.id}`;
        const lf = supply.load_factor;
        if (!lf || !(lf.halfhourly || []).length) {
            return {
                id: sectionId,
                html: `<section class="section-card" style="margin-bottom:0.85rem;">
                    <h3 style="margin:0 0 0.25rem;">Electricity Load Factor</h3>
                    ${createPlaceholderSlot('No load factor data available')}
                    ${createCommentBox(sectionId)}</section>`,
                init() {},
            };
        }
        const values = lf.halfhourly;
        const labels = values.map((_, i) => i + 1);
        const maxDemand = Number(lf.max_demand_kw || 0);
        const availCap = lf.available_capacity_kva === null ? null : Number(lf.available_capacity_kva || 0);
        const sub = monthlySubtitle(supply.meter_number);

        return {
            id: sectionId,
            html: `
                <section class="section-card" style="margin-bottom:0.85rem;">
                    <h3 style="margin:0 0 0.25rem;">Electricity Load Factor</h3>
                    ${subtitleHtml(sub)}
                    ${createChartSlot(chartId, '20rem')}
                    <div class="metric-grid" style="margin-top:0.9rem;grid-template-columns:repeat(3,minmax(0,1fr));">
                        <div class="metric"><div class="metric-label">Load Factor</div><div class="metric-value">${formatNumber(lf.load_factor_pct, 2)}%</div></div>
                        <div class="metric"><div class="metric-label">Maximum Demand (kW)</div><div class="metric-value">${formatNumber(lf.max_demand_kw, 1)}</div></div>
                        <div class="metric"><div class="metric-label">Available Capacity (kVA)</div><div class="metric-value">${availCap === null ? 'N/A' : formatNumber(availCap, 0)}</div></div>
                    </div>
                    ${createCommentBox(sectionId)}
                </section>`,
            init() {
                const canvas = document.getElementById(chartId);
                if (!canvas) { return; }
                const datasets = [
                    { label: 'Consumption', data: values.map((item) => Number(item.consumption_kwh || 0)), borderColor: palette.electricity, backgroundColor: 'rgba(122,184,0,0.15)', fill: true, pointRadius: 0, tension: 0.2, borderWidth: 1.5 },
                    { label: 'Maximum Demand', data: labels.map(() => maxDemand), borderColor: palette.gas, borderDash: [5, 4], pointRadius: 0, fill: false, borderWidth: 1.5 },
                ];
                if (availCap !== null) {
                    datasets.push({ label: 'Available Capacity', data: labels.map(() => availCap), borderColor: palette.benchmark, borderDash: [2, 3], pointRadius: 0, fill: false, borderWidth: 1.5 });
                }
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'line',
                    data: { labels, datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: 'bottom' } },
                        scales: {
                            x: {
                                ticks: { display: false },
                                grid: { display: false },
                            },
                            y: {
                                beginAtZero: true,
                                title: { display: true, text: 'kWh' },
                                grid: { color: 'rgba(0,0,0,0.06)' },
                            },
                        },
                    },
                }));
            },
        };
    }

    // ─── HH comparison ────────────────────────────────────────────────────────

    function renderComparisonCard(title, sectionId, chartId, comparison, colorA, colorB, meterNumber) {
        if (!comparison || !(comparison.current || []).length) {
            return {
                id: sectionId,
                html: `<section class="section-card" style="margin-bottom:0.85rem;">
                    <h3 style="margin:0 0 0.25rem;">${escapeHtml(title)}</h3>
                    ${createPlaceholderSlot('No half-hourly data available')}
                    ${createCommentBox(sectionId)}</section>`,
                init() {},
            };
        }
        const sub = monthlySubtitle(meterNumber);
        const rawLabels = comparison.current.map((item) => item.ts);
        const step = Math.max(1, Math.floor(rawLabels.length / 10));
        const displayLabels = rawLabels.map((ts, i) => (i % step === 0 ? formatHhDateLabel(ts) : ''));

        return {
            id: sectionId,
            html: `
                <section class="section-card" style="margin-bottom:0.85rem;">
                    <h3 style="margin:0 0 0.25rem;">${escapeHtml(title)}</h3>
                    ${subtitleHtml(sub)}
                    ${createChartSlot(chartId, '20rem')}
                    ${createCommentBox(sectionId)}
                </section>`,
            init() {
                const canvas = document.getElementById(chartId);
                if (!canvas) { return; }
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels: displayLabels,
                        datasets: [
                            { label: 'Current Year', data: comparison.current.map((item) => Number(item.consumption_kwh || 0)), borderColor: colorA, backgroundColor: colorA, pointRadius: 0, tension: 0.15, borderWidth: 1.5 },
                            { label: 'Previous Year the Same Month', data: (comparison.previous_year || []).map((item) => Number(item.consumption_kwh || 0)), borderColor: colorB, backgroundColor: colorB, pointRadius: 0, tension: 0.15, borderWidth: 1.5 },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: 'bottom' } },
                        scales: {
                            x: { ticks: { maxRotation: 0, callback(v, i) { return displayLabels[i] || ''; } }, title: { display: true, text: 'Month' }, grid: { display: false } },
                            y: { beginAtZero: true, title: { display: true, text: 'kWh' }, grid: { color: 'rgba(0,0,0,0.06)' } },
                        },
                    },
                }));
            },
        };
    }

    // ─── Day/Night ────────────────────────────────────────────────────────────

    function renderDayNightCard(supply) {
        const sectionId = `day-night-${supply.id}`;
        const chartId = `day-night-chart-${supply.id}`;
        const dn = supply.day_night;
        if (!dn || !(dn.records || []).length) {
            return {
                id: sectionId,
                html: `<section class="section-card" style="margin-bottom:0.85rem;">
                    <h3 style="margin:0 0 0.25rem;">HH Electricity Day / Night Usage Last Month</h3>
                    ${createPlaceholderSlot('No half-hourly data available')}
                    ${createCommentBox(sectionId)}</section>`,
                init() {},
            };
        }
        const sub = monthlySubtitle(supply.meter_number);
        const rawLabels = dn.records.map((item) => item.ts);
        const step = Math.max(1, Math.floor(rawLabels.length / 10));
        const displayLabels = rawLabels.map((ts, i) => (i % step === 0 ? formatHhDateLabel(ts) : ''));

        return {
            id: sectionId,
            html: `
                <section class="section-card" style="margin-bottom:0.85rem;">
                    <h3 style="margin:0 0 0.25rem;">HH Electricity Day / Night Usage Last Month</h3>
                    ${subtitleHtml(sub)}
                    ${createChartSlot(chartId, '20rem')}
                    ${createCommentBox(sectionId)}
                </section>`,
            init() {
                const canvas = document.getElementById(chartId);
                if (!canvas) { return; }
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels: displayLabels,
                        datasets: [
                            { label: 'Day', data: dn.records.map((item) => item.period === 'day' ? Number(item.consumption_kwh || 0) : 0), backgroundColor: palette.electricity, stack: 'usage' },
                            { label: 'Night', data: dn.records.map((item) => item.period === 'night' ? Number(item.consumption_kwh || 0) : 0), backgroundColor: palette.water, stack: 'usage' },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: 'bottom' } },
                        scales: {
                            x: { stacked: true, ticks: { maxRotation: 0, callback(v, i) { return displayLabels[i] || ''; } }, title: { display: true, text: 'Date' }, grid: { display: false } },
                            y: { stacked: true, beginAtZero: true, title: { display: true, text: 'kWh' }, grid: { color: 'rgba(0,0,0,0.06)' } },
                        },
                    },
                }));
            },
        };
    }

    // ─── Weekday / Weekend ────────────────────────────────────────────────────

    function renderWeekComparisonCard(title, sectionId, chartId, comparison, meterNumber) {
        if (!comparison || !comparison.days || !comparison.days.length) {
            return {
                id: sectionId,
                html: `<section class="section-card" style="margin-bottom:0.85rem;">
                    <h3 style="margin:0 0 0.25rem;">${escapeHtml(title)}</h3>
                    ${createPlaceholderSlot('No day comparison data available')}
                    ${createCommentBox(sectionId)}</section>`,
                init() {},
            };
        }
        const sub = dayRangeSubtitle(meterNumber, comparison.days);
        // Time labels from the first day's records (HH:MM strings like "00:00", "00:30"…)
        const timeLabels = (comparison.days[0]?.records || []).map((r) => r.time || '');

        return {
            id: sectionId,
            html: `
                <section class="section-card" style="margin-bottom:0.85rem;">
                    <h3 style="margin:0 0 0.25rem;">${escapeHtml(title)}</h3>
                    ${subtitleHtml(sub)}
                    ${createChartSlot(chartId, '22rem')}
                    ${createCommentBox(sectionId)}
                </section>`,
            init() {
                const canvas = document.getElementById(chartId);
                if (!canvas) { return; }
                const datasets = comparison.days.map((day, index) => ({
                    label: `${day.day_name || ''}, ${ddMmYyyy(day.date)}`,
                    data: (day.records || []).map((r) => Number(r.consumption_kwh || 0)),
                    borderColor: multiLineColours[index % multiLineColours.length],
                    backgroundColor: multiLineColours[index % multiLineColours.length],
                    pointRadius: 0,
                    tension: 0.15,
                    borderWidth: 1.5,
                }));
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'line',
                    data: { labels: timeLabels, datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'right', labels: { boxWidth: 10, font: { size: 10 } } },
                        },
                        scales: {
                            x: { ticks: { maxTicksLimit: 9, maxRotation: 0 }, grid: { color: 'rgba(0,0,0,0.05)' } },
                            y: { beginAtZero: true, title: { display: true, text: 'kWh' }, grid: { color: 'rgba(0,0,0,0.06)' } },
                        },
                    },
                }));
            },
        };
    }

    // ─── Supply section ───────────────────────────────────────────────────────

    function renderSupplySection(supply) {
        const sectionId = `supply-${supply.id}`;
        const cards = [];
        cards.push(renderMonthlyChartCard(supply));

        if (supply.utility_type === 'electricity') {
            cards.push(renderLoadFactorCard(supply));
            cards.push(renderComparisonCard('HH Electricity Data Comparison \u2013 Last Month', `hh-${supply.id}`, `hh-chart-${supply.id}`, supply.hh_comparison, palette.electricity, palette.gas, supply.meter_number));
            cards.push(renderDayNightCard(supply));
            cards.push(renderWeekComparisonCard('Daily Comparison \u2013 Weekday Usage', `weekday-${supply.id}`, `weekday-chart-${supply.id}`, supply.weekday_comparison, supply.meter_number));
            cards.push(renderWeekComparisonCard('Daily Comparison \u2013 Weekend Usage', `weekend-${supply.id}`, `weekend-chart-${supply.id}`, supply.weekend_comparison, supply.meter_number));
        } else if (supply.utility_type === 'gas') {
            cards.push(renderComparisonCard('HH Gas Data Comparison \u2013 Last Month', `hh-${supply.id}`, `hh-chart-${supply.id}`, supply.hh_comparison, palette.electricity, palette.gas, supply.meter_number));
            cards.push(renderWeekComparisonCard('Daily Comparison \u2013 Weekday Usage (Gas)', `weekday-${supply.id}`, `weekday-chart-${supply.id}`, supply.weekday_comparison, supply.meter_number));
            cards.push(renderWeekComparisonCard('Daily Comparison \u2013 Weekend Usage (Gas)', `weekend-${supply.id}`, `weekend-chart-${supply.id}`, supply.weekend_comparison, supply.meter_number));
        }

        const header = `
            <div class="section-card pdf-exclude" style="margin-bottom:0.85rem;">
                <h2 style="margin:0 0 0.2rem;">${escapeHtml(supply.label || supply.utility_type_display || 'Supply')}</h2>
                <div style="color:#5b7080;font-size:0.84rem;">${escapeHtml(supply.utility_type_display || '')} — Meter: ${escapeHtml(supply.meter_number || 'N/A')}</div>
            </div>`;

        return {
            id: sectionId,
            html: `<section class="section" id="${sectionId}">${header}${cards.map((c) => c.html).join('')}</section>`,
            init() { cards.forEach((c) => c.init()); },
        };
    }

    function coverContentsLines() {
        return String(state.cover?.contentsText || '')
            .split('\n')
            .map((line) => line.trim())
            .filter(Boolean);
    }

    function renderCoverSections() {
        const clientLogoHtml = `
            <div class="cover-front-logo${state.cover.logoDataUrl ? ' is-visible' : ''}" id="cover-front-logo-view">
                ${state.cover.logoDataUrl ? `<img id="cover-front-logo-preview" src="${escapeHtml(state.cover.logoDataUrl)}" alt="Client logo" />` : ''}
            </div>`;

        const contentsItems = coverContentsLines()
            .map((line) => `<li class="cover-text-block">${escapeHtml(line)}</li>`)
            .join('');

        const frontCover = {
            id: 'cover-front-page-1',
            html: `
                <section class="section section-card cover-page" id="cover-front-page-1">
                    <div class="cover-page-front">
                        <div class="cover-front-left">
                            <div class="cover-front-brand"><img src="/static/sitesync/images/logo.png" alt="Carbonxgen logo" /></div>
                            <div class="cover-front-box cover-text-block cover-front-site-title" id="cover-front-site-title-view">${escapeHtml(state.cover.siteTitle)}</div>
                            <div class="cover-front-site-rule" aria-hidden="true"></div>
                            <div class="cover-front-box cover-text-block cover-front-month-title" id="cover-front-month-title-view">${escapeHtml(state.cover.monthTitle)}</div>
                            <div class="cover-front-box cover-text-block cover-front-date" id="cover-front-date-view">${escapeHtml(state.cover.dateText)}</div>
                            ${clientLogoHtml}
                        </div>
                        <div class="cover-front-image" id="cover-front-bg-view" style="background-image:url('${escapeHtml(state.cover.backgroundDataUrl || COVER_DEFAULT_BACKGROUND_CANDIDATES[0])}');"></div>
                    </div>
                </section>`,
            init() {},
        };

        const secondCover = {
            id: 'cover-front-page-2',
            html: `
                <section class="section section-card cover-page" id="cover-front-page-2">
                    <div class="cover-page-two">
                        <div class="cover-page-two-brand"><img src="/static/sitesync/images/logo.png" alt="Carbonxgen logo" /></div>
                        <h3 class="cover-text-block cover-page-two-scope-title" id="cover-scope-title-view">${escapeHtml(state.cover.scopeTitle)}</h3>
                        <p class="cover-text-block" id="cover-scope-body-view">${escapeHtml(state.cover.scopeBody)}</p>
                        <h3 class="cover-text-block" id="cover-contents-title-view">${escapeHtml(state.cover.contentsTitle)}</h3>
                        <ol id="cover-contents-list-view" style="margin:0.25rem 0 0 1.45rem;">${contentsItems}</ol>
                    </div>
                </section>`,
            init() {},
        };

        const backCover = {
            id: 'cover-back-page',
            html: `
                <section class="section section-card cover-page" id="cover-back-page" aria-label="Back cover">
                    <div class="cover-page-back" id="cover-back-bg-view" style="background-image:url('${escapeHtml(state.cover.backCoverDataUrl || COVER_BACK_STATIC_CANDIDATES[0])}');"></div>
                </section>`,
            init() {},
        };

        return { frontCover, secondCover, backCover };
    }

    function syncCoverEditorFromState() {
        const mapping = {
            'cover-site-title-input': 'siteTitle',
            'cover-month-title-input': 'monthTitle',
            'cover-date-input': 'dateText',
            'cover-scope-title-input': 'scopeTitle',
            'cover-scope-body-input': 'scopeBody',
            'cover-contents-title-input': 'contentsTitle',
            'cover-contents-body-input': 'contentsText',
        };
        Object.entries(mapping).forEach(([id, key]) => {
            const el = document.getElementById(id);
            if (el) { el.value = state.cover[key] || ''; }
        });
    }

    function updateCoverPreviewFromState() {
        const siteTitle = document.getElementById('cover-front-site-title-view');
        if (siteTitle) { siteTitle.textContent = state.cover.siteTitle || ''; }

        const monthTitle = document.getElementById('cover-front-month-title-view');
        if (monthTitle) { monthTitle.textContent = state.cover.monthTitle || ''; }

        const dateTitle = document.getElementById('cover-front-date-view');
        if (dateTitle) { dateTitle.textContent = state.cover.dateText || ''; }

        const bgView = document.getElementById('cover-front-bg-view');
        if (bgView) {
            bgView.style.backgroundImage = `url('${state.cover.backgroundDataUrl || COVER_DEFAULT_BACKGROUND_CANDIDATES[0]}')`;
        }

        const logoView = document.getElementById('cover-front-logo-view');
        if (logoView) {
            if (state.cover.logoDataUrl) {
                logoView.classList.add('is-visible');
                logoView.innerHTML = `<img id="cover-front-logo-preview" src="${escapeHtml(state.cover.logoDataUrl)}" alt="Client logo" />`;
            } else {
                logoView.classList.remove('is-visible');
                logoView.innerHTML = '';
            }
        }

        const scopeTitle = document.getElementById('cover-scope-title-view');
        if (scopeTitle) { scopeTitle.textContent = state.cover.scopeTitle || ''; }

        const scopeBody = document.getElementById('cover-scope-body-view');
        if (scopeBody) { scopeBody.textContent = state.cover.scopeBody || ''; }

        const contentsTitle = document.getElementById('cover-contents-title-view');
        if (contentsTitle) { contentsTitle.textContent = state.cover.contentsTitle || ''; }

        const contentsList = document.getElementById('cover-contents-list-view');
        if (contentsList) {
            contentsList.innerHTML = coverContentsLines().map((line) => `<li class="cover-text-block">${escapeHtml(line)}</li>`).join('');
        }
    }

    function updateCoverStateField(key, value) {
        state.cover[key] = value;
        persistCoverState();
        updateCoverPreviewFromState();
    }

    async function handleBackgroundUpload(inputEl) {
        const messageEl = document.getElementById('cover-background-validation');
        const file = inputEl?.files?.[0];
        if (!file) { return; }
        const result = validateUpload(file, ALLOWED_BACKGROUND_TYPES, ALLOWED_BACKGROUND_EXTENSIONS, MAX_BACKGROUND_BYTES);
        if (!result.ok) {
            state.cover.backgroundDataUrl = COVER_DEFAULT_BACKGROUND_CANDIDATES[0];
            persistCoverState();
            updateCoverPreviewFromState();
            if (messageEl) { messageEl.textContent = result.message; }
            inputEl.value = '';
            return;
        }
        try {
            state.cover.backgroundDataUrl = await fileToDataUrl(file);
            persistCoverState();
            updateCoverPreviewFromState();
            if (messageEl) { messageEl.textContent = ''; }
        } catch (_error) {
            if (messageEl) { messageEl.textContent = 'Unable to read selected image.'; }
        }
    }

    async function handleLogoUpload(inputEl) {
        const messageEl = document.getElementById('cover-logo-validation');
        const file = inputEl?.files?.[0];
        if (!file) { return; }
        const result = validateUpload(file, ALLOWED_LOGO_TYPES, ALLOWED_LOGO_EXTENSIONS, MAX_LOGO_BYTES);
        if (!result.ok) {
            state.cover.logoDataUrl = '';
            persistCoverState();
            updateCoverPreviewFromState();
            if (messageEl) { messageEl.textContent = result.message; }
            inputEl.value = '';
            return;
        }
        try {
            state.cover.logoDataUrl = await fileToDataUrl(file);
            persistCoverState();
            updateCoverPreviewFromState();
            if (messageEl) { messageEl.textContent = ''; }
        } catch (_error) {
            if (messageEl) { messageEl.textContent = 'Unable to read selected logo.'; }
        }
    }

    function initializeCoverEditor() {
        if (!state.cover) { return; }
        syncCoverEditorFromState();

        if (state.coverEditorBound) {
            return;
        }

        const mapping = {
            'cover-site-title-input': 'siteTitle',
            'cover-month-title-input': 'monthTitle',
            'cover-date-input': 'dateText',
            'cover-scope-title-input': 'scopeTitle',
            'cover-scope-body-input': 'scopeBody',
            'cover-contents-title-input': 'contentsTitle',
            'cover-contents-body-input': 'contentsText',
        };
        Object.entries(mapping).forEach(([id, key]) => {
            const el = document.getElementById(id);
            if (!el) { return; }
            el.addEventListener('input', () => updateCoverStateField(key, el.value));
        });

        const bgUpload = document.getElementById('cover-background-upload-input');
        if (bgUpload) {
            bgUpload.addEventListener('change', () => {
                handleBackgroundUpload(bgUpload).catch(() => {
                    const messageEl = document.getElementById('cover-background-validation');
                    if (messageEl) { messageEl.textContent = 'Unable to process selected image.'; }
                });
            });
        }

        const logoUpload = document.getElementById('cover-logo-upload-input');
        if (logoUpload) {
            logoUpload.addEventListener('change', () => {
                handleLogoUpload(logoUpload).catch(() => {
                    const messageEl = document.getElementById('cover-logo-validation');
                    if (messageEl) { messageEl.textContent = 'Unable to process selected logo.'; }
                });
            });
        }

        state.coverEditorBound = true;
    }

    // ─── Page builder ─────────────────────────────────────────────────────────

    function renderNoSuppliesState() {
        const sections = document.getElementById('report-sections');
        const nav = document.getElementById('report-nav');
        if (!sections || !nav) { return; }
        nav.innerHTML = renderNavEntry('Overview', 'overview');
        sections.innerHTML = `
            <section class="section section-card" id="overview">
                <h2>Overview</h2>
                <div class="empty-state">No supplies were found for this site.</div>
            </section>`;
    }

    function buildPage(reportData) {
        const sections = document.getElementById('report-sections');
        const nav = document.getElementById('report-nav');
        const empty = document.getElementById('report-empty');
        if (!sections || !nav || !empty) { return; }

        destroyCharts();
        sections.innerHTML = '';
        nav.innerHTML = '';
        clearEmptyState();

        const rendered = [];
        const coverSections = renderCoverSections();
        rendered.push(coverSections.frontCover);
        rendered.push(coverSections.secondCover);

        nav.insertAdjacentHTML('beforeend', renderNavEntry('Front Cover 1', 'cover-front-page-1'));
        nav.insertAdjacentHTML('beforeend', renderNavEntry('Front Cover 2', 'cover-front-page-2'));

        const overview = renderOverviewSection(reportData);
        rendered.push(overview);
        nav.insertAdjacentHTML('beforeend', renderNavEntry('Overview', overview.id));

        const supplies = reportData.supplies || [];
        supplies.forEach((supply) => {
            const sec = renderSupplySection(supply);
            rendered.push(sec);
            nav.insertAdjacentHTML('beforeend', renderNavEntry(supply.label || supply.utility_type_display || 'Supply', sec.id));
        });

        rendered.push(coverSections.backCover);

        nav.insertAdjacentHTML('beforeend', renderNavEntry('Back Cover', 'cover-back-page'));

        sections.innerHTML = rendered.map((r) => r.html).join('');
        rendered.forEach((r) => r.init());
        registerCommentBoxes(sections);
        initializeCoverEditor();
        updateCoverPreviewFromState();
    }

    function isCoverSection(section) {
        return ['cover-front-page-1', 'cover-front-page-2', 'cover-back-page'].includes(section?.id || '');
    }

    // ─── Data fetch ───────────────────────────────────────────────────────────

    async function fetchReportData() {
        const ctx = getContext();
        const params = new URLSearchParams({ site_id: ctx.siteId || '', end_month: ctx.endMonth || '' });
        if (ctx.supplyIds) { params.set('supply_ids', ctx.supplyIds); }
        const response = await fetch('/api/report-data/?' + params.toString(), { credentials: 'same-origin' });
        if (!response.ok) { throw new Error('Unable to load report data.'); }
        return response.json();
    }

    async function loadReport() {
        try {
            const reportData = await fetchReportData();
            state.reportData = reportData;
            const resolvedCoverAssets = await resolveCoverDefaultAssets(reportData);
            loadCoverState(reportData, resolvedCoverAssets);
            setSubtitle(`${reportData.site.name} \u00b7 ${reportData.reporting_period.end_month}`);
            setMeta(reportData);
            buildPage(reportData);
            restoreScrollAfterReload();
        } catch (error) {
            console.error(error);
            renderEmptyState('Unable to load report data.');
            setSubtitle('Report data unavailable');
        }
    }

    // ─── PDF export ───────────────────────────────────────────────────────────

    /**
     * html2canvas only rasterises the visible (scrolled) viewport of a
     * <textarea>, so multi-line comments get cropped to whatever fits in
     * the box on screen. To capture the full comment text in the PDF we
     * temporarily swap each non-empty textarea for a plain block element
     * that displays the complete value and grows to fit it, then restore
     * the textarea afterwards.
     */
    function swapCommentBoxForCapture(ta) {
        const cs = window.getComputedStyle(ta);
        const div = document.createElement('div');
        div.textContent = ta.value;
        div.style.whiteSpace = 'pre-wrap';
        div.style.wordBreak = 'break-word';
        div.style.overflow = 'visible';
        div.style.boxSizing = cs.boxSizing;
        div.style.width = cs.width;
        div.style.minHeight = cs.minHeight;
        div.style.font = cs.font;
        div.style.lineHeight = cs.lineHeight;
        div.style.color = cs.color;
        div.style.padding = cs.padding;
        div.style.border = cs.border;
        div.style.borderRadius = cs.borderRadius;
        div.style.background = cs.backgroundColor;
        div.style.margin = cs.margin;
        ta.insertAdjacentElement('afterend', div);
        ta.style.display = 'none';
        return div;
    }

    function restoreCommentBox(ta, div) {
        div.remove();
        ta.style.display = '';
    }

    function firstFontFamily(fontFamily) {
        return String(fontFamily || 'Arial').split(',')[0].replace(/["']/g, '').trim() || 'Arial';
    }

    function cssColorToHex(color) {
        const value = String(color || '').trim();
        if (!value) { return '333333'; }
        if (/^#[0-9a-fA-F]{6}$/.test(value)) {
            return value.slice(1).toUpperCase();
        }
        if (/^#[0-9a-fA-F]{3}$/.test(value)) {
            return value.slice(1).split('').map((ch) => `${ch}${ch}`).join('').toUpperCase();
        }
        const rgbaMatch = value.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/i);
        if (rgbaMatch) {
            const alpha = rgbaMatch[4] === undefined ? 1 : Number.parseFloat(rgbaMatch[4]);
            if (Number.isFinite(alpha) && alpha <= 0) { return 'FFFFFF'; }
            return [rgbaMatch[1], rgbaMatch[2], rgbaMatch[3]].map((part) => Number(part).toString(16).padStart(2, '0')).join('').toUpperCase();
        }
        const rgbMatch = value.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/i);
        if (rgbMatch) {
            return [rgbMatch[1], rgbMatch[2], rgbMatch[3]].map((part) => Number(part).toString(16).padStart(2, '0')).join('').toUpperCase();
        }
        return '333333';
    }

    function pxToPt(px) {
        const value = Number.parseFloat(px);
        return Number.isFinite(value) ? value * 0.75 : 11;
    }

    function getPptxConstructor() {
        return window.PptxGenJS || window.pptxgen || window.pptxgenjs || null;
    }

    function collectPptxTextBlocks(section) {
        const textSelectors = 'h2, h3, .card-subtitle-screen, .metric-label, .metric-value, .comment-reference-warning, .comment-box, th, .cover-text-block';
        return Array.from(section.querySelectorAll(textSelectors)).map((el) => {
            const isCommentBox = el.classList.contains('comment-box');
            const isCommentNote = el.classList.contains('comment-reference-warning');
            const commentValue = isCommentBox ? String(el.value || '').trim() : '';

            if (isCommentBox && !commentValue) {
                return null;
            }
            if (isCommentNote) {
                const nextComment = el.nextElementSibling;
                if (!nextComment || !nextComment.classList || !nextComment.classList.contains('comment-box') || !String(nextComment.value || '').trim()) {
                    return null;
                }
            }

            return {
                el,
                kind: isCommentBox ? 'comment'
                    : isCommentNote ? 'comment-note'
                        : el.classList.contains('metric-label') ? 'metric-label'
                            : el.classList.contains('metric-value') ? 'metric-value'
                                : el.classList.contains('card-subtitle-screen') ? 'subtitle'
                                    : el.tagName === 'TH' ? 'table-header'
                                        : 'heading',
                text: isCommentBox
                    ? commentValue
                    : (el.textContent || '').trim(),
                rect: el.getBoundingClientRect(),
                style: window.getComputedStyle(el),
            };
        }).filter(Boolean).filter((item) => item.text || item.kind === 'comment');
    }

    function hidePptxTextBlocks(blocks) {
        blocks.forEach(({ el }) => {
            el.dataset.pptxPreviousVisibility = el.style.visibility;
            el.style.visibility = 'hidden';
        });
    }

    function restorePptxTextBlocks(blocks) {
        blocks.forEach(({ el }) => {
            el.style.visibility = el.dataset.pptxPreviousVisibility || '';
            delete el.dataset.pptxPreviousVisibility;
        });
    }

    function hideValidationPanelsForExport(section) {
        const hidden = [];
        section.querySelectorAll('.validation-panel').forEach((panel) => {
            hidden.push({ el: panel, display: panel.style.display });
            panel.style.display = 'none';
        });
        return hidden;
    }

    function restoreValidationPanelsForExport(hiddenPanels) {
        hiddenPanels.forEach(({ el, display }) => {
            el.style.display = display || '';
        });
    }

    function addPptxTextBlock(slide, block, sectionRect, imagePlacement, imageScale) {
        const relativeLeft = block.rect.left - sectionRect.left;
        const relativeTop = block.rect.top - sectionRect.top;
        const x = imagePlacement.x + (relativeLeft * imageScale);
        const y = imagePlacement.y + (relativeTop * imageScale);
        const w = Math.max(0.18, block.rect.width * imageScale);
        const h = Math.max(0.14, block.rect.height * imageScale);
        const fontWeight = Number.parseInt(block.style.fontWeight, 10);
        const baseOptions = {
            x,
            y,
            w,
            h,
            fontFace: firstFontFamily(block.style.fontFamily),
            fontSize: Math.max(8, pxToPt(block.style.fontSize)),
            color: cssColorToHex(block.style.color),
            bold: Number.isFinite(fontWeight) ? fontWeight >= 600 : block.style.fontWeight === 'bold',
            italic: block.style.fontStyle === 'italic',
            align: (block.style.textAlign || 'left').toLowerCase(),
            fit: 'shrink',
            margin: 0.02,
            valign: 'mid',
            breakLine: false,
        };

        if (block.kind === 'comment') {
            slide.addText(block.text, {
                ...baseOptions,
                fill: { color: 'FFFFFF' },
                line: { color: 'FFFFFF', transparency: 100, pt: 0 },
                margin: 0.06,
                valign: 'top',
            });
            return;
        }

        slide.addText(block.text || ' ', {
            ...baseOptions,
            fill: { color: 'FFFFFF', transparency: 100 },
            line: { color: 'FFFFFF', transparency: 100 },
        });
    }

    async function loadLogoDataUrl() {
        try {
            const response = await fetch('/static/sitesync/images/logo.png');
            if (!response.ok) { return null; }
            const blob = await response.blob();
            return await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = () => resolve(null);
                reader.readAsDataURL(blob);
            });
        } catch (_error) {
            return null;
        }
    }

    async function downloadPptx() {
        const sections = Array.from(document.querySelectorAll('#report-sections .section-card'))
            .filter((el) => !el.classList.contains('pdf-exclude'));

        if (!sections.length) {
            window.alert('No report sections are available to export as PPTX.');
            return;
        }

        const PptxCtor = getPptxConstructor();
        if (!PptxCtor || !window.html2canvas) {
            window.alert('PPTX export is not available in this browser.');
            return;
        }

        const pptx = new PptxCtor();
        if (typeof pptx.defineLayout === 'function') {
            pptx.defineLayout({ name: 'ENERLYTIX_WIDE', width: 13.333, height: 7.5 });
            pptx.layout = 'ENERLYTIX_WIDE';
        } else {
            pptx.layout = 'LAYOUT_WIDE';
        }
        pptx.author = 'Enerlytix';
        pptx.company = 'Enerlytix';
        pptx.subject = 'Report export';
        pptx.title = 'Enerlytix Report';
        pptx.lang = 'en-GB';

        const slideW = 13.333;
        const slideH = 7.5;
        const margin = 0.35;
        const logoAreaH = 0.38;
        const logoPad = 0.1;
        const logoDataUrl = await loadLogoDataUrl();
        const logoAspect = logoDataUrl
            ? await new Promise((resolve) => {
                const img = new Image();
                img.onload = () => resolve(img.naturalWidth && img.naturalHeight ? img.naturalWidth / img.naturalHeight : 1);
                img.onerror = () => resolve(1);
                img.src = logoDataUrl;
            })
            : 1;

        document.body.classList.add('is-exporting');

        try {
            for (let index = 0; index < sections.length; index += 1) {
                const section = sections[index];
                const sectionRect = section.getBoundingClientRect();
                const hiddenValidationPanels = hideValidationPanelsForExport(section);
                const textBlocks = collectPptxTextBlocks(section);
                hidePptxTextBlocks(textBlocks);

                let canvas;
                try {
                    canvas = await window.html2canvas(section, {
                        scale: 1.5,
                        backgroundColor: '#ffffff',
                        useCORS: true,
                        allowTaint: false,
                        logging: false,
                    });
                } finally {
                    restorePptxTextBlocks(textBlocks);
                    restoreValidationPanelsForExport(hiddenValidationPanels);
                }

                const slide = pptx.addSlide();
                slide.background = { color: 'FFFFFF' };

                const coverSection = isCoverSection(section);
                const exportMargin = coverSection ? 0 : margin;
                const exportLogoDataUrl = coverSection ? null : logoDataUrl;
                const imageX = exportMargin;
                const imageY = coverSection ? 0 : margin + logoAreaH + logoPad;
                const availableW = slideW - (exportMargin * 2);
                const availableH = slideH - imageY - exportMargin;
                const ratio = Math.min(availableW / canvas.width, availableH / canvas.height);
                const imageW = canvas.width * ratio;
                const imageH = canvas.height * ratio;
                const positionedX = imageX + (availableW - imageW) / 2;

                if (exportLogoDataUrl) {
                    const logoH = logoAreaH;
                    const logoW = logoH * logoAspect;
                    slide.addImage({ data: exportLogoDataUrl, x: margin, y: margin, w: logoW, h: logoH });
                }

                slide.addImage({
                    data: canvas.toDataURL('image/jpeg', 0.85),
                    x: positionedX,
                    y: imageY,
                    w: imageW,
                    h: imageH,
                });

                const textScale = imageW / sectionRect.width;
                textBlocks.forEach((block) => addPptxTextBlock(slide, block, sectionRect, { x: positionedX, y: imageY }, textScale));
            }

            const ctx = getContext();
            const fileName = `Enerlytix_Report_${ctx.siteName || 'Site'}_${ctx.endMonth || 'report'}.pptx`;
            await pptx.writeFile({ fileName });
        } catch (error) {
            console.error('Unable to generate PPTX export.', error);
            window.alert('Unable to generate PPTX export. Please try again.');
        } finally {
            document.body.classList.remove('is-exporting');
        }
    }

    async function downloadPdf() {
        const sections = Array.from(document.querySelectorAll('#report-sections .section-card'))
            .filter((el) => !el.classList.contains('pdf-exclude'));
        if (!sections.length || !window.jspdf || !window.html2canvas) { return; }
        const { jsPDF } = window.jspdf;

        // 16:9 widescreen landscape in points (1pt = 1/72 inch) - standard
        // 13.333in x 7.5in slide size, replacing the previous A4 (~4:3-ish) page.
        const pdf = new jsPDF({ orientation: 'landscape', unit: 'pt', format: [960, 540], compress: true });
        const PW = pdf.internal.pageSize.getWidth();   // 960 pt
        const PH = pdf.internal.pageSize.getHeight();  // 540 pt
        const MARGIN = 32;                             // page margin all sides
        const LOGO_AREA_H = 36;                        // vertical space reserved for logo
        const LOGO_PAD = 10;                           // gap between logo and content

        document.body.classList.add('is-exporting');

        // ── Try to load the logo from the static file ──
        let logoData = null;
        let logoAspect = 1;
        try {
            const res = await fetch('/static/sitesync/images/logo.png');
            if (res.ok) {
                const blob = await res.blob();
                logoData = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result);
                    reader.readAsDataURL(blob);
                });
                // Measure aspect ratio via an off-screen Image
                await new Promise((resolve) => {
                    const img = new Image();
                    img.onload = () => { logoAspect = img.naturalWidth / img.naturalHeight; resolve(); };
                    img.onerror = resolve;
                    img.src = logoData;
                });
            }
        } catch (_e) { /* logo file not found — skip */ }

        try {
            for (let i = 0; i < sections.length; i += 1) {
                const section = sections[i];
                const coverSection = isCoverSection(section);
                const hiddenValidationPanels = hideValidationPanelsForExport(section);

                // Hide empty comment boxes so blank textareas don't waste space,
                // and swap non-empty ones for full-text blocks (see note above)
                // so multi-line comments aren't cropped to the on-screen viewport.
                const hiddenComments = [];
                const swappedComments = [];
                section.querySelectorAll('.comment-box').forEach((ta) => {
                    if (!ta.value.trim()) {
                        ta.style.visibility = 'hidden';
                        ta.style.height = '0';
                        ta.style.minHeight = '0';
                        ta.style.margin = '0';
                        ta.style.padding = '0';
                        hiddenComments.push(ta);
                    } else {
                        swappedComments.push({ ta, div: swapCommentBoxForCapture(ta) });
                    }
                });

                let canvas;
                try {
                    canvas = await window.html2canvas(section, {
                        scale: 1.5,
                        backgroundColor: '#ffffff',
                        useCORS: true,
                        allowTaint: false,
                        logging: false,
                    });
                } finally {
                    // Restore hidden comment boxes
                    hiddenComments.forEach((ta) => {
                        ta.style.visibility = '';
                        ta.style.height = '';
                        ta.style.minHeight = '';
                        ta.style.margin = '';
                        ta.style.padding = '';
                    });
                    // Restore swapped comment boxes
                    swappedComments.forEach(({ ta, div }) => restoreCommentBox(ta, div));
                    restoreValidationPanelsForExport(hiddenValidationPanels);
                }

                // JPEG at 0.85 quality keeps charts legible while cutting file
                // size by an order of magnitude versus lossless PNG output.
                const img = canvas.toDataURL('image/jpeg', 0.85);
                if (i > 0) { pdf.addPage(); }

                // White page background
                pdf.setFillColor(255, 255, 255);
                pdf.rect(0, 0, PW, PH, 'F');

                const exportLogoData = coverSection ? null : logoData;
                const pageMargin = coverSection ? 0 : MARGIN;
                const logoSpace = coverSection ? 0 : LOGO_AREA_H;
                const logoGap = coverSection ? 0 : LOGO_PAD;

                // ── Logo (top-left) ──────────────────────────────────────────
                if (exportLogoData) {
                    const logoH = LOGO_AREA_H;
                    const logoW = logoH * logoAspect;
                    pdf.addImage(exportLogoData, 'PNG', pageMargin, pageMargin, logoW, logoH);
                }

                // ── Content area: below logo, centred horizontally ───────────
                const contentTop = pageMargin + logoSpace + logoGap;
                const availW = PW - pageMargin * 2;
                const availH = PH - contentTop - pageMargin;
                const ratio = Math.min(availW / canvas.width, availH / canvas.height);
                const imgW = canvas.width * ratio;
                const imgH = canvas.height * ratio;
                const imgX = pageMargin + (availW - imgW) / 2;
                pdf.addImage(img, 'JPEG', imgX, contentTop, imgW, imgH, undefined, 'MEDIUM');
            }
        } finally {
            document.body.classList.remove('is-exporting');
        }

        const ctx = getContext();
        pdf.save(`Enerlytix_Report_${ctx.siteName || 'Site'}_${ctx.endMonth || 'report'}.pdf`);
    }

    // ─── Smooth nav scrolling ─────────────────────────────────────────────────

    function syncAnchorScrolling() {
        document.addEventListener('click', (event) => {
            const anchor = event.target.closest('#report-nav a');
            if (!anchor) { return; }
            const targetId = anchor.getAttribute('href');
            if (!targetId || targetId === '#') { return; }
            const target = document.querySelector(targetId);
            if (target) { event.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
        });
    }

    window.renderReport = buildPage;

    document.addEventListener('DOMContentLoaded', () => {
        const btn = document.getElementById('download-pdf-button');
        if (btn) { btn.addEventListener('click', downloadPdf); }
        const pptxBtn = document.getElementById('download-pptx-button');
        if (pptxBtn) { pptxBtn.addEventListener('click', downloadPptx); }
        syncAnchorScrolling();
        loadReport();
    });
})();
