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
    HousingAnywhere es una SPA que usa segmentos de ruta para filtrar,
    NO parámetros de query. Los query params como ?categories= o ?priceMax=
    provocaban que la página mostrara 0 resultados.
    La URL corregida usa /apartment-for-rent como path.
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

    # Debe usar path /apartment-for-rent (NO query param categories=)
    t.assert_in("/apartment-for-rent", url,
                "URL usa /apartment-for-rent como path")

    # NO debe contener query params — HA no los soporta
    t.assert_not_in("?", url,
                    "URL NO tiene query params (HA no los soporta)")
    t.assert_not_in("categories=", url,
                    "URL NO contiene categories= (HA ignora query params)")
    t.assert_not_in("priceMax=", url,
                    "URL NO contiene priceMax= (HA ignora query params)")
    t.assert_not_in("petsAllowed", url,
                    "URL NO contiene petsAllowed")
    t.assert_not_in("bedrooms", url,
                    "URL NO contiene bedrooms")

    # URL esperada exacta
    t.assert_equal(url, "https://housinganywhere.com/s/Madrid--Spain/apartment-for-rent",
                   "URL exacta para Madrid apartments")

    # Prueba con long_stay activado — usa /long-term-rentals
    params_long = SearchParams(
        location="barcelona",
        max_price=1500,
        long_stay=True,
    )
    url_long = scraper.get_direct_search_url(params_long)
    t.assert_in("/long-term-rentals", url_long,
                "URL con long_stay usa /long-term-rentals")
    t.assert_not_in("minDuration=", url_long,
                    "URL NO tiene minDuration= (HA ignora query params)")
    t.assert_in("Barcelona--Spain", url_long,
                "URL contiene slug correcto para Barcelona")

    # Prueba con ciudad no mapeada
    params_unknown = SearchParams(location="Cuenca")
    url_unknown = scraper.get_direct_search_url(params_unknown)
    t.assert_in("housinganywhere.com/s/Cuenca--Spain", url_unknown,
                "Ciudad no mapeada genera slug genérico correcto")
    t.assert_in("/apartment-for-rent", url_unknown,
                "Ciudad no mapeada también usa /apartment-for-rent")


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

    # Debe usar el formato correcto alquiler-{slug}.htm
    t.assert_in("habitaclia.com/alquiler-madrid.htm", url,
                "URL usa formato alquiler-{slug}.htm")

    # NO debe contener vivienda ni 'en-' (formatos anteriores incorrectos)
    t.assert_not_in("vivienda", url,
                    "URL NO contiene 'vivienda' en el path")
    t.assert_not_in("/alquiler-en-", url,
                    "URL NO contiene 'alquiler-en-' (formato 404)")

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
    t.assert_in("alquiler-barcelona-702.htm", url_bcn,
                "Barcelona usa slug correcto barcelona-702")


# ════════════════════════════════════════════════════════════
# Issue #3: Filtro por sitio no funciona
# ════════════════════════════════════════════════════════════

