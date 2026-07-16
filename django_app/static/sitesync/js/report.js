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
        referenceCommentKeys: new Set(),
        charts: new Map(),
    };

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(';').shift();
        }
        return '';
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

    (function initializeCommentState() {
        const ctx = getContext();
        const initial = ctx.initialComments || {};
        Object.entries(initial).forEach(([key, value]) => {
            state.comments.set(String(key), String(value || ''));
        });
        const refKeys = Array.isArray(ctx.referenceCommentKeys) ? ctx.referenceCommentKeys : [];
        refKeys.forEach((key) => state.referenceCommentKeys.add(String(key)));
    }());

    async function saveDraftReport() {
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
        const ctx = getContext();
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

        window.alert('Final report saved.');
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
    if (saveDraftButton) {
        saveDraftButton.addEventListener('click', () => {
            saveDraftReport().catch(() => window.alert('Unable to save draft report.'));
        });
    }

    const saveFinalButton = document.getElementById('save-final-button');
    if (saveFinalButton) {
        saveFinalButton.addEventListener('click', () => {
            saveFinalReport(false).catch(() => window.alert('Unable to save final report.'));
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
        return `${warning}<textarea class="comment-box" data-section-id="${escapeHtml(id)}" placeholder="Add a comment..." style="margin-top:0.6rem;"></textarea>`;
    }

    function registerCommentBoxes(root) {
        root.querySelectorAll('.comment-box').forEach((ta) => {
            const sid = ta.dataset.sectionId;
            if (sid && state.comments.has(sid)) { ta.value = state.comments.get(sid); }
            ta.addEventListener('input', () => state.comments.set(sid, ta.value));
        });
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
        const availCap = lf.available_capacity_kw === null ? null : Number(lf.available_capacity_kw || 0);
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
                        <div class="metric"><div class="metric-label">Available Capacity (kW)</div><div class="metric-value">${availCap === null ? 'N/A' : formatNumber(availCap, 0)}</div></div>
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
        const overview = renderOverviewSection(reportData);
        rendered.push(overview);
        nav.insertAdjacentHTML('beforeend', renderNavEntry('Overview', overview.id));

        const supplies = reportData.supplies || [];
        if (!supplies.length) {
            renderNoSuppliesState();
            registerCommentBoxes(document);
            return;
        }

        supplies.forEach((supply) => {
            const sec = renderSupplySection(supply);
            rendered.push(sec);
            nav.insertAdjacentHTML('beforeend', renderNavEntry(supply.label || supply.utility_type_display || 'Supply', sec.id));
        });

        sections.innerHTML = rendered.map((r) => r.html).join('');
        rendered.forEach((r) => r.init());
        registerCommentBoxes(sections);
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
            setSubtitle(`${reportData.site.name} \u00b7 ${reportData.reporting_period.end_month}`);
            setMeta(reportData);
            buildPage(reportData);
        } catch (error) {
            console.error(error);
            renderEmptyState('Unable to load report data.');
            setSubtitle('Report data unavailable');
        }
    }

    // ─── PDF export ───────────────────────────────────────────────────────────

    async function downloadPdf() {
        const sections = Array.from(document.querySelectorAll('#report-sections .section-card'))
            .filter((el) => !el.classList.contains('pdf-exclude'));
        if (!sections.length || !window.jspdf || !window.html2canvas) { return; }
        const { jsPDF } = window.jspdf;

        // A4 landscape in points (1pt = 1/72 inch)
        const pdf = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
        const PW = pdf.internal.pageSize.getWidth();   // ~841.89 pt
        const PH = pdf.internal.pageSize.getHeight();  // ~595.28 pt
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

                // Hide empty comment boxes so blank textareas don't waste space
                const hiddenComments = [];
                section.querySelectorAll('.comment-box').forEach((ta) => {
                    if (!ta.value.trim()) {
                        ta.style.visibility = 'hidden';
                        ta.style.height = '0';
                        ta.style.minHeight = '0';
                        ta.style.margin = '0';
                        ta.style.padding = '0';
                        hiddenComments.push(ta);
                    }
                });

                const canvas = await window.html2canvas(section, {
                    scale: 2,
                    backgroundColor: '#ffffff',
                    useCORS: true,
                    allowTaint: false,
                    logging: false,
                });

                // Restore hidden comment boxes
                hiddenComments.forEach((ta) => {
                    ta.style.visibility = '';
                    ta.style.height = '';
                    ta.style.minHeight = '';
                    ta.style.margin = '';
                    ta.style.padding = '';
                });

                const img = canvas.toDataURL('image/png');
                if (i > 0) { pdf.addPage(); }

                // White page background
                pdf.setFillColor(255, 255, 255);
                pdf.rect(0, 0, PW, PH, 'F');

                // ── Logo (top-left) ──────────────────────────────────────────
                if (logoData) {
                    const logoH = LOGO_AREA_H;
                    const logoW = logoH * logoAspect;
                    pdf.addImage(logoData, 'PNG', MARGIN, MARGIN, logoW, logoH);
                }

                // ── Content area: below logo, centred horizontally ───────────
                const contentTop = MARGIN + LOGO_AREA_H + LOGO_PAD;
                const availW = PW - MARGIN * 2;
                const availH = PH - contentTop - MARGIN;
                const ratio = Math.min(availW / canvas.width, availH / canvas.height);
                const imgW = canvas.width * ratio;
                const imgH = canvas.height * ratio;
                const imgX = MARGIN + (availW - imgW) / 2;
                pdf.addImage(img, 'PNG', imgX, contentTop, imgW, imgH);
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
        syncAnchorScrolling();
        loadReport();
    });
})();
