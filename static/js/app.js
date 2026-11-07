// RetailIQ Frontend Application Logic

let rawInventoryData = [];
let salesTrendChartInstance = null;
let categoryChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    checkHealth();
});

// Switch Main Navigation Tabs
function switchTab(tabId) {
    const tabs = ['sales', 'inventory', 'risks', 'copilot'];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-btn-${t}`);
        const content = document.getElementById(`tab-content-${t}`);
        if (t === tabId) {
            btn.classList.add('active-tab');
            btn.classList.remove('text-slate-400', 'hover:bg-slate-700/50');
            content.classList.remove('hidden');
        } else {
            btn.classList.remove('active-tab');
            btn.classList.add('text-slate-400', 'hover:bg-slate-700/50');
            content.classList.add('hidden');
        }
    });

    if (tabId === 'inventory') {
        filterInventoryTable();
    }
}

// Drawer Toggle
function toggleCopilotDrawer() {
    const drawer = document.getElementById('copilot-drawer');
    const backdrop = document.getElementById('copilot-drawer-backdrop');
    if (drawer.classList.contains('translate-x-full')) {
        drawer.classList.remove('translate-x-full');
        backdrop.classList.remove('hidden');
        setTimeout(() => document.getElementById('drawer-input').focus(), 150);
    } else {
        drawer.classList.add('translate-x-full');
        backdrop.classList.add('hidden');
    }
}

// Check Backend Health and AI Engine
async function checkHealth() {
    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        const label = document.getElementById('ai-engine-label');
        if (data.gemini_active) {
            label.textContent = 'Gemini AI Active';
            label.parentElement.classList.remove('border-slate-700');
            label.parentElement.classList.add('border-emerald-500/40', 'bg-emerald-950/30');
        } else {
            label.textContent = 'Deterministic Grounding';
        }
    } catch (e) {
        console.error('Health check failed', e);
    }
}

// Load all Dashboard Data with resilient individual fetching
async function loadDashboardData() {
    const safeFetch = async (url) => {
        try {
            const res = await fetch(url);
            if (!res.ok) {
                console.error(`HTTP error ${res.status} on ${url}`);
                return null;
            }
            return await res.json();
        } catch (e) {
            console.error(`Fetch failed for ${url}:`, e);
            return null;
        }
    };

    try {
        const [kpisRes, trendsRes, catRes, chanRes, topRes, invRes, risksRes] = await Promise.all([
            safeFetch('/api/kpis'),
            safeFetch('/api/sales/trends'),
            safeFetch('/api/categories'),
            safeFetch('/api/channels'),
            safeFetch('/api/top-products'),
            safeFetch('/api/inventory'),
            safeFetch('/api/risks')
        ]);

        if (kpisRes) renderKPIs(kpisRes);
        if (trendsRes) renderSalesTrendChart(trendsRes);
        if (catRes) renderCategoryChart(catRes);
        if (chanRes) renderChannelSplit(chanRes);
        if (topRes) renderTopProducts(topRes);
        
        if (invRes) {
            rawInventoryData = invRes;
            renderInventoryTable(rawInventoryData);
        }
        if (risksRes) renderRiskCards(risksRes);

    } catch (err) {
        console.error('Failed loading dashboard data:', err);
    }
}

// 1. Render Executive KPIs
function renderKPIs(data) {
    if (!data) return;
    const rev = data.total_revenue ?? data.revenue ?? 0;
    const prof = data.total_profit ?? data.profit ?? 0;
    const margin = data.gross_margin_pct ?? data.margin_pct ?? 0;
    const units = data.total_units_sold ?? data.units_sold ?? 0;
    const orders = data.total_orders ?? 0;
    const aov = data.avg_order_value ?? (orders > 0 ? (rev / orders) : 0);
    const crit = data.critical_risk_count ?? 0;

    const elRev = document.getElementById('kpi-revenue');
    if (elRev) elRev.textContent = `$${Number(rev).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    const elProf = document.getElementById('kpi-profit');
    if (elProf) elProf.textContent = `$${Number(prof).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    const elMargin = document.getElementById('kpi-margin');
    if (elMargin) elMargin.textContent = `${margin}%`;

    const elUnits = document.getElementById('kpi-units');
    if (elUnits) elUnits.textContent = `${Number(units).toLocaleString()} units`;

    const elAov = document.getElementById('kpi-aov');
    if (elAov) elAov.textContent = `$${Number(aov).toFixed(2)}`;

    const elCrit = document.getElementById('kpi-critical');
    if (elCrit) elCrit.textContent = `${crit} SKUs`;

    const elBadge = document.getElementById('nav-risk-badge');
    if (elBadge) elBadge.textContent = crit;

    if (data.total_skus !== undefined) {
        const elSkus = document.getElementById('inv-total-skus');
        if (elSkus) elSkus.textContent = `${data.total_skus} SKUs`;
    }
    if (data.total_stock_units !== undefined) {
        const elTotalUnits = document.getElementById('inv-total-units');
        if (elTotalUnits) elTotalUnits.textContent = `${Number(data.total_stock_units).toLocaleString()} Units`;
    }
    if (data.inventory_valuation_cost !== undefined) {
        const elCost = document.getElementById('inv-total-cost');
        if (elCost) elCost.textContent = `$${Number(data.inventory_valuation_cost).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
}

// 2. Render Sales Trend Line Chart
function renderSalesTrendChart(trends) {
    const ctx = document.getElementById('salesTrendChart').getContext('2d');
    if (salesTrendChartInstance) {
        salesTrendChartInstance.destroy();
    }

    const labels = trends.map(t => t.date.slice(5)); // MM-DD
    const revenues = trends.map(t => t.daily_revenue);
    const profits = trends.map(t => t.daily_profit);

    salesTrendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Daily Revenue ($)',
                    data: revenues,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 2,
                    pointHoverRadius: 5
                },
                {
                    label: 'Daily Profit ($)',
                    data: profits,
                    borderColor: '#10b981',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [4, 4],
                    tension: 0.35,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: $${ctx.raw.toLocaleString()}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: { color: '#94a3b8', font: { size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: {
                        color: '#94a3b8',
                        font: { size: 10 },
                        callback: (v) => `$${v}`
                    }
                }
            }
        }
    });
}

