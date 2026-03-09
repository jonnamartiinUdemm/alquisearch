/**
 * search.js — Búsqueda, filtros, sugerencias, quick-filters y paginación
 */

// ── Sugerencias de ciudad ─────────────────────────────────────────────────

let suggestionsTimeout = null;

function showSuggestions(cities, historyItems) {
    const dropdown = elements.citySuggestions;
    const items = [];

    (historyItems || []).forEach(h => {
        items.push(`<div class="suggestion-item suggestion-history" data-city="${h}">
            <i class="fas fa-history"></i> ${h}
        </div>`);
    });

    (cities || []).forEach(city => {
        if (!items.some(i => i.includes(`data-city="${city}"`))) {
            const icon = city.includes(',') ? 'fa-building' : 'fa-city';
            items.push(`<div class="suggestion-item" data-city="${city}">
                <i class="fas ${icon}"></i> ${city}
            </div>`);
        }
    });

    if (!items.length) { dropdown.classList.add('hidden'); return; }

    dropdown.innerHTML = items.join('');
    dropdown.classList.remove('hidden');

    dropdown.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', async () => {
            elements.locationInput.value = item.dataset.city;
            dropdown.classList.add('hidden');
            const isCoastal = await checkCoastalCity(item.dataset.city);
            elements.seaViewToggle.classList.toggle('hidden', !isCoastal);
            if (!isCoastal) elements.seaView.checked = false;
        });
    });
}

elements.locationInput.addEventListener('input', (e) => {
    clearTimeout(suggestionsTimeout);
    const query = e.target.value.trim();
    if (query.length < 2) {
        const history = getSearchHistory();
        history.length ? showSuggestions([], history) : elements.citySuggestions.classList.add('hidden');
        return;
    }
    suggestionsTimeout = setTimeout(async () => {
        showSuggestions(await fetchCities(query), []);
    }, 200);
});

elements.locationInput.addEventListener('focus', async () => {
    const query = elements.locationInput.value.trim();
    if (query.length >= 2) showSuggestions(await fetchCities(query), []);
    else { const h = getSearchHistory(); if (h.length) showSuggestions([], h); }
});

elements.locationInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { elements.citySuggestions.classList.add('hidden'); performSearch(); }
});

document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-input-wrapper')) elements.citySuggestions.classList.add('hidden');
});

// ── Toggle filtros ────────────────────────────────────────────────────────

elements.toggleFilters.addEventListener('click', () => {
    elements.filtersPanel.classList.toggle('hidden');
    elements.toggleFilters.classList.toggle('active');
});

// ── Limpiar / compartir filtros ──────────────────────────────────────────

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

function copyShareableUrl() {
    const params = getSearchParams();
    const base = window.location.origin + window.location.pathname;
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
        if (v !== null && v !== undefined && v !== '' && v !== false)
            qs.set(k, Array.isArray(v) ? v.join(',') : String(v));
    });
    navigator.clipboard.writeText(`${base}?${qs}`).then(
        () => showToast('URL copiada al portapapeles ✅'),
        () => prompt('Copia esta URL:', `${base}?${qs}`),
    );
}

if (elements.clearFiltersBtn) elements.clearFiltersBtn.addEventListener('click', clearFilters);
if (elements.shareUrlBtn) elements.shareUrlBtn.addEventListener('click', copyShareableUrl);

// ── Parámetros de búsqueda ────────────────────────────────────────────────

function getSearchParams() {
    const platforms = Array.from(document.querySelectorAll('input[name="platform"]:checked')).map(cb => cb.value);
    const params = {
        location:       elements.locationInput.value.trim(),
        max_price:      parseFloat(elements.maxPrice.value) || 2800,
        min_bedrooms:   parseInt(elements.minBedrooms.value) || 2,
        min_bathrooms:  parseInt(elements.minBathrooms.value) || 2,
        available_from: elements.availableFrom.value || '2026-10-01',
        pets_allowed:   elements.petsAllowed.checked,
        strict_pets:    elements.strictPets ? elements.strictPets.checked : false,
        need_elevator:  elements.needElevator.checked,
        prefer_terrace: elements.preferTerrace.checked,
        prefer_balcony: elements.preferBalcony.checked,
        prefer_transport: elements.preferTransport.checked,
        prefer_services:  elements.preferServices.checked,
        long_stay:        elements.longStay.checked,
        sea_view:         elements.seaView.checked || null,
        platforms,
    };
    const minArea = parseFloat(elements.minArea.value);
    if (minArea > 0) params.min_area = minArea;
    const maxArea = parseFloat(elements.maxArea.value);
    if (maxArea > 0) params.max_area = maxArea;
    const propType = elements.propertyType.value;
    if (propType) params.property_type = propType;
    return params;
}

// ── Ejecución de búsqueda ────────────────────────────────────────────────

async function performSearch() {
    const params = getSearchParams();
    if (!params.location) {
        elements.locationInput.focus();
        elements.locationInput.style.outline = '2px solid #ef4444';
        setTimeout(() => elements.locationInput.style.outline = '', 2000);
        return;
    }

    searchParams = params;
    addToSearchHistory(params.location);
    currentPage = 1;
    compareSet.clear();
    updateCompareUI();

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
        if (result.errors?.length) showPlatformErrors(result.errors);

        allProperties = result.properties || [];
        currentProperties = [...allProperties];
        elements.resultsTitle.textContent = `${result.total} propiedades en ${params.location}`;
        elements.resultsSubtitle.textContent =
            `Buscado en: ${result.platforms_searched.join(', ')} · Precio máx: ${params.max_price}€ · ${params.min_bedrooms}+ hab`;

        if (currentProperties.length > 0) { setupQuickFilters(); renderCurrentPage(); }
        else elements.emptyState.classList.remove('hidden');

    } catch {
        elements.loadingState.classList.add('hidden');
        elements.emptyState.classList.remove('hidden');
        elements.emptyState.querySelector('h3').textContent = 'Error en la búsqueda';
        elements.emptyState.querySelector('p').textContent = 'No se pudo completar. Verifica tu conexión.';
    }
}

