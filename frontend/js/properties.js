/**
 * properties.js — Renderizado de tarjetas de propiedad y ordenación
 */

function renderProperties(properties) {
    elements.resultsGrid.innerHTML = properties.map((prop, i) => createPropertyCard(prop, i)).join('');

    elements.resultsGrid.querySelectorAll('.property-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.closest('.btn-view,.btn-fav,.btn-compare-card,.btn-track-card,.card-actions')) return;
            const prop = allProperties.find(p => p.id === card.dataset.propId)
                      || currentProperties.find(p => p.id === card.dataset.propId);
            if (prop) openPropertyModal(prop);
        });
    });

    elements.resultsGrid.querySelectorAll('.btn-view, .btn-view-demo').forEach(btn => {
        btn.addEventListener('click', (e) => { e.stopPropagation(); window.open(btn.dataset.url, '_blank'); });
    });

    elements.resultsGrid.querySelectorAll('.btn-fav').forEach(btn => {
        btn.addEventListener('click', (e) => { e.stopPropagation(); toggleFavorite(btn.dataset.propId); });
    });

    elements.resultsGrid.querySelectorAll('.btn-compare-card').forEach(btn => {
        btn.addEventListener('click', (e) => { e.stopPropagation(); toggleCompare(btn.dataset.propId); });
    });

    elements.resultsGrid.querySelectorAll('.btn-track-card').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const propId = btn.dataset.propId;
            const prop = allProperties.find(p => p.id === propId) || currentProperties.find(p => p.id === propId);
            if (trackedIds.has(propId)) openTrackingPanel();
            else if (prop) showStagePicker(prop, btn);
        });
    });
}

