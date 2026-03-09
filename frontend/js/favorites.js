/**
 * favorites.js — Gestión de propiedades favoritas
 */

async function loadFavoritesFromAPI() {
    try {
        const res = await fetch(`/api/favorites/${SESSION_ID}`);
        if (!res.ok) throw new Error('API error');
        const data = await res.json();
        favorites     = data.ids       || [];
        favoriteProps = data.favorites || [];
    } catch {
        favorites     = JSON.parse(localStorage.getItem('alquisearch_favorites') || '[]');
        favoriteProps = [];
    }
    updateFavCount();
}

function saveFavorites() {
    localStorage.setItem('alquisearch_favorites', JSON.stringify(favorites));
    updateFavCount();
}

function updateFavCount() {
    elements.favCount.textContent = favorites.length;
    elements.favCount.classList.toggle('hidden', favorites.length === 0);
}

async function toggleFavorite(propId) {
    const propObj = allProperties.find(p => p.id === propId)
                 || favoriteProps.find(p => p.id === propId);
    if (!propObj) return;

    try {
        const res = await fetch(`/api/favorites/${SESSION_ID}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(propObj),
        });
        if (!res.ok) throw new Error('API error');
        const data = await res.json();
        if (data.action === 'added') {
            if (!favorites.includes(propId)) favorites.push(propId);
            if (!favoriteProps.find(p => p.id === propId)) favoriteProps.push(propObj);
            showToast('❤️ Añadido a favoritos');
        } else {
            favorites     = favorites.filter(id => id !== propId);
            favoriteProps = favoriteProps.filter(p => p.id !== propId);
            showToast('Eliminado de favoritos');
        }
    } catch {
        const idx = favorites.indexOf(propId);
        if (idx === -1) {
            favorites.push(propId);
            if (!favoriteProps.find(p => p.id === propId)) favoriteProps.push(propObj);
        } else {
            favorites.splice(idx, 1);
            favoriteProps = favoriteProps.filter(p => p.id !== propId);
        }
    }
    saveFavorites();

    document.querySelectorAll(`.btn-fav[data-prop-id="${propId}"]`).forEach(btn => {
        btn.classList.toggle('active', favorites.includes(propId));
    });
}

function openFavoritesPanel() {
    const favProps = favoriteProps.length > 0
        ? favoriteProps
        : allProperties.filter(p => favorites.includes(p.id));

    if (favProps.length > 0) {
        elements.favoritesGrid.innerHTML = favProps.map((prop, i) => createPropertyCard(prop, i)).join('');
        elements.favoritesEmpty.classList.add('hidden');
        elements.favoritesGrid.classList.remove('hidden');

        elements.favoritesGrid.querySelectorAll('.btn-fav').forEach(btn => {
            btn.addEventListener('click', (e) => { e.stopPropagation(); toggleFavorite(btn.dataset.propId); openFavoritesPanel(); });
        });
        elements.favoritesGrid.querySelectorAll('.btn-view').forEach(btn => {
            btn.addEventListener('click', (e) => { e.stopPropagation(); window.open(btn.dataset.url, '_blank'); });
        });
        elements.favoritesGrid.querySelectorAll('.property-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('.btn-view,.btn-fav,.btn-compare-card,.btn-track-card,.card-actions')) return;
                const prop = allProperties.find(p => p.id === card.dataset.propId);
                if (prop) openPropertyModal(prop);
            });
        });
    } else {
        elements.favoritesGrid.innerHTML = '';
        elements.favoritesGrid.classList.add('hidden');
        elements.favoritesEmpty.classList.remove('hidden');
    }

    elements.favoritesPanel.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeFavoritesPanel() {
    elements.favoritesPanel.classList.add('hidden');
    document.body.style.overflow = '';
}

elements.favoritesNavLink.addEventListener('click', (e) => { e.preventDefault(); openFavoritesPanel(); });
elements.closeFavorites.addEventListener('click', closeFavoritesPanel);
document.querySelector('.favorites-overlay').addEventListener('click', closeFavoritesPanel);
