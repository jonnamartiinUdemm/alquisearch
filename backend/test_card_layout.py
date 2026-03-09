"""
tests/test_card_layout.py
=========================
Garantías de no-solapamiento para la UI de tarjetas y filtros de mascotas.

Cubre tres dimensiones:
  1. CSS: comprueba que los selectores clave tienen las propiedades correctas
     para que los elementos nunca se superpongan.
  2. JS HTML: valida que createPropertyCard() genera el marcado esperado
     (wrapper .card-actions, atributos aria-label, etc.).
  3. Backend: verifica el filtro pets_allowed en modo normal y estricto.
"""

import re
import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).parent.parent
CSS_PATH = ROOT / "frontend" / "styles.css"
JS_PATH  = ROOT / "frontend" / "app.js"

sys.path.insert(0, str(pathlib.Path(__file__).parent))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_rule(css: str, selector: str) -> str:
    """Devuelve el bloque de propiedades CSS del primer selector que coincida."""
    # Escapa caracteres especiales para regex
    escaped = re.escape(selector)
    pattern = rf"{escaped}\s*\{{([^}}]*)\}}"
    m = re.search(pattern, css, re.DOTALL)
    if not m:
        raise AssertionError(f"Selector no encontrado en CSS: {selector!r}")
    return m.group(1)


def _has_prop(block: str, prop: str, value: str) -> bool:
    """Comprueba que un bloque CSS contiene 'prop: value' (insensible a espacios)."""
    pattern = rf"{re.escape(prop)}\s*:\s*{re.escape(value)}"
    return bool(re.search(pattern, block))


def _prop_value(block: str, prop: str) -> str | None:
    """Devuelve el valor de una propiedad CSS en un bloque."""
    m = re.search(rf"{re.escape(prop)}\s*:\s*([^;]+);", block)
    return m.group(1).strip() if m else None


# ---------------------------------------------------------------------------
# Cargar ficheros
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def js() -> str:
    return JS_PATH.read_text(encoding="utf-8")


# ===========================================================================
# 1. CSS: Garantías anti-solapamiento
# ===========================================================================

class TestCSSNoOverlap:

    def test_card_actions_is_absolute_top_right(self, css):
        """.card-actions debe ser position:absolute en top-right."""
        block = _extract_rule(css, ".card-actions")
        assert _has_prop(block, "position", "absolute"), \
            ".card-actions debe tener position: absolute"
        assert _has_prop(block, "top", "8px"), \
            ".card-actions debe estar a top: 8px"
        assert _has_prop(block, "right", "8px"), \
            ".card-actions debe estar a right: 8px"

    def test_card_actions_flex_column(self, css):
        """.card-actions agrupa los botones verticalmente para no solapar badges."""
        block = _extract_rule(css, ".card-actions")
        assert _has_prop(block, "flex-direction", "column"), \
            ".card-actions debe usar flex-direction: column"

    def test_card_actions_z_index_above_badges(self, css):
        """.card-actions tiene z-index > 1 (mayor que .property-card-badges)."""
        block = _extract_rule(css, ".card-actions")
        z = _prop_value(block, "z-index")
        assert z is not None, ".card-actions debe tener z-index"
        assert int(z) >= 2, f".card-actions z-index debe ser >=2, es {z}"

    def test_badges_has_right_constraint(self, css):
        """.property-card-badges debe tener right: definido para no invadir la zona de botones."""
        block = _extract_rule(css, ".property-card-badges")
        right_val = _prop_value(block, "right")
        assert right_val is not None, \
            ".property-card-badges debe tener propiedad 'right' para evitar solapamiento"
        # Debe ser al menos 40px para separarse de los botones (34px + 8px margen)
        numeric = int(re.sub(r"[^0-9]", "", right_val) or "0")
        assert numeric >= 40, \
            f".property-card-badges right debe ser >=40px (es {right_val})"

    def test_badges_max_width_set(self, css):
        """.property-card-badges debe tener max-width para no desbordarse."""
        block = _extract_rule(css, ".property-card-badges")
        assert _prop_value(block, "max-width") is not None, \
            ".property-card-badges debe tener max-width"

    def test_score_is_bottom_left(self, css):
        """.property-card-score debe estar en la esquina inferior-izquierda (no top-right)."""
        block = _extract_rule(css, ".property-card-score")
        assert _has_prop(block, "bottom", "8px"), \
            ".property-card-score debe estar en bottom: 8px"
        assert _has_prop(block, "left", "8px"), \
            ".property-card-score debe estar en left: 8px (no en right, para no solapar botones)"
        # Asegura que NO tiene top ni right (que causarían solapamiento)
        assert _prop_value(block, "top") is None, \
            ".property-card-score NO debe tener 'top' — iría encima de los botones de acción"

    def test_btn_fav_no_absolute_position(self, css):
        """btn-fav y btn-compare-card NO deben tener position:absolute propia.
        Su posición la hereda de .card-actions."""
        # El bloque combinado .btn-fav, .btn-compare-card
        # Buscamos que no aparezca position:absolute en los bloques individuales
        individual_fav = re.search(
            r"\.btn-fav\s*\{([^}]*)\}", css, re.DOTALL
        )
        if individual_fav:
            block = individual_fav.group(1)
            assert not _has_prop(block, "position", "absolute"), \
                ".btn-fav NO debe tener position:absolute propia (la hereda de .card-actions)"

    def test_btn_compare_card_no_top_right(self, css):
        """btn-compare-card no debe tener top/right propios que lo alejen del flujo de .card-actions."""
        individual = re.search(
            r"\.btn-compare-card\s*\{([^}]*)\}", css, re.DOTALL
        )
        if individual:
            block = individual.group(1)
            assert not _has_prop(block, "position", "absolute"), \
                ".btn-compare-card NO debe tener position:absolute propia"
            # No debe tener top: XYpx que lo desplace fuera del flex container
            assert _prop_value(block, "top") is None, \
                ".btn-compare-card no debe definir top (se posiciona por flex-direction:column)"


