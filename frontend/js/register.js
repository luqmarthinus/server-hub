const registerBtn = document.getElementById('registerBtn');
const emailField = document.getElementById('email');
const fullnameField = document.getElementById('fullname');
const passwordField = document.getElementById('password');
const errorDiv = document.getElementById('errorMsg');
const successDiv = document.getElementById('successMsg');

registerBtn.addEventListener('click', async () => {
    const email = emailField.value.trim();
    const fullname = fullnameField.value.trim();
    const password = passwordField.value;

    if (!email || !password) {
        showError('Email and password are required.');
        return;
    }

    try {
        const res = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                full_name: fullname,
                password: password
            })
        });

        if (res.ok) {
            showSuccess('Registration successful! Redirecting to login...');
            setTimeout(() => window.location.href = '/login', 2000);
        } else {
            const err = await res.json();
            showError(err.detail || 'Registration failed');
        }
    } catch (err) {
        showError('Network error. Please try again.');
    }
});

function showError(msg) {
    errorDiv.textContent = msg;
    errorDiv.classList.remove('d-none');
    successDiv.classList.add('d-none');
    setTimeout(() => errorDiv.classList.add('d-none'), 5000);
}

function showSuccess(msg) {
    successDiv.textContent = msg;
    successDiv.classList.remove('d-none');
    errorDiv.classList.add('d-none');
}

// Allow Enter key submission
emailField.addEventListener('keypress', (e) => e.key === 'Enter' && registerBtn.click());
fullnameField.addEventListener('keypress', (e) => e.key === 'Enter' && registerBtn.click());
passwordField.addEventListener('keypress', (e) => e.key === 'Enter' && registerBtn.click());