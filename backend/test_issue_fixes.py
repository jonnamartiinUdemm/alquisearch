"""
Tests de regresión para los issues #1-#4 de GitHub.
Ejecutar con: cd backend && python3 test_issue_fixes.py

Issue #1: Enlaces a HousingAnywhere no funcionan
Issue #2: Enlaces a Habitaclia no funcionan
Issue #3: Filtro por sitio no funciona
Issue #4: No se pueden ordenar los resultados
"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))

from models import Property, SearchParams
from scrapers.housinganywhere import HousingAnywhereScraper
from scrapers.habitaclia import HabitacliaScraper
from config import SCRAPERS


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def assert_true(self, condition, test_name):
        if condition:
            self.passed += 1
            print(f"  ✓ {test_name}")
        else:
            self.failed += 1
            self.errors.append(test_name)
            print(f"  ✗ {test_name}")

    def assert_equal(self, actual, expected, test_name):
        if actual == expected:
            self.passed += 1
            print(f"  ✓ {test_name}")
        else:
            self.failed += 1
            self.errors.append(f"{test_name} (esperado: {expected!r}, obtenido: {actual!r})")
            print(f"  ✗ {test_name} (esperado: {expected!r}, obtenido: {actual!r})")

    def assert_in(self, substring, string, test_name):
        if substring in string:
            self.passed += 1
            print(f"  ✓ {test_name}")
        else:
            self.failed += 1
            self.errors.append(f"{test_name} ({substring!r} no está en {string!r})")
            print(f"  ✗ {test_name} ({substring!r} no está en {string!r})")

    def assert_not_in(self, substring, string, test_name):
        if substring not in string:
            self.passed += 1
            print(f"  ✓ {test_name}")
        else:
            self.failed += 1
            self.errors.append(f"{test_name} ({substring!r} NO debería estar en {string!r})")
            print(f"  ✗ {test_name} ({substring!r} NO debería estar en {string!r})")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Resultados: {self.passed}/{total} tests pasados")
        if self.errors:
            print("Fallos:")
            for e in self.errors:
                print(f"  - {e}")
        print(f"{'='*60}")
        return self.failed == 0


# ════════════════════════════════════════════════════════════
# Issue #1: Enlaces a HousingAnywhere no funcionan
# ════════════════════════════════════════════════════════════

def test_issue_1_housinganywhere_urls(t: TestRunner):
    """
    HousingAnywhere generaba URLs con parámetros inválidos (petsAllowed, bedrooms)
    que provocaban que la página no mostrara resultados.
    La URL corregida solo debe incluir categories y priceMax.
    """
    print("\n── Issue #1: Enlaces a HousingAnywhere ──")

    scraper = HousingAnywhereScraper()
    params = SearchParams(
        location="madrid",
        max_price=2250,
        min_bedrooms=3,
        pets_allowed=True,
    )
    url = scraper.get_direct_search_url(params)

    # Debe contener la base correcta
    t.assert_in("housinganywhere.com/s/Madrid--Spain", url,
                "URL contiene path correcto para Madrid")

    # Debe contener categories=apartment
    t.assert_in("categories=apartment", url,
                "URL incluye categories=apartment")

    # Debe contener priceMax
    t.assert_in("priceMax=2250", url,
                "URL incluye priceMax=2250")

    # NO debe contener petsAllowed (parámetro no reconocido por HA)
    t.assert_not_in("petsAllowed", url,
                    "URL NO contiene petsAllowed (parámetro inválido)")

    # NO debe contener bedrooms (parámetro no reconocido por HA)
    t.assert_not_in("bedrooms", url,
                    "URL NO contiene bedrooms (parámetro inválido)")

    # Prueba con long_stay activado
    params_long = SearchParams(
        location="barcelona",
        max_price=1500,
        long_stay=True,
    )
    url_long = scraper.get_direct_search_url(params_long)
    t.assert_in("minDuration=6", url_long,
                "URL con long_stay incluye minDuration=6")
    t.assert_in("Barcelona--Spain", url_long,
                "URL contiene slug correcto para Barcelona")

    # Prueba con ciudad no mapeada
    params_unknown = SearchParams(location="Cuenca")
    url_unknown = scraper.get_direct_search_url(params_unknown)
    t.assert_in("housinganywhere.com/s/Cuenca--Spain", url_unknown,
                "Ciudad no mapeada genera slug genérico correcto")


# ════════════════════════════════════════════════════════════
# Issue #2: Enlaces a Habitaclia no funcionan
# ════════════════════════════════════════════════════════════

def test_issue_2_habitaclia_urls(t: TestRunner):
    """
    Habitaclia generaba URLs con formato incorrecto (alquiler-vivienda-en-).
    El formato correcto de Habitaclia es alquiler-en-{ciudad}.htm.
    """
    print("\n── Issue #2: Enlaces a Habitaclia ──")

    scraper = HabitacliaScraper()
    params = SearchParams(
        location="madrid",
        max_price=1800,
        min_bedrooms=2,
        min_bathrooms=1,
        pets_allowed=True,
        need_elevator=True,
        prefer_terrace=True,
    )
    url = scraper.get_direct_search_url(params)

    # Debe usar el formato correcto alquiler-en-{slug}.htm
    t.assert_in("habitaclia.com/alquiler-en-madrid.htm", url,
                "URL usa formato alquiler-en-{slug}.htm")

    # NO debe contener vivienda (el formato anterior era incorrecto)
    t.assert_not_in("vivienda", url,
                    "URL NO contiene 'vivienda' en el path")

    # Debe incluir filtros de query correctos
    t.assert_in("preciohasta=1800", url,
                "URL incluye filtro de precio máximo")
    t.assert_in("habdesde=2", url,
                "URL incluye filtro de habitaciones")
    t.assert_in("mascotas=si", url,
                "URL incluye filtro de mascotas")
    t.assert_in("ascensor=si", url,
                "URL incluye filtro de ascensor")

    # Prueba con Barcelona (slug especial)
    params_bcn = SearchParams(location="Barcelona")
    url_bcn = scraper.get_direct_search_url(params_bcn)
    t.assert_in("alquiler-en-barcelona-702.htm", url_bcn,
                "Barcelona usa slug correcto barcelona-702")


# ════════════════════════════════════════════════════════════
# Issue #3: Filtro por sitio no funciona
# ════════════════════════════════════════════════════════════

def test_issue_3_platform_filter(t: TestRunner):
    """
    El buscador ignoraba el filtro de plataforma para los datos de demostración.
    Las propiedades demo deben filtrarse por la plataforma seleccionada.
    """
    print("\n── Issue #3: Filtro por sitio ──")

    from demo_data import DEMO_PROPERTIES
    from config import normalize

    # Verificar que los datos demo tienen plataformas asignadas
    platforms_in_demo = set(p.platform for p in DEMO_PROPERTIES)
    t.assert_true(len(platforms_in_demo) > 1,
                  f"Demo data tiene múltiples plataformas: {platforms_in_demo}")

    # Simular el filtrado de demo data como lo hace search.py
    location = "madrid"
    location_lower = location.lower().strip()

    def get_demo_filtered(platforms_list):
        """Replica la lógica de filtrado de search.py con el fix aplicado."""
        demo_filtered = []
        for prop in DEMO_PROPERTIES:
            city_n = normalize(prop.city)
            hood_n = normalize(prop.neighborhood)
            prov_n = normalize(prop.province)
            loc_n = normalize(location_lower)
            if loc_n in f"{city_n} {prov_n} {hood_n}":
                demo_filtered.append(prop)

        # Fix: filtrar por plataformas seleccionadas
        selected_platforms = set(platforms_list)
        demo_filtered = [p for p in demo_filtered if p.platform in selected_platforms]
        return demo_filtered

    # Con todas las plataformas
    all_platform_results = get_demo_filtered(
        ["idealista", "fotocasa", "habitaclia", "pisos.com", "housinganywhere"]
    )
    t.assert_true(len(all_platform_results) > 0,
                  f"Madrid tiene resultados demo ({len(all_platform_results)} props)")

    # Solo idealista
    idealista_only = get_demo_filtered(["idealista"])
    t.assert_true(
        all(p.platform == "idealista" for p in idealista_only),
        "Filtro 'idealista' solo devuelve propiedades de idealista"
    )

    # Solo fotocasa
    fotocasa_only = get_demo_filtered(["fotocasa"])
    t.assert_true(
        all(p.platform == "fotocasa" for p in fotocasa_only),
        "Filtro 'fotocasa' solo devuelve propiedades de fotocasa"
    )

    # Resultado filtrado debe ser subconjunto del total
    t.assert_true(
        len(idealista_only) + len(fotocasa_only) <= len(all_platform_results),
        "Resultado por plataforma es subconjunto del total"
    )

    # Una sola plataforma debe dar menos resultados que todas
    t.assert_true(
        len(idealista_only) < len(all_platform_results),
        f"idealista ({len(idealista_only)}) < total ({len(all_platform_results)})"
    )

    # Plataforma vacía devuelve 0
    empty = get_demo_filtered([])
    t.assert_equal(len(empty), 0,
                   "Sin plataformas seleccionadas = 0 resultados")


# ════════════════════════════════════════════════════════════
# Issue #4: No se pueden ordenar los resultados
# ════════════════════════════════════════════════════════════

def test_issue_4_sort_option_values(t: TestRunner):
    """
    Los valores de las opciones del <select> en el HTML no coincidían con los
    cases del switch en properties.js. El HTML usaba guiones (price-asc) pero
    el JS esperaba guiones bajos (price_asc).
    """
    print("\n── Issue #4: Ordenar resultados ──")

    # Leer el HTML del frontend
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Leer el JS de properties
    js_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "js", "properties.js")
    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()

    # Extraer option values del HTML
    option_values = re.findall(r'<select id="sortBy">.*?</select>', html_content, re.DOTALL)
    t.assert_true(len(option_values) == 1, "Existe un <select id='sortBy'>")

    select_html = option_values[0]
    html_values = re.findall(r'value="([^"]+)"', select_html)
    t.assert_true(len(html_values) >= 5,
                  f"sortBy tiene {len(html_values)} opciones (>=5 esperadas)")

    # Extraer case values del JS switch
    js_cases = re.findall(r"case\s+'([^']+)'", js_content)
    t.assert_true(len(js_cases) >= 5,
                  f"JS switch tiene {len(js_cases)} cases (>=5 esperados)")

    # Verificar que cada case del JS tiene su correspondiente option value en HTML
    for case_val in js_cases:
        t.assert_in(case_val, html_values,
                    f"JS case '{case_val}' tiene option value correspondiente en HTML")

    # Verificar valores específicos esperados
    expected_values = ["score_desc", "price_asc", "price_desc", "area_desc", "bedrooms_desc"]
    for val in expected_values:
        t.assert_in(val, html_values,
                    f"Option value '{val}' existe en el HTML")

    # Verificar que NO hay valores con guiones (el bug original)
    for val in html_values:
        t.assert_true("-" not in val or val.startswith("score"),
                      f"Option '{val}' no usa guiones (evita mismatch con JS)")


# ════════════════════════════════════════════════════════════
# Test integración: /api/search-urls genera URLs válidas
# ════════════════════════════════════════════════════════════

def test_search_urls_integration(t: TestRunner):
    """Verifica que todas las plataformas generan URLs con formato válido."""
    print("\n── Integración: search-urls ──")

    params = SearchParams(location="madrid", max_price=2000, min_bedrooms=2)
    urls = {name: SCRAPERS[name]().get_direct_search_url(params) for name in SCRAPERS}

    for platform, url in urls.items():
        t.assert_true(url.startswith("http"), f"{platform}: URL empieza con http")
        t.assert_true(len(url) > 20, f"{platform}: URL tiene longitud razonable ({len(url)} chars)")

    # HousingAnywhere NO debe tener petsAllowed ni bedrooms
    t.assert_not_in("petsAllowed", urls["housinganywhere"],
                    "search-urls: HousingAnywhere sin petsAllowed")
    t.assert_not_in("bedrooms", urls["housinganywhere"],
                    "search-urls: HousingAnywhere sin bedrooms")

    # Habitaclia debe usar alquiler-en-
    t.assert_in("alquiler-en-", urls["habitaclia"],
                "search-urls: Habitaclia usa alquiler-en-")
    t.assert_not_in("vivienda", urls["habitaclia"],
                    "search-urls: Habitaclia sin 'vivienda' en URL")


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t = TestRunner()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Tests de regresión — Issues #1, #2, #3, #4            ║")
    print("╚══════════════════════════════════════════════════════════╝")

    test_issue_1_housinganywhere_urls(t)
    test_issue_2_habitaclia_urls(t)
    test_issue_3_platform_filter(t)
    test_issue_4_sort_option_values(t)
    test_search_urls_integration(t)

    success = t.summary()
    sys.exit(0 if success else 1)
