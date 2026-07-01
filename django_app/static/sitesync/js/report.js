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

    const state = {
        reportData: null,
        comments: new Map(),
        charts: new Map(),
    };

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

    function getContext() {
        return window.ENERLYTIX_REPORT_CONTEXT || {};
    }

    function renderEmptyState(message) {
        const empty = document.getElementById('report-empty');
        if (empty) {
            empty.textContent = message;
            empty.style.display = 'block';
        }
    }

    function clearEmptyState() {
        const empty = document.getElementById('report-empty');
        if (empty) {
            empty.style.display = 'none';
        }
    }

    function setSubtitle(text) {
        const subtitle = document.getElementById('report-subtitle');
        if (subtitle) {
            subtitle.textContent = text;
        }
    }

    function setMeta(reportData) {
        const meta = document.getElementById('report-meta');
        if (!meta) {
            return;
        }

        const months = reportData.reporting_period?.months || [];
        const startLabel = months[0]?.label || '';
        const endLabel = months[months.length - 1]?.label || '';
        meta.innerHTML = [
            `<span><strong>Site:</strong> ${escapeHtml(reportData.site?.name || 'Unknown')}</span>`,
            `<span><strong>End month:</strong> ${escapeHtml(reportData.reporting_period?.end_month || '')}</span>`,
            `<span><strong>Window:</strong> ${escapeHtml(startLabel)} to ${escapeHtml(endLabel)}</span>`,
        ].join('');
    }

    function destroyCharts() {
        state.charts.forEach((chart) => chart.destroy());
        state.charts.clear();
    }

    function createCard(title, bodyHtml, cardClass = '') {
        return `
            <section class="section-card ${cardClass}" style="margin-bottom:0.85rem;">
                <div style="display:flex;justify-content:space-between;gap:0.75rem;align-items:flex-start;flex-wrap:wrap;">
                    <h3 style="margin:0;">${escapeHtml(title)}</h3>
                </div>
                ${bodyHtml}
            </section>
        `;
    }

    function createChartSlot(chartId, height = '18rem') {
        return `
            <div style="margin-top:0.7rem;">
                <div class="chart-box" style="height:${height}; padding:0.5rem;">
                    <canvas id="${escapeHtml(chartId)}"></canvas>
                </div>
            </div>
        `;
    }

    function createPlaceholderSlot(message) {
        return `
            <div style="margin-top:0.7rem;">
                <div class="chart-box" style="min-height:10rem; height:auto; padding:1rem; text-align:center;">
                    <div>${escapeHtml(message)}</div>
                </div>
            </div>
        `;
    }

    function createCommentBox(sectionId) {
        return `
            <textarea class="comment-box" data-section-id="${escapeHtml(sectionId)}" placeholder="Add a comment..."></textarea>
        `;
    }

    function registerCommentBoxes(root) {
        root.querySelectorAll('.comment-box').forEach((textarea) => {
            const sectionId = textarea.dataset.sectionId;
            if (sectionId && state.comments.has(sectionId)) {
                textarea.value = state.comments.get(sectionId);
            }
            textarea.addEventListener('input', () => {
                state.comments.set(sectionId, textarea.value);
            });
        });
    }

    function renderNavEntry(label, targetId) {
        return `<a href="#${escapeHtml(targetId)}">${escapeHtml(label)}</a>`;
    }

    function normaliseMonthlySeries(series, utilityType) {
        const months = series?.months || [];
        const currentKey = utilityType === 'water' ? 'current_m3' : 'current_kwh';
        const previousKey = utilityType === 'water' ? 'previous_year_m3' : 'previous_year_kwh';
        const benchmarkKey = utilityType === 'water' ? 'benchmark_m3' : 'benchmark_kwh';

        return {
            labels: months.map((item) => item.label),
            current: series?.[currentKey] || [],
            previous: series?.[previousKey] || [],
            benchmark: series?.[benchmarkKey] || [],
        };
    }

    function renderOverviewSection(reportData) {
        const targetId = 'overview';
        const items = reportData.overview?.by_utility || [];
        const chartId = 'overview-chart';
        const tableId = 'overview-table';
        const chartContainer = createChartSlot(chartId, '18rem');
        const chartCard = createCard('Total Utility Usage (£)', `
            <div style="color:#5b7080;font-size:0.86rem;">Site-wide cost summary for the selected 12-month period.</div>
            ${chartContainer}
            ${createCommentBox(`overview-chart-${targetId}`)}
        `);
        const tableRows = items.map((item) => `
            <tr>
                <td>${escapeHtml(item.label)}</td>
                <td>${formatCurrency(item.total_cost)}</td>
                <td>${formatNumber(item.percentage, 1)}%</td>
                <td>${escapeHtml((item.meter_numbers || []).join(', '))}</td>
            </tr>
        `).join('');
        const tableCard = createCard('Overview Breakdown', `
            <table id="${tableId}">
                <thead><tr><th>Utility</th><th>Total Cost</th><th>Share</th><th>Meters</th></tr></thead>
                <tbody>${tableRows || '<tr><td colspan="4">No overview data available.</td></tr>'}</tbody>
            </table>
            ${createCommentBox(`overview-table-${targetId}`)}
        `);

        return {
            id: targetId,
            html: `<section class="section" id="${targetId}"><h2>Overview</h2>${chartCard}${tableCard}</section>`,
            init() {
                const canvas = document.getElementById(chartId);
                if (!canvas) {
                    return;
                }
                const dataset = {
                    labels: items.map((item) => item.label),
                    datasets: [{
                        data: items.map((item) => Number(item.total_cost || 0)),
                        backgroundColor: [palette.electricity, palette.gas, palette.water],
                        borderColor: '#FFFFFF',
                        borderWidth: 2,
                    }],
                };
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'doughnut',
                    data: dataset,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom' },
                        },
                    },
                }));
            },
        };
    }

    function renderMonthlyChartCard(supply) {
        const sectionId = `monthly-${supply.id}`;
        const chartId = `monthly-chart-${supply.id}`;
        const series = normaliseMonthlySeries(supply.monthly, supply.utility_type);
        const hasData = series.labels.length > 0;

        const cardHtml = hasData ? createChartSlot(chartId, '20rem') : createPlaceholderSlot('No monthly data available');
        return {
            id: `${sectionId}-card`,
            html: createCard(`Monthly ${supply.utility_type_display} Usage`, `
                <div style="color:#5b7080;font-size:0.86rem;">Current year, previous year and benchmark comparison for the selected reporting window.</div>
                ${cardHtml}
                <div style="margin-top:0.75rem;">
                    <table>
                        <thead><tr><th>Date</th><th>Last 12 Months</th><th>Prev. 12 Months</th><th>Gross Variance</th><th>Relative Variance</th></tr></thead>
                        <tbody>
                            ${(supply.monthly?.table || []).map((row) => `
                                <tr>
                                    <td>${escapeHtml(row.date)}</td>
                                    <td>${formatNumber(row.current, 2)}</td>
                                    <td>${formatNumber(row.previous_year, 2)}</td>
                                    <td>${formatNumber(row.gross_variance, 2)}</td>
                                    <td>${formatNumber(row.relative_variance, 1)}%</td>
                                </tr>
                            `).join('') || '<tr><td colspan="5">No monthly table data available.</td></tr>'}
                        </tbody>
                    </table>
                </div>
                ${createCommentBox(`monthly-table-${sectionId}`)}
                ${createCommentBox(`monthly-chart-${sectionId}`)}
            `),
            init() {
                if (!hasData) {
                    return;
                }
                const canvas = document.getElementById(chartId);
                if (!canvas) {
                    return;
                }
                const datasets = [
                    {
                        label: 'Current',
                        data: series.current,
                        backgroundColor: palette.electricity,
                        borderColor: palette.electricity,
                    },
                    {
                        label: 'Previous Year',
                        data: series.previous,
                        backgroundColor: palette.gas,
                        borderColor: palette.gas,
                    },
                ];
                if (series.benchmark.some((item) => item !== null && item !== undefined)) {
                    datasets.push({
                        label: 'Benchmark',
                        data: series.benchmark,
                        backgroundColor: palette.benchmark,
                        borderColor: palette.benchmark,
                    });
                }
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'bar',
                    data: { labels: series.labels, datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        parsing: false,
                        normalized: true,
                        scales: {
                            x: { stacked: false },
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback(value) {
                                        return `${formatNumber(value, 0)}K`;
                                    },
                                },
                            },
                        },
                        plugins: {
                            legend: { position: 'bottom' },
                        },
                    },
                }));
            },
        };
    }

    function renderLoadFactorCard(supply) {
        const sectionId = `load-factor-${supply.id}`;
        const chartId = `load-factor-chart-${supply.id}`;
        if (!supply.load_factor || !(supply.load_factor.halfhourly || []).length) {
            return {
                id: sectionId,
                html: createCard('Load Factor', `${createPlaceholderSlot('No load factor data available')}${createCommentBox(sectionId)}`),
                init() {},
            };
        }

        const values = supply.load_factor.halfhourly || [];
        const labels = values.map((item, index) => index + 1);
        return {
            id: sectionId,
            html: createCard('Load Factor', `
                <div class="metric-grid">
                    <div class="metric"><div class="metric-label">Load Factor</div><div class="metric-value">${formatNumber(supply.load_factor.load_factor_pct, 1)}%</div></div>
                    <div class="metric"><div class="metric-label">Max Demand</div><div class="metric-value">${formatNumber(supply.load_factor.max_demand_kw, 2)} kW</div></div>
                    <div class="metric"><div class="metric-label">Available Capacity</div><div class="metric-value">${supply.load_factor.available_capacity_kw === null ? 'N/A' : `${formatNumber(supply.load_factor.available_capacity_kw, 2)} kW`}</div></div>
                    <div class="metric"><div class="metric-label">Readings</div><div class="metric-value">${values.length}</div></div>
                </div>
                ${createChartSlot(chartId, '17rem')}
                ${createCommentBox(sectionId)}
            `),
            init() {
                const canvas = document.getElementById(chartId);
                if (!canvas) {
                    return;
                }
                const maxDemand = Number(supply.load_factor.max_demand_kw || 0);
                const availableCapacity = supply.load_factor.available_capacity_kw === null ? null : Number(supply.load_factor.available_capacity_kw || 0);
                const series = [
                    {
                        label: 'Consumption',
                        data: values.map((item) => Number(item.consumption_kwh || 0)),
                        borderColor: palette.electricity,
                        backgroundColor: 'rgba(122, 184, 0, 0.16)',
                        fill: true,
                        pointRadius: 0,
                        tension: 0.2,
                    },
                    {
                        label: 'Max Demand',
                        data: labels.map(() => maxDemand),
                        borderColor: palette.gas,
                        backgroundColor: palette.gas,
                        borderDash: [5, 4],
                        pointRadius: 0,
                        fill: false,
                    },
                ];
                if (availableCapacity !== null) {
                    series.push({
                        label: 'Available Capacity',
                        data: labels.map(() => availableCapacity),
                        borderColor: palette.benchmark,
                        backgroundColor: palette.benchmark,
                        borderDash: [2, 3],
                        pointRadius: 0,
                        fill: false,
                    });
                }
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'line',
                    data: { labels, datasets: series },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        parsing: false,
                        normalized: true,
                        plugins: { legend: { position: 'bottom' } },
                        scales: {
                            x: { ticks: { display: false } },
                            y: { beginAtZero: true },
                        },
                    },
                }));
            },
        };
    }

    function renderComparisonCard(title, sectionId, chartId, comparison, colorA, colorB) {
        if (!comparison || !(comparison.current || []).length) {
            return {
                id: sectionId,
                html: createCard(title, `${createPlaceholderSlot('No half-hourly data available')}${createCommentBox(sectionId)}`),
                init() {},
            };
        }

        const labels = comparison.current.map((item) => item.ts);
        return {
            id: sectionId,
            html: createCard(title, `
                ${createChartSlot(chartId, '17rem')}
                ${createCommentBox(sectionId)}
            `),
            init() {
                const canvas = document.getElementById(chartId);
                if (!canvas) {
                    return;
                }
                const currentSeries = comparison.current.map((item) => Number(item.consumption_kwh || 0));
                const previousSeries = (comparison.previous_year || []).map((item) => Number(item.consumption_kwh || 0));
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels,
                        datasets: [
                            {
                                label: 'Current Year',
                                data: currentSeries,
                                borderColor: colorA,
                                backgroundColor: colorA,
                                pointRadius: 0,
                                tension: 0.15,
                            },
                            {
                                label: 'Previous Year Same Month',
                                data: previousSeries,
                                borderColor: colorB,
                                backgroundColor: colorB,
                                pointRadius: 0,
                                tension: 0.15,
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        parsing: false,
                        normalized: true,
                        plugins: { legend: { position: 'bottom' } },
                        scales: {
                            x: { ticks: { display: false } },
                            y: { beginAtZero: true },
                        },
                    },
                }));
            },
        };
    }

    function renderDayNightCard(supply) {
        const sectionId = `day-night-${supply.id}`;
        const chartId = `day-night-chart-${supply.id}`;
        const dayNight = supply.day_night;
        if (!dayNight || !(dayNight.records || []).length) {
            return {
                id: sectionId,
                html: createCard('HH Electricity Day/Night Usage - Last Month', `${createPlaceholderSlot('No half-hourly data available')}${createCommentBox(sectionId)}`),
                init() {},
            };
        }

        const labels = dayNight.records.map((item) => item.ts);
        return {
            id: sectionId,
            html: createCard('HH Electricity Day/Night Usage - Last Month', `
                ${createChartSlot(chartId, '17rem')}
                ${createCommentBox(sectionId)}
            `),
            init() {
                const canvas = document.getElementById(chartId);
                if (!canvas) {
                    return;
                }
                const daySeries = dayNight.records.map((item) => item.period === 'day' ? Number(item.consumption_kwh || 0) : 0);
                const nightSeries = dayNight.records.map((item) => item.period === 'night' ? Number(item.consumption_kwh || 0) : 0);
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels,
                        datasets: [
                            { label: 'Day', data: daySeries, backgroundColor: palette.electricity, stack: 'usage' },
                            { label: 'Night', data: nightSeries, backgroundColor: palette.water, stack: 'usage' },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        parsing: false,
                        normalized: true,
                        plugins: { legend: { position: 'bottom' } },
                        scales: {
                            x: { stacked: true, ticks: { display: false } },
                            y: { stacked: true, beginAtZero: true },
                        },
                    },
                }));
            },
        };
    }

    function renderWeekComparisonCard(title, sectionId, chartId, comparison) {
        if (!comparison || !comparison.days || !comparison.days.length) {
            return {
                id: sectionId,
                html: createCard(title, `${createPlaceholderSlot('No day comparison data available')}${createCommentBox(sectionId)}`),
                init() {},
            };
        }

        return {
            id: sectionId,
            html: createCard(title, `
                ${createChartSlot(chartId, '17rem')}
                ${createCommentBox(sectionId)}
            `),
            init() {
                const canvas = document.getElementById(chartId);
                if (!canvas) {
                    return;
                }
                const colours = [palette.electricity, palette.gas, palette.water, palette.benchmark, palette.greenDark, '#9B59B6', '#E67E22', '#1ABC9C'];
                const datasets = comparison.days.map((day, index) => ({
                    label: day.day_name || day.date,
                    data: (day.records || []).map((record) => Number(record.consumption_kwh || 0)),
                    borderColor: colours[index % colours.length],
                    backgroundColor: colours[index % colours.length],
                    pointRadius: 0,
                    tension: 0.15,
                }));
                state.charts.set(chartId, new Chart(canvas, {
                    type: 'line',
                    data: { datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        parsing: false,
                        normalized: true,
                        plugins: { legend: { position: 'bottom' } },
                        scales: {
                            x: {
                                title: { display: true, text: 'Half-hour interval' },
                                ticks: { callback(value) { return value; } },
                            },
                            y: { beginAtZero: true },
                        },
                    },
                }));
            },
        };
    }

    function renderSupplySection(supply) {
        const sectionId = `supply-${supply.id}`;
        const cards = [];
        cards.push(renderMonthlyChartCard(supply));
        if (supply.utility_type === 'electricity') {
            cards.push(renderLoadFactorCard(supply));
            cards.push(renderComparisonCard('HH Electricity Data Comparison - Last Month', `hh-${supply.id}`, `hh-chart-${supply.id}`, supply.hh_comparison, palette.electricity, palette.gas));
            cards.push(renderDayNightCard(supply));
            cards.push(renderWeekComparisonCard('Daily Comparison - Weekday Usage', `weekday-${supply.id}`, `weekday-chart-${supply.id}`, supply.weekday_comparison));
            cards.push(renderWeekComparisonCard('Daily Comparison - Weekend Usage', `weekend-${supply.id}`, `weekend-chart-${supply.id}`, supply.weekend_comparison));
        } else if (supply.utility_type === 'gas') {
            cards.push(renderComparisonCard('HH Gas Data Comparison - Last Month', `hh-${supply.id}`, `hh-chart-${supply.id}`, supply.hh_comparison, palette.electricity, palette.gas));
            cards.push(renderWeekComparisonCard('Daily Comparison - Weekday Usage (Gas)', `weekday-${supply.id}`, `weekday-chart-${supply.id}`, supply.weekday_comparison));
            cards.push(renderWeekComparisonCard('Daily Comparison - Weekend Usage (Gas)', `weekend-${supply.id}`, `weekend-chart-${supply.id}`, supply.weekend_comparison));
        }

        const header = `
            <div class="empty-state" style="margin-bottom:0.75rem;">Meter: ${escapeHtml(supply.meter_number || 'N/A')}</div>
            <div class="section-card" style="margin-bottom:0.85rem;">
                <h2 style="margin:0;">${escapeHtml(supply.label || supply.utility_type_display || 'Supply')}</h2>
                <div style="color:#5b7080;font-size:0.84rem;margin-top:0.25rem;">${escapeHtml(supply.utility_type_display || '')}</div>
            </div>
        `;

        return {
            id: sectionId,
            html: `<section class="section" id="${sectionId}">${header}${cards.map((card) => card.html).join('')}</section>`,
            init() {
                cards.forEach((card) => card.init());
            },
        };
    }

    function renderNoSuppliesState() {
        const sections = document.getElementById('report-sections');
        const nav = document.getElementById('report-nav');
        if (!sections || !nav) {
            return;
        }
        nav.innerHTML = renderNavEntry('Overview', 'overview');
        sections.innerHTML = `
            <section class="section section-card" id="overview">
                <h2>Overview</h2>
                <div class="empty-state">No supplies were found for this site.</div>
            </section>
        `;
    }

    function buildPage(reportData) {
        const sections = document.getElementById('report-sections');
        const nav = document.getElementById('report-nav');
        const empty = document.getElementById('report-empty');
        if (!sections || !nav || !empty) {
            return;
        }

        destroyCharts();
        sections.innerHTML = '';
        nav.innerHTML = '';
        clearEmptyState();

        const renderedSections = [];
        const overview = renderOverviewSection(reportData);
        renderedSections.push(overview);
        nav.insertAdjacentHTML('beforeend', renderNavEntry('Overview', overview.id));

        const supplies = reportData.supplies || [];
        if (!supplies.length) {
            renderNoSuppliesState();
            registerCommentBoxes(document);
            return;
        }

        supplies.forEach((supply) => {
            const rendered = renderSupplySection(supply);
            renderedSections.push(rendered);
            nav.insertAdjacentHTML('beforeend', renderNavEntry(supply.label || supply.utility_type_display || 'Supply', rendered.id));
        });

        sections.innerHTML = renderedSections.map((item) => item.html).join('');
        renderedSections.forEach((item) => item.init());
        registerCommentBoxes(sections);
        registerCommentBoxes(nav);
        empty.style.display = 'none';
    }

    async function fetchReportData() {
        const context = getContext();
        const params = new URLSearchParams({
            site_id: context.siteId || '',
            end_month: context.endMonth || '',
        });

        const response = await fetch('/api/report-data/?' + params.toString(), {
            credentials: 'same-origin',
        });
        if (!response.ok) {
            throw new Error('Unable to load report data.');
        }
        return response.json();
    }

    async function loadReport() {
        try {
            const reportData = await fetchReportData();
            state.reportData = reportData;
            setSubtitle(`${reportData.site.name} · ${reportData.reporting_period.end_month}`);
            setMeta(reportData);
            buildPage(reportData);
        } catch (error) {
            console.error(error);
            renderEmptyState('Unable to load report data.');
            setSubtitle('Report data unavailable');
        }
    }

    async function downloadPdf() {
        const sections = Array.from(document.querySelectorAll('#report-sections .section-card'));
        if (!sections.length || !window.jspdf || !window.html2canvas) {
            return;
        }

        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
        document.body.classList.add('is-exporting');

        try {
            for (let index = 0; index < sections.length; index += 1) {
                const canvas = await window.html2canvas(sections[index], { scale: 2, backgroundColor: '#ffffff' });
                const image = canvas.toDataURL('image/png');
                const pageWidth = pdf.internal.pageSize.getWidth();
                const pageHeight = pdf.internal.pageSize.getHeight();
                const ratio = Math.min((pageWidth - 40) / canvas.width, (pageHeight - 40) / canvas.height);
                const imageWidth = canvas.width * ratio;
                const imageHeight = canvas.height * ratio;
                if (index > 0) {
                    pdf.addPage();
                }
                pdf.addImage(image, 'PNG', 20, 20, imageWidth, imageHeight);
            }
        } finally {
            document.body.classList.remove('is-exporting');
        }

        const context = getContext();
        pdf.save(`Enerlytix_Report_${context.siteName || 'Site'}_${context.endMonth || 'report'}.pdf`);
    }

    function syncAnchorScrolling() {
        document.addEventListener('click', (event) => {
            const anchor = event.target.closest('#report-nav a');
            if (!anchor) {
                return;
            }
            const targetId = anchor.getAttribute('href');
            if (!targetId || targetId === '#') {
                return;
            }
            const target = document.querySelector(targetId);
            if (target) {
                event.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }

    window.renderReport = buildPage;

    document.addEventListener('DOMContentLoaded', () => {
        const downloadButton = document.getElementById('download-pdf-button');
        if (downloadButton) {
            downloadButton.addEventListener('click', downloadPdf);
        }
        syncAnchorScrolling();
        loadReport();
    });
})();
