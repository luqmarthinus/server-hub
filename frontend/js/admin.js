const API_BASE = '';

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
    if (res.status === 403) {
        alert('Admin access required');
        window.location.href = '/dashboard';
        throw new Error('Forbidden');
    }
    return res;
}

async function loadUsers() {
    const res = await apiFetch('/api/v1/admin/users');
    if (res.ok) {
        const data = await res.json();
        const tbody = document.getElementById('userTableBody');
        if (!data.users.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No users found<\/td></tr>';
            return;
        }
        tbody.innerHTML = data.users.map(u => `
            <tr>
                <td>${u.id}</td>
                <td>${escapeHtml(u.email)}</td>
                <td>${escapeHtml(u.full_name || '—')}</td>
                <td>${u.report_count || 0}</td>
                <td>${u.is_superuser ? '<span class="badge bg-success">Yes</span>' : '<span class="badge bg-secondary">No</span>'}</td>
                <td>${u.is_active ? '<span class="badge bg-success">Active</span>' : '<span class="badge bg-danger">Inactive</span>'}</td>
                <td>${new Date(u.created_at).toLocaleDateString()}</td>
                <td>
                    ${!u.is_superuser ? `<button class="btn btn-sm btn-warning toggle-role" data-id="${u.id}" data-email="${escapeHtml(u.email)}">Make Admin</button>` : `<button class="btn btn-sm btn-secondary toggle-role" data-id="${u.id}" data-email="${escapeHtml(u.email)}">Remove Admin</button>`}
                    <button class="btn btn-sm btn-danger delete-user" data-id="${u.id}" data-email="${escapeHtml(u.email)}">Delete</button>
                </td>
            </tr>
        `).join('');

        document.querySelectorAll('.toggle-role').forEach(btn => {
            btn.addEventListener('click', () => toggleRole(btn.dataset.id, btn.dataset.email));
        });
        document.querySelectorAll('.delete-user').forEach(btn => {
            btn.addEventListener('click', () => deleteUser(btn.dataset.id, btn.dataset.email));
        });
    }
}

async function toggleRole(userId, userEmail) {
    if (!confirm(`Toggle admin role for ${userEmail}?`)) return;
    const res = await apiFetch(`/api/v1/admin/users/${userId}/role`, { method: 'PUT' });
    if (res.ok) {
        await loadUsers();
    } else {
        const err = await res.json();
        alert(`Failed: ${err.detail}`);
    }
}

async function deleteUser(userId, userEmail) {
    if (!confirm(`Delete user ${userEmail} and all their reports? This cannot be undone.`)) return;
    const res = await apiFetch(`/api/v1/admin/users/${userId}`, { method: 'DELETE' });
    if (res.ok) {
        await loadUsers();
    } else {
        const err = await res.json();
        alert(`Failed: ${err.detail}`);
    }
}

async function createUser(email, fullName, password) {
    const res = await apiFetch('/api/v1/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, full_name: fullName, password })
    });
    if (res.ok) {
        return { success: true, data: await res.json() };
    } else {
        const err = await res.json();
        return { success: false, message: err.detail || 'Failed to create user' };
    }
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

async function loadUserEmail() {
    const res = await apiFetch('/api/v1/auth/me');
    if (res.ok) {
        const user = await res.json();
        document.getElementById('userEmailNav').innerText = user.email;
    }
}

// Add User Modal Logic
document.getElementById('addUserBtn').addEventListener('click', () => {
    document.getElementById('addUserForm').reset();
    document.getElementById('addUserMsg').innerHTML = '';
    const modal = new bootstrap.Modal(document.getElementById('addUserModal'));
    modal.show();
});

document.getElementById('confirmAddUserBtn').addEventListener('click', async () => {
    const email = document.getElementById('userEmail').value.trim();
    const fullName = document.getElementById('userFullname').value.trim();
    const password = document.getElementById('userPassword').value;
    const msgDiv = document.getElementById('addUserMsg');
    if (!email || !password) {
        msgDiv.innerHTML = '<div class="alert alert-danger">Email and password are required.</div>';
        return;
    }
    msgDiv.innerHTML = '<div class="spinner-border spinner-border-sm text-light" role="status"></div> Creating...';
    const result = await createUser(email, fullName, password);
    if (result.success) {
        msgDiv.innerHTML = '<div class="alert alert-success">User created successfully!</div>';
        setTimeout(() => {
            const modalEl = document.getElementById('addUserModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            modal.hide();
            loadUsers(); // refresh list
        }, 1500);
    } else {
        msgDiv.innerHTML = `<div class="alert alert-danger">${result.message}</div>`;
    }
});

document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
});

if (!getToken()) {
    window.location.href = '/login';
} else {
    loadUserEmail();
    loadUsers();
}