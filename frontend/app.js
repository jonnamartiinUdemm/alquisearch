/**
 * AlquiSearch España - Frontend Application v3.0.0
 * Búsqueda integrada de alquileres en España
 * Features: search, filters, favorites, compare, pagination, quick-filters, dark mode, map
 */

// ========== State ==========
let allProperties = [];        // todos los resultados del servidor
let currentProperties = [];    // filtrados por quick-filters
let searchParams = {};
let currentView = 'grid';      // 'grid' or 'map'
let map = null;
let markerClusterGroup = null;

// Pagination
const PAGE_SIZE = 20;
let currentPage = 1;

// Favorites (IDs array — synced with backend)
let favorites = [];            // IDs de props favoritas
let favoriteProps = [];        // objetos completos (desde API)

// Session ID persistente, se envía al backend
function getOrCreateSessionId() {
    let sid = localStorage.getItem('aq_session');
    if (!sid) {
        sid = 'aq_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 10);
        localStorage.setItem('aq_session', sid);
    }
    return sid;
}
const SESSION_ID = getOrCreateSessionId();

// Auth state
let authUser = null;
let authToken = localStorage.getItem('aq_auth_token') || null;

// Tracking state
let trackingData = {};          // { stage: [entry, ...] }
let trackedIds = new Set();     // prop_ids en seguimiento
let trackingStages = [];        // [{id, label}] desde API

// Compare
let compareSet = new Set();

// ========== DOM Elements ==========
const elements = {
    locationInput: document.getElementById('locationInput'),
    citySuggestions: document.getElementById('citySuggestions'),
    searchBtn: document.getElementById('searchBtn'),
    toggleFilters: document.getElementById('toggleFilters'),
    filtersPanel: document.getElementById('filtersPanel'),
    maxPrice: document.getElementById('maxPrice'),
    minBedrooms: document.getElementById('minBedrooms'),
    minBathrooms: document.getElementById('minBathrooms'),
    availableFrom: document.getElementById('availableFrom'),
    minArea: document.getElementById('minArea'),
    maxArea: document.getElementById('maxArea'),
    propertyType: document.getElementById('propertyType'),
    petsAllowed: document.getElementById('petsAllowed'),
    needElevator: document.getElementById('needElevator'),
    preferTerrace: document.getElementById('preferTerrace'),
    preferBalcony: document.getElementById('preferBalcony'),
    preferTransport: document.getElementById('preferTransport'),
    preferServices: document.getElementById('preferServices'),
    longStay: document.getElementById('longStay'),
    seaView: document.getElementById('seaView'),
    seaViewToggle: document.getElementById('seaViewToggle'),
    resultsSection: document.getElementById('resultsSection'),
    resultsTitle: document.getElementById('resultsTitle'),
    resultsSubtitle: document.getElementById('resultsSubtitle'),
    resultsGrid: document.getElementById('resultsGrid'),
    loadingState: document.getElementById('loadingState'),
    emptyState: document.getElementById('emptyState'),
    directLinks: document.getElementById('directLinks'),
    directLinksGrid: document.getElementById('directLinksGrid'),
    platformErrors: document.getElementById('platformErrors'),
    sortBy: document.getElementById('sortBy'),
    propertyModal: document.getElementById('propertyModal'),
    modalBody: document.getElementById('modalBody'),
    modalClose: document.getElementById('modalClose'),
    mapContainer: document.getElementById('mapContainer'),
    mapEl: document.getElementById('map'),
    gridViewBtn: document.getElementById('gridViewBtn'),
    mapViewBtn: document.getElementById('mapViewBtn'),
    // New elements
    darkModeToggle: document.getElementById('darkModeToggle'),
    favoritesNavLink: document.getElementById('favoritesNavLink'),
    favCount: document.getElementById('favCount'),
    favoritesPanel: document.getElementById('favoritesPanel'),
    favoritesGrid: document.getElementById('favoritesGrid'),
    favoritesEmpty: document.getElementById('favoritesEmpty'),
    closeFavorites: document.getElementById('closeFavorites'),
    compareBtn: document.getElementById('compareBtn'),
    compareCount: document.getElementById('compareCount'),
    compareModal: document.getElementById('compareModal'),
    compareBody: document.getElementById('compareBody'),
    closeCompare: document.getElementById('closeCompare'),
    // Quick filters
    quickFilters: document.getElementById('quickFilters'),
    qfPriceMin: document.getElementById('qfPriceMin'),
    qfPriceMax: document.getElementById('qfPriceMax'),
    qfPriceLabel: document.getElementById('qfPriceLabel'),
    qfAreaMin: document.getElementById('qfAreaMin'),
    qfAreaMax: document.getElementById('qfAreaMax'),
    qfAreaLabel: document.getElementById('qfAreaLabel'),
    // Pagination
    pagination: document.getElementById('pagination'),
    prevPage: document.getElementById('prevPage'),
    nextPage: document.getElementById('nextPage'),
    pageInfo: document.getElementById('pageInfo'),
    // Extra controls
    strictPets: document.getElementById('strictPets'),
    clearFiltersBtn: document.getElementById('clearFiltersBtn'),
    shareUrlBtn: document.getElementById('shareUrlBtn'),
    // Auth
    loginBtn: document.getElementById('loginBtn'),
    userMenuLogged: document.getElementById('userMenuLogged'),
    userAvatarBtn: document.getElementById('userAvatarBtn'),
    userDropdown: document.getElementById('userDropdown'),
    userDisplayName: document.getElementById('userDisplayName'),
    userDropdownInfo: document.getElementById('userDropdownInfo'),
    adminPanelLink: document.getElementById('adminPanelLink'),
    logoutBtn: document.getElementById('logoutBtn'),
    loginModal: document.getElementById('loginModal'),
    loginForm: document.getElementById('loginForm'),
    registerForm: document.getElementById('registerForm'),
    loginError: document.getElementById('loginError'),
    registerError: document.getElementById('registerError'),
    // Tracking
    trackingNavLink: document.getElementById('trackingNavLink'),
    trackCount: document.getElementById('trackCount'),
    trackingPanel: document.getElementById('trackingPanel'),
    trackingBoard: document.getElementById('trackingBoard'),
    closeTracking: document.getElementById('closeTracking'),
};

// ========== API Functions ==========
const API_BASE = '';

async function fetchCities(query) {
    try {
        const response = await fetch(`${API_BASE}/api/cities?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Error fetching cities');
        return await response.json();
    } catch (error) {
        console.error('Error fetching cities:', error);
        return [];
    }
}

async function searchProperties(params) {
    try {
        const response = await fetch(`${API_BASE}/api/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error searching properties:', error);
        throw error;
    }
}

async function fetchSearchUrls(location) {
    try {
        const response = await fetch(`${API_BASE}/api/search-urls?location=${encodeURIComponent(location)}`);
        if (!response.ok) throw new Error('Error fetching URLs');
        return await response.json();
    } catch (error) {
        console.error('Error fetching search URLs:', error);
        return {};
    }
}

async function checkCoastalCity(city) {
    try {
        const response = await fetch(`${API_BASE}/api/is-coastal?city=${encodeURIComponent(city)}`);
        if (!response.ok) return false;
        const data = await response.json();
        return data.is_coastal;
    } catch (error) {
        return false;
    }
}

// ========== City Suggestions + Search History ==========
let suggestionsTimeout = null;

// Search history: últimas 6 búsquedas
function getSearchHistory() {
    return JSON.parse(localStorage.getItem('aq_search_history') || '[]');
}
function addToSearchHistory(location) {
    if (!location) return;
    let history = getSearchHistory().filter(h => h !== location);
    history.unshift(location);
    localStorage.setItem('aq_search_history', JSON.stringify(history.slice(0, 6)));
}

function showSuggestions(cities, historyItems) {
    const dropdown = elements.citySuggestions;
    const items = [];

    // Primero historial de búsqueda
    (historyItems || []).forEach(h => {
        items.push(`<div class="suggestion-item suggestion-history" data-city="${h}">
            <i class="fas fa-history"></i> ${h}
        </div>`);
    });

    // Luego sugerencias de API
    (cities || []).forEach(city => {
        if (!items.some(i => i.includes(`data-city="${city}"`))) {
            const icon = city.includes(',') ? 'fa-building' : 'fa-city';
            items.push(`<div class="suggestion-item" data-city="${city}">
                <i class="fas ${icon}"></i> ${city}
            </div>`);
        }
    });

    if (!items.length) {
        dropdown.classList.add('hidden');
        return;
    }

    dropdown.innerHTML = items.join('');
    dropdown.classList.remove('hidden');

    dropdown.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', async () => {
            elements.locationInput.value = item.dataset.city;
            dropdown.classList.add('hidden');
            const isCoastal = await checkCoastalCity(item.dataset.city);
            if (isCoastal) {
                elements.seaViewToggle.classList.remove('hidden');
            } else {
                elements.seaViewToggle.classList.add('hidden');
                elements.seaView.checked = false;
            }
        });
    });
}

