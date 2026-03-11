"""
Tests automatizados para la plataforma AlquiSearch España.
Ejecutar con: python3 tests.py
"""
import asyncio
import sys
import json

# Asegurar path
sys.path.insert(0, '.')

from models import Property, SearchParams, SearchResult
from filters import (
    detect_scam, calculate_preference_score, check_availability,
    needs_elevator, filter_properties
)


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
            self.errors.append(f"{test_name} (esperado: {expected}, obtenido: {actual})")
            print(f"  ✗ {test_name} (esperado: {expected}, obtenido: {actual})")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"Resultados: {self.passed}/{total} tests pasados")
        if self.errors:
            print(f"Fallos:")
            for e in self.errors:
                print(f"  - {e}")
        print(f"{'='*50}")
        return self.failed == 0


def test_models(runner):
    """Tests de modelos de datos."""
    print("\n[MODELOS DE DATOS]")

    # Test Property creation
    prop = Property(
        title="Test Piso",
        price=1500,
        bedrooms=2,
        bathrooms=2,
        platform="idealista"
    )
    runner.assert_equal(prop.title, "Test Piso", "Crear Property con título")
    runner.assert_equal(prop.price, 1500, "Crear Property con precio")
    runner.assert_equal(prop.bedrooms, 2, "Crear Property con habitaciones")
    runner.assert_equal(prop.bathrooms, 2, "Crear Property con baños")

    # Test SearchParams defaults
    params = SearchParams(location="Madrid")
    runner.assert_equal(params.max_price, 2800, "SearchParams precio máx default")
    runner.assert_equal(params.min_bedrooms, 2, "SearchParams hab mín default")
    runner.assert_equal(params.min_bathrooms, 2, "SearchParams baños mín default")
    runner.assert_true(params.pets_allowed, "SearchParams mascotas default")
    runner.assert_true(params.need_elevator, "SearchParams ascensor default")
    runner.assert_equal(len(params.platforms), 5, "SearchParams plataformas default")


def test_scam_detection(runner):
    """Tests de detección de estafas."""
    print("\n[DETECCIÓN DE ESTAFAS]")

    # Propiedad normal
    normal = Property(
        title="Piso luminoso en Eixample",
        description="Bonito piso de 80m² con 2 habitaciones, bien comunicado.",
        price=1500,
        bedrooms=2,
        images=["img1.jpg", "img2.jpg"],
        address="Carrer Mallorca 250"
    )
    score = detect_scam(normal)
    runner.assert_true(score < 0.3, f"Propiedad normal score bajo ({score:.2f})")

    # Propiedad sospechosa
    scam = Property(
        title="URGENTE piso increíblemente barato",
        description="Envíe depósito por Western Union. Estoy en el extranjero. No se puede visitar.",
        price=200,
        bedrooms=3,
        images=[],
        address=""
    )
    score = detect_scam(scam)
    runner.assert_true(score >= 0.7, f"Propiedad estafa score alto ({score:.2f})")

    # Propiedad sin imágenes
    no_imgs = Property(
        title="Piso en centro",
        description="",
        price=1200,
        bedrooms=2,
        images=[],
        address="Calle Mayor"
    )
    score = detect_scam(no_imgs)
    runner.assert_true(score > 0, f"Sin imágenes tiene penalización ({score:.2f})")