// 3. Render Category Donut Chart
function renderCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    if (categoryChartInstance) {
        categoryChartInstance.destroy();
    }

    const labels = categories.map(c => c.category);
    const revenues = categories.map(c => c.total_revenue);

    categoryChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: revenues,
                backgroundColor: [
                    '#6366f1',
                    '#38bdf8',
                    '#10b981',
                    '#f59e0b',
                    '#ec4899'
                ],
                borderWidth: 2,
                borderColor: '#1e293b'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#cbd5e1', boxWidth: 10, font: { size: 10 } }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.label}: $${ctx.raw.toLocaleString()} (${ctx.parsed}%)`
                    }
                }
            },
            cutout: '65%'
        }
    });
}

// 4. Render Channel Distribution
function renderChannelSplit(channels) {
    const container = document.getElementById('channel-split-container');
    if (!container || !channels || !Array.isArray(channels)) return;
    const totalRev = channels.reduce((sum, c) => sum + (c.total_revenue ?? c.revenue ?? 0), 0);

    container.innerHTML = channels.map(c => {
        const rev = c.total_revenue ?? c.revenue ?? 0;
        const pct = totalRev > 0 ? ((rev / totalRev) * 100).toFixed(1) : 0;
        const icon = c.channel === 'In-Store' ? 'fa-store text-emerald-400' : 'fa-globe text-indigo-400';
        return `
            <div class="space-y-1">
                <div class="flex justify-between text-xs font-semibold text-slate-300">
                    <span class="flex items-center space-x-1.5">
                        <i class="fa-solid ${icon}"></i>
                        <span>${escapeHtml(c.channel)}</span>
                    </span>
                    <span>$${Number(rev).toLocaleString()} <span class="text-slate-400 font-normal">(${pct}%)</span></span>
                </div>
                <div class="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
                    <div class="bg-indigo-500 h-full rounded-full" style="width: ${pct}%"></div>
                </div>
            </div>
        `;
    }).join('');
}