elements.locationInput.addEventListener('input', (e) => {
    clearTimeout(suggestionsTimeout);
    const query = e.target.value.trim();
    if (query.length < 2) {
        // Mostrar historial al borrar
        const history = getSearchHistory();
        if (history.length) showSuggestions([], history);
        else elements.citySuggestions.classList.add('hidden');
        return;
    }
    suggestionsTimeout = setTimeout(async () => {
        const cities = await fetchCities(query);
        showSuggestions(cities, []);
    }, 200);
});

elements.locationInput.addEventListener('focus', async () => {
    const query = elements.locationInput.value.trim();
    if (query.length >= 2) {
        const cities = await fetchCities(query);
        showSuggestions(cities, []);
    } else {
        const history = getSearchHistory();
        if (history.length) showSuggestions([], history);
    }
});

document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-input-wrapper')) {
        elements.citySuggestions.classList.add('hidden');
    }
});

// ========== Toggle Filters ==========
elements.toggleFilters.addEventListener('click', () => {
    elements.filtersPanel.classList.toggle('hidden');
    elements.toggleFilters.classList.toggle('active');
});

// ========== Search ==========
function getSearchParams() {
    const platforms = Array.from(document.querySelectorAll('input[name="platform"]:checked'))
        .map(cb => cb.value);

    const params = {
        location: elements.locationInput.value.trim(),
        max_price: parseFloat(elements.maxPrice.value) || 2800,
        min_bedrooms: parseInt(elements.minBedrooms.value) || 2,
        min_bathrooms: parseInt(elements.minBathrooms.value) || 2,
        available_from: elements.availableFrom.value || '2026-10-01',
        pets_allowed: elements.petsAllowed.checked,
        strict_pets: elements.strictPets ? elements.strictPets.checked : false,
        need_elevator: elements.needElevator.checked,
        prefer_terrace: elements.preferTerrace.checked,
        prefer_balcony: elements.preferBalcony.checked,
        prefer_transport: elements.preferTransport.checked,
        prefer_services: elements.preferServices.checked,
        long_stay: elements.longStay.checked,
        sea_view: elements.seaView.checked || null,
        platforms: platforms,
    };

    // New optional filters
    const minArea = parseFloat(elements.minArea.value);
    if (minArea > 0) params.min_area = minArea;
    const maxArea = parseFloat(elements.maxArea.value);
    if (maxArea > 0) params.max_area = maxArea;
    const propType = elements.propertyType.value;
    if (propType) params.property_type = propType;

    return params;
}

async function performSearch() {
    const params = getSearchParams();

    if (!params.location) {
        elements.locationInput.focus();
        elements.locationInput.style.outline = '2px solid #ef4444';
        setTimeout(() => elements.locationInput.style.outline = '', 2000);
        return;
    }

    searchParams = params;
    addToSearchHistory(params.location);   // guardar en historial
    currentPage = 1;
    compareSet.clear();
    updateCompareUI();

    // Show results section and loading
    elements.resultsSection.classList.remove('hidden');
    elements.loadingState.classList.remove('hidden');
    elements.resultsGrid.innerHTML = '';
    elements.emptyState.classList.add('hidden');
    elements.directLinks.classList.add('hidden');
    elements.platformErrors.classList.add('hidden');
    elements.quickFilters.classList.add('hidden');
    elements.pagination.classList.add('hidden');

    elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    try {
        const [result, urls] = await Promise.all([
            searchProperties(params),
            fetchSearchUrls(params.location),
        ]);

        elements.loadingState.classList.add('hidden');
        showDirectLinks(urls);

        if (result.errors && result.errors.length > 0) {
            showPlatformErrors(result.errors);
        }

        allProperties = result.properties || [];
        currentProperties = [...allProperties];

        elements.resultsTitle.textContent = `${result.total} propiedades en ${params.location}`;
        elements.resultsSubtitle.textContent =
            `Buscado en: ${result.platforms_searched.join(', ')} · ` +
            `Precio máx: ${params.max_price}€ · ${params.min_bedrooms}+ hab · ${params.min_bathrooms}+ baños`;

        if (currentProperties.length > 0) {
            setupQuickFilters();
            renderCurrentPage();
        } else {
            elements.emptyState.classList.remove('hidden');
        }

    } catch (error) {
        elements.loadingState.classList.add('hidden');
        elements.emptyState.classList.remove('hidden');
        elements.emptyState.querySelector('h3').textContent = 'Error en la búsqueda';
        elements.emptyState.querySelector('p').textContent =
            'No se pudo completar la búsqueda. Verifica tu conexión e inténtalo de nuevo.';
    }
}

elements.searchBtn.addEventListener('click', performSearch);

// ========== Clear Filters ==========
function clearFilters() {
    elements.maxPrice.value = '2800';
    elements.minBedrooms.value = '2';
    elements.minBathrooms.value = '2';
    elements.minArea.value = '';
    elements.maxArea.value = '';
    elements.propertyType.value = '';
    elements.petsAllowed.checked = true;
    if (elements.strictPets) elements.strictPets.checked = false;
    elements.needElevator.checked = true;
    elements.preferTerrace.checked = true;
    elements.preferBalcony.checked = true;
    elements.preferTransport.checked = true;
    elements.preferServices.checked = true;
    elements.longStay.checked = false;
    if (elements.seaView) elements.seaView.checked = false;
    document.querySelectorAll('input[name="platform"]').forEach(cb => cb.checked = true);
    showToast('Filtros restablecidos');
}

// ========== Sharable URL ==========
function copyShareableUrl() {
    const params = getSearchParams();
    const base = window.location.origin + window.location.pathname;
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
        if (v !== null && v !== undefined && v !== '' && v !== false) {
            qs.set(k, Array.isArray(v) ? v.join(',') : String(v));
        }
    });
    const url = `${base}?${qs.toString()}`;
    navigator.clipboard.writeText(url).then(() => showToast('URL copiada al portapapeles ✅')).catch(() => {
        prompt('Copia esta URL:', url);
    });
}

if (elements.clearFiltersBtn) elements.clearFiltersBtn.addEventListener('click', clearFilters);
if (elements.shareUrlBtn) elements.shareUrlBtn.addEventListener('click', copyShareableUrl);