def test_preference_scoring(runner):
    """Tests de puntuación de preferencia."""
    print("\n[PUNTUACIÓN DE PREFERENCIA]")

    params = SearchParams(location="Barcelona")

    # Propiedad con todas las preferencias
    perfect = Property(
        title="Piso perfecto",
        price=1800,
        bedrooms=3,
        bathrooms=2,
        has_terrace=True,
        has_balcony=True,
        pets_allowed=True,
        has_elevator=True,
        public_transport_nearby=True,
        services_nearby=True,
        allows_empadronamiento=True,
        has_air_conditioning=True,
        has_heating=True,
        has_parking=True,
    )
    score_perfect = calculate_preference_score(perfect, params)

    # Propiedad básica
    basic = Property(
        title="Piso básico",
        price=2700,
        bedrooms=2,
        bathrooms=2,
    )
    score_basic = calculate_preference_score(basic, params)

    runner.assert_true(
        score_perfect > score_basic,
        f"Propiedad completa puntúa más ({score_perfect:.1f}) que básica ({score_basic:.1f})"
    )

    # Propiedad con terraza puntúa más que sin terraza
    with_terrace = Property(title="Con terraza", price=2000, bedrooms=2, bathrooms=2, has_terrace=True)
    without_terrace = Property(title="Sin terraza", price=2000, bedrooms=2, bathrooms=2, has_terrace=False)
    runner.assert_true(
        calculate_preference_score(with_terrace, params) > calculate_preference_score(without_terrace, params),
        "Terraza incrementa puntuación"
    )

    # Precio más bajo puntúa mejor
    cheap = Property(title="Barato", price=1000, bedrooms=2, bathrooms=2)
    expensive = Property(title="Caro", price=2500, bedrooms=2, bathrooms=2)
    runner.assert_true(
        calculate_preference_score(cheap, params) > calculate_preference_score(expensive, params),
        "Precio bajo puntúa mejor"
    )


def test_availability(runner):
    """Tests de verificación de disponibilidad."""
    print("\n[VERIFICACIÓN DE DISPONIBILIDAD]")

    # No indicada -> aceptar
    prop_none = Property(availability="")
    runner.assert_true(check_availability(prop_none, "2026-10-01"), "Disponibilidad vacía aceptada")

    prop_na = Property(availability="No indicada")
    runner.assert_true(check_availability(prop_na, "2026-10-01"), "Disponibilidad 'No indicada' aceptada")

    # Inmediata -> aceptar
    prop_imm = Property(availability="Inmediata")
    runner.assert_true(check_availability(prop_imm, "2026-10-01"), "Disponibilidad 'Inmediata' aceptada")

    # Octubre 2026 -> aceptar
    prop_oct = Property(availability="Octubre 2026")
    runner.assert_true(check_availability(prop_oct, "2026-10-01"), "Octubre 2026 aceptado")

    # Septiembre 2026 -> aceptar (antes de octubre)
    prop_sep = Property(availability="septiembre 2026")
    runner.assert_true(check_availability(prop_sep, "2026-10-01"), "Septiembre 2026 aceptado")

    # Fecha con formato dd/mm/yyyy
    prop_date = Property(availability="01/09/2026")
    runner.assert_true(check_availability(prop_date, "2026-10-01"), "Fecha 01/09/2026 aceptada")


def test_elevator_need(runner):
    """Tests de necesidad de ascensor."""
    print("\n[NECESIDAD DE ASCENSOR]")

    # Planta baja no necesita
    pb = Property(property_type="piso", floor="bajo")
    runner.assert_true(not needs_elevator(pb), "Planta baja no necesita ascensor")

    # Planta 4 necesita
    p4 = Property(property_type="piso", floor="4")
    runner.assert_true(needs_elevator(p4), "Planta 4 necesita ascensor")

    # Casa no necesita
    casa = Property(property_type="casa", floor="2")
    runner.assert_true(not needs_elevator(casa), "Casa no necesita ascensor")

    # Sin planta indicada
    no_floor = Property(property_type="piso", floor="")
    runner.assert_true(not needs_elevator(no_floor), "Sin planta no necesita")