// 5. Render Top Products Table
function renderTopProducts(products) {
    const tbody = document.getElementById('top-products-table-body');
    if (!tbody || !products || !Array.isArray(products)) return;

    tbody.innerHTML = products.map((p, idx) => {
        const rank = p.rank || (idx + 1);
        const name = p.name || p.product_name || 'Product';
        const sku = p.sku || '';
        const category = p.category || '';
        const units = p.total_units_sold ?? p.quantity_sold ?? p.units_sold ?? 0;
        const rev = p.total_revenue ?? p.revenue ?? 0;
        const margin = p.margin_pct ?? p.profit_margin_pct ?? 0;

        return `
        <tr class="hover:bg-slate-750/50 transition-colors">
            <td class="py-2.5 px-3 font-bold text-slate-400 text-xs">#${rank}</td>
            <td class="py-2.5 px-3">
                <div class="font-semibold text-white">${escapeHtml(name)}</div>
                <div class="text-[11px] text-slate-400 font-mono">${escapeHtml(sku)}</div>
            </td>
            <td class="py-2.5 px-3 text-xs text-slate-300">${escapeHtml(category)}</td>
            <td class="py-2.5 px-3 text-xs text-right font-medium text-slate-200">${Number(units).toLocaleString()}</td>
            <td class="py-2.5 px-3 text-xs text-right font-bold text-emerald-400">$${Number(rev).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td class="py-2.5 px-3 text-xs text-right">
                <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-500/20 text-indigo-300">${margin}%</span>
            </td>
        </tr>
    `}).join('');
}

// 6. Render Full Inventory Table
function renderInventoryTable(items) {
    const tbody = document.getElementById('inventory-table-body');
    if (!tbody) return;
    const matchCount = document.getElementById('inv-match-count');
    if (matchCount) matchCount.textContent = `Showing ${items.length} of ${rawInventoryData.length} products`;

    if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center py-8 text-slate-500 text-sm">No products match the selected filters.</td></tr>`;
        return;
    }

    tbody.innerHTML = items.map(p => {
        const name = p.name || p.product_name || '';
        const sku = p.sku || '';
        const supplier = p.supplier_name || '';
        const cat = p.category || '';
        const cost = p.unit_cost ?? 0;
        const price = p.selling_price ?? 0;
        const stock = p.current_stock ?? 0;
        const ads = p.avg_daily_sales ?? 0;
        const doi = p.days_of_inventory ?? p.days_remaining ?? 0;
        const lt = p.lead_time_days ?? 0;
        const rop = p.calculated_reorder_point ?? p.reorder_level ?? 0;
        const badge = p.risk_badge || 'bg-slate-500 text-white';
        const riskLevel = p.risk_level || (p.risk_status ? p.risk_status.charAt(0) + p.risk_status.slice(1).toLowerCase() : 'Healthy');
        const reorderQty = p.suggested_reorder_qty ?? 0;

        // DOI runway color & width calculation (capped at 100%)
        let meterColor = 'bg-emerald-500';
        if (doi < 2.0) meterColor = 'bg-rose-500 animate-pulse';
        else if (doi <= 5.0) meterColor = 'bg-amber-500';
        else if (doi <= 14.0) meterColor = 'bg-yellow-500';
        else if (doi > 45.0) meterColor = 'bg-purple-500';

        const meterWidth = Math.min(100, Math.max(5, (doi / 30) * 100));

        return `
            <tr class="hover:bg-slate-800/60 transition-colors border-b border-slate-700/40">
                <td class="py-3 px-4">
                    <div class="font-semibold text-white text-xs sm:text-sm">${escapeHtml(name)}</div>
                    <div class="text-[11px] text-slate-400 font-mono">${escapeHtml(sku)} &bull; <span class="text-slate-500">${escapeHtml(supplier)}</span></div>
                </td>
                <td class="py-3 px-3 text-xs text-slate-300">${escapeHtml(cat)}</td>
                <td class="py-3 px-3 text-xs text-right text-slate-300">
                    <span class="text-slate-400">$${Number(cost).toFixed(2)}</span> / 
                    <strong class="text-white">$${Number(price).toFixed(2)}</strong>
                </td>
                <td class="py-3 px-3 text-xs text-right">
                    <strong class="text-sm ${stock <= 5 ? 'text-rose-400 font-black' : 'text-white'}">${stock}</strong>
                </td>
                <td class="py-3 px-3 text-xs text-right text-slate-300 font-mono">
                    ${ads}/day
                </td>
                <td class="py-3 px-3 w-36">
                    <div class="flex items-center justify-between text-xs mb-1">
                        <span class="font-bold text-slate-200">${doi}d</span>
                        <span class="text-[10px] text-slate-400">LT: ${lt}d</span>
                    </div>
                    <div class="runway-meter-track">
                        <div class="runway-meter-fill ${meterColor}" style="width: ${meterWidth}%"></div>
                    </div>
                </td>
                <td class="py-3 px-3 text-xs text-right font-semibold text-slate-300">
                    ${rop} units
                </td>
                <td class="py-3 px-3 text-center">
                    <span class="px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider ${badge}">
                        ${escapeHtml(riskLevel)}
                    </span>
                </td>
                <td class="py-3 px-4 text-center">
                    ${reorderQty > 0 ? `
                        <button onclick="askCopilotPrompt('Draft restock purchase order for ${escapeQuote(name)} (${escapeQuote(sku)}) to supplier ${escapeQuote(supplier)}')" class="px-2.5 py-1 rounded bg-indigo-600/30 hover:bg-indigo-600 text-indigo-200 hover:text-white border border-indigo-500/40 text-xs font-semibold transition-all">
                            + Reorder ${reorderQty}
                        </button>
                    ` : `
                        <span class="text-slate-500 text-xs font-medium">Optimal</span>
                    `}
                </td>
            </tr>
        `;
    }).join('');
}