function createPropertyCard(prop, index) {
    const imageUrl = prop.images?.length
        ? prop.images[0]
        : 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop';

    const isFav     = favorites.includes(prop.id);
    const isCompare = compareSet.has(prop.id);
    const isTracked = trackedIds.has(prop.id);

    const badges = [`<span class="badge badge-platform">${escapeHtml(prop.platform)}</span>`];
    if (prop.is_demo) badges.push('<span class="badge badge-demo" title="Propiedad de ejemplo — el enlace abre una búsqueda similar en la plataforma"><i class="fas fa-flask"></i> Demo</span>');
    const petsOn = elements.petsAllowed?.checked;
    if (prop.pets_allowed === true)  badges.push('<span class="badge badge-pets"><i class="fas fa-paw"></i> Mascotas ✓</span>');
    else if ((prop.pets_allowed == null) && petsOn) badges.push('<span class="badge badge-pets-unknown" title="Sin confirmar"><i class="fas fa-paw"></i> Sin confirmar</span>');
    if (prop.has_terrace)  badges.push('<span class="badge badge-terrace"><i class="fas fa-sun"></i> Terraza</span>');
    if (prop.has_elevator) badges.push('<span class="badge badge-elevator"><i class="fas fa-arrows-alt-v"></i> Ascensor</span>');
    if (prop.has_sea_view) badges.push('<span class="badge badge-seaview"><i class="fas fa-water"></i> Vista al mar</span>');
    if (prop.is_long_stay) badges.push('<span class="badge badge-longstay"><i class="fas fa-calendar-check"></i> Larga estancia</span>');

    const MAX_BADGES = 3;
    let visibleBadges = badges.slice(0, MAX_BADGES);
    const hidden = badges.length - MAX_BADGES;
    if (hidden > 0) visibleBadges.push(`<span class="badge badge-more" title="${badges.slice(MAX_BADGES).map(b => b.replace(/<[^>]+>/g,'')).join(', ')}">+${hidden}</span>`);

    const tags = [];
    if (prop.has_balcony)          tags.push('<span class="tag positive">Balcón</span>');
    if (prop.has_air_conditioning) tags.push('<span class="tag positive">A/C</span>');
    if (prop.has_heating)          tags.push('<span class="tag positive">Calefacción</span>');
    if (prop.has_parking)          tags.push('<span class="tag positive">Parking</span>');
    if (prop.has_pool)             tags.push('<span class="tag positive">Piscina</span>');
    if (prop.furnished)            tags.push('<span class="tag positive">Amueblado</span>');
    if (prop.public_transport_nearby) tags.push('<span class="tag positive">Transporte</span>');
    if (prop.services_nearby)         tags.push('<span class="tag positive">Servicios</span>');
    if (prop.allows_empadronamiento)  tags.push('<span class="tag positive">Empadronamiento</span>');

    const scoreLabel = prop.score >= 80 ? '⭐ Excelente' : prop.score >= 60 ? '✓ Bueno' : '~ Normal';
    const scoreClass = prop.score >= 80 ? 'score-excellent' : prop.score >= 60 ? 'score-good' : 'score-normal';

    return `
    <div class="property-card" data-prop-id="${escapeHtml(prop.id)}">
        <div class="property-card-image">
            <img src="${imageUrl}" alt="${escapeHtml(prop.title)}" loading="lazy"
                 onerror="this.src='https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop'">
            <div class="property-card-badges">${visibleBadges.join('')}</div>
            <div class="property-card-score ${scoreClass}">${scoreLabel} <strong>${Math.round(prop.score)}</strong></div>
            <div class="card-actions">
                <button class="btn-fav ${isFav ? 'active' : ''}" data-prop-id="${escapeHtml(prop.id)}" title="${isFav ? 'Quitar de favoritos' : 'Añadir a favoritos'}">
                    <i class="fas fa-heart"></i>
                </button>
                <button class="btn-compare-card ${isCompare ? 'active' : ''}" data-prop-id="${escapeHtml(prop.id)}" title="Comparar">
                    <i class="fas fa-columns"></i>
                </button>
                <button class="btn-track-card ${isTracked ? 'active' : ''}" data-prop-id="${escapeHtml(prop.id)}" title="${isTracked ? 'En seguimiento' : 'Seguimiento'}">
                    <i class="fas fa-tasks"></i>
                </button>
            </div>
        </div>
        <div class="property-card-body">
            <div class="property-card-price">${formatPrice(prop.price)} <span>€/mes</span></div>
            <h3 class="property-card-title">${escapeHtml(prop.title)}</h3>
            <div class="property-card-location">
                <i class="fas fa-map-marker-alt"></i>
                ${escapeHtml(prop.address || prop.neighborhood || prop.city)}
            </div>
            <div class="property-card-features">
                <div class="feature"><i class="fas fa-bed"></i> ${prop.bedrooms} hab.</div>
                <div class="feature"><i class="fas fa-bath"></i> ${prop.bathrooms} baños</div>
                <div class="feature"><i class="fas fa-ruler-combined"></i> ${prop.area_m2 > 0 ? prop.area_m2 + ' m²' : '—'}</div>
                ${prop.floor ? `<div class="feature"><i class="fas fa-building"></i> ${prop.floor === 'bajo' ? 'PB' : 'Planta ' + prop.floor}</div>` : ''}
            </div>
            ${tags.length ? `<div class="property-card-tags">${tags.join('')}</div>` : ''}
            <div class="property-card-footer">
                <div class="property-card-availability"><i class="fas fa-calendar-alt"></i> ${prop.availability || 'Sin especificar'}</div>
                ${prop.is_demo
                    ? `<button class="btn-view btn-view-demo" data-url="${escapeHtml(prop.url)}" title="Esta es una propiedad de ejemplo. El enlace abre una búsqueda con filtros similares en ${escapeHtml(prop.platform)}">Buscar similares <i class="fas fa-search"></i></button>`
                    : `<button class="btn-view" data-url="${escapeHtml(prop.url)}">Ver anuncio <i class="fas fa-external-link-alt"></i></button>`
                }
            </div>
        </div>
    </div>`;
}

// ── Ordenación ─────────────────────────────────────────────────────────────

elements.sortBy.addEventListener('change', () => {
    const sorted = [...currentProperties];
    switch (elements.sortBy.value) {
        case 'price_asc':   sorted.sort((a, b) => a.price - b.price); break;
        case 'price_desc':  sorted.sort((a, b) => b.price - a.price); break;
        case 'score_desc':  sorted.sort((a, b) => b.score - a.score); break;
        case 'area_desc':   sorted.sort((a, b) => b.area_m2 - a.area_m2); break;
        case 'bedrooms_desc': sorted.sort((a, b) => b.bedrooms - a.bedrooms); break;
    }
    currentProperties = sorted;
    currentPage = 1;
    renderCurrentPage();
});
