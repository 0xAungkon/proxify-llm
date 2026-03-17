export function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
    localStorage.setItem('theme', newTheme);
}

export function applyTheme(theme) {
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');

    if (theme === 'light') {
        html.setAttribute('data-theme', 'light');
        html.classList.add('light-mode');
        html.classList.remove('dark-mode');
        if (icon) icon.setAttribute('data-lucide', 'sun');
    } else {
        html.setAttribute('data-theme', 'dark');
        html.classList.add('dark-mode');
        html.classList.remove('light-mode');
        if (icon) icon.setAttribute('data-lucide', 'moon');
    }

    if (window.lucide) {
        window.lucide.createIcons();
    }
}

export function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
}
