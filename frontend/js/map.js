/**
 * map.js — Vista de mapa Leaflet con clustering
 */

const CITY_COORDS = {
    'madrid':             [40.4168, -3.7038],
    'barcelona':          [41.3874,  2.1686],
    'valencia':           [39.4699, -0.3763],
    'sevilla':            [37.3891, -5.9845],
    'málaga':             [36.7213, -4.4214],
    'malaga':             [36.7213, -4.4214],
    'zaragoza':           [41.6488, -0.8891],
    'bilbao':             [43.2630, -2.9350],
    'alicante':           [38.3452, -0.4810],
    'córdoba':            [37.8882, -4.7794],
    'cordoba':            [37.8882, -4.7794],
    'valladolid':         [41.6523, -4.7245],
    'granada':            [37.1773, -3.5986],
    'murcia':             [37.9922, -1.1307],
    'palma de mallorca':  [39.5696,  2.6502],
    'santander':          [43.4623, -3.8100],
    'san sebastián':      [43.3183, -1.9812],
    'san sebastian':      [43.3183, -1.9812],
    'gijón':              [43.5322, -5.6611],
    'gijon':              [43.5322, -5.6611],
    'vigo':               [42.2406, -8.7207],
    'a coruña':           [43.3623, -8.4115],
    'a coruna':           [43.3623, -8.4115],
    'marbella':           [36.5099, -4.8862],
    'cádiz':              [36.5271, -6.2886],
    'cadiz':              [36.5271, -6.2886],
    'tarragona':          [41.1189,  1.2445],
};

function normalizeCityKey(cityName) {
    return (cityName || '')
        .toLowerCase()
        .trim()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');
}

function getCityCenter(cityName) {
    return CITY_COORDS[normalizeCityKey(cityName)] || [40.0, -3.7];
}

function initMap(properties) {
    if (map) { map.remove(); map = null; }

    const isDark = document.body.classList.contains('dark-theme');

    map = L.map('map', { zoomControl: true, scrollWheelZoom: true });

    L.tileLayer(
        isDark
            ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
            : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
            attribution: isDark
                ? '&copy; <a href="https://carto.com/">CARTO</a>'
                : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 18,
        }
    ).addTo(map);

    markerClusterGroup = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: true,
        zoomToBoundsOnClick: true,
        iconCreateFunction(cluster) {
            const count = cluster.getChildCount();
            const size  = count >= 20 ? 'large' : count >= 10 ? 'medium' : 'small';
            return L.divIcon({
                html:      `<div class="cluster-icon cluster-${size}">${count}</div>`,
                className: 'marker-cluster-custom',
                iconSize:  L.point(44, 44),
            });
        },
    });

    const bounds = [];

    properties.forEach((prop, index) => {
        let lat = prop.latitude;
        let lng = prop.longitude;

        const hasExactCoords = Number.isFinite(lat) && Number.isFinite(lng);
        const locationPrecision = hasExactCoords ? 'exact' : (prop.location_precision || 'approximate');

        if (!hasExactCoords) {
            const center = getCityCenter(prop.city || searchParams.location || '');
            lat = center[0];
            lng = center[1];
        }

        if (Number.isFinite(lat) && Number.isFinite(lng)) {
            const priceStr = formatPrice(prop.price);
            const marker   = L.marker([lat, lng], {
                icon: L.divIcon({
                    html:      `<div class="price-marker${prop.has_sea_view ? ' sea-view' : ''}${locationPrecision !== 'exact' ? ' location-approx' : ''}">${priceStr}€</div>`,
                    className: 'custom-price-icon',
                    iconSize:  [80, 30],
                    iconAnchor:[40, 30],
                }),
            });

            marker.bindPopup(`
                <div class="map-popup">
                    <div class="map-popup-price">${priceStr} €/mes</div>
                    <div class="map-popup-title">${escapeHtml(prop.title)}</div>
                    <div class="map-popup-features">
                        ${prop.bedrooms} hab · ${prop.bathrooms} baños · ${prop.area_m2 > 0 ? prop.area_m2 + ' m²' : '—'}
                        ${prop.has_sea_view ? ' · 🌊 Vista mar' : ''}
                    </div>
                    <div style="font-size:.75rem;color:#6b7280;margin-bottom:6px;">
                        ${escapeHtml(prop.address || prop.neighborhood || prop.city)}
                        · <em>${escapeHtml(prop.platform)}</em>
                        ${locationPrecision !== 'exact' ? ' · <span title="Ubicación aproximada por centro de ciudad">📍 aproximada</span>' : ''}
                    </div>
                    <a href="${escapeHtml(prop.url)}" target="_blank" rel="noopener" class="map-popup-link">
                        Ver anuncio <i class="fas fa-external-link-alt" style="font-size:.7rem;"></i>
                    </a>
                </div>`);

            markerClusterGroup.addLayer(marker);
            bounds.push([lat, lng]);
        }
    });

    map.addLayer(markerClusterGroup);

    if (bounds.length === 1)      map.setView(bounds[0], 14);
    else if (bounds.length > 1)   map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    else                           map.setView(getCityCenter(searchParams.location || ''), 12);
}

// ── View toggle ────────────────────────────────────────────────────────────

elements.gridViewBtn.addEventListener('click', () => {
    currentView = 'grid';
    elements.gridViewBtn.classList.add('active');
    elements.mapViewBtn.classList.remove('active');
    elements.resultsGrid.classList.remove('hidden');
    elements.mapContainer.classList.add('hidden');
});

elements.mapViewBtn.addEventListener('click', () => {
    currentView = 'map';
    elements.mapViewBtn.classList.add('active');
    elements.gridViewBtn.classList.remove('active');
    elements.resultsGrid.classList.add('hidden');
    elements.mapContainer.classList.remove('hidden');
    if (currentProperties.length > 0) setTimeout(() => initMap(currentProperties), 100);
});
