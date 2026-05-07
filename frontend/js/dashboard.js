const API_BASE = '';
let historyChart = null;
let cpuGauge = null;
let memGauge = null;
let diskGauge = null;
let autoRefreshInterval = null;
let currentDays = 7;

function getToken() {
    return localStorage.getItem('access_token');
}

async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const res = await fetch(API_BASE + endpoint, {
        ...options,
        headers: { 'Authorization': `Bearer ${token}`, ...options.headers }
    });
    if (res.status === 401) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }
    return res;
}

async function loadUser() {
    const res = await apiFetch('/api/v1/auth/me');
    if (res.ok) {
        const user = await res.json();
        document.getElementById('userEmailNav').innerText = user.email;
        const adminLink = document.getElementById('adminNavLink');
        if (adminLink) {
            adminLink.style.display = user.is_superuser ? 'inline-block' : 'none';
        }
        // Show/hide stress test buttons for super admin only
        const stressCpu = document.getElementById('stressCpuBtn');
        const stressMem = document.getElementById('stressMemBtn');
        const stressDisk = document.getElementById('stressDiskBtn');
        if (stressCpu) stressCpu.style.display = user.is_superuser ? 'inline-block' : 'none';
        if (stressMem) stressMem.style.display = user.is_superuser ? 'inline-block' : 'none';
        if (stressDisk) stressDisk.style.display = user.is_superuser ? 'inline-block' : 'none';
    }
}

async function loadSystemInfo() {
    const res = await apiFetch('/api/v1/system/info');
    if (res.ok) {
        const info = await res.json();
        const sysHtml = `
            <div class="col-md-3"><strong>Hostname:</strong> ${info.hostname}</div>
            <div class="col-md-3"><strong>OS:</strong> ${info.system} ${info.release}</div>
            <div class="col-md-3"><strong>Python:</strong> ${info.python_version}</div>
            <div class="col-md-3"><strong>CPU Cores:</strong> ${info.cpu_cores}</div>
            <div class="col-md-3"><strong>Total Memory:</strong> ${info.memory_total_gb} GB</div>
            <div class="col-md-3"><strong>Disk Total:</strong> ${info.disk_total_gb} GB</div>
            <div class="col-md-3"><strong>Disk Used:</strong> ${info.disk_used_gb} GB</div>
            <div class="col-md-3"><strong>Disk Free:</strong> ${info.disk_free_gb} GB</div>
        `;
        document.getElementById('sysInfo').innerHTML = sysHtml;
        document.getElementById('diskDetails').innerHTML = `${info.disk_used_gb} GB / ${info.disk_total_gb} GB`;
        document.getElementById('memDetails').innerHTML = `${info.memory_used_gb} GB / ${info.memory_total_gb} GB`;
    }
}

