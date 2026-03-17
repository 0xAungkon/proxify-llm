import { toggleTheme, initTheme } from './theme.js';
import { initLoginForm } from './auth.js';

window.toggleTheme = toggleTheme;

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initLoginForm();
    if (window.lucide) {
        window.lucide.createIcons();
    }
});
