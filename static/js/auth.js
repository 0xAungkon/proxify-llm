export async function handleLogout() {
    window.location.href = '/app/logout';
}

export function initLoginForm() {
    const form = document.getElementById('login-form');
    if (!form) return;

    const message = document.getElementById('login-message');
    const renderMessage = (text, isError = false) => {
        message.textContent = text;
        message.classList.remove('hidden', 'border-[#2e7d32]', 'bg-[#1b2b1b]', 'text-[#a5d6a7]', 'border-[#8b2e2e]', 'bg-[#2b1b1b]', 'text-[#ffb4b4]');

        if (isError) {
            message.classList.add('border-[#8b2e2e]', 'bg-[#2b1b1b]', 'text-[#ffb4b4]');
            return;
        }

        message.classList.add('border-[#2e7d32]', 'bg-[#1b2b1b]', 'text-[#a5d6a7]');
    };

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.textContent = 'Signing In...';

        const payload = {
            username: document.getElementById('username').value.trim(),
            password: document.getElementById('password').value,
        };

        try {
            const response = await fetch('/common/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (!response.ok) {
                renderMessage(data.detail || 'Login failed.', true);
                return;
            }

            renderMessage(data.message || 'Login successful. Redirecting...');
            window.location.href = '/app';
        } catch (error) {
            renderMessage('Unable to complete login request.', true);
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Sign In';
        }
    });
}