// Filter Inventory Table dynamically
function filterInventoryTable() {
    const searchInput = document.getElementById('inv-search');
    const searchVal = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const catSelect = document.getElementById('inv-category-filter');
    const categoryVal = catSelect ? catSelect.value : 'ALL';
    const riskSelect = document.getElementById('inv-risk-filter');
    const riskVal = riskSelect ? riskSelect.value : 'ALL';

    const filtered = rawInventoryData.filter(p => {
        const name = (p.name || p.product_name || '').toLowerCase();
        const sku = (p.sku || '').toLowerCase();
        const supplier = (p.supplier_name || '').toLowerCase();

        const matchesSearch = !searchVal || 
            name.includes(searchVal) ||
            sku.includes(searchVal) ||
            supplier.includes(searchVal);

        const matchesCat = categoryVal === 'ALL' || p.category === categoryVal;
        
        let matchesRisk = true;
        if (riskVal !== 'ALL') {
            const rLevel = (p.risk_level || p.risk_status || '').toLowerCase();
            const targetRisk = riskVal.toLowerCase();
            if (targetRisk === 'critical') matchesRisk = rLevel.includes('crit');
            else if (targetRisk === 'high' || targetRisk === 'high risk') matchesRisk = rLevel.includes('high');
            else if (targetRisk === 'low' || targetRisk === 'warning') matchesRisk = rLevel.includes('low') || rLevel.includes('warn');
            else if (targetRisk === 'healthy' || targetRisk === 'optimal') matchesRisk = rLevel.includes('health') || rLevel.includes('opt');
            else matchesRisk = rLevel.includes(targetRisk);
        }

        return matchesSearch && matchesCat && matchesRisk;
    });

    renderInventoryTable(filtered);
}

// 7. Render Stockout Risk Cards
function renderRiskCards(risks) {
    const container = document.getElementById('risk-cards-grid');
    if (!container || !risks || !Array.isArray(risks)) return;

    container.innerHTML = risks.map(r => {
        const rLevel = r.risk_level || (r.risk_status ? r.risk_status.charAt(0) + r.risk_status.slice(1).toLowerCase() : 'Critical');
        const isCritical = rLevel.toLowerCase().includes('crit');
        const borderColor = isCritical ? 'border-rose-500/50 bg-rose-950/10' : 'border-amber-500/40 bg-amber-950/10';
        const badgeColor = isCritical ? 'bg-rose-500 text-white' : 'bg-amber-500 text-white';
        const name = r.name || r.product_name || '';
        const sku = r.sku || '';
        const cat = r.category || '';
        const doi = r.days_of_inventory ?? r.days_remaining ?? 0;
        const stock = r.current_stock ?? 0;
        const ads = r.avg_daily_sales ?? 0;
        const lt = r.lead_time_days ?? 0;
        const supplier = r.supplier_name ?? '';
        const reorderQty = r.suggested_reorder_qty ?? 0;
        const reorderCost = r.reorder_estimated_cost ?? 0;

        return `
            <div class="border ${borderColor} rounded-xl p-5 shadow-lg space-y-4">
                <div class="flex items-start justify-between">
                    <div>
                        <span class="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider ${badgeColor}">
                            ${escapeHtml(rLevel)} Stockout Threat
                        </span>
                        <h4 class="text-lg font-bold text-white mt-2">${escapeHtml(name)}</h4>
                        <p class="text-xs text-slate-400 font-mono">${escapeHtml(sku)} &bull; Category: ${escapeHtml(cat)}</p>
                    </div>
                    <div class="text-right">
                        <span class="text-xs text-slate-400 block">Days of Runway</span>
                        <strong class="text-2xl font-black ${isCritical ? 'text-rose-400' : 'text-amber-400'}">${doi} Days</strong>
                    </div>
                </div>

                <!-- Risk breakdown metrics -->
                <div class="grid grid-cols-3 gap-2 bg-slate-900/80 rounded-lg p-3 text-xs">
                    <div>
                        <span class="text-slate-400 block">Current Stock</span>
                        <strong class="text-white text-sm">${r.current_stock} units</strong>
                    </div>
                    <div>
                        <span class="text-slate-400 block">Daily Velocity</span>
                        <strong class="text-white text-sm">${r.avg_daily_sales}/day</strong>
                    </div>
                    <div>
                        <span class="text-slate-400 block">Lead Time</span>
                        <strong class="text-white text-sm">${r.lead_time_days} days</strong>
                    </div>
                </div>

                <div class="text-xs text-slate-300">
                    <p class="mb-1"><i class="fa-solid fa-truck text-indigo-400 mr-1.5"></i> Supplier: <strong class="text-white">${r.supplier_name}</strong></p>
                    <p><i class="fa-solid fa-triangle-exclamation text-rose-400 mr-1.5"></i> Projected Stockout: <strong class="text-rose-300">In ${r.days_of_inventory} days</strong> (Supplier takes ${r.lead_time_days} days to deliver).</p>
                </div>

                <div class="pt-3 border-t border-slate-700/60 flex items-center justify-between">
                    <span class="text-xs text-slate-400">Suggested PO: <strong class="text-emerald-400">${r.suggested_reorder_qty} units</strong> (~$${r.reorder_estimated_cost.toLocaleString()})</span>
                    <button onclick="askCopilotPrompt('Generate emergency restock plan for ${r.name} (${r.sku}) from supplier ${r.supplier_name}')" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-md transition-all flex items-center space-x-1.5">
                        <i class="fa-solid fa-file-invoice text-[10px]"></i>
                        <span>Generate PO</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// 8. Handle Copilot Chat Submission
async function handleChatSubmit(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('copilot-input');
    const query = input.value.trim();
    if (!query) return;

    input.value = '';
    appendUserMessage(query, 'copilot-messages-log');

    // Add thinking loader
    const loadingId = appendThinkingBubble('copilot-messages-log');

    try {
        const res = await fetch('/api/copilot/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await res.json();
        removeThinkingBubble(loadingId);
        const modeLabel = data.mode_label || (data.mode === 'gemini' ? 'Gemini AI Synthesis' : 'Grounded Deterministic Mode');
        appendCopilotMessage(data.answer, data.suggested_followups, 'copilot-messages-log', modeLabel);
        renderEvidenceAndRecommendations(data.evidence_metrics || data.evidence, data.recommendations || (data.recommendation ? [data.recommendation] : []));
    } catch (err) {
        removeThinkingBubble(loadingId);
        appendCopilotMessage("⚠️ An error occurred while communicating with the Copilot service. Please try again.", [], 'copilot-messages-log', 'System Error');
    }
}

// Handle Drawer Chat Submission
async function handleDrawerChatSubmit(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('drawer-input');
    const query = input.value.trim();
    if (!query) return;

    input.value = '';
    appendUserMessage(query, 'drawer-messages-log');
    const loadingId = appendThinkingBubble('drawer-messages-log');

    try {
        const res = await fetch('/api/copilot/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await res.json();
        removeThinkingBubble(loadingId);
        const modeLabel = data.mode_label || (data.mode === 'gemini' ? 'Gemini AI Synthesis' : 'Grounded Deterministic Mode');
        appendCopilotMessage(data.answer, data.suggested_followups, 'drawer-messages-log', modeLabel);
        renderEvidenceAndRecommendations(data.evidence_metrics || data.evidence, data.recommendations || (data.recommendation ? [data.recommendation] : []));
    } catch (err) {
        removeThinkingBubble(loadingId);
        appendCopilotMessage("⚠️ An error occurred while communicating with the Copilot service.", [], 'drawer-messages-log', 'System Error');
    }
}

// Quick Prompt Helper
function askCopilotPrompt(promptText) {
    switchTab('copilot');
    document.getElementById('copilot-input').value = promptText;
    handleChatSubmit(null);
}

// Chat UI DOM Helpers
function appendUserMessage(text, containerId) {
    const container = document.getElementById(containerId);
    const div = document.createElement('div');
    div.className = 'flex items-start justify-end space-x-2 animate-fade-in';
    div.innerHTML = `
        <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-2.5 max-w-lg text-xs sm:text-sm leading-relaxed shadow-sm">
            ${escapeHtml(text)}
        </div>
        <div class="w-7 h-7 rounded bg-slate-700 flex-shrink-0 flex items-center justify-center text-xs text-slate-300 mt-1">
            <i class="fa-solid fa-user"></i>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function appendThinkingBubble(containerId) {
    const container = document.getElementById(containerId);
    const id = 'thinking-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'flex items-start space-x-3 animate-fade-in';
    div.innerHTML = `
        <div class="w-7 h-7 rounded bg-indigo-600 flex-shrink-0 flex items-center justify-center text-xs text-white mt-1 animate-pulse">
            <i class="fa-solid fa-sparkles"></i>
        </div>
        <div class="bg-slate-800 border border-slate-700 rounded-2xl rounded-tl-none px-4 py-3 text-xs text-slate-400 flex items-center space-x-2">
            <i class="fa-solid fa-spinner fa-spin text-indigo-400"></i>
            <span>Analyzing deterministic retail facts...</span>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeThinkingBubble(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendCopilotMessage(markdownText, followups, containerId, modeLabel = 'Grounded Deterministic Mode') {
    const container = document.getElementById(containerId);
    const div = document.createElement('div');
    div.className = 'flex items-start space-x-3 animate-fade-in';
    
    // Parse basic markdown (bold, lists, code, headers)
    const formattedHtml = formatMarkdown(markdownText);

    let followupsHtml = '';
    if (followups && followups.length > 0) {
        followupsHtml = `
            <div class="mt-3 pt-2 border-t border-slate-700/60 flex flex-wrap gap-1.5">
                <span class="text-[10px] text-slate-400 w-full mb-0.5">Suggested Follow-ups:</span>
                ${followups.map(f => `
                    <button onclick="askCopilotPrompt('${escapeQuote(f)}')" class="text-[11px] bg-slate-800 hover:bg-slate-700 border border-slate-600/50 px-2 py-1 rounded text-slate-300 transition-all">
                        ${escapeHtml(f)}
                    </button>
                `).join('')}
            </div>
        `;
    }

    const isGenAi = modeLabel.toLowerCase().includes('gemini');
    const badgeColor = isGenAi ? 'text-indigo-400 border-indigo-500/30 bg-indigo-950/40' : 'text-emerald-400 border-emerald-500/30 bg-emerald-950/40';
    const badgeIcon = isGenAi ? 'fa-sparkles' : 'fa-shield-halved';

    div.innerHTML = `
        <div class="w-7 h-7 rounded bg-indigo-600 flex-shrink-0 flex items-center justify-center text-xs text-white mt-1">
            <i class="fa-solid fa-sparkles"></i>
        </div>
        <div class="bg-slate-800 border border-slate-700/80 rounded-2xl rounded-tl-none p-4 max-w-xl text-xs sm:text-sm text-slate-200 leading-relaxed shadow-md space-y-2">
            <div class="flex items-center justify-between pb-2 mb-1 border-b border-slate-700/60 text-[10px]">
                <span class="inline-flex items-center px-2 py-0.5 rounded border font-semibold ${badgeColor}">
                    <i class="fa-solid ${badgeIcon} mr-1.5"></i>
                    ${escapeHtml(modeLabel)}
                </span>
                <span class="text-slate-400 font-mono">SQLite Ground Truth</span>
            </div>
            ${formattedHtml}
            ${followupsHtml}
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// Render Evidence & Recommendations in Right Inspector
function renderEvidenceAndRecommendations(evidenceList, recommendationsList) {
    const evContainer = document.getElementById('copilot-evidence-list');
    const recContainer = document.getElementById('copilot-recommendations-list');

    if (evidenceList && evidenceList.length > 0) {
        evContainer.innerHTML = evidenceList.map(e => {
            let text = '';
            if (typeof e === 'object' && e !== null) {
                const prod = e.product || e.name || 'Item';
                const stock = e.stock !== undefined ? `Stock: ${e.stock}` : '';
                const runway = e.days_remaining !== undefined ? `Runway: ${e.days_remaining}d` : '';
                const risk = e.risk ? `Risk: ${e.risk}` : '';
                text = [prod, stock, runway, risk].filter(Boolean).join(' | ');
            } else {
                text = String(e);
            }
            return `
                <div class="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 flex items-start space-x-2">
                    <i class="fa-solid fa-check-circle text-emerald-400 mt-0.5 flex-shrink-0 text-xs"></i>
                    <span class="text-xs leading-tight">${escapeHtml(text)}</span>
                </div>
            `;
        }).join('');
    } else {
        evContainer.innerHTML = `
            <div class="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800 text-slate-400 italic text-xs">
                No specific inventory evidence cited for this query.
            </div>
        `;
    }

    if (recommendationsList && recommendationsList.length > 0) {
        recContainer.innerHTML = recommendationsList.map(r => `
            <div class="p-2.5 rounded-lg bg-indigo-950/20 border border-indigo-500/30 text-indigo-200 flex items-start space-x-2">
                <i class="fa-solid fa-arrow-right text-indigo-400 mt-0.5 flex-shrink-0 text-xs"></i>
                <span class="text-xs leading-tight">${escapeHtml(String(r))}</span>
            </div>
        `).join('');
    } else {
        recContainer.innerHTML = `
            <div class="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800 text-slate-400 italic text-xs">
                No active operational recommendations for this query.
            </div>
        `;
    }
}


function clearChatHistory() {
    const log = document.getElementById('copilot-messages-log');
    log.innerHTML = `
        <div class="flex items-start space-x-3">
            <div class="w-7 h-7 rounded bg-indigo-600 flex-shrink-0 flex items-center justify-center text-xs text-white mt-1">
                <i class="fa-solid fa-sparkles"></i>
            </div>
            <div class="bg-slate-700/50 border border-slate-600/50 rounded-2xl rounded-tl-none p-4 max-w-xl text-sm space-y-2">
                <p class="font-semibold text-indigo-300">Chat reset.</p>
                <p class="text-slate-300 text-xs">How can I assist you with your sales and inventory operations today?</p>
            </div>
        </div>
    `;
}

// Utility: Markdown Formatter
function formatMarkdown(md) {
    if (!md) return '';
    let html = md
        .replace(/^### (.*$)/gim, '<h5 class="text-sm font-bold text-indigo-300 mt-2 mb-1">$1</h5>')
        .replace(/^## (.*$)/gim, '<h4 class="text-base font-bold text-white mt-2 mb-1">$1</h4>')
        .replace(/^# (.*$)/gim, '<h3 class="text-lg font-bold text-white mt-2 mb-1">$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-bold">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em class="text-slate-300">$1</em>')
        .replace(/`([^`]+)`/g, '<code class="bg-slate-900 px-1.5 py-0.5 rounded text-indigo-300 font-mono text-[11px]">$1</code>')
        .replace(/^\> (.*$)/gim, '<blockquote class="border-l-2 border-indigo-500 pl-2 text-slate-400 text-xs my-1 italic">$1</blockquote>')
        .replace(/^\- (.*$)/gim, '<li class="ml-4 list-disc text-slate-200 text-xs my-0.5">$1</li>')
        .replace(/\n\n/g, '<br/>');
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeQuote(text) {
    return text.replace(/'/g, "\\'");
}

// 1-Click Purchase Orders CSV Export
function downloadPurchaseOrdersCsv() {
    window.location.href = '/api/export/purchase-orders';
}
