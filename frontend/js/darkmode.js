/**
 * darkmode.js — Tema claro/oscuro
 */

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
    elements.darkModeToggle.innerHTML = isDark
        ? '<i class="fas fa-sun"></i>'
        : '<i class="fas fa-moon"></i>';

    // Reiniciar mapa si está visible (el tema cambia los tiles)
    if (currentView === 'map' && currentProperties.length > 0) {
        setTimeout(() => initMap(currentProperties), 100);
    }
});
