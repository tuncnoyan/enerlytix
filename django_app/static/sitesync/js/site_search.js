document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('site-search');
    if (!searchInput) {
        return;
    }

    const cards = Array.from(document.querySelectorAll('.site-card'));

    const filterSites = () => {
        const query = searchInput.value.trim().toLowerCase();
        cards.forEach((card) => {
            const text = card.textContent.toLowerCase();
            const visible = !query || text.includes(query);
            card.style.display = visible ? '' : 'none';
        });
    };

    searchInput.addEventListener('input', filterSites);
    filterSites();
});
