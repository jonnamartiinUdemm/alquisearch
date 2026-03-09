/**
 * api.js — Todas las llamadas al backend
 */

const API_BASE = '';

async function fetchCities(query) {
    try {
        const res = await fetch(`${API_BASE}/api/cities?q=${encodeURIComponent(query)}`);
        if (!res.ok) throw new Error('Error fetching cities');
        return await res.json();
    } catch { return []; }
}

async function searchProperties(params) {
    const res = await fetch(`${API_BASE}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
}

async function fetchSearchUrls(location) {
    try {
        const res = await fetch(`${API_BASE}/api/search-urls?location=${encodeURIComponent(location)}`);
        if (!res.ok) throw new Error();
        return await res.json();
    } catch { return {}; }
}

async function checkCoastalCity(city) {
    try {
        const res = await fetch(`${API_BASE}/api/is-coastal?city=${encodeURIComponent(city)}`);
        if (!res.ok) return false;
        return (await res.json()).is_coastal;
    } catch { return false; }
}
