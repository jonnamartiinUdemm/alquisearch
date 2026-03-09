/**
 * auth.js — Autenticación y gestión de sesión de usuario
 */

function _authHeaders() {
    return authToken
        ? { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' }
        : { 'Content-Type': 'application/json' };
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
        elements.userMenuLogged?.classList.remove('hidden');
        if (elements.userDisplayName) elements.userDisplayName.textContent = user.username;
        if (elements.userDropdownInfo)  elements.userDropdownInfo.textContent  = user.email || user.username;
        if (elements.adminPanelLink) {
            elements.adminPanelLink.classList.toggle('hidden', !user.is_admin);
        }
    } else {
        elements.loginBtn.classList.remove('hidden');
        elements.userMenuLogged?.classList.add('hidden');
        elements.adminPanelLink?.classList.add('hidden');
    }
}

function openLoginModal() {
    if (!elements.loginModal) return;
    elements.loginModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.add('hidden'));
    document.getElementById('tabLoginBtn')?.classList.add('active');
    document.getElementById('loginForm')?.classList.remove('hidden');
}

function closeLoginModal() {
    if (!elements.loginModal) return;
    elements.loginModal.classList.add('hidden');
    document.body.style.overflow = '';
    if (elements.loginError)    { elements.loginError.textContent = '';    elements.loginError.classList.add('hidden'); }
    if (elements.registerError) { elements.registerError.textContent = ''; elements.registerError.classList.add('hidden'); }
}

async function logoutUser() {
    try {
        if (authToken) await fetch('/api/auth/logout', { method: 'POST', headers: { 'Authorization': `Bearer ${authToken}` } });
    } catch {}
    authToken = null;
    authUser  = null;
    localStorage.removeItem('aq_auth_token');
    updateUserUI(null);
    trackedIds.clear();
    trackingData = {};
    updateTrackCount();
    loadFavoritesFromAPI();
    showToast('Sesión cerrada', 'info');
}

// ── Auth tab switching ─────────────────────────────────────────────────────

document.addEventListener('click', (e) => {
    const tab = e.target.closest('.auth-tab');
    if (!tab) return;
    const target = tab.dataset.tab;
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === target));
    document.querySelectorAll('.auth-form').forEach(f => {
        if (target === 'login')    f.classList.toggle('hidden', f.id !== 'loginForm');
        else                        f.classList.toggle('hidden', f.id !== 'registerForm');
    });
});

// ── Overlay y cierre ──────────────────────────────────────────────────────

document.addEventListener('click', (e) => {
    if (e.target.id === 'loginModalOverlay') closeLoginModal();
});

document.getElementById('closeLoginModal')?.addEventListener('click', closeLoginModal);

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeLoginModal();
});

// ── Botones de cabecera ───────────────────────────────────────────────────

elements.loginBtn?.addEventListener('click', openLoginModal);

elements.userAvatarBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    elements.userDropdown?.classList.toggle('hidden');
});

document.addEventListener('click', () => {
    elements.userDropdown?.classList.add('hidden');
});

elements.logoutBtn?.addEventListener('click', (e) => { e.preventDefault(); logoutUser(); });

// ── Login form ────────────────────────────────────────────────────────────

elements.loginForm?.addEventListener('submit', async (e) => {
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
            authUser  = data;
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

// ── Register form ─────────────────────────────────────────────────────────

elements.registerForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('regUsername')?.value?.trim();
    const email    = document.getElementById('regEmail')?.value?.trim();
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
            authUser  = data;
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
