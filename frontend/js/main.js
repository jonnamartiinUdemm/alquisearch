/**
 * main.js — Punto de entrada: inicialización al cargar el DOM
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('AlquiSearch España — v4.0.0');

    initDarkMode();
    initAuth();
    loadTrackingStages().then(() => loadTrackingData());
    loadFavoritesFromAPI();
    elements.locationInput.focus();

    const initialCity = elements.locationInput.value.trim();
    if (initialCity) {
        checkCoastalCity(initialCity).then(isCoastal => {
            if (isCoastal) elements.seaViewToggle.classList.remove('hidden');
        });
    }
});
