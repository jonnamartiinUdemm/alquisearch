/**
 * state.js — Estado global compartido de la aplicación
 */

// Propiedades
let allProperties = [];        // todos los resultados del servidor
let currentProperties = [];    // filtrados por quick-filters
let searchParams = {};

// Vista
let currentView = 'grid';      // 'grid' | 'map'
let map = null;
let markerClusterGroup = null;

// Paginación
const PAGE_SIZE = 20;
let currentPage = 1;

// Favoritos
let favorites = [];            // IDs
let favoriteProps = [];        // objetos completos

// Sesión anónima persistente
function getOrCreateSessionId() {
    let sid = localStorage.getItem('aq_session');
    if (!sid) {
        sid = 'aq_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 10);
        localStorage.setItem('aq_session', sid);
    }
    return sid;
}
const SESSION_ID = getOrCreateSessionId();

// Auth
let authUser = null;
let authToken = localStorage.getItem('aq_auth_token') || null;

// Tracking
let trackingData  = {};         // { stage: [entry, ...] }
let trackedIds    = new Set();  // prop_ids en seguimiento
let trackingStages = [];        // [{ id, label }] desde API

// Comparador
let compareSet = new Set();