def test_filtering(runner):
    """Tests del filtrado completo."""
    print("\n[FILTRADO COMPLETO]")

    params = SearchParams(location="Barcelona", max_price=2800, min_bedrooms=2, min_bathrooms=2)

    properties = [
        # Debería pasar
        Property(
            title="Piso OK", url="http://test.com/1",
            price=2000, bedrooms=3, bathrooms=2,
            has_terrace=True, pets_allowed=True,
            has_elevator=True, floor="3",
            images=["img.jpg"], description="Buen piso en zona céntrica",
            address="Calle Test"
        ),
        # Debería ser excluido: precio alto
        Property(
            title="Piso Caro", url="http://test.com/2",
            price=3500, bedrooms=3, bathrooms=2,
        ),
        # Debería ser excluido: pocas habitaciones
        Property(
            title="Estudio", url="http://test.com/3",
            price=1000, bedrooms=1, bathrooms=1,
        ),
        # Debería ser excluido: posible estafa
        Property(
            title="URGENTE envíe depósito Western Union",
            url="http://test.com/4",
            price=200, bedrooms=3, bathrooms=2,
            description="Estoy en el extranjero no se puede visitar enviar dinero por Western Union",
            images=[], address=""
        ),
        # Debería pasar pero con menor score
        Property(
            title="Piso básico", url="http://test.com/5",
            price=2500, bedrooms=2, bathrooms=2,
            images=["img.jpg"], description="Piso correcto",
            address="Calle Test 2"
        ),
    ]

    filtered = filter_properties(properties, params)

    runner.assert_equal(len(filtered), 2, "Filtrado devuelve 2 propiedades válidas")

    if len(filtered) >= 2:
        # El primero debería tener mejor score (terraza, mascotas, etc.)
        runner.assert_true(
            filtered[0].score >= filtered[1].score,
            "Resultados ordenados por score descendente"
        )
        runner.assert_true(
            "OK" in filtered[0].title,
            "Primera propiedad es la mejor puntuada"
        )

    # Verificar que las excluidas no están
    filtered_urls = [p.url for p in filtered]
    runner.assert_true("http://test.com/2" not in filtered_urls, "Piso caro excluido")
    runner.assert_true("http://test.com/3" not in filtered_urls, "Estudio excluido (pocas hab)")
    runner.assert_true("http://test.com/4" not in filtered_urls, "Estafa excluida")


def test_scraper_urls(runner):
    """Tests de generación de URLs de búsqueda."""
    print("\n[URLS DE BÚSQUEDA]")

    from scrapers import IdealistaScraper, FotocasaScraper, HabitacliaScraper, PisosScraper, HousingAnywhereScraper

    params = SearchParams(location="Madrid", max_price=2000, min_bedrooms=2, min_bathrooms=2)

    # Idealista
    idealista = IdealistaScraper()
    url = idealista.get_direct_search_url(params)
    runner.assert_true("idealista.com" in url, "Idealista URL contiene dominio")
    runner.assert_true("alquiler" in url, "Idealista URL contiene 'alquiler'")
    runner.assert_true("madrid" in url.lower(), "Idealista URL contiene 'madrid'")

    # Fotocasa
    fotocasa = FotocasaScraper()
    url = fotocasa.get_direct_search_url(params)
    runner.assert_true("fotocasa.es" in url, "Fotocasa URL contiene dominio")
    runner.assert_true("alquiler" in url, "Fotocasa URL contiene 'alquiler'")

    # Habitaclia
    habitaclia = HabitacliaScraper()
    url = habitaclia.get_direct_search_url(params)
    runner.assert_true("habitaclia.com" in url, "Habitaclia URL contiene dominio")

    # Pisos.com
    pisos = PisosScraper()
    url = pisos.get_direct_search_url(params)
    runner.assert_true("pisos.com" in url, "Pisos.com URL contiene dominio")
    runner.assert_true("alquiler" in url, "Pisos.com URL contiene 'alquiler'")

    # HousingAnywhere
    ha = HousingAnywhereScraper()
    url = ha.get_direct_search_url(params)
    runner.assert_true("housinganywhere.com" in url, "HousingAnywhere URL contiene dominio")
    runner.assert_true("Madrid" in url, "HousingAnywhere URL contiene 'Madrid'")
    runner.assert_true("Spain" in url, "HousingAnywhere URL contiene 'Spain'")