async function loadReports() {
    let url = '/api/v1/reports/';
    if (currentDays) url += `?days=${currentDays}`;
    const res = await apiFetch(url);
    if (res.ok) {
        const data = await res.json();
        const reports = data.reports;
        const latest = reports[0] || null;
        if (latest) {
            // CPU gauge
            if (cpuGauge) cpuGauge.destroy();
            const cpuCtx = document.getElementById('cpuGauge').getContext('2d');
            cpuGauge = new Chart(cpuCtx, {
                type: 'doughnut',
                data: { datasets: [{ data: [latest.cpu_percent, 100 - latest.cpu_percent], backgroundColor: ['#ff6b6b', '#2c3e50'], borderWidth: 0 }] },
                options: { cutout: '70%', plugins: { tooltip: { callbacks: { label: () => `${latest.cpu_percent.toFixed(1)}%` } } } }
            });
            document.getElementById('cpuPercent').innerText = `${latest.cpu_percent.toFixed(1)}%`;

            // Memory gauge
            if (memGauge) memGauge.destroy();
            const memCtx = document.getElementById('memGauge').getContext('2d');
            memGauge = new Chart(memCtx, {
                type: 'doughnut',
                data: { datasets: [{ data: [latest.memory_percent, 100 - latest.memory_percent], backgroundColor: ['#4d9fff', '#2c3e50'], borderWidth: 0 }] },
                options: { cutout: '70%', plugins: { tooltip: { callbacks: { label: () => `${latest.memory_percent.toFixed(1)}%` } } } }
            });
            document.getElementById('memPercent').innerText = `${latest.memory_percent.toFixed(1)}%`;

            // Disk gauge
            if (diskGauge) diskGauge.destroy();
            const diskCtx = document.getElementById('diskGauge').getContext('2d');
            diskGauge = new Chart(diskCtx, {
                type: 'doughnut',
                data: { datasets: [{ data: [latest.disk_percent, 100 - latest.disk_percent], backgroundColor: ['#f39c12', '#2c3e50'], borderWidth: 0 }] },
                options: { cutout: '70%', plugins: { tooltip: { callbacks: { label: () => `${latest.disk_percent.toFixed(1)}%` } } } }
            });
            document.getElementById('diskPercent').innerText = `${latest.disk_percent.toFixed(1)}%`;
        } else {
            // No reports: show 0% gauges
            if (cpuGauge) cpuGauge.destroy();
            if (memGauge) memGauge.destroy();
            if (diskGauge) diskGauge.destroy();
            const cpuCtx = document.getElementById('cpuGauge').getContext('2d');
            const memCtx = document.getElementById('memGauge').getContext('2d');
            const diskCtx = document.getElementById('diskGauge').getContext('2d');
            cpuGauge = new Chart(cpuCtx, {
                type: 'doughnut',
                data: { datasets: [{ data: [0, 100], backgroundColor: ['#ff6b6b', '#2c3e50'], borderWidth: 0 }] },
                options: { cutout: '70%', plugins: { tooltip: { callbacks: { label: () => '0%' } } } }
            });
            memGauge = new Chart(memCtx, {
                type: 'doughnut',
                data: { datasets: [{ data: [0, 100], backgroundColor: ['#4d9fff', '#2c3e50'], borderWidth: 0 }] },
                options: { cutout: '70%', plugins: { tooltip: { callbacks: { label: () => '0%' } } } }
            });
            diskGauge = new Chart(diskCtx, {
                type: 'doughnut',
                data: { datasets: [{ data: [0, 100], backgroundColor: ['#f39c12', '#2c3e50'], borderWidth: 0 }] },
                options: { cutout: '70%', plugins: { tooltip: { callbacks: { label: () => '0%' } } } }
            });
            document.getElementById('cpuPercent').innerText = '0%';
            document.getElementById('memPercent').innerText = '0%';
            document.getElementById('diskPercent').innerText = '0%';
        }

        const tbody = document.getElementById('reportTable');
        if (!reports.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No reports yet. Click "Generate Report"</td></tr>';
            if (historyChart) historyChart.destroy();
            return;
        }

        tbody.innerHTML = reports.map(r => `
            <tr>
                <td>${new Date(r.created_at).toLocaleString()}</td>
                <td><span class="badge bg-info text-dark">${r.cpu_percent.toFixed(1)}%</span></td>
                <td><span class="badge bg-primary">${r.memory_percent.toFixed(1)}%</span></td>
                <td><span class="badge bg-warning text-dark">${r.disk_percent.toFixed(1)}%</span></td>
                <td><i class="bi bi-arrow-down-up"></i> ${((r.network?.bytes_recv || 0) / 1024).toFixed(1)} / ${((r.network?.bytes_sent || 0) / 1024).toFixed(1)}</td>
                <td><button class="btn btn-sm btn-outline-danger delete-report" data-id="${r.id}"><i class="bi bi-trash"></i></button></td>
            </tr>
        `).join('');

        const last10 = reports.slice(-10);
        const labels = last10.map(r => new Date(r.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}));
        const cpuData = last10.map(r => r.cpu_percent);
        const memData = last10.map(r => r.memory_percent);
        if (historyChart) historyChart.destroy();
        const ctx = document.getElementById('historyChart').getContext('2d');
        historyChart = new Chart(ctx, {
            type: 'bar',
            data: { labels, datasets: [
                { label: 'CPU %', data: cpuData, backgroundColor: '#ff6b6b' },
                { label: 'Memory %', data: memData, backgroundColor: '#4d9fff' }
            ] },
            options: { responsive: true, maintainAspectRatio: true, scales: { y: { beginAtZero: true, max: 100 } } }
        });

        document.querySelectorAll('.delete-report').forEach(btn => {
            btn.addEventListener('click', () => deleteReport(btn.dataset.id));
        });
    }
}

