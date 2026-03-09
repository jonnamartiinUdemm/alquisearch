/**
 * modal.js — Modal de detalle de propiedad
 */

function openPropertyModal(prop) {
    const imageUrl = prop.images?.length
        ? prop.images[0]
        : 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop';

    const isFav = favorites.includes(prop.id);

    const features = [];
    features.push({ icon: 'fa-bed', text: `${prop.bedrooms} habitaciones` });
    features.push({ icon: 'fa-bath', text: `${prop.bathrooms} baños` });
    if (prop.area_m2 > 0) features.push({ icon: 'fa-ruler-combined', text: `${prop.area_m2} m²` });
    if (prop.floor)            features.push({ icon: 'fa-building', text: `Planta ${prop.floor}` });
    if (prop.has_elevator)     features.push({ icon: 'fa-arrows-alt-v', text: 'Con ascensor' });
    if (prop.pets_allowed)     features.push({ icon: 'fa-paw', text: 'Mascotas OK' });
    if (prop.has_terrace)      features.push({ icon: 'fa-sun', text: 'Terraza' });
    if (prop.has_balcony)      features.push({ icon: 'fa-door-open', text: 'Balcón' });
    if (prop.has_air_conditioning) features.push({ icon: 'fa-snowflake', text: 'Aire acondicionado' });
    if (prop.has_heating)      features.push({ icon: 'fa-fire', text: 'Calefacción' });
    if (prop.has_parking)      features.push({ icon: 'fa-car', text: 'Parking' });
    if (prop.has_pool)         features.push({ icon: 'fa-swimming-pool', text: 'Piscina' });
    if (prop.furnished)        features.push({ icon: 'fa-couch', text: 'Amueblado' });
    if (prop.has_sea_view)     features.push({ icon: 'fa-water', text: 'Vista al mar' });
    if (prop.is_long_stay)     features.push({ icon: 'fa-calendar-check', text: 'Larga estancia' });
    if (prop.energy_rating)    features.push({ icon: 'fa-leaf', text: `Energía: ${prop.energy_rating}` });

    const tags = [];
    if (prop.public_transport_nearby) tags.push('<span class="tag positive"><i class="fas fa-bus"></i> Transporte público cercano</span>');
    if (prop.services_nearby)         tags.push('<span class="tag positive"><i class="fas fa-store"></i> Servicios cercanos</span>');
    if (prop.allows_empadronamiento)  tags.push('<span class="tag positive"><i class="fas fa-id-card"></i> Permite empadronamiento</span>');

    elements.modalBody.innerHTML = `
        <img class="modal-image" src="${imageUrl}" alt="${escapeHtml(prop.title)}"
             onerror="this.src='https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop'">
        <div class="modal-body-content">
            <div class="modal-price">${formatPrice(prop.price)} <small style="font-size:1rem;color:var(--gray-400);">€/mes</small></div>
            <h2 class="modal-title">${escapeHtml(prop.title)}</h2>
            <div class="modal-location">
                <i class="fas fa-map-marker-alt"></i>
                ${escapeHtml([prop.address, prop.neighborhood, prop.city].filter(Boolean).join(', '))}
            </div>
            <div class="modal-features-grid">
                ${features.map(f => `<div class="modal-feature"><i class="fas ${f.icon}"></i> ${f.text}</div>`).join('')}
            </div>
            ${prop.description ? `<div class="modal-description">${escapeHtml(prop.description)}</div>` : ''}
            ${tags.length ? `<div class="modal-tags">${tags.join('')}</div>` : ''}
            <div style="margin-bottom:16px;font-size:.85rem;color:var(--gray-500);">
                <i class="fas fa-calendar-alt"></i> Disponibilidad: ${prop.availability || 'No especificada'}
                &nbsp;|&nbsp;
                <i class="fas fa-star"></i> Puntuación: ${Math.round(prop.score)} / 100
                ${prop.scam_score > 0 ? `&nbsp;|&nbsp;<span style="color:var(--warning);"><i class="fas fa-exclamation-triangle"></i> Riesgo: ${Math.round(prop.scam_score * 100)}%</span>` : ''}
            </div>
            <div class="modal-actions">
                <a href="${escapeHtml(prop.url)}" target="_blank" rel="noopener noreferrer" class="btn-primary">
                    <i class="fas fa-external-link-alt"></i> Ver en ${escapeHtml(prop.platform)}
                </a>
                <button class="btn-secondary modal-fav-btn ${isFav ? 'active' : ''}" data-prop-id="${escapeHtml(prop.id)}">
                    <i class="fas fa-heart"></i> ${isFav ? 'En favoritos' : 'Favorito'}
                </button>
                <button class="btn-secondary" onclick="closePropertyModal()">
                    <i class="fas fa-times"></i> Cerrar
                </button>
            </div>
        </div>`;

    const modalFavBtn = elements.modalBody.querySelector('.modal-fav-btn');
    if (modalFavBtn) {
        modalFavBtn.addEventListener('click', () => {
            toggleFavorite(prop.id);
            const nowFav = favorites.includes(prop.id);
            modalFavBtn.classList.toggle('active', nowFav);
            modalFavBtn.innerHTML = `<i class="fas fa-heart"></i> ${nowFav ? 'En favoritos' : 'Favorito'}`;
        });
    }

    elements.propertyModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closePropertyModal() {
    elements.propertyModal.classList.add('hidden');
    document.body.style.overflow = '';
}

elements.modalClose.addEventListener('click', closePropertyModal);
document.querySelector('#propertyModal .modal-overlay').addEventListener('click', closePropertyModal);

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closePropertyModal();
        closeFavoritesPanel();
        closeCompareModal();
        // tracking y auth cierran su propio Escape en sus módulos
    }
});