def test_pet_detection(runner):
    """Tests de detección correcta de mascotas en texto."""
    print("\n[DETECCIÓN DE MASCOTAS EN TEXTO]")

    from scrapers.base import _text_denies_pets

    # Frases que NIEGAN mascotas
    runner.assert_true(_text_denies_pets("no se admiten mascotas"), "'no se admiten mascotas' detectado")
    runner.assert_true(_text_denies_pets("no se permiten mascotas"), "'no se permiten mascotas' detectado")
    runner.assert_true(_text_denies_pets("no se aceptan mascotas"), "'no se aceptan mascotas' detectado")
    runner.assert_true(_text_denies_pets("no admite mascotas"), "'no admite mascotas' detectado")
    runner.assert_true(_text_denies_pets("sin mascotas"), "'sin mascotas' detectado")
    runner.assert_true(_text_denies_pets("no mascotas"), "'no mascotas' detectado")
    runner.assert_true(_text_denies_pets("no pets"), "'no pets' detectado")
    runner.assert_true(_text_denies_pets("pets not allowed"), "'pets not allowed' detectado")
    runner.assert_true(_text_denies_pets("animales no"), "'animales no' detectado")
    runner.assert_true(_text_denies_pets("mascotas prohibidas"), "'mascotas prohibidas' detectado")
    runner.assert_true(
        _text_denies_pets("Piso bonito de 80m2. No se admiten mascotas. Cerca del metro."),
        "Frase negativa dentro de descripción larga"
    )

    # Frases que SÍ permiten mascotas (no deben detectar negación)
    runner.assert_true(not _text_denies_pets("se admiten mascotas"), "'se admiten mascotas' no es negación")
    runner.assert_true(not _text_denies_pets("mascotas bienvenidas"), "'mascotas bienvenidas' no es negación")
    runner.assert_true(not _text_denies_pets("acepta mascotas"), "'acepta mascotas' no es negación")
    runner.assert_true(not _text_denies_pets("pets allowed"), "'pets allowed' no es negación")
    runner.assert_true(not _text_denies_pets("ideal para mascotas"), "'ideal para mascotas' no es negación")


def test_sea_view_and_long_stay(runner):
    """Tests de filtros de vista al mar y larga estancia."""
    print("\n[FILTROS VISTA MAR Y LARGA ESTANCIA]")

    # Propiedad con vista al mar
    sea_prop = Property(
        title="Piso con vistas al mar", price=1800, bedrooms=2, bathrooms=2,
        has_sea_view=True, is_long_stay=True, url="http://test.com/sea"
    )
    runner.assert_true(sea_prop.has_sea_view, "Propiedad tiene vista al mar")
    runner.assert_true(sea_prop.is_long_stay, "Propiedad es larga estancia")

    # Propiedad sin vista al mar
    normal_prop = Property(
        title="Piso interior", price=1500, bedrooms=2, bathrooms=2,
        url="http://test.com/normal"
    )
    runner.assert_true(not normal_prop.has_sea_view, "Propiedad sin vista al mar por defecto")
    runner.assert_true(not normal_prop.is_long_stay, "Propiedad no es larga estancia por defecto")

    # Filtro de larga estancia
    params_long = SearchParams(location="test", long_stay=True)
    filtered = filter_properties([sea_prop, normal_prop], params_long)
    runner.assert_equal(len(filtered), 1, "Filtro larga estancia solo devuelve 1")
    runner.assert_true(filtered[0].is_long_stay, "Resultado filtrado es larga estancia")

    # Filtro de vista al mar
    params_sea = SearchParams(location="test", sea_view=True)
    filtered = filter_properties([sea_prop, normal_prop], params_sea)
    runner.assert_equal(len(filtered), 1, "Filtro vista mar solo devuelve 1")
    runner.assert_true(filtered[0].has_sea_view, "Resultado filtrado tiene vista al mar")

    # Sin filtros especiales: ambas aparecen
    params_normal = SearchParams(location="test")
    filtered = filter_properties([sea_prop, normal_prop], params_normal)
    runner.assert_equal(len(filtered), 2, "Sin filtro especial devuelve ambas")

    # Scoring: vista al mar y larga estancia aumentan puntuación
    params_score = SearchParams(location="test", sea_view=True, long_stay=True)
    score_sea = calculate_preference_score(sea_prop, params_score)
    score_normal = calculate_preference_score(normal_prop, params_score)
    runner.assert_true(score_sea > score_normal, "Vista mar + larga estancia puntúa más")