async function deleteReport(id) {
    if (!confirm('Delete this report?')) return;
    const res = await apiFetch(`/api/v1/reports/${id}`, { method: 'DELETE' });
    if (res.ok) loadReports();
    else alert('Delete failed');
}

async function generateReport() {
    const btn = document.getElementById('generateBtn');
    const msgDiv = document.getElementById('generateMsg');
    btn.disabled = true;
    msgDiv.innerHTML = '<div class="spinner-border spinner-border-sm text-light me-2" role="status"></div> Generating...';
    const res = await apiFetch('/api/v1/reports/', { method: 'POST' });
    if (res.ok) {
        msgDiv.innerHTML = '<div class="alert alert-success py-2">Report generated successfully!</div>';
        await loadReports();
        setTimeout(() => msgDiv.innerHTML = '', 3000);
    } else {
        const err = await res.text();
        msgDiv.innerHTML = `<div class="alert alert-danger py-2">Error: ${err}</div>`;
    }
    btn.disabled = false;
}

async function exportCSV() {
    let url = '/api/v1/reports/export?format=csv';
    if (currentDays) url += `&days=${currentDays}`;
    const res = await apiFetch(url);
    if (res.ok) {
        const blob = await res.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'reports.csv';
        link.click();
    }
}

function startAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    autoRefreshInterval = setInterval(() => {
        loadReports();
        loadSystemInfo();
    }, 10000);
}
function stopAutoRefresh() {
    if (autoRefreshInterval) { clearInterval(autoRefreshInterval); autoRefreshInterval = null; }
}

document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
});
document.getElementById('generateBtn').addEventListener('click', generateReport);
document.getElementById('exportBtn').addEventListener('click', exportCSV);
document.getElementById('autoRefreshCheck').addEventListener('change', (e) => {
    if (e.target.checked) startAutoRefresh();
    else stopAutoRefresh();
});
document.getElementById('dateRangeSelect').addEventListener('change', (e) => {
    currentDays = e.target.value || null;
    loadReports();
});

async function stress(type) {
    const msgDiv = document.getElementById('stressMsg');
    msgDiv.innerHTML = `<i class="bi bi-hourglass-split"></i> Running ${type} stress test...`;
    const res = await apiFetch(`/api/v1/system/stress/${type}`, { method: 'POST' });
    if (res.ok) {
        const data = await res.json();
        msgDiv.innerHTML = `<i class="bi bi-check-circle"></i> ${data.status}`;
        await generateReport();
        setTimeout(() => msgDiv.innerHTML = '', 5000);
    } else if (res.status === 403) {
        msgDiv.innerHTML = '<i class="bi bi-shield-lock"></i> Only super admin can run stress tests.';
        setTimeout(() => msgDiv.innerHTML = '', 3000);
    } else {
        msgDiv.innerHTML = `<i class="bi bi-x-circle"></i> Stress test failed`;
    }
}

document.getElementById('stressCpuBtn').addEventListener('click', () => stress('cpu'));
document.getElementById('stressMemBtn').addEventListener('click', () => stress('memory'));
document.getElementById('stressDiskBtn').addEventListener('click', () => stress('disk'));

if (!getToken()) {
    window.location.href = '/login';
} else {
    loadUser();
    loadSystemInfo();
    loadReports();
    startAutoRefresh();
}