const API_BASE = '';
let cpuChart = null;

function getToken() {
    return localStorage.getItem('access_token');
}

async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };
    const res = await fetch(API_BASE + endpoint, { ...options, headers });
    if (res.status === 401) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }
    return res;
}

async function loadUser() {
    const res = await apiFetch('/api/auth/me');
    if (res.ok) {
        const user = await res.json();
        const html = `
            <p><strong><i class="bi bi-envelope-fill me-1"></i> Email:</strong> ${escapeHtml(user.email)}</p>
            <p><strong><i class="bi bi-person-fill me-1"></i> Name:</strong> ${escapeHtml(user.full_name || '—')}</p>
            <p><strong><i class="bi bi-key-fill me-1"></i> User ID:</strong> ${user.id}</p>
        `;
        document.getElementById('userInfo').innerHTML = html;
        document.getElementById('userEmailNav').innerText = user.email;
    }
}

async function loadReports() {
    const res = await apiFetch('/api/reports/');
    if (res.ok) {
        const data = await res.json();
        const reports = data.reports;
        const tbody = document.getElementById('reportTable');
        if (!reports.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No reports yet. Click "New Report"</td></tr>';
            if (cpuChart) cpuChart.destroy();
            return;
        }
        // Build table rows
        tbody.innerHTML = reports.map(r => `
            <tr>
                <td>${new Date(r.created_at).toLocaleString()}</td>
                <td><span class="badge bg-info text-dark">${r.cpu_percent.toFixed(1)}%</span></td>
                <td><span class="badge bg-primary">${r.memory_percent.toFixed(1)}%</span></td>
                <td><span class="badge bg-warning text-dark">${r.disk_percent.toFixed(1)}%</span></td>
                <td><i class="bi bi-arrow-down-up"></i> ${((r.network?.bytes_recv || 0) / 1024).toFixed(1)} / ${((r.network?.bytes_sent || 0) / 1024).toFixed(1)}</td>
            </tr>
        `).join('');

        // Update chart with last 10 values
        const last10 = reports.slice(-10);
        const labels = last10.map(r => new Date(r.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}));
        const cpuData = last10.map(r => r.cpu_percent);
        const memData = last10.map(r => r.memory_percent);
        if (cpuChart) cpuChart.destroy();
        const ctx = document.getElementById('cpuChart').getContext('2d');
        cpuChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    { label: 'CPU %', data: cpuData, borderColor: '#ff6b6b', backgroundColor: 'rgba(255,107,107,0.1)', tension: 0.3, fill: true, pointBackgroundColor: '#ff6b6b' },
                    { label: 'Memory %', data: memData, borderColor: '#4d9fff', backgroundColor: 'rgba(77,159,255,0.1)', tension: 0.3, fill: true, pointBackgroundColor: '#4d9fff' }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { labels: { color: '#f0f0f0' } },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#ccc' } },
                    x: { grid: { display: false }, ticks: { color: '#ccc' } }
                }
            }
        });
    }
}

async function generateReport() {
    const btn = document.getElementById('generateBtn');
    const msgDiv = document.getElementById('generateMsg');
    btn.disabled = true;
    msgDiv.innerHTML = '<div class="spinner-border spinner-border-sm text-light me-2" role="status"></div> Generating...';
    const res = await apiFetch('/api/reports/', { method: 'POST' });
    if (res.ok) {
        msgDiv.innerHTML = '<div class="alert alert-success py-2">✔ Report generated successfully!</div>';
        await loadReports();
        setTimeout(() => { if (msgDiv.firstChild) msgDiv.innerHTML = ''; }, 3000);
    } else {
        const err = await res.text();
        msgDiv.innerHTML = `<div class="alert alert-danger py-2">❌ Error: ${err}</div>`;
    }
    btn.disabled = false;
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

// Event listeners
document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
});
document.getElementById('generateBtn').addEventListener('click', generateReport);

// Initial load
if (!getToken()) {
    window.location.href = '/login';
} else {
    loadUser();
    loadReports();
    // Auto-refresh every 30 seconds
    setInterval(loadReports, 30000);
}