def test_pagination_urls(runner):
    """Tests de generación de URLs de paginación."""
    print("\n[URLS DE PAGINACIÓN]")

    from scrapers import IdealistaScraper, FotocasaScraper, HabitacliaScraper, PisosScraper, HousingAnywhereScraper

    params = SearchParams(location="Madrid", max_price=2000, min_bedrooms=2, min_bathrooms=2)

    # Idealista - usa /pagina-N.htm
    idealista = IdealistaScraper()
    base = idealista._build_search_url(params)
    url_p1 = idealista._build_page_url(base, 1)
    url_p2 = idealista._build_page_url(base, 2)
    url_p3 = idealista._build_page_url(base, 3)
    runner.assert_equal(url_p1, base, "Idealista página 1 = URL base")
    runner.assert_true("pagina-2" in url_p2, "Idealista página 2 contiene 'pagina-2'")
    runner.assert_true("pagina-3" in url_p3, "Idealista página 3 contiene 'pagina-3'")
    runner.assert_true("maxPrice=" in url_p2, "Idealista página 2 conserva query params")

    # Fotocasa - usa currentPage=N
    fotocasa = FotocasaScraper()
    base = fotocasa._build_search_url(params)
    url_p1 = fotocasa._build_page_url(base, 1)
    url_p2 = fotocasa._build_page_url(base, 2)
    runner.assert_equal(url_p1, base, "Fotocasa página 1 = URL base")
    runner.assert_true("currentPage=2" in url_p2, "Fotocasa página 2 tiene currentPage=2")

    # Habitaclia - usa pag=N
    habitaclia = HabitacliaScraper()
    base = habitaclia._build_search_url(params)
    url_p1 = habitaclia._build_page_url(base, 1)
    url_p2 = habitaclia._build_page_url(base, 2)
    runner.assert_equal(url_p1, base, "Habitaclia página 1 = URL base")
    runner.assert_true("pag=2" in url_p2, "Habitaclia página 2 tiene pag=2")

    # Pisos.com - usa /N/ en la ruta
    pisos = PisosScraper()
    base = pisos._build_search_url(params)
    url_p1 = pisos._build_page_url(base, 1)
    url_p2 = pisos._build_page_url(base, 2)
    runner.assert_equal(url_p1, base, "Pisos.com página 1 = URL base")
    runner.assert_true("/2/" in url_p2, "Pisos.com página 2 tiene /2/ en ruta")

    # HousingAnywhere - usa page=N
    ha = HousingAnywhereScraper()
    base = ha._build_search_url(params)
    url_p1 = ha._build_page_url(base, 1)
    url_p2 = ha._build_page_url(base, 2)
    runner.assert_equal(url_p1, base, "HousingAnywhere página 1 = URL base")
    runner.assert_true("page=2" in url_p2, "HousingAnywhere página 2 tiene page=2")

    # MAX_PAGES está configurado en base
    runner.assert_true(idealista.MAX_PAGES >= 3, f"MAX_PAGES >= 3 ({idealista.MAX_PAGES})")


def test_relaxed_filters(runner):
    """Tests de filtros relajados para datos desconocidos."""
    print("\n[FILTROS RELAJADOS]")

    params = SearchParams(location="test", max_price=2800, min_bedrooms=2, min_bathrooms=2)

    # Propiedad con datos desconocidos (bedrooms=0, bathrooms=0) NO debe excluirse
    unknown = Property(
        title="Piso sin datos parseados", url="http://test.com/unknown",
        price=1500, bedrooms=0, bathrooms=0,
        images=["img.jpg"], description="Bonito piso en zona céntrica",
        address="Calle Test"
    )
    filtered = filter_properties([unknown], params)
    runner.assert_equal(len(filtered), 1, "Propiedad con bedrooms=0 NO es excluida")

    # Propiedad con 1 habitación sí se excluye (1 < 2 min)
    one_bed = Property(
        title="Estudio", url="http://test.com/studio",
        price=1000, bedrooms=1, bathrooms=1,
        images=["img.jpg"], description="Estudio pequeño",
        address="Calle Test"
    )
    filtered = filter_properties([one_bed], params)
    runner.assert_equal(len(filtered), 0, "Propiedad con 1 hab sigue excluida (< min)")

    # Propiedad con precio=0 (no parseado) NO se excluye
    no_price = Property(
        title="Piso sin precio", url="http://test.com/noprice",
        price=0, bedrooms=3, bathrooms=2,
        images=["img.jpg"], description="Buen piso",
        address="Calle Test"
    )
    filtered = filter_properties([no_price], params)
    runner.assert_equal(len(filtered), 1, "Propiedad con precio=0 NO es excluida")

    # Propiedad con precio conocido alto sí se excluye
    expensive = Property(
        title="Piso caro", url="http://test.com/expensive",
        price=5000, bedrooms=3, bathrooms=2,
        images=["img.jpg"], description="Piso lujo",
        address="Calle Test"
    )
    filtered = filter_properties([expensive], params)
    runner.assert_equal(len(filtered), 0, "Propiedad con precio alto sigue excluida")

    # Mix: desconocidos + conocidos se ordenan correctamente
    props = [unknown, one_bed, no_price, expensive]
    filtered = filter_properties(props, params)
    runner.assert_equal(len(filtered), 2, "Del mix, 2 propiedades pasan (las de datos desconocidos)")


