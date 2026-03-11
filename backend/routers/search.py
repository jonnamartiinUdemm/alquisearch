"""
routers/search.py
=================
Rutas de búsqueda de propiedades, autocompletado y URLs directas.
"""
import asyncio
from typing import List

from fastapi import APIRouter, Query

from models import Property, SearchParams, SearchResult
from filters import filter_properties
from cache import get_cached, set_cached, params_to_hash
from neighborhoods import get_suggestions
from config import SCRAPERS, COASTAL_CITIES, SPANISH_CITIES, normalize

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/cities")
async def get_cities(q: str = Query("", description="Filtro de búsqueda")):
    """Búsqueda predictiva de ciudades y barrios (490+ barrios, 25 ciudades)."""
    if not q:
        return SPANISH_CITIES[:20]
    return [s["label"] for s in get_suggestions(q, limit=15)]


@router.post("/search", response_model=SearchResult)
async def search_properties(params: SearchParams):
    """
    Busca propiedades en todas las plataformas configuradas.
    Solo devuelve resultados reales de scraping — sin datos demo.
    """
    all_properties: List[Property] = []
    errors: List[str] = []
    platforms_searched: List[str] = []

    # 1. Caché de scraping
    p_hash = params_to_hash(params.model_dump())
    cached = get_cached(params.location, p_hash)
    if cached is not None:
        print(f"[Cache] HIT — {len(cached)} propiedades para «{params.location}»")
        all_properties = [Property(**p) for p in cached]
        platforms_searched = list(params.platforms)
    else:
        # 2. Scraping real en paralelo
        async def _scrape(platform_name: str) -> List[Property]:
            if platform_name not in SCRAPERS:
                return []
            scraper = SCRAPERS[platform_name]()
            try:
                print(f"--- Buscando en {platform_name} ---")
                props = await scraper.search(params)
                print(f"[{platform_name}] {len(props)} resultados")
                return props
            except Exception as e:
                errors.append(f"Error en {platform_name}: {e}")
                return []
            finally:
                await scraper.close()

        valid_platforms = [p for p in params.platforms if p in SCRAPERS]
        if valid_platforms:
            results = await asyncio.gather(*[_scrape(p) for p in valid_platforms], return_exceptions=True)
            for platform, result in zip(valid_platforms, results):
                platforms_searched.append(platform)
                if isinstance(result, list):
                    all_properties.extend(result)
                elif isinstance(result, Exception):
                    errors.append(f"Error en {platform}: {result}")

        if all_properties:
            set_cached(params.location, p_hash, [p.model_dump() for p in all_properties])

    # 3. Deduplicar por URL
    seen, unique = set(), []
    for prop in all_properties:
        if prop.url not in seen:
            seen.add(prop.url)
            unique.append(prop)

    # 4. Filtrar y puntuar
    filtered = filter_properties(unique, params)
    print(f"=== Total: {len(filtered)} propiedades reales ===")

    return SearchResult(
        properties=filtered,
        total=len(filtered),
        location=params.location,
        platforms_searched=platforms_searched,
        errors=errors,
    )


@router.get("/search-urls")
async def get_search_urls(
    location: str = Query(...),
    max_price: float = Query(2800),
    min_bedrooms: int = Query(2),
    min_bathrooms: int = Query(2),
    pets_allowed: bool = Query(True),
    need_elevator: bool = Query(True),
    prefer_terrace: bool = Query(True),
):
    """URLs directas de búsqueda en cada plataforma (fallback si scraping falla)."""
    params = SearchParams(
        location=location, max_price=max_price, min_bedrooms=min_bedrooms,
        min_bathrooms=min_bathrooms, pets_allowed=pets_allowed,
        need_elevator=need_elevator, prefer_terrace=prefer_terrace,
    )
    return {name: SCRAPERS[name]().get_direct_search_url(params) for name in SCRAPERS}


@router.get("/is-coastal")
async def is_coastal_city(city: str = Query(...)):
    """Verifica si una ciudad tiene costa (para el filtro vista al mar)."""
    city_n = normalize(city)
    is_coastal = any(city_n in normalize(c) or normalize(c) in city_n for c in COASTAL_CITIES)
    return {"city": city, "is_coastal": is_coastal}
