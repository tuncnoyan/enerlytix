document.addEventListener('DOMContentLoaded', () => {
    "use strict";

    const form = document.getElementById('settings-form');
    if (!form) {
        return;
    }

    form.addEventListener('submit', () => {
        const button = form.querySelector('button[type="submit"]');
        if (button) {
            button.disabled = true;
            button.textContent = 'Saving...';
        }
    });
});