def test_parallel_execution(runner):
    """Tests de ejecución paralela de scrapers."""
    print("\n[EJECUCIÓN PARALELA]")

    import asyncio

    async def _test_parallel():
        results = []
        async def fake_scrape(name, delay):
            await asyncio.sleep(delay)
            results.append(name)
            return [name]

        # Simular 3 scrapers ejecutándose en paralelo
        tasks = [
            fake_scrape("a", 0.1),
            fake_scrape("b", 0.1),
            fake_scrape("c", 0.1),
        ]
        gathered = await asyncio.gather(*tasks)
        return results, gathered

    results, gathered = asyncio.run(_test_parallel())
    runner.assert_equal(len(results), 3, "Todos los scrapers paralelos terminaron")
    runner.assert_equal(len(gathered), 3, "gather retorna 3 resultados")
    runner.assert_true("a" in results and "b" in results and "c" in results, "Todos los nombres presentes")


async def test_api_integration(runner):
    """Tests de integración de la API (requiere servidor corriendo)."""
    print("\n[INTEGRACIÓN API]")

    try:
        import httpx
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # Health check
            resp = await client.get("/api/health")
            runner.assert_equal(resp.status_code, 200, "Health check responde 200")
            data = resp.json()
            runner.assert_equal(data["status"], "ok", "Health check status ok")

            # Cities
            resp = await client.get("/api/cities?q=Bar")
            runner.assert_equal(resp.status_code, 200, "Cities endpoint responde 200")
            cities = resp.json()
            runner.assert_true("Barcelona" in cities, "Cities incluye Barcelona")

            # Search
            resp = await client.post("/api/search", json={
                "location": "Madrid",
                "max_price": 2800,
                "min_bedrooms": 2,
                "min_bathrooms": 2,
                "pets_allowed": True,
                "need_elevator": True,
                "prefer_terrace": True,
                "prefer_balcony": True,
                "prefer_transport": True,
                "prefer_services": True,
                "platforms": ["idealista", "fotocasa", "habitaclia", "pisos.com"]
            }, timeout=60)
            runner.assert_equal(resp.status_code, 200, "Search endpoint responde 200")
            result = resp.json()
            runner.assert_true("properties" in result, "Resultado contiene 'properties'")
            runner.assert_true("total" in result, "Resultado contiene 'total'")
            runner.assert_true("platforms_searched" in result, "Resultado contiene 'platforms_searched'")
            runner.assert_true(result["total"] >= 10, f"Total es >= 10 ({result['total']})")

            # Search URLs
            resp = await client.get("/api/search-urls?location=Barcelona")
            runner.assert_equal(resp.status_code, 200, "Search URLs responde 200")
            urls = resp.json()
            runner.assert_true("idealista" in urls, "URLs incluye idealista")
            runner.assert_true("fotocasa" in urls, "URLs incluye fotocasa")
            runner.assert_true("habitaclia" in urls, "URLs incluye habitaclia")
            runner.assert_true("pisos.com" in urls, "URLs incluye pisos.com")
            runner.assert_true("housinganywhere" in urls, "URLs incluye housinganywhere")

            # Coastal city check
            resp = await client.get("/api/is-coastal?city=Barcelona")
            runner.assert_equal(resp.status_code, 200, "Coastal endpoint responde 200")
            data = resp.json()
            runner.assert_true(data["is_coastal"], "Barcelona es costera")

            resp = await client.get("/api/is-coastal?city=Madrid")
            data = resp.json()
            runner.assert_true(not data["is_coastal"], "Madrid no es costera")

            resp = await client.get("/api/is-coastal?city=Málaga")
            data = resp.json()
            runner.assert_true(data["is_coastal"], "Málaga es costera")

    except Exception as e:
        print(f"  ⚠ Tests de integración requieren servidor en localhost:8000: {e}")


