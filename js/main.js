const API = 'http://localhost:5000/api';
let currentPeriod = '90d';
let demandChart = null;

async function get(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function loadSummary() {
  const data = await get(`${API}/dashboard/summary`);
  document.getElementById('metric-units').textContent    = data.total_units_sold.toLocaleString();
  document.getElementById('metric-revenue').textContent  = '$' + (data.total_revenue / 1_000_000).toFixed(2) + 'M';
  document.getElementById('metric-products').textContent = data.num_products.toLocaleString();
  document.getElementById('metric-stores').textContent   = data.num_stores;
  document.getElementById('dash-desc').textContent =
    `${data.num_products.toLocaleString()} SKUs across ${data.num_stores} stores · Updated just now`;
}

async function loadChart(period) {
  const data = await get(`${API}/dashboard/trend?period=${period}`);
  const labels  = data.map(d => {
    const dt = new Date(d.date);
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  const actuals = data.map(d => d.actual);

  if (demandChart) demandChart.destroy();
  demandChart = new Chart(document.getElementById('demandChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Actual',
        data: actuals,
        borderColor: '#1d4ed8',
        borderWidth: 2,
        pointRadius: 2,
        pointBackgroundColor: '#1d4ed8',
        tension: 0.4,
        fill: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { font: { size: 11 }, maxTicksLimit: 10 }
        },
        y: {
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { font: { size: 11 }, callback: v => v.toLocaleString() }
        }
      }
    }
  });
}

async function loadTopProducts() {
  const data = await get(`${API}/dashboard/top-products?limit=10`);
  const tbody = document.getElementById('sku-tbody');
  if (!tbody) return;
  tbody.innerHTML = data.map(item => {
    const name = item.product_name || item.item_id;
    const sold = (item.total_sold || 0).toLocaleString();
    return `
      <tr>
        <td class="sku-code">${item.item_id}</td>
        <td class="prod-name">${name}</td>
        <td class="right">${sold}</td>
        <td class="right">—</td>
        <td class="right">—</td>
        <td class="right"><span class="badge-healthy">active</span></td>
      </tr>`;
  }).join('');
}

async function loadCategories() {
  const data = await get(`${API}/dashboard/by-category`);
  const el = document.getElementById('category-breakdown');
  if (!el) return;
  const total = data.reduce((s, d) => s + d.total, 0);
  el.innerHTML = data.map(d => {
    const pct = total ? ((d.total / total) * 100).toFixed(1) : 0;
    return `
      <div class="alert-item">
        <div class="alert-top">
          <div><div class="alert-name">${d.category}</div></div>
          <span class="badge-healthy">${pct}%</span>
        </div>
        <div class="prog-bar">
          <div class="prog-fill" style="width:${pct}%"></div>
        </div>
        <div class="prog-labels">
          <span>${d.total.toLocaleString()} units</span>
        </div>
      </div>`;
  }).join('');
}

function initPeriodFilters() {
  document.querySelectorAll('.tf').forEach(btn => {
    btn.addEventListener('click', async () => {
      document.querySelectorAll('.tf').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentPeriod = btn.textContent.trim();
      await loadChart(currentPeriod);
    });
  });
}

async function init() {
  try {
    await Promise.all([
      loadSummary(),
      loadChart(currentPeriod),
      loadTopProducts(),
      loadCategories(),
    ]);
  } catch (err) {
    console.error('Failed to load dashboard data:', err);
    document.getElementById('dash-desc').textContent = 'Failed to load data — is the Flask server running?';
  }
}

document.addEventListener('DOMContentLoaded', init);
initPeriodFilters();