// ========== Toast Notifications ==========
function showToast(message, duration = 3000) {
    let toast = document.getElementById('appToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'appToast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('toast-visible');
    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(() => toast.classList.remove('toast-visible'), duration);
}
elements.locationInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        elements.citySuggestions.classList.add('hidden');
        performSearch();
    }
});

// ========== Quick Filters (client-side) ==========
function setupQuickFilters() {
    if (allProperties.length === 0) return;

    const prices = allProperties.map(p => p.price).filter(p => p > 0);
    const areas = allProperties.map(p => p.area_m2).filter(a => a > 0);

    const minP = Math.floor(Math.min(...prices, 0));
    const maxP = Math.ceil(Math.max(...prices, 10000));
    const minA = Math.floor(Math.min(...areas, 0));
    const maxA = Math.ceil(Math.max(...areas, 500));

    elements.qfPriceMin.min = minP; elements.qfPriceMin.max = maxP; elements.qfPriceMin.value = minP;
    elements.qfPriceMax.min = minP; elements.qfPriceMax.max = maxP; elements.qfPriceMax.value = maxP;
    elements.qfAreaMin.min = minA; elements.qfAreaMin.max = maxA; elements.qfAreaMin.value = minA;
    elements.qfAreaMax.min = minA; elements.qfAreaMax.max = maxA; elements.qfAreaMax.value = maxA;

    updateQuickFilterLabels();
    elements.quickFilters.classList.remove('hidden');
}

function updateQuickFilterLabels() {
    elements.qfPriceLabel.textContent = `${elements.qfPriceMin.value} – ${elements.qfPriceMax.value}€`;
    elements.qfAreaLabel.textContent = `${elements.qfAreaMin.value} – ${elements.qfAreaMax.value} m²`;
}

function applyQuickFilters() {
    const pMin = parseFloat(elements.qfPriceMin.value);
    const pMax = parseFloat(elements.qfPriceMax.value);
    const aMin = parseFloat(elements.qfAreaMin.value);
    const aMax = parseFloat(elements.qfAreaMax.value);

    currentProperties = allProperties.filter(p => {
        if (p.price > 0 && (p.price < pMin || p.price > pMax)) return false;
        if (p.area_m2 > 0 && (p.area_m2 < aMin || p.area_m2 > aMax)) return false;
        return true;
    });

    currentPage = 1;
    updateQuickFilterLabels();
    renderCurrentPage();
}

[elements.qfPriceMin, elements.qfPriceMax, elements.qfAreaMin, elements.qfAreaMax].forEach(el => {
    el.addEventListener('input', applyQuickFilters);
});

// ========== Pagination ==========
function getTotalPages() {
    return Math.max(1, Math.ceil(currentProperties.length / PAGE_SIZE));
}

function getPageSlice() {
    const start = (currentPage - 1) * PAGE_SIZE;
    return currentProperties.slice(start, start + PAGE_SIZE);
}

function renderCurrentPage() {
    const totalPages = getTotalPages();
    const pageItems = getPageSlice();

    if (pageItems.length > 0) {
        renderProperties(pageItems);
        elements.emptyState.classList.add('hidden');
    } else {
        elements.resultsGrid.innerHTML = '';
        elements.emptyState.classList.remove('hidden');
    }

    // Update pagination
    if (currentProperties.length > PAGE_SIZE) {
        elements.pagination.classList.remove('hidden');
        elements.prevPage.disabled = currentPage <= 1;
        elements.nextPage.disabled = currentPage >= totalPages;
        elements.pageInfo.textContent = `Página ${currentPage} de ${totalPages} (${currentProperties.length} propiedades)`;
    } else {
        elements.pagination.classList.add('hidden');
    }

    // Update results title with count
    elements.resultsTitle.textContent = `${currentProperties.length} propiedades en ${searchParams.location || ''}`;
}

elements.prevPage.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        renderCurrentPage();
        elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
});

elements.nextPage.addEventListener('click', () => {
    if (currentPage < getTotalPages()) {
        currentPage++;
        renderCurrentPage();
        elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
});

// ========== Show Direct Links ==========
function showDirectLinks(urls) {
    if (!urls || Object.keys(urls).length === 0) return;

    const platformIcons = {
        'idealista': 'fa-building',
        'fotocasa': 'fa-camera',
        'habitaclia': 'fa-house-user',
        'pisos.com': 'fa-home',
        'housinganywhere': 'fa-globe',
    };

    elements.directLinksGrid.innerHTML = Object.entries(urls).map(([name, url]) => `
        <a href="${url}" target="_blank" rel="noopener noreferrer" class="direct-link">
            <i class="fas ${platformIcons[name] || 'fa-link'}"></i>
            ${name.charAt(0).toUpperCase() + name.slice(1)}
            <i class="fas fa-external-link-alt" style="margin-left: auto; font-size: 0.75rem; opacity: 0.5;"></i>
        </a>
    `).join('');

    elements.directLinks.classList.remove('hidden');
}

// ========== Show Platform Errors ==========
function showPlatformErrors(errors) {
    elements.platformErrors.innerHTML = errors.map(err => `
        <div class="platform-error">
            <i class="fas fa-exclamation-triangle"></i>
            ${err}
        </div>
    `).join('');
    elements.platformErrors.classList.remove('hidden');
}

// ========== Render Properties ==========
function renderProperties(properties) {
    elements.resultsGrid.innerHTML = properties.map((prop, index) => createPropertyCard(prop, index)).join('');

    // Card click -> modal
    elements.resultsGrid.querySelectorAll('.property-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.closest('.btn-view') || e.target.closest('.btn-fav') || e.target.closest('.btn-compare-card') || e.target.closest('.btn-track-card') || e.target.closest('.card-actions')) return;
            const id = card.dataset.propId;
            const prop = allProperties.find(p => p.id === id) || currentProperties.find(p => p.id === id);
            if (prop) openPropertyModal(prop);
        });
    });

    // View button
    elements.resultsGrid.querySelectorAll('.btn-view').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            window.open(btn.dataset.url, '_blank');
        });
    });

    // Fav button
    elements.resultsGrid.querySelectorAll('.btn-fav').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleFavorite(btn.dataset.propId);
        });
    });

    // Compare checkbox
    elements.resultsGrid.querySelectorAll('.btn-compare-card').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleCompare(btn.dataset.propId);
        });
    });

    // Tracking button
    elements.resultsGrid.querySelectorAll('.btn-track-card').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const propId = btn.dataset.propId;
            const prop = allProperties.find(p => p.id === propId) || currentProperties.find(p => p.id === propId);
            if (trackedIds.has(propId)) {
                openTrackingPanel();
            } else if (prop) {
                showStagePicker(prop, btn);
            }
        });
    });
}