# ===========================================================================
# 2. JS HTML: Garantías de marcado en createPropertyCard
# ===========================================================================

class TestJSCardMarkup:

    def test_card_actions_wrapper_present(self, js):
        """createPropertyCard() debe generar un div.card-actions que envuelva los botones."""
        assert 'class="card-actions"' in js, \
            "app.js debe generar <div class=\"card-actions\"> en createPropertyCard()"

    def test_btn_fav_inside_card_actions(self, js):
        """btn-fav debe aparecer DESPUÉS de card-actions (dentro del bloque)."""
        idx_actions = js.index('class="card-actions"')
        idx_fav     = js.index('class="btn-fav', idx_actions)
        assert idx_fav > idx_actions, \
            "btn-fav debe estar dentro del bloque .card-actions"

    def test_btn_compare_inside_card_actions(self, js):
        """btn-compare-card debe aparecer DESPUÉS de card-actions (dentro del bloque)."""
        idx_actions  = js.index('class="card-actions"')
        idx_compare  = js.index('class="btn-compare-card', idx_actions)
        assert idx_compare > idx_actions, \
            "btn-compare-card debe estar dentro del bloque .card-actions"

    def test_btn_fav_has_aria_label(self, js):
        """Los botones de favorito deben tener aria-label para accesibilidad."""
        assert 'aria-label=' in js, \
            "btn-fav debe incluir aria-label"

    def test_score_in_correct_div(self, js):
        """property-card-score debe estar dentro de property-card-image."""
        card_image_start = js.index('class="property-card-image"')
        card_image_end   = js.index('class="property-card-body"', card_image_start)
        # El div ahora tiene clase dinámica: "property-card-score ${scoreClass}"
        score_idx = js.index('property-card-score', card_image_start)
        assert card_image_start < score_idx < card_image_end, \
            "property-card-score debe estar dentro de property-card-image, no en el body"

    def test_score_has_dynamic_class(self, js):
        """El score debe tener una clase dinámica para colorear por calidad."""
        assert 'scoreClass' in js or 'score-excellent' in js, \
            "El score debe tener variantes de color (score-excellent, score-good, score-normal)"

    def test_badge_overflow_protection(self, js):
        """Debe existir MAX_VISIBLE_BADGES para limitar el número de badges visibles."""
        assert 'MAX_VISIBLE_BADGES' in js, \
            "createPropertyCard() debe definir MAX_VISIBLE_BADGES para evitar overflow visual"

    def test_badge_more_generated(self, js):
        """Debe generarse un badge '+N' cuando las badges excedan el máximo."""
        assert 'badge-more' in js, \
            "Debe generarse un badge badge-more para indicar badges ocultas"

    def test_pets_unknown_badge_exists(self, js):
        """El badge badge-pets-unknown debe estar implementado para mascotas no confirmadas."""
        assert 'badge-pets-unknown' in js, \
            "Debe existir lógica para mostrar badge-pets-unknown cuando pets_allowed es null"

    def test_strict_pets_sent_in_params(self, js):
        """getSearchParams() debe incluir strict_pets al construir los parámetros de búsqueda."""
        assert 'strict_pets' in js, \
            "getSearchParams() debe enviar strict_pets al backend"


# ===========================================================================
# 3. Backend: Filtro de mascotas — modo normal y estricto
# ===========================================================================

from models import Property, SearchParams


