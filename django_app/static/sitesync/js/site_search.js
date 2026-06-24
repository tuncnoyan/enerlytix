document.addEventListener('DOMContentLoaded', () => {
    "use strict";
    
    const searchInput = document.getElementById('site-search');
    if (!searchInput) {
        return;
    }

    const siteItems = Array.from(document.querySelectorAll('.site-item'));

    const filterSites = () => {
        const query = searchInput.value.trim().toLowerCase();
        siteItems.forEach((item) => {
            const text = item.textContent.toLowerCase();
            const visible = !query || text.includes(query);
            item.style.display = visible ? '' : 'none';
        });
    };

    searchInput.addEventListener('input', filterSites);
    filterSites();
});

// Make filterSites available globally for the Clear button
function filterSites() {
    "use strict";
    const searchInput = document.getElementById('site-search');
    if (searchInput) {
        const event = new Event('input', { bubbles: true });
        searchInput.dispatchEvent(event);
    }
}

