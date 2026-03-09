/**
 * utils.js — Funciones de utilidad reutilizables
 */

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

function showToast(message, type = 'info', duration = 3000) {
    let toast = document.getElementById('appToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'appToast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.className = `toast-visible toast-${type}`;
    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(() => toast.classList.remove('toast-visible'), duration);
}

// Historial de búsqueda (localStorage)
function getSearchHistory() {
    return JSON.parse(localStorage.getItem('aq_search_history') || '[]');
}
function addToSearchHistory(location) {
    if (!location) return;
    let history = getSearchHistory().filter(h => h !== location);
    history.unshift(location);
    localStorage.setItem('aq_search_history', JSON.stringify(history.slice(0, 6)));
}
