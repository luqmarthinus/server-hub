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
    return res;
}

async function loadUser() {
    const res = await apiFetch('/api/v1/auth/me');
    if (res.ok) {
        const user = await res.json();
        const html = `
            <p><strong><i class="bi bi-envelope-fill me-1"></i> Email:</strong> ${escapeHtml(user.email)}</p>
            <p><strong><i class="bi bi-person-fill me-1"></i> Name:</strong> ${escapeHtml(user.full_name || '—')}</p>
            <p><strong><i class="bi bi-key-fill me-1"></i> User ID:</strong> ${user.id}</p>
            <p><strong><i class="bi bi-calendar me-1"></i> Joined:</strong> ${new Date(user.created_at).toLocaleString()}</p>
        `;
        document.getElementById('userInfo').innerHTML = html;
        document.getElementById('userEmailNav').innerText = user.email;
    }
}

async function changePassword(currentPassword, newPassword) {
    const res = await apiFetch('/api/v1/auth/change-password', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
    });
    if (res.ok) {
        return { success: true, message: 'Password updated successfully.' };
    } else {
        const err = await res.json();
        return { success: false, message: err.detail || 'Failed to update password.' };
    }
}

async function deleteAccount() {
    const res = await apiFetch('/api/v1/auth/delete-account', { method: 'DELETE' });
    if (res.ok) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
    } else {
        const err = await res.json();
        throw new Error(err.detail || 'Delete failed');
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

// Change password form
const changeForm = document.getElementById('changePasswordForm');
const passwordMsg = document.getElementById('passwordMsg');
changeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const currentPass = document.getElementById('currentPassword').value;
    const newPass = document.getElementById('newPassword').value;
    const confirmPass = document.getElementById('confirmPassword').value;
    if (newPass !== confirmPass) {
        passwordMsg.innerHTML = '<div class="alert alert-danger">New passwords do not match.</div>';
        return;
    }
    passwordMsg.innerHTML = '<div class="spinner-border spinner-border-sm text-light me-2" role="status"></div> Updating...';
    const result = await changePassword(currentPass, newPass);
    if (result.success) {
        passwordMsg.innerHTML = '<div class="alert alert-success">Password updated successfully.</div>';
        changeForm.reset();
    } else {
        passwordMsg.innerHTML = `<div class="alert alert-danger">${result.message}</div>`;
    }
});

// Delete account button
const deleteBtn = document.getElementById('deleteAccountBtn');
const deleteMsg = document.getElementById('deleteMsg');
deleteBtn.addEventListener('click', async () => {
    if (!confirm('Are you absolutely sure? This will delete your account and all reports permanently.')) return;
    deleteMsg.innerHTML = '<div class="spinner-border spinner-border-sm text-light me-2" role="status"></div> Deleting...';
    try {
        await deleteAccount();
        // Redirect will happen in deleteAccount function
    } catch (err) {
        deleteMsg.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
    }
});

// Logout
document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
});

if (!getToken()) {
    window.location.href = '/login';
} else {
    loadUser();
}