function createPropertyCard(prop, index) {
    const imageUrl = prop.images && prop.images.length > 0
        ? prop.images[0]
        : 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop';

    const isFav = favorites.includes(prop.id);
    const isCompare = compareSet.has(prop.id);
    const isTracked = trackedIds.has(prop.id);

    const badges = [];
    badges.push(`<span class="badge badge-platform">${escapeHtml(prop.platform)}</span>`);
    const petsFilterOn = elements.petsAllowed && elements.petsAllowed.checked;
    if (prop.pets_allowed === true) {
        badges.push('<span class="badge badge-pets"><i class="fas fa-paw"></i> Mascotas ✓</span>');
    } else if (prop.pets_allowed === null || prop.pets_allowed === undefined) {
        if (petsFilterOn) badges.push('<span class="badge badge-pets-unknown" title="No se ha confirmado si admite mascotas"><i class="fas fa-paw"></i> Sin confirmar</span>');
    }
    if (prop.has_terrace) badges.push('<span class="badge badge-terrace"><i class="fas fa-sun"></i> Terraza</span>');
    if (prop.has_elevator) badges.push('<span class="badge badge-elevator"><i class="fas fa-arrows-alt-v"></i> Ascensor</span>');
    if (prop.has_sea_view) badges.push('<span class="badge badge-seaview"><i class="fas fa-water"></i> Vista al mar</span>');
    if (prop.is_long_stay) badges.push('<span class="badge badge-longstay"><i class="fas fa-calendar-check"></i> Larga estancia</span>');

    const tags = [];
    if (prop.has_balcony) tags.push('<span class="tag positive">Balcón</span>');
    if (prop.has_air_conditioning) tags.push('<span class="tag positive">A/C</span>');
    if (prop.has_heating) tags.push('<span class="tag positive">Calefacción</span>');
    if (prop.has_parking) tags.push('<span class="tag positive">Parking</span>');
    if (prop.has_pool) tags.push('<span class="tag positive">Piscina</span>');
    if (prop.furnished) tags.push('<span class="tag positive">Amueblado</span>');
    if (prop.public_transport_nearby) tags.push('<span class="tag positive">Transporte</span>');
    if (prop.services_nearby) tags.push('<span class="tag positive">Servicios</span>');
    if (prop.allows_empadronamiento) tags.push('<span class="tag positive">Empadronamiento</span>');

    const scoreLabel = prop.score >= 80 ? '⭐ Excelente' : prop.score >= 60 ? '✓ Bueno' : '~ Normal';
    const scoreClass = prop.score >= 80 ? 'score-excellent' : prop.score >= 60 ? 'score-good' : 'score-normal';

    // Limitar badges visibles: plataforma + máx 2 extras + indicador "+N más"
    const MAX_VISIBLE_BADGES = 3;
    let visibleBadges = badges.slice(0, MAX_VISIBLE_BADGES);
    const hiddenCount = badges.length - MAX_VISIBLE_BADGES;
    if (hiddenCount > 0) {
        visibleBadges.push(`<span class="badge badge-more" title="${badges.slice(MAX_VISIBLE_BADGES).map(b => b.replace(/<[^>]+>/g,'')).join(', ')}">+${hiddenCount}</span>`);
    }

    return `
        <div class="property-card" data-prop-id="${escapeHtml(prop.id)}">
            <div class="property-card-image">
                <img src="${imageUrl}" alt="${escapeHtml(prop.title)}" loading="lazy"
                     onerror="this.src='https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop'">
                <div class="property-card-badges">
                    ${visibleBadges.join('')}
                </div>
                <div class="property-card-score ${scoreClass}">${scoreLabel} <strong>${Math.round(prop.score)}</strong></div>
                <!-- Columna de acciones: siempre en top-right, nunca solapa badges ni score -->
                <div class="card-actions">
                    <button class="btn-fav ${isFav ? 'active' : ''}" data-prop-id="${escapeHtml(prop.id)}" title="${isFav ? 'Quitar de favoritos' : 'Añadir a favoritos'}" aria-label="${isFav ? 'Quitar de favoritos' : 'Añadir a favoritos'}">
                        <i class="fas fa-heart"></i>
                    </button>
                    <button class="btn-compare-card ${isCompare ? 'active' : ''}" data-prop-id="${escapeHtml(prop.id)}" title="Comparar propiedad" aria-label="Añadir a comparador">
                        <i class="fas fa-columns"></i>
                    </button>
                    <button class="btn-track-card ${isTracked ? 'active' : ''}" data-prop-id="${escapeHtml(prop.id)}" title="${isTracked ? 'En seguimiento' : 'Añadir a seguimiento'}" aria-label="Seguimiento">
                        <i class="fas fa-tasks"></i>
                    </button>
                </div>
            </div>
            <div class="property-card-body">
                <div class="property-card-price">
                    ${formatPrice(prop.price)} <span>€/mes</span>
                </div>
                <h3 class="property-card-title">${escapeHtml(prop.title)}</h3>
                <div class="property-card-location">
                    <i class="fas fa-map-marker-alt"></i>
                    ${escapeHtml(prop.address || prop.neighborhood || prop.city)}
                </div>
                <div class="property-card-features">
                    <div class="feature">
                        <i class="fas fa-bed"></i>
                        ${prop.bedrooms} hab.
                    </div>
                    <div class="feature">
                        <i class="fas fa-bath"></i>
                        ${prop.bathrooms} baños
                    </div>
                    <div class="feature">
                        <i class="fas fa-ruler-combined"></i>
                        ${prop.area_m2 > 0 ? prop.area_m2 + ' m²' : '—'}
                    </div>
                    ${prop.floor ? `
                    <div class="feature">
                        <i class="fas fa-building"></i>
                        ${prop.floor === 'bajo' ? 'PB' : 'Planta ' + prop.floor}
                    </div>` : ''}
                </div>
                ${tags.length > 0 ? `<div class="property-card-tags">${tags.join('')}</div>` : ''}
                <div class="property-card-footer">
                    <div class="property-card-availability">
                        <i class="fas fa-calendar-alt"></i>
                        ${prop.availability || 'Sin especificar'}
                    </div>
                    <button class="btn-view" data-url="${escapeHtml(prop.url)}">
                        Ver anuncio <i class="fas fa-external-link-alt"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// ========== Sorting ==========
elements.sortBy.addEventListener('change', () => {
    const sortBy = elements.sortBy.value;
    const sorted = [...currentProperties];

    switch (sortBy) {
        case 'score':
            sorted.sort((a, b) => b.score - a.score);
            break;
        case 'price-asc':
            sorted.sort((a, b) => a.price - b.price);
            break;
        case 'price-desc':
            sorted.sort((a, b) => b.price - a.price);
            break;
        case 'area':
            sorted.sort((a, b) => b.area_m2 - a.area_m2);
            break;
        case 'bedrooms':
            sorted.sort((a, b) => b.bedrooms - a.bedrooms);
            break;
    }

    currentProperties = sorted;
    currentPage = 1;
    renderCurrentPage();
});

// ========== Property Modal ==========
function openPropertyModal(prop) {
    const imageUrl = prop.images && prop.images.length > 0
        ? prop.images[0]
        : 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop';

    const isFav = favorites.includes(prop.id);

    const features = [];
    features.push({ icon: 'fa-bed', text: `${prop.bedrooms} habitaciones` });
    features.push({ icon: 'fa-bath', text: `${prop.bathrooms} baños` });
    if (prop.area_m2 > 0) features.push({ icon: 'fa-ruler-combined', text: `${prop.area_m2} m²` });
    if (prop.floor) features.push({ icon: 'fa-building', text: `Planta ${prop.floor}` });
    if (prop.has_elevator) features.push({ icon: 'fa-arrows-alt-v', text: 'Con ascensor' });
    if (prop.pets_allowed) features.push({ icon: 'fa-paw', text: 'Mascotas OK' });
    if (prop.has_terrace) features.push({ icon: 'fa-sun', text: 'Terraza' });
    if (prop.has_balcony) features.push({ icon: 'fa-door-open', text: 'Balcón' });
    if (prop.has_air_conditioning) features.push({ icon: 'fa-snowflake', text: 'Aire acondicionado' });
    if (prop.has_heating) features.push({ icon: 'fa-fire', text: 'Calefacción' });
    if (prop.has_parking) features.push({ icon: 'fa-car', text: 'Parking' });
    if (prop.has_pool) features.push({ icon: 'fa-swimming-pool', text: 'Piscina' });
    if (prop.furnished) features.push({ icon: 'fa-couch', text: 'Amueblado' });
    if (prop.has_sea_view) features.push({ icon: 'fa-water', text: 'Vista al mar' });
    if (prop.is_long_stay) features.push({ icon: 'fa-calendar-check', text: 'Larga estancia' });
    if (prop.energy_rating) features.push({ icon: 'fa-leaf', text: `Energía: ${prop.energy_rating}` });

    const tags = [];
    if (prop.public_transport_nearby) tags.push('<span class="tag positive"><i class="fas fa-bus"></i> Transporte público cercano</span>');
    if (prop.services_nearby) tags.push('<span class="tag positive"><i class="fas fa-store"></i> Servicios cercanos</span>');
    if (prop.allows_empadronamiento) tags.push('<span class="tag positive"><i class="fas fa-id-card"></i> Permite empadronamiento</span>');

    elements.modalBody.innerHTML = `
        <img class="modal-image" src="${imageUrl}" alt="${escapeHtml(prop.title)}"
             onerror="this.src='https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop'">
        <div class="modal-body-content">
            <div class="modal-price">${formatPrice(prop.price)} <small style="font-size: 1rem; color: var(--gray-400);">€/mes</small></div>
            <h2 class="modal-title">${escapeHtml(prop.title)}</h2>
            <div class="modal-location">
                <i class="fas fa-map-marker-alt"></i>
                ${escapeHtml([prop.address, prop.neighborhood, prop.city].filter(Boolean).join(', '))}
            </div>

            <div class="modal-features-grid">
                ${features.map(f => `
                    <div class="modal-feature">
                        <i class="fas ${f.icon}"></i>
                        ${f.text}
                    </div>
                `).join('')}
            </div>

            ${prop.description ? `<div class="modal-description">${escapeHtml(prop.description)}</div>` : ''}

            ${tags.length > 0 ? `<div class="modal-tags">${tags.join('')}</div>` : ''}

            <div style="margin-bottom: 16px; font-size: 0.85rem; color: var(--gray-500);">
                <i class="fas fa-calendar-alt"></i> Disponibilidad: ${prop.availability || 'No especificada'}
                &nbsp;|&nbsp;
                <i class="fas fa-star"></i> Puntuación: ${Math.round(prop.score)} / 100
                ${prop.scam_score > 0 ? `&nbsp;|&nbsp;<span style="color: var(--warning);"><i class="fas fa-exclamation-triangle"></i> Riesgo: ${Math.round(prop.scam_score * 100)}%</span>` : ''}
            </div>

            <div class="modal-actions">
                <a href="${escapeHtml(prop.url)}" target="_blank" rel="noopener noreferrer" class="btn-primary">
                    <i class="fas fa-external-link-alt"></i>
                    Ver en ${escapeHtml(prop.platform)}
                </a>
                <button class="btn-secondary modal-fav-btn ${isFav ? 'active' : ''}" data-prop-id="${escapeHtml(prop.id)}">
                    <i class="fas fa-heart"></i>
                    ${isFav ? 'En favoritos' : 'Favorito'}
                </button>
                <button class="btn-secondary" onclick="closePropertyModal()">
                    <i class="fas fa-times"></i>
                    Cerrar
                </button>
            </div>
        </div>
    `;

    // Fav button in modal
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
    }
});

// ========== Favorites ==========
async function loadFavoritesFromAPI() {
    try {
        const res = await fetch(`/api/favorites/${SESSION_ID}`);
        if (!res.ok) throw new Error('API error');
        const data = await res.json();
        favorites = data.ids || [];
        favoriteProps = data.favorites || [];
    } catch {
        // Fallback: cargar desde localStorage
        favorites = JSON.parse(localStorage.getItem('alquisearch_favorites') || '[]');
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
    if (favorites.length > 0) {
        elements.favCount.classList.remove('hidden');
    } else {
        elements.favCount.classList.add('hidden');
    }
}

async function toggleFavorite(propId) {
    const propObj = allProperties.find(p => p.id === propId) ||
                    favoriteProps.find(p => p.id === propId);
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
            favorites = favorites.filter(id => id !== propId);
            favoriteProps = favoriteProps.filter(p => p.id !== propId);
            showToast('Eliminado de favoritos');
        }
    } catch {
        // Fallback local
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

    // Actualizar todos los botones fav de esta propiedad
    document.querySelectorAll(`.btn-fav[data-prop-id="${propId}"]`).forEach(btn => {
        btn.classList.toggle('active', favorites.includes(propId));
    });
}

function openFavoritesPanel() {
    // Usar favoriteProps del API; si está vacío, filtrar allProperties localmente
    const favProps = favoriteProps.length > 0
        ? favoriteProps
        : allProperties.filter(p => favorites.includes(p.id));

    if (favProps.length > 0) {
        elements.favoritesGrid.innerHTML = favProps.map((prop, i) => createPropertyCard(prop, i)).join('');
        elements.favoritesEmpty.classList.add('hidden');
        elements.favoritesGrid.classList.remove('hidden');

        // Reattach handlers inside favorites grid
        elements.favoritesGrid.querySelectorAll('.btn-fav').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleFavorite(btn.dataset.propId);
                openFavoritesPanel();
            });
        });
        elements.favoritesGrid.querySelectorAll('.btn-view').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                window.open(btn.dataset.url, '_blank');
            });
        });
        elements.favoritesGrid.querySelectorAll('.property-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('.btn-view') || e.target.closest('.btn-fav') || e.target.closest('.btn-compare-card') || e.target.closest('.card-actions')) return;
                const id = card.dataset.propId;
                const prop = allProperties.find(p => p.id === id);
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

elements.favoritesNavLink.addEventListener('click', (e) => {
    e.preventDefault();
    openFavoritesPanel();
});
elements.closeFavorites.addEventListener('click', closeFavoritesPanel);
document.querySelector('.favorites-overlay').addEventListener('click', closeFavoritesPanel);

// ========== Compare ==========
function toggleCompare(propId) {
    if (compareSet.has(propId)) {
        compareSet.delete(propId);
    } else {
        if (compareSet.size >= 4) {
            alert('Máximo 4 propiedades para comparar');
            return;
        }
        compareSet.add(propId);
    }
    updateCompareUI();

    // Update buttons
    document.querySelectorAll(`.btn-compare-card[data-prop-id="${propId}"]`).forEach(btn => {
        btn.classList.toggle('active', compareSet.has(propId));
    });
}

function updateCompareUI() {
    elements.compareCount.textContent = compareSet.size;
    if (compareSet.size >= 2) {
        elements.compareBtn.classList.remove('hidden');
    } else {
        elements.compareBtn.classList.add('hidden');
    }
}

function openCompareModal() {
    const props = [...compareSet].map(id => allProperties.find(p => p.id === id)).filter(Boolean);
    if (props.length < 2) return;

    const rows = [
        { label: 'Precio', fn: p => `${formatPrice(p.price)} €/mes` },
        { label: 'Habitaciones', fn: p => p.bedrooms },
        { label: 'Baños', fn: p => p.bathrooms },
        { label: 'Superficie', fn: p => p.area_m2 > 0 ? `${p.area_m2} m²` : '—' },
        { label: 'Planta', fn: p => p.floor || '—' },
        { label: 'Ascensor', fn: p => p.has_elevator ? '✓' : '✗' },
        { label: 'Mascotas', fn: p => p.pets_allowed ? '✓' : p.pets_allowed === false ? '✗' : '?' },
        { label: 'Terraza', fn: p => p.has_terrace ? '✓' : '✗' },
        { label: 'Balcón', fn: p => p.has_balcony ? '✓' : '✗' },
        { label: 'A/C', fn: p => p.has_air_conditioning ? '✓' : '✗' },
        { label: 'Calefacción', fn: p => p.has_heating ? '✓' : '✗' },
        { label: 'Parking', fn: p => p.has_parking ? '✓' : '✗' },
        { label: 'Piscina', fn: p => p.has_pool ? '✓' : '✗' },
        { label: 'Puntuación', fn: p => Math.round(p.score) },
        { label: 'Plataforma', fn: p => p.platform },
    ];

    const colWidth = Math.floor(100 / (props.length + 1));

    let html = `<table class="compare-table">
        <thead><tr>
            <th style="width:${colWidth}%">Característica</th>
            ${props.map(p => `<th style="width:${colWidth}%">${escapeHtml(p.title.slice(0, 40))}</th>`).join('')}
        </tr></thead><tbody>`;

    for (const row of rows) {
        html += `<tr><td class="compare-label">${row.label}</td>`;
        for (const p of props) {
            html += `<td>${row.fn(p)}</td>`;
        }
        html += '</tr>';
    }

    html += `<tr><td class="compare-label">Enlace</td>`;
    for (const p of props) {
        html += `<td><a href="${escapeHtml(p.url)}" target="_blank" class="btn-primary btn-sm">Ver anuncio</a></td>`;
    }
    html += '</tr></tbody></table>';

    elements.compareBody.innerHTML = html;
    elements.compareModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeCompareModal() {
    elements.compareModal.classList.add('hidden');
    document.body.style.overflow = '';
}

elements.compareBtn.addEventListener('click', openCompareModal);
elements.closeCompare.addEventListener('click', closeCompareModal);
document.querySelector('#compareModal .modal-overlay').addEventListener('click', closeCompareModal);

// ========== Dark Mode ==========
function initDarkMode() {
    const saved = localStorage.getItem('alquisearch_theme');
    if (saved === 'dark') {
        document.body.classList.add('dark-theme');
        elements.darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }
}

elements.darkModeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    localStorage.setItem('alquisearch_theme', isDark ? 'dark' : 'light');
    elements.darkModeToggle.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';

    // Re-init map if visible
    if (currentView === 'map' && currentProperties.length > 0) {
        setTimeout(() => initMap(currentProperties), 100);
    }
});

// ========== Utility Functions ==========
function formatPrice(price) {
    return new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(price);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== Auth ==========

function _authHeaders() {
    return authToken ? { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

async function initAuth() {
    if (!authToken) { updateUserUI(null); return; }
    try {
        const res = await fetch('/api/auth/me', { headers: { 'Authorization': `Bearer ${authToken}` } });
        if (!res.ok) {
            authToken = null;
            localStorage.removeItem('aq_auth_token');
            updateUserUI(null);
            return;
        }
        authUser = await res.json();
        updateUserUI(authUser);
    } catch {
        authToken = null;
        updateUserUI(null);
    }
}

function updateUserUI(user) {
    if (!elements.loginBtn) return;
    if (user) {
        elements.loginBtn.classList.add('hidden');
        elements.userMenuLogged && elements.userMenuLogged.classList.remove('hidden');
        if (elements.userDisplayName) elements.userDisplayName.textContent = user.username;
        if (elements.userDropdownInfo) elements.userDropdownInfo.textContent = user.email || user.username;
        if (elements.adminPanelLink) {
            user.is_admin ? elements.adminPanelLink.classList.remove('hidden') : elements.adminPanelLink.classList.add('hidden');
        }
    } else {
        elements.loginBtn.classList.remove('hidden');
        elements.userMenuLogged && elements.userMenuLogged.classList.add('hidden');
        if (elements.adminPanelLink) elements.adminPanelLink.classList.add('hidden');
    }
}

function openLoginModal() {
    if (!elements.loginModal) return;
    elements.loginModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    // Default to login tab
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.add('hidden'));
    const loginTab = document.getElementById('tabLoginBtn');
    const loginForm = document.getElementById('loginForm');
    if (loginTab) loginTab.classList.add('active');
    if (loginForm) loginForm.classList.remove('hidden');
}

function closeLoginModal() {
    if (!elements.loginModal) return;
    elements.loginModal.classList.add('hidden');
    document.body.style.overflow = '';
    if (elements.loginError) { elements.loginError.textContent = ''; elements.loginError.classList.add('hidden'); }
    if (elements.registerError) { elements.registerError.textContent = ''; elements.registerError.classList.add('hidden'); }
}

async function logoutUser() {
    try {
        if (authToken) await fetch('/api/auth/logout', { method: 'POST', headers: { 'Authorization': `Bearer ${authToken}` } });
    } catch {}
    authToken = null;
    authUser = null;
    localStorage.removeItem('aq_auth_token');
    updateUserUI(null);
    // Reset favorites/tracking for anonymous session
    trackedIds.clear();
    trackingData = {};
    updateTrackCount();
    loadFavoritesFromAPI();
    showToast('Sesión cerrada', 'info');
}

// Auth tab switching
document.addEventListener('click', (e) => {
    const tab = e.target.closest('.auth-tab');
    if (!tab) return;
    const target = tab.dataset.tab;
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === target));
    document.querySelectorAll('.auth-form').forEach(f => {
        const isLogin = f.id === 'loginForm';
        const isRegister = f.id === 'registerForm';
        if (target === 'login') f.classList.toggle('hidden', !isLogin);
        else f.classList.toggle('hidden', !isRegister);
    });
});

// Login modal close on overlay click
document.addEventListener('click', (e) => {
    if (e.target.id === 'loginModalOverlay') closeLoginModal();
});

// Close button
const _closeLoginBtn = document.getElementById('closeLoginModal');
if (_closeLoginBtn) _closeLoginBtn.addEventListener('click', closeLoginModal);

// Login button (anon)
if (elements.loginBtn) {
    elements.loginBtn.addEventListener('click', openLoginModal);
}

// Avatar button - toggle dropdown
if (elements.userAvatarBtn) {
    elements.userAvatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        elements.userDropdown && elements.userDropdown.classList.toggle('hidden');
    });
}
document.addEventListener('click', () => {
    elements.userDropdown && elements.userDropdown.classList.add('hidden');
});

// Logout
if (elements.logoutBtn) {
    elements.logoutBtn.addEventListener('click', (e) => { e.preventDefault(); logoutUser(); });
}

// Login form submit
if (elements.loginForm) {
    elements.loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername')?.value?.trim();
        const password = document.getElementById('loginPassword')?.value;
        if (!username || !password) return;
        const btn = elements.loginForm.querySelector('button[type=submit]');
        if (btn) btn.disabled = true;
        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });
            const data = await res.json();
            if (!res.ok) {
                if (elements.loginError) {
                    elements.loginError.textContent = data.detail || 'Credenciales incorrectas';
                    elements.loginError.classList.remove('hidden');
                }
            } else {
                authToken = data.token;
                authUser = data;
                localStorage.setItem('aq_auth_token', authToken);
                updateUserUI(authUser);
                closeLoginModal();
                loadFavoritesFromAPI();
                loadTrackingData();
                showToast(`Bienvenido, ${data.username}!`, 'success');
            }
        } catch {
            if (elements.loginError) {
                elements.loginError.textContent = 'Error de conexión';
                elements.loginError.classList.remove('hidden');
            }
        } finally {
            if (btn) btn.disabled = false;
        }
    });
}

// Register form submit
if (elements.registerForm) {
    elements.registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('regUsername')?.value?.trim();
        const email = document.getElementById('regEmail')?.value?.trim();
        const password = document.getElementById('regPassword')?.value;
        if (!username || !password) return;
        const btn = elements.registerForm.querySelector('button[type=submit]');
        if (btn) btn.disabled = true;
        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email: email || undefined, password }),
            });
            const data = await res.json();
            if (!res.ok) {
                if (elements.registerError) {
                    elements.registerError.textContent = data.detail || 'Error al registrar';
                    elements.registerError.classList.remove('hidden');
                }
            } else {
                authToken = data.token;
                authUser = data;
                localStorage.setItem('aq_auth_token', authToken);
                updateUserUI(authUser);
                closeLoginModal();
                loadFavoritesFromAPI();
                loadTrackingData();
                showToast(`Cuenta creada. ¡Bienvenido, ${data.username}!`, 'success');
            }
        } catch {
            if (elements.registerError) {
                elements.registerError.textContent = 'Error de conexión';
                elements.registerError.classList.remove('hidden');
            }
        } finally {
            if (btn) btn.disabled = false;
        }
    });
}

// ========== Tracking ==========

async function loadTrackingStages() {
    try {
        const res = await fetch('/api/tracking/stages');
        if (res.ok) trackingStages = await res.json();
    } catch {}
}

async function loadTrackingData() {
    try {
        const params = authToken ? '' : `?session_id=${SESSION_ID}`;
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        const res = await fetch(`/api/tracking${params}`, { headers });
        if (res.ok) {
            const d = await res.json();
            trackingData = d.board || {};
            if (d.stages && d.stages.length) trackingStages = d.stages;
            trackedIds = new Set(Object.values(trackingData).flat().map(e => e.prop_id));
            updateTrackCount();
        }
    } catch {}
}

function updateTrackCount() {
    if (!elements.trackCount) return;
    const n = trackedIds.size;
    elements.trackCount.textContent = n;
    elements.trackCount.classList.toggle('hidden', n === 0);
}

async function addToTracking(propObj, stage) {
    stage = stage || 'interesado';
    try {
        const params = authToken ? '' : `?session_id=${SESSION_ID}`;
        const headers = authToken
            ? { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' }
            : { 'Content-Type': 'application/json' };
        const res = await fetch(`/api/tracking${params}`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ prop_id: propObj.id, prop_data: propObj, stage }),
        });
        if (res.ok) {
            trackedIds.add(propObj.id);
            updateTrackCount();
            updateAllTrackButtons();
            showToast(`Añadido a seguimiento: ${trackingStages.find(s => s.id === stage)?.label || stage}`, 'success');
            if (trackingData[stage]) {
                await loadTrackingData();
            }
        }
    } catch {
        showToast('Error al añadir seguimiento', 'error');
    }
}

async function removeFromTracking(trackingId, propId) {
    try {
        const params = authToken ? '' : `?session_id=${SESSION_ID}`;
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        const res = await fetch(`/api/tracking/${trackingId}${params}`, { method: 'DELETE', headers });
        if (res.ok) {
            if (propId) trackedIds.delete(propId);
            updateTrackCount();
            updateAllTrackButtons();
            await loadTrackingData();
            renderKanbanBoard();
            showToast('Eliminado del seguimiento', 'info');
        }
    } catch {}
}

async function updateTrackingStage(trackingId, stage, notes) {
    try {
        const params = authToken ? '' : `?session_id=${SESSION_ID}`;
        const headers = authToken
            ? { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' }
            : { 'Content-Type': 'application/json' };
        const body = { stage };
        if (notes !== undefined) body.notes = notes;
        await fetch(`/api/tracking/${trackingId}${params}`, { method: 'PATCH', headers, body: JSON.stringify(body) });
        await loadTrackingData();
        renderKanbanBoard();
    } catch {}
}

function updateAllTrackButtons() {
    document.querySelectorAll('.btn-track-card').forEach(btn => {
        const id = btn.dataset.propId;
        const tracked = trackedIds.has(id);
        btn.classList.toggle('active', tracked);
        btn.title = tracked ? 'En seguimiento' : 'Añadir a seguimiento';
    });
}

async function openTrackingPanel() {
    if (!elements.trackingPanel) return;
    // Asegurar que las etapas están cargadas antes de renderizar
    if (!trackingStages.length) await loadTrackingStages();
    await loadTrackingData();
    renderKanbanBoard();
    elements.trackingPanel.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeTrackingPanel() {
    if (!elements.trackingPanel) return;
    elements.trackingPanel.classList.add('hidden');
    document.body.style.overflow = '';
}

function renderKanbanBoard() {
    if (!elements.trackingBoard) return;
    if (!trackingStages.length) {
        elements.trackingBoard.innerHTML = '<p style="color:var(--text-secondary);padding:2rem;">Cargando columnas…</p>';
        return;
    }
    elements.trackingBoard.innerHTML = trackingStages.map(stage => {
        const entries = trackingData[stage.id] || [];
        const stageColor = {
            interesado: '#3b82f6', contactado: '#8b5cf6', visita_programada: '#f59e0b',
            visitado: '#06b6d4', oferta_enviada: '#f97316', negociacion: '#ec4899',
            contrato: '#7c3aed', alquilado: '#10b981', descartado: '#ef4444',
        }[stage.id] || '#6b7280';
        return `
        <div class="kanban-col" data-stage="${stage.id}">
            <div class="kanban-col-header" style="border-top:3px solid ${stageColor}">
                <span class="kanban-col-title">${stage.label}</span>
                <span class="kanban-col-count">${entries.length}</span>
            </div>
            <div class="kanban-col-body">
                ${entries.map(e => createKanbanCard(e)).join('') || '<p class="kanban-empty">Sin propiedades</p>'}
            </div>
        </div>`;
    }).join('');

    // Attach event listeners
    elements.trackingBoard.querySelectorAll('.btn-stage').forEach(btn => {
        btn.addEventListener('click', () => updateTrackingStage(btn.dataset.id, btn.dataset.stage, undefined));
    });
    elements.trackingBoard.querySelectorAll('.btn-stage-remove').forEach(btn => {
        btn.addEventListener('click', () => removeFromTracking(btn.dataset.id, btn.dataset.propId));
    });
    elements.trackingBoard.querySelectorAll('.btn-track-notes').forEach(btn => {
        btn.addEventListener('click', () => {
            const notes = prompt('Notas para esta propiedad:', btn.dataset.notes || '');
            if (notes !== null) updateTrackingStage(btn.dataset.id, btn.dataset.stage, notes);
        });
    });
}

function createKanbanCard(entry) {
    const pd = entry.prop_data || {};
    const title = escapeHtml(pd.title || entry.prop_id);
    const price = pd.price ? `${formatPrice(pd.price)} €/mes` : '';
    const addr = escapeHtml(pd.address || pd.neighborhood || pd.city || '');
    const nextStages = trackingStages.filter(s => s.id !== entry.stage && s.id !== 'descartado');
    const stageButtons = nextStages.slice(0, 3).map(s =>
        `<button class="btn-stage" data-id="${entry.id}" data-stage="${s.id}" title="Mover a ${s.label}">→ ${s.label}</button>`
    ).join('');
    return `
    <div class="kanban-card" data-tracking-id="${entry.id}">
        <div class="kanban-card-title" title="${title}">${title}</div>
        ${price ? `<div class="kanban-card-price">${price}</div>` : ''}
        ${addr ? `<div class="kanban-card-addr"><i class="fas fa-map-marker-alt"></i> ${addr}</div>` : ''}
        ${entry.notes ? `<div class="kanban-card-notes">${escapeHtml(entry.notes)}</div>` : ''}
        <div class="kanban-card-actions">
            <div class="stage-buttons">${stageButtons}</div>
            <div class="kanban-card-footer-btns">
                <button class="btn-track-notes" data-id="${entry.id}" data-stage="${entry.stage}" data-notes="${escapeHtml(entry.notes || '')}" title="Editar notas"><i class="fas fa-sticky-note"></i></button>
                ${pd.url ? `<a href="${escapeHtml(pd.url)}" target="_blank" rel="noopener" class="btn-track-link" title="Ver anuncio"><i class="fas fa-external-link-alt"></i></a>` : ''}
                <button class="btn-stage-remove" data-id="${entry.id}" data-prop-id="${entry.prop_id}" title="Eliminar"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    </div>`;
}

function showStagePicker(propObj, anchorEl) {
    // Remove any existing picker
    document.querySelectorAll('.stage-picker').forEach(p => p.remove());
    if (!trackingStages.length) {
        addToTracking(propObj, 'interesado');
        return;
    }
    const picker = document.createElement('div');
    picker.className = 'stage-picker';
    picker.innerHTML = `
        <div class="stage-picker-title">Añadir a seguimiento</div>
        ${trackingStages.filter(s => s.id !== 'descartado').map(s =>
            `<button class="stage-picker-item" data-stage="${s.id}">${s.label}</button>`
        ).join('')}
    `;
    document.body.appendChild(picker);

    // Position near anchor
    if (anchorEl) {
        const rect = anchorEl.getBoundingClientRect();
        picker.style.position = 'fixed';
        picker.style.top = `${rect.bottom + 4}px`;
        picker.style.left = `${Math.min(rect.left, window.innerWidth - 180)}px`;
        picker.style.zIndex = '9999';
    }

    picker.querySelectorAll('.stage-picker-item').forEach(btn => {
        btn.addEventListener('click', () => {
            addToTracking(propObj, btn.dataset.stage);
            picker.remove();
        });
    });

    // Close on outside click
    setTimeout(() => {
        document.addEventListener('click', function handler(e) {
            if (!picker.contains(e.target)) { picker.remove(); document.removeEventListener('click', handler); }
        });
    }, 0);
}

// Tracking nav link
if (elements.trackingNavLink) {
    elements.trackingNavLink.addEventListener('click', (e) => { e.preventDefault(); openTrackingPanel(); });
}
if (elements.closeTracking) {
    elements.closeTracking.addEventListener('click', closeTrackingPanel);
}
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeTrackingPanel();
        closeLoginModal();
    }
});

// ========== Initialize ==========
document.addEventListener('DOMContentLoaded', () => {
    console.log('AlquiSearch España - v4.0.0');
    initDarkMode();
    initAuth();                    // verifica token guardado
    loadTrackingStages().then(() => loadTrackingData()); // carga pipeline y datos
    loadFavoritesFromAPI();        // carga favoritos desde DB (con fallback a localStorage)
    elements.locationInput.focus();

    const initialCity = elements.locationInput.value.trim();
    if (initialCity) {
        checkCoastalCity(initialCity).then(isCoastal => {
            if (isCoastal) elements.seaViewToggle.classList.remove('hidden');
        });
    }
});

// ========== Map View ==========

const CITY_COORDS = {
    'madrid': [40.4168, -3.7038],
    'barcelona': [41.3874, 2.1686],
    'valencia': [39.4699, -0.3763],
    'sevilla': [37.3891, -5.9845],
    'málaga': [36.7213, -4.4214],
    'malaga': [36.7213, -4.4214],
    'zaragoza': [41.6488, -0.8891],
    'bilbao': [43.2630, -2.9350],
    'alicante': [38.3452, -0.4810],
    'córdoba': [37.8882, -4.7794],
    'cordoba': [37.8882, -4.7794],
    'valladolid': [41.6523, -4.7245],
    'granada': [37.1773, -3.5986],
    'murcia': [37.9922, -1.1307],
    'palma de mallorca': [39.5696, 2.6502],
    'santander': [43.4623, -3.8100],
    'san sebastián': [43.3183, -1.9812],
    'san sebastian': [43.3183, -1.9812],
    'gijón': [43.5322, -5.6611],
    'gijon': [43.5322, -5.6611],
    'vigo': [42.2406, -8.7207],
    'a coruña': [43.3623, -8.4115],
    'a coruna': [43.3623, -8.4115],
    'marbella': [36.5099, -4.8862],
    'cádiz': [36.5271, -6.2886],
    'cadiz': [36.5271, -6.2886],
    'tarragona': [41.1189, 1.2445],
};

function getCityCenter(cityName) {
    const normalized = cityName.toLowerCase().trim();
    return CITY_COORDS[normalized] || [40.0, -3.7];
}

function initMap(properties) {
    if (map) {
        map.remove();
        map = null;
    }

    const isDark = document.body.classList.contains('dark-theme');

    map = L.map('map', {
        zoomControl: true,
        scrollWheelZoom: true,
    });

    const tileUrl = isDark
        ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    const tileAttr = isDark
        ? '&copy; <a href="https://carto.com/">CARTO</a>'
        : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';

    L.tileLayer(tileUrl, {
        attribution: tileAttr,
        maxZoom: 18,
    }).addTo(map);

    markerClusterGroup = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: true,
        zoomToBoundsOnClick: true,
        iconCreateFunction: function(cluster) {
            const count = cluster.getChildCount();
            let size = 'small';
            if (count >= 10) size = 'medium';
            if (count >= 20) size = 'large';
            return L.divIcon({
                html: `<div class="cluster-icon cluster-${size}">${count}</div>`,
                className: 'marker-cluster-custom',
                iconSize: L.point(44, 44),
            });
        },
    });

    const bounds = [];

    properties.forEach((prop, index) => {
        let lat = prop.latitude;
        let lng = prop.longitude;

        if (!lat || !lng) {
            const center = getCityCenter(prop.city || searchParams.location || '');
            const hash = prop.id ? prop.id.charCodeAt(0) + (prop.id.charCodeAt(1) || 0) : index;
            lat = center[0] + ((hash % 100) - 50) * 0.001;
            lng = center[1] + (((hash * 7) % 100) - 50) * 0.001;
        }

        if (lat && lng) {
            const priceStr = formatPrice(prop.price);
            const marker = L.marker([lat, lng], {
                icon: L.divIcon({
                    html: `<div class="price-marker${prop.has_sea_view ? ' sea-view' : ''}">${priceStr}€</div>`,
                    className: 'custom-price-icon',
                    iconSize: [80, 30],
                    iconAnchor: [40, 30],
                }),
            });

            const popupContent = `
                <div class="map-popup">
                    <div class="map-popup-price">${priceStr} €/mes</div>
                    <div class="map-popup-title">${escapeHtml(prop.title)}</div>
                    <div class="map-popup-features">
                        ${prop.bedrooms} hab · ${prop.bathrooms} baños · ${prop.area_m2 > 0 ? prop.area_m2 + ' m²' : '—'}
                        ${prop.has_sea_view ? ' · 🌊 Vista mar' : ''}
                    </div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 6px;">
                        ${escapeHtml(prop.address || prop.neighborhood || prop.city)}
                        · <em>${escapeHtml(prop.platform)}</em>
                    </div>
                    <a href="${escapeHtml(prop.url)}" target="_blank" rel="noopener" class="map-popup-link">
                        Ver anuncio <i class="fas fa-external-link-alt" style="font-size:0.7rem;"></i>
                    </a>
                </div>
            `;

            marker.bindPopup(popupContent);
            markerClusterGroup.addLayer(marker);
            bounds.push([lat, lng]);
        }
    });

    map.addLayer(markerClusterGroup);

    if (bounds.length > 0) {
        if (bounds.length === 1) {
            map.setView(bounds[0], 14);
        } else {
            map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
        }
    } else {
        const center = getCityCenter(searchParams.location || '');
        map.setView(center, 12);
    }
}

// ========== View Toggle ==========
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

    if (currentProperties.length > 0) {
        setTimeout(() => initMap(currentProperties), 100);
    }
});
