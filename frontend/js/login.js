const loginBtn = document.getElementById('loginBtn');
const emailField = document.getElementById('email');
const passwordField = document.getElementById('password');
const errorDiv = document.getElementById('errorMsg');

loginBtn.addEventListener('click', async () => {
    const email = emailField.value.trim();
    const password = passwordField.value;
    if (!email || !password) {
        showError('Please fill in both fields.');
        return;
    }
    try {
        const res = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username: email, password })
        });
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem('access_token', data.access_token);
            window.location.href = '/dashboard';
        } else {
            const err = await res.json();
            showError(err.detail || 'Invalid credentials');
        }
    } catch (err) {
        showError('Network error');
    }
});

function showError(msg) {
    errorDiv.textContent = msg;
    errorDiv.classList.remove('d-none');
    setTimeout(() => errorDiv.classList.add('d-none'), 4000);
}

emailField.addEventListener('keypress', (e) => e.key === 'Enter' && loginBtn.click());
passwordField.addEventListener('keypress', (e) => e.key === 'Enter' && loginBtn.click());