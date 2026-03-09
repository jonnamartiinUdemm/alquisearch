/**
 * compare.js — Comparador de propiedades
 */

function toggleCompare(propId) {
    if (compareSet.has(propId)) {
        compareSet.delete(propId);
    } else {
        if (compareSet.size >= 4) { alert('Máximo 4 propiedades para comparar'); return; }
        compareSet.add(propId);
    }
    updateCompareUI();
    document.querySelectorAll(`.btn-compare-card[data-prop-id="${propId}"]`).forEach(btn => {
        btn.classList.toggle('active', compareSet.has(propId));
    });
}

function updateCompareUI() {
    elements.compareCount.textContent = compareSet.size;
    elements.compareBtn.classList.toggle('hidden', compareSet.size < 2);
}

function openCompareModal() {
    const props = [...compareSet].map(id => allProperties.find(p => p.id === id)).filter(Boolean);
    if (props.length < 2) return;

    const rows = [
        { label: 'Precio',        fn: p => `${formatPrice(p.price)} €/mes` },
        { label: 'Habitaciones',  fn: p => p.bedrooms },
        { label: 'Baños',         fn: p => p.bathrooms },
        { label: 'Superficie',    fn: p => p.area_m2 > 0 ? `${p.area_m2} m²` : '—' },
        { label: 'Planta',        fn: p => p.floor || '—' },
        { label: 'Ascensor',      fn: p => p.has_elevator ? '✓' : '✗' },
        { label: 'Mascotas',      fn: p => p.pets_allowed ? '✓' : p.pets_allowed === false ? '✗' : '?' },
        { label: 'Terraza',       fn: p => p.has_terrace ? '✓' : '✗' },
        { label: 'Balcón',        fn: p => p.has_balcony ? '✓' : '✗' },
        { label: 'A/C',           fn: p => p.has_air_conditioning ? '✓' : '✗' },
        { label: 'Calefacción',   fn: p => p.has_heating ? '✓' : '✗' },
        { label: 'Parking',       fn: p => p.has_parking ? '✓' : '✗' },
        { label: 'Piscina',       fn: p => p.has_pool ? '✓' : '✗' },
        { label: 'Puntuación',    fn: p => Math.round(p.score) },
        { label: 'Plataforma',    fn: p => p.platform },
    ];

    const colWidth = Math.floor(100 / (props.length + 1));

    let html = `<table class="compare-table">
        <thead><tr>
            <th style="width:${colWidth}%">Característica</th>
            ${props.map(p => `<th style="width:${colWidth}%">${escapeHtml(p.title.slice(0, 40))}</th>`).join('')}
        </tr></thead><tbody>`;

    for (const row of rows) {
        html += `<tr><td class="compare-label">${row.label}</td>${props.map(p => `<td>${row.fn(p)}</td>`).join('')}</tr>`;
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