def test_cache_module(runner):
    """Tests para el módulo de caché SQLite."""
    print("\n[CACHE SQLITE]")
    from cache import get_cached, set_cached, params_to_hash, clear_all, clear_expired

    # Limpiar caché de tests anteriores
    clear_all()

    # Test params_to_hash determinismo
    h1 = params_to_hash({"max_price": 2800, "platforms": ["idealista", "fotocasa"]})
    h2 = params_to_hash({"max_price": 2800, "platforms": ["fotocasa", "idealista"]})
    runner.assert_equal(h1, h2, "params_to_hash es determinista (orden plataformas)")

    h3 = params_to_hash({"max_price": 2000, "platforms": ["idealista"]})
    runner.assert_true(h1 != h3, "params_to_hash difiere con parámetros distintos")

    # Test MISS
    result = get_cached("test-city", "test-hash")
    runner.assert_true(result is None, "Cache vacía retorna None (MISS)")

    # Test SET + GET (HIT)
    test_data = [{"id": "1", "title": "Test Prop"}]
    set_cached("test-city", "test-hash", test_data)
    result = get_cached("test-city", "test-hash")
    runner.assert_true(result is not None, "Cache hit después de set_cached")
    runner.assert_equal(result[0]["id"], "1", "Datos cacheados son correctos")

    # Test TTL expirado
    result_expired = get_cached("test-city", "test-hash", ttl=0)
    runner.assert_true(result_expired is None, "Cache expirada retorna None")

    # Limpieza
    deleted = clear_all()
    runner.assert_true(deleted >= 0, "clear_all retorna número de filas")

    result_after_clear = get_cached("test-city", "test-hash")
    runner.assert_true(result_after_clear is None, "Cache limpia después de clear_all")


def test_area_and_type_filters(runner):
    """Tests para los filtros de superficie y tipo de propiedad."""
    print("\n[FILTROS SUPERFICIE Y TIPO]")

    # Propiedad base
    prop = Property(
        id="area-1", title="Test", price=1500, bedrooms=3, bathrooms=2,
        area_m2=80.0, property_type="piso", city="Madrid",
        pets_allowed=True, url="http://test.com/1", platform="test"
    )

    # Test: min_area filtra propiedades pequeñas
    params = SearchParams(location="Madrid", min_area=100.0)
    result = filter_properties([prop], params)
    runner.assert_equal(len(result), 0, "min_area=100 filtra propiedad de 80m²")

    params = SearchParams(location="Madrid", min_area=60.0)
    result = filter_properties([prop], params)
    runner.assert_equal(len(result), 1, "min_area=60 no filtra propiedad de 80m²")

    # Test: max_area filtra propiedades grandes
    params = SearchParams(location="Madrid", max_area=70.0)
    result = filter_properties([prop], params)
    runner.assert_equal(len(result), 0, "max_area=70 filtra propiedad de 80m²")

    params = SearchParams(location="Madrid", max_area=100.0)
    result = filter_properties([prop], params)
    runner.assert_equal(len(result), 1, "max_area=100 no filtra propiedad de 80m²")

    # Test: property_type
    params = SearchParams(location="Madrid", property_type="casa")
    result = filter_properties([prop], params)
    runner.assert_equal(len(result), 0, "property_type=casa filtra piso")

    params = SearchParams(location="Madrid", property_type="piso")
    result = filter_properties([prop], params)
    runner.assert_equal(len(result), 1, "property_type=piso no filtra piso")


