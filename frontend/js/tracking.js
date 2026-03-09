/**
 * tracking.js — Pipeline kanban de seguimiento de alquileres
 */

async function loadTrackingStages() {
    try {
        const res = await fetch('/api/tracking/stages');
        if (res.ok) trackingStages = await res.json();
    } catch {}
}

async function loadTrackingData() {
    try {
        const params  = authToken ? '' : `?session_id=${SESSION_ID}`;
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        const res = await fetch(`/api/tracking${params}`, { headers });
        if (res.ok) {
            const d = await res.json();
            trackingData  = d.board || {};
            if (d.stages?.length) trackingStages = d.stages;
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
        const params  = authToken ? '' : `?session_id=${SESSION_ID}`;
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
            showToast(`Añadido: ${trackingStages.find(s => s.id === stage)?.label || stage}`, 'success');
            await loadTrackingData();
        }
    } catch {
        showToast('Error al añadir seguimiento', 'error');
    }
}

async function removeFromTracking(trackingId, propId) {
    try {
        const params  = authToken ? '' : `?session_id=${SESSION_ID}`;
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
        const params  = authToken ? '' : `?session_id=${SESSION_ID}`;
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
        const tracked = trackedIds.has(btn.dataset.propId);
        btn.classList.toggle('active', tracked);
        btn.title = tracked ? 'En seguimiento' : 'Añadir a seguimiento';
    });
}

async function openTrackingPanel() {
    if (!elements.trackingPanel) return;
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

    const stageColors = {
        interesado: '#3b82f6', contactado: '#8b5cf6', visita_programada: '#f59e0b',
        visitado: '#06b6d4', oferta_enviada: '#f97316', negociacion: '#ec4899',
        contrato: '#7c3aed', alquilado: '#10b981', descartado: '#ef4444',
    };

    elements.trackingBoard.innerHTML = trackingStages.map(stage => {
        const entries = trackingData[stage.id] || [];
        const color   = stageColors[stage.id] || '#6b7280';
        return `
        <div class="kanban-col" data-stage="${stage.id}">
            <div class="kanban-col-header" style="border-top:3px solid ${color}">
                <span class="kanban-col-title">${stage.label}</span>
                <span class="kanban-col-count">${entries.length}</span>
            </div>
            <div class="kanban-col-body">
                ${entries.map(e => createKanbanCard(e)).join('') || '<p class="kanban-empty">Sin propiedades</p>'}
            </div>
        </div>`;
    }).join('');

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
    const addr  = escapeHtml(pd.address || pd.neighborhood || pd.city || '');
    const nextStages = trackingStages.filter(s => s.id !== entry.stage && s.id !== 'descartado');
    const stageButtons = nextStages.slice(0, 3).map(s =>
        `<button class="btn-stage" data-id="${entry.id}" data-stage="${s.id}" title="Mover a ${s.label}">→ ${s.label}</button>`
    ).join('');

    return `
    <div class="kanban-card" data-tracking-id="${entry.id}">
        <div class="kanban-card-title" title="${title}">${title}</div>
        ${price ? `<div class="kanban-card-price">${price}</div>` : ''}
        ${addr  ? `<div class="kanban-card-addr"><i class="fas fa-map-marker-alt"></i> ${addr}</div>` : ''}
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
    document.querySelectorAll('.stage-picker').forEach(p => p.remove());

    if (!trackingStages.length) { addToTracking(propObj, 'interesado'); return; }

    const picker = document.createElement('div');
    picker.className = 'stage-picker';
    picker.innerHTML = `
        <div class="stage-picker-title">Añadir a seguimiento</div>
        ${trackingStages.filter(s => s.id !== 'descartado').map(s =>
            `<button class="stage-picker-item" data-stage="${s.id}">${s.label}</button>`
        ).join('')}`;
    document.body.appendChild(picker);

    if (anchorEl) {
        const rect = anchorEl.getBoundingClientRect();
        Object.assign(picker.style, {
            position: 'fixed',
            top:  `${rect.bottom + 4}px`,
            left: `${Math.min(rect.left, window.innerWidth - 180)}px`,
            zIndex: '9999',
        });
    }

    picker.querySelectorAll('.stage-picker-item').forEach(btn => {
        btn.addEventListener('click', () => { addToTracking(propObj, btn.dataset.stage); picker.remove(); });
    });

    setTimeout(() => {
        document.addEventListener('click', function handler(e) {
            if (!picker.contains(e.target)) { picker.remove(); document.removeEventListener('click', handler); }
        });
    }, 0);
}

// ── Event listeners ────────────────────────────────────────────────────────

elements.trackingNavLink?.addEventListener('click', (e) => { e.preventDefault(); openTrackingPanel(); });
elements.closeTracking?.addEventListener('click', closeTrackingPanel);

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeTrackingPanel();
});