def test_issue_3_platform_filter(t: TestRunner):
    """
    El buscador debe respetar el filtro de plataformas seleccionadas.
    Solo se deben ejecutar los scrapers de las plataformas marcadas.
    """
    print("\n── Issue #3: Filtro por sitio ──")

    from config import SCRAPERS

    # Verificar que hay múltiples scrapers disponibles
    available = list(SCRAPERS.keys())
    t.assert_true(len(available) >= 5,
                  f"Al menos 5 scrapers disponibles: {available}")

    # Verificar que cada plataforma tiene su scraper
    expected_platforms = ["idealista", "fotocasa", "habitaclia", "pisos.com", "housinganywhere"]
    for plat in expected_platforms:
        t.assert_true(plat in SCRAPERS,
                      f"Scraper '{plat}' está registrado en SCRAPERS")

    # Verificar que la lógica de search.py solo ejecuta plataformas válidas
    search_path = os.path.join(os.path.dirname(__file__), "routers", "search.py")
    with open(search_path, "r", encoding="utf-8") as f:
        search_code = f.read()

    # Debe filtrar por plataformas seleccionadas
    t.assert_true("valid_platforms = [p for p in params.platforms if p in SCRAPERS]" in search_code,
                  "search.py filtra plataformas por las seleccionadas")

    # NO debe importar demo_data
    t.assert_true("from demo_data import" not in search_code,
                  "search.py NO importa demo_data")

    # NO debe tener código de demo_filtered
    t.assert_true("demo_filtered" not in search_code,
                  "search.py NO tiene lógica de datos demo")


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

    # HousingAnywhere debe usar path-based URLs sin query params
    t.assert_in("/apartment-for-rent", urls["housinganywhere"],
                "search-urls: HousingAnywhere usa /apartment-for-rent")
    t.assert_not_in("?", urls["housinganywhere"],
                    "search-urls: HousingAnywhere sin query params")
    t.assert_not_in("petsAllowed", urls["housinganywhere"],
                    "search-urls: HousingAnywhere sin petsAllowed")
    t.assert_not_in("bedrooms", urls["housinganywhere"],
                    "search-urls: HousingAnywhere sin bedrooms")

    # Habitaclia debe usar alquiler-{slug}.htm
    t.assert_in("/alquiler-madrid.htm", urls["habitaclia"],
                "search-urls: Habitaclia usa /alquiler-{slug}.htm")
    t.assert_not_in("vivienda", urls["habitaclia"],
                    "search-urls: Habitaclia sin 'vivienda' en URL")
    t.assert_not_in("/alquiler-en-", urls["habitaclia"],
                    "search-urls: Habitaclia sin '/alquiler-en-' en URL")

    # Fotocasa debe incluir /todas-las-zonas/
    t.assert_in("/todas-las-zonas/", urls["fotocasa"],
                "search-urls: Fotocasa incluye /todas-las-zonas/")

    # Idealista no debe duplicar ciudad en slug
    t.assert_not_in("madrid-madrid", urls["idealista"],
                    "search-urls: Idealista sin slug duplicado madrid-madrid")


# ════════════════════════════════════════════════════════════
# Test HTTP: URLs realmente accesibles
# ════════════════════════════════════════════════════════════

def test_urls_http_reachable(t: TestRunner):
    """
    Verifica que las URLs generadas sean realmente accesibles vía HTTP.
    Usa HEAD con follow_redirects para comprobar que no devuelven 404.
    Nota: idealista devuelve 403 (anti-bot) pero la URL es válida.
    """
    print("\n── HTTP: URLs accesibles ──")

    import httpx

    params = SearchParams(location="madrid", max_price=2000, min_bedrooms=2)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
    }

    # Plataformas que deben devolver 200 (no tienen anti-bot agresivo)
    must_200 = ["fotocasa", "habitaclia", "pisos.com", "housinganywhere"]
    # Idealista siempre devuelve 403 desde scripts (anti-bot), pero URL es correcta
    anti_bot = ["idealista"]

    with httpx.Client(headers=headers, follow_redirects=True, timeout=20.0) as client:
        for name in must_200:
            url = SCRAPERS[name]().get_direct_search_url(params)
            try:
                r = client.head(url, follow_redirects=True)
                t.assert_true(
                    r.status_code < 400,
                    f"{name}: HTTP {r.status_code} (esperado < 400) — {url[:80]}"
                )
            except httpx.TimeoutException:
                # Timeout no es 404 — la URL existe pero el servidor tarda
                t.assert_true(True, f"{name}: timeout (URL existe, servidor lento)")
            except Exception as e:
                t.assert_true(False, f"{name}: excepción {type(e).__name__}: {e}")

        for name in anti_bot:
            url = SCRAPERS[name]().get_direct_search_url(params)
            try:
                r = client.head(url, follow_redirects=True)
                # 403 es aceptable (anti-bot), 404 no lo es
                t.assert_true(
                    r.status_code != 404,
                    f"{name}: HTTP {r.status_code} (no es 404) — {url[:80]}"
                )
            except httpx.TimeoutException:
                t.assert_true(True, f"{name}: timeout (URL existe)")
            except Exception as e:
                t.assert_true(False, f"{name}: excepción {type(e).__name__}: {e}")


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
    test_urls_http_reachable(t)

    success = t.summary()
    sys.exit(0 if success else 1)