elements.searchBtn.addEventListener('click', performSearch);

// ── Links directos / errores de plataforma ───────────────────────────────

function showDirectLinks(urls) {
    if (!urls || !Object.keys(urls).length) return;
    const icons = { idealista: 'fa-building', fotocasa: 'fa-camera', habitaclia: 'fa-house-user', 'pisos.com': 'fa-home', housinganywhere: 'fa-globe' };
    elements.directLinksGrid.innerHTML = Object.entries(urls).map(([name, url]) =>
        `<a href="${url}" target="_blank" rel="noopener noreferrer" class="direct-link">
            <i class="fas ${icons[name] || 'fa-link'}"></i>
            ${name.charAt(0).toUpperCase() + name.slice(1)}
            <i class="fas fa-external-link-alt" style="margin-left:auto;font-size:.75rem;opacity:.5;"></i>
        </a>`
    ).join('');
    elements.directLinks.classList.remove('hidden');
}

function showPlatformErrors(errors) {
    elements.platformErrors.innerHTML = errors.map(err =>
        `<div class="platform-error"><i class="fas fa-exclamation-triangle"></i> ${err}</div>`
    ).join('');
    elements.platformErrors.classList.remove('hidden');
}

// ── Quick Filters (client-side) ──────────────────────────────────────────

function setupQuickFilters() {
    if (!allProperties.length) return;
    const prices = allProperties.map(p => p.price).filter(p => p > 0);
    const areas  = allProperties.map(p => p.area_m2).filter(a => a > 0);
    const [minP, maxP] = [Math.floor(Math.min(...prices, 0)), Math.ceil(Math.max(...prices, 10000))];
    const [minA, maxA] = [Math.floor(Math.min(...areas, 0)),  Math.ceil(Math.max(...areas, 500))];

    elements.qfPriceMin.min = minP; elements.qfPriceMin.max = maxP; elements.qfPriceMin.value = minP;
    elements.qfPriceMax.min = minP; elements.qfPriceMax.max = maxP; elements.qfPriceMax.value = maxP;
    elements.qfAreaMin.min  = minA; elements.qfAreaMin.max  = maxA; elements.qfAreaMin.value  = minA;
    elements.qfAreaMax.min  = minA; elements.qfAreaMax.max  = maxA; elements.qfAreaMax.value  = maxA;
    updateQuickFilterLabels();
    elements.quickFilters.classList.remove('hidden');
}

function updateQuickFilterLabels() {
    elements.qfPriceLabel.textContent = `${elements.qfPriceMin.value} – ${elements.qfPriceMax.value}€`;
    elements.qfAreaLabel.textContent  = `${elements.qfAreaMin.value} – ${elements.qfAreaMax.value} m²`;
}

function applyQuickFilters() {
    const [pMin, pMax, aMin, aMax] = [
        parseFloat(elements.qfPriceMin.value), parseFloat(elements.qfPriceMax.value),
        parseFloat(elements.qfAreaMin.value),  parseFloat(elements.qfAreaMax.value),
    ];
    currentProperties = allProperties.filter(p =>
        !(p.price > 0 && (p.price < pMin || p.price > pMax)) &&
        !(p.area_m2 > 0 && (p.area_m2 < aMin || p.area_m2 > aMax))
    );
    currentPage = 1;
    updateQuickFilterLabels();
    renderCurrentPage();
}

[elements.qfPriceMin, elements.qfPriceMax, elements.qfAreaMin, elements.qfAreaMax].forEach(el => {
    el.addEventListener('input', applyQuickFilters);
});

// ── Paginación ────────────────────────────────────────────────────────────

function getTotalPages() { return Math.max(1, Math.ceil(currentProperties.length / PAGE_SIZE)); }
function getPageSlice()   { return currentProperties.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE); }

function renderCurrentPage() {
    const totalPages = getTotalPages();
    const pageItems  = getPageSlice();

    if (pageItems.length) {
        renderProperties(pageItems);
        elements.emptyState.classList.add('hidden');
    } else {
        elements.resultsGrid.innerHTML = '';
        elements.emptyState.classList.remove('hidden');
    }

    if (currentProperties.length > PAGE_SIZE) {
        elements.pagination.classList.remove('hidden');
        elements.prevPage.disabled = currentPage <= 1;
        elements.nextPage.disabled = currentPage >= totalPages;
        elements.pageInfo.textContent = `Página ${currentPage} de ${totalPages} (${currentProperties.length} props.)`;
    } else {
        elements.pagination.classList.add('hidden');
    }
    elements.resultsTitle.textContent = `${currentProperties.length} propiedades en ${searchParams.location || ''}`;
}

elements.prevPage.addEventListener('click', () => {
    if (currentPage > 1) { currentPage--; renderCurrentPage(); elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
});
elements.nextPage.addEventListener('click', () => {
    if (currentPage < getTotalPages()) { currentPage++; renderCurrentPage(); elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
});