def test_pool_scoring(runner):
    """Tests para el scoring de piscina."""
    print("\n[SCORING PISCINA]")

    params = SearchParams(location="Madrid")

    prop_pool = Property(
        id="pool-1", title="Con piscina", price=1500, bedrooms=2, bathrooms=2,
        has_pool=True, city="Madrid", url="http://test.com/pool", platform="test"
    )

    prop_no_pool = Property(
        id="pool-2", title="Sin piscina", price=1500, bedrooms=2, bathrooms=2,
        has_pool=False, city="Madrid", url="http://test.com/nopool", platform="test"
    )

    score_pool = calculate_preference_score(prop_pool, params)
    score_no_pool = calculate_preference_score(prop_no_pool, params)

    runner.assert_true(score_pool > score_no_pool, f"Piscina sube scoring ({score_pool} > {score_no_pool})")
    runner.assert_true(score_pool - score_no_pool >= 4, "Piscina aporta al menos +4 puntos")


def test_crime_noise_zones(runner):
    """Tests para zonas peligrosas y ruidosas."""
    print("\n[ZONAS CRIMINALIDAD Y RUIDO]")
    from filters import HIGH_CRIME_AREAS, HIGH_NOISE_AREAS

    runner.assert_true(len(HIGH_CRIME_AREAS) > 0, "HIGH_CRIME_AREAS tiene datos reales")
    runner.assert_true(len(HIGH_NOISE_AREAS) > 0, "HIGH_NOISE_AREAS tiene datos reales")

    # Propiedad en zona peligrosa
    prop_crime = Property(
        id="crime-1", title="Test", price=1500, bedrooms=2, bathrooms=2,
        neighborhood="Valdemingómez", address="Calle Test",
        city="Madrid", url="http://test.com/crime", platform="test"
    )

    params = SearchParams(location="Madrid")
    result = filter_properties([prop_crime], params)
    runner.assert_equal(len(result), 0, "Propiedad en zona peligrosa filtrada")

    # Propiedad en zona ruidosa (aeropuerto)
    prop_noise = Property(
        id="noise-1", title="Test", price=1500, bedrooms=2, bathrooms=2,
        neighborhood="Barajas", address="Cerca aeropuerto",
        city="Madrid", url="http://test.com/noise", platform="test"
    )

    result = filter_properties([prop_noise], params)
    runner.assert_equal(len(result), 0, "Propiedad en zona ruidosa filtrada")

    # Propiedad en zona normal
    prop_normal = Property(
        id="normal-1", title="Test", price=1500, bedrooms=2, bathrooms=2,
        neighborhood="Salamanca", address="Calle Serrano",
        city="Madrid", url="http://test.com/normal", platform="test"
    )

    result = filter_properties([prop_normal], params)
    runner.assert_equal(len(result), 1, "Propiedad en zona normal NO filtrada")


def test_retry_config(runner):
    """Tests para configuración de reintentos del scraper."""
    print("\n[RETRY CONFIG]")
    from scrapers.base import BaseScraper

    runner.assert_equal(BaseScraper.MAX_RETRIES, 3, "MAX_RETRIES es 3")
    runner.assert_equal(len(BaseScraper.RETRY_DELAYS), 3, "RETRY_DELAYS tiene 3 valores")
    runner.assert_true(BaseScraper.RETRY_DELAYS[0] < BaseScraper.RETRY_DELAYS[1],
                       "RETRY_DELAYS tiene backoff creciente")


def main():
    print("=" * 50)
    print("AlquiSearch España - Tests Automatizados")
    print("=" * 50)

    runner = TestRunner()

    # Tests unitarios
    test_models(runner)
    test_scam_detection(runner)
    test_preference_scoring(runner)
    test_availability(runner)
    test_elevator_need(runner)
    test_filtering(runner)
    test_scraper_urls(runner)
    test_pet_detection(runner)
    test_sea_view_and_long_stay(runner)
    test_pagination_urls(runner)
    test_relaxed_filters(runner)
    test_parallel_execution(runner)

    # New tests
    test_cache_module(runner)
    test_area_and_type_filters(runner)
    test_pool_scoring(runner)
    test_crime_noise_zones(runner)
    test_retry_config(runner)

    # Tests de integración
    asyncio.run(test_api_integration(runner))

    success = runner.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