def _make_prop(**kwargs) -> Property:
    defaults = dict(
        id="test-1", title="Test", platform="test", price=1500,
        address="Calle Test 1", city="Madrid", bedrooms=2, bathrooms=1,
        area_m2=70, score=50, images=[], url="http://example.com",
        latitude=40.4, longitude=-3.7,
    )
    defaults.update(kwargs)
    return Property(**defaults)


def _make_params(**kwargs) -> SearchParams:
    defaults = dict(location="Madrid", max_price=3000, min_bedrooms=1, min_bathrooms=1)
    defaults.update(kwargs)
    return SearchParams(**defaults)


class TestPetsFilter:

    def test_explicit_false_always_excluded_in_normal_mode(self):
        """pets_allowed=False siempre filtra en modo normal."""
        from filters import filter_properties
        prop = _make_prop(id="p1", pets_allowed=False)
        params = _make_params(pets_allowed=True, strict_pets=False)
        result = filter_properties([prop], params)
        assert len(result) == 0, \
            "Propiedad con pets_allowed=False debe excluirse cuando el usuario quiere mascotas"

    def test_unknown_passes_in_normal_mode(self):
        """pets_allowed=None pasa el filtro en modo normal (solo penalización en score)."""
        from filters import filter_properties
        prop = _make_prop(id="p2", pets_allowed=None)
        params = _make_params(pets_allowed=True, strict_pets=False)
        result = filter_properties([prop], params)
        assert len(result) == 1, \
            "Propiedad con pets_allowed=None debe PASAR en modo normal"

    def test_unknown_excluded_in_strict_mode(self):
        """pets_allowed=None se excluye en modo estricto."""
        from filters import filter_properties
        prop = _make_prop(id="p3", pets_allowed=None)
        params = _make_params(pets_allowed=True, strict_pets=True)
        result = filter_properties([prop], params)
        assert len(result) == 0, \
            "Propiedad con pets_allowed=None debe excluirse en modo estricto"

    def test_confirmed_true_passes_always(self):
        """pets_allowed=True pasa en cualquier modo."""
        from filters import filter_properties
        prop = _make_prop(id="p4", pets_allowed=True)
        for strict in (False, True):
            result = filter_properties([prop], _make_params(pets_allowed=True, strict_pets=strict))
            assert len(result) == 1, \
                f"pets_allowed=True debe pasar siempre (strict={strict})"

    def test_no_pets_filter_includes_all(self):
        """Si pets_allowed=False en params, no filtra por mascotas."""
        from filters import filter_properties
        props = [
            _make_prop(id="a", pets_allowed=True),
            _make_prop(id="b", pets_allowed=False),
            _make_prop(id="c", pets_allowed=None),
        ]
        params = _make_params(pets_allowed=False, strict_pets=False)
        result = filter_properties(props, params)
        ids = {p.id for p in result}
        assert "a" in ids and "b" in ids and "c" in ids, \
            "Sin filtro de mascotas se deben incluir todos los tipos"

    def test_unknown_gets_score_penalty_in_normal_mode(self):
        """En modo normal, pets_allowed=None recibe penalización de score vs pets_allowed=True."""
        from filters import calculate_preference_score
        p_true = _make_prop(id="s1", pets_allowed=True)
        p_none = _make_prop(id="s2", pets_allowed=None)
        params = _make_params(pets_allowed=True, strict_pets=False)
        score_true = calculate_preference_score(p_true, params)
        score_none = calculate_preference_score(p_none, params)
        assert score_true > score_none, \
            "pets_allowed=True debe tener mayor score que pets_allowed=None"

    def test_strict_pets_field_in_model(self):
        """SearchParams debe tener campo strict_pets con valor por defecto False."""
        p = SearchParams(location="Barcelona")
        assert hasattr(p, "strict_pets"), "SearchParams debe tener campo strict_pets"
        assert p.strict_pets is False, "strict_pets debe ser False por defecto"


# ===========================================================================
# 4. CSS: Garantías adicionales de colores y accesibilidad
# ===========================================================================

class TestCSSAccessibility:

    def test_badge_pets_unknown_color_defined(self, css):
        """El badge de mascotas desconocidas debe tener un color distintivo (naranja)."""
        block = _extract_rule(css, ".badge-pets-unknown")
        bg = _prop_value(block, "background")
        assert bg is not None, ".badge-pets-unknown debe tener background definido"

    def test_toast_defined(self, css):
        """El sistema de toast debe estar definido en CSS."""
        assert "#appToast" in css, "El toast #appToast debe tener estilos en CSS"

    def test_dark_theme_card_actions(self, css):
        """Los botones de acción deben tener estilos para dark mode."""
        assert ".dark-theme .btn-fav" in css or ".dark-theme .btn-compare-card" in css, \
            "Los botones de acción deben tener overrides para .dark-theme"
