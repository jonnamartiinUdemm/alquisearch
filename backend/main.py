"""
API principal de la plataforma de búsqueda de alquileres en España.
Busca en múltiples plataformas (Idealista, Fotocasa, Habitaclia, Pisos.com)
y filtra resultados según criterios específicos.
"""
import asyncio
import os
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import Property, SearchParams, SearchResult
from filters import filter_properties
from scrapers import IdealistaScraper, FotocasaScraper, HabitacliaScraper, PisosScraper, HousingAnywhereScraper
from demo_data import DEMO_PROPERTIES, CITY_DATA
from cache import get_cached, set_cached, params_to_hash, clear_expired
from favorites import get_favorites, add_favorite, remove_favorite, toggle_favorite, clear_favorites, get_favorite_ids
from neighborhoods import get_suggestions
from auth import (
    register_user, login_user, logout_token, validate_token,
    get_current_user, list_users, get_user, update_user,
    delete_user, purge_expired_sessions,
)
from tracking import (
    get_tracking, get_tracking_flat, add_to_tracking,
    update_stage, update_notes, delete_from_tracking,
    get_stages_info, STAGES,
)

app = FastAPI(
    title="Buscador de Alquileres España",
    description="Plataforma unificada de búsqueda de alquileres en España",
    version="1.0.0",
)

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir frontend estático
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# Mapa de scrapers por plataforma
SCRAPERS = {
    "idealista": IdealistaScraper,
    "fotocasa": FotocasaScraper,
    "habitaclia": HabitacliaScraper,
    "pisos.com": PisosScraper,
    "housinganywhere": HousingAnywhereScraper,
}

# Ciudades costeras de España (para filtro de vista al mar)
COASTAL_CITIES = [
    "barcelona", "valencia", "málaga", "malaga", "alicante", "cádiz", "cadiz",
    "bilbao", "santander", "gijón", "gijon", "vigo", "a coruña", "a coruna",
    "san sebastián", "san sebastian", "tarragona", "castellón", "castellon",
    "almería", "almeria", "huelva", "marbella", "palma de mallorca", "palma",
    "las palmas de gran canaria", "las palmas", "santa cruz de tenerife",
    "ibiza", "menorca", "cartagena", "benidorm", "torrevieja", "estepona",
    "fuengirola", "nerja", "lloret de mar", "sitges", "roses", "salou",
    "dénia", "denia", "gandía", "gandia", "badalona", "el puerto de santa maría",
    "rota", "chipiona", "conil", "zahara", "pontevedra",
]

# Datos de demostración importados desde demo_data.py (176+ propiedades)
# DEMO_PROPERTIES se importa de demo_data.py – ver import arriba


def _normalize(text: str) -> str:
    """Normaliza texto quitando tildes para búsqueda aproximada."""
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n", "ü": "u", "à": "a", "è": "e", "ì": "i",
        "ò": "o", "ù": "u", "ï": "i", "ç": "c",
    }
    result = text.lower()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


# Ciudades principales para sugerencias de auto-complete
SPANISH_CITIES = [
    "Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga", "Zaragoza",
    "Bilbao", "Alicante", "Córdoba", "Valladolid", "Granada", "Murcia",
    "Palma de Mallorca", "Las Palmas de Gran Canaria", "San Sebastián",
    "Vitoria-Gasteiz", "Pamplona", "Santander", "Gijón", "Oviedo",
    "Santa Cruz de Tenerife", "Salamanca", "Burgos", "León", "Tarragona",
    "Girona", "Lleida", "Cádiz", "Huelva", "Almería", "Jaén",
    "Toledo", "Badajoz", "Cáceres", "Logroño", "Huesca", "Teruel",
    "Soria", "Segovia", "Ávila", "Zamora", "Palencia", "Cuenca",
    "Guadalajara", "Ciudad Real", "Albacete", "Lugo", "Ourense",
    "Pontevedra", "A Coruña", "Vigo", "Marbella", "Elche",
    "Sabadell", "Terrassa", "Hospitalet de Llobregat", "Badalona",
    "Getafe", "Alcalá de Henares", "Fuenlabrada", "Leganés",
    "Torrejón de Ardoz", "Alcorcón", "Móstoles", "Reus",
    "Sant Cugat del Vallès", "Castellón de la Plana",
]


@app.get("/")
async def root():
    """Sirve la página principal."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Buscador de Alquileres España - API activa"}


@app.get("/api/cities")
async def get_cities(q: str = Query("", description="Filtro de búsqueda")):
    """
    Búsqueda predictiva de ciudades y barrios.
    Usa el índice completo de neighborhoods.py (1200+ barrios, 25 ciudades).
    """
    if not q:
        return [c for c in SPANISH_CITIES[:20]]

    suggestions = get_suggestions(q, limit=15)
    # Devolver labels formateados para retrocompatibilidad con el frontend
    return [s["label"] for s in suggestions]


@app.post("/api/search", response_model=SearchResult)
async def search_properties(params: SearchParams):
    """
    Busca propiedades en todas las plataformas configuradas.
    Combina resultados de scraping real y datos de demostración.
    """
    all_properties: List[Property] = []
    errors: List[str] = []
    platforms_searched: List[str] = []

    # 0. Comprobar caché de scraping
    p_hash = params_to_hash(params.model_dump())
    cached = get_cached(params.location, p_hash)
    if cached is not None:
        print(f"[Cache] HIT — {len(cached)} propiedades cacheadas para «{params.location}»")
        all_properties = [Property(**p) for p in cached]
        platforms_searched = list(params.platforms)
    else:
        # 1. Intentar scraping real en las plataformas seleccionadas (en paralelo)
        async def _scrape_platform(platform_name: str) -> List[Property]:
            """Ejecuta un scraper individual y retorna sus resultados."""
            if platform_name not in SCRAPERS:
                return []
            scraper_class = SCRAPERS[platform_name]
            scraper = scraper_class()
            try:
                print(f"\n--- Buscando en {platform_name} ---")
                props = await scraper.search(params)
                print(f"[{platform_name}] {len(props)} propiedades encontradas vía scraping")
                return props
            except Exception as e:
                error_msg = f"Error buscando en {platform_name}: {str(e)}"
                errors.append(error_msg)
                print(f"[{platform_name}] {error_msg}")
                return []
            finally:
                await scraper.close()

        # Lanzar todos los scrapers en paralelo con asyncio.gather
        tasks = []
        valid_platforms = []
        for platform_name in params.platforms:
            if platform_name in SCRAPERS:
                tasks.append(_scrape_platform(platform_name))
                valid_platforms.append(platform_name)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for platform_name, result in zip(valid_platforms, results):
                platforms_searched.append(platform_name)
                if isinstance(result, Exception):
                    errors.append(f"Error en {platform_name}: {str(result)}")
                elif isinstance(result, list):
                    all_properties.extend(result)

        # Guardar en caché los resultados del scraping (antes de mezclar con demos)
        if all_properties:
            set_cached(params.location, p_hash,
                       [p.model_dump() for p in all_properties])
            print(f"[Cache] MISS — guardadas {len(all_properties)} propiedades en caché")

    # 2. Agregar datos de demostración filtrados por ubicación
    location_lower = params.location.lower().strip()

    # Parsear si es "Barrio, Ciudad" 
    search_neighborhood = ""
    search_city = location_lower
    if "," in location_lower:
        parts = [p.strip() for p in location_lower.split(",", 1)]
        search_neighborhood = parts[0]
        search_city = parts[1]

    demo_filtered = []
    for prop in DEMO_PROPERTIES:
        if not location_lower:
            demo_filtered.append(prop.model_copy(deep=True))
            continue

        prop_city_norm = _normalize(prop.city)
        prop_neighborhood_norm = _normalize(prop.neighborhood)
        prop_province_norm = _normalize(prop.province)

        # Si se especificó barrio, filtrar por barrio + ciudad
        if search_neighborhood:
            city_match = _normalize(search_city) in prop_city_norm or _normalize(search_city) in prop_province_norm
            neighborhood_match = _normalize(search_neighborhood) in prop_neighborhood_norm
            if city_match and neighborhood_match:
                demo_filtered.append(prop.model_copy(deep=True))
        else:
            # Búsqueda general por ciudad/provincia/barrio (insensible a tildes)
            location_norm = _normalize(location_lower)
            prop_location = f"{prop_city_norm} {prop_province_norm} {prop_neighborhood_norm}"
            if location_norm in prop_location:
                demo_filtered.append(prop.model_copy(deep=True))

    # Siempre agregar demos para garantizar resultados completos
    all_properties.extend(demo_filtered)
    if demo_filtered:
        print(f"[Demo] Agregadas {len(demo_filtered)} propiedades de demostración")

    # 3. Eliminar duplicados por URL
    seen_urls = set()
    unique_properties = []
    for prop in all_properties:
        if prop.url not in seen_urls:
            seen_urls.add(prop.url)
            unique_properties.append(prop)

    # 4. Aplicar filtros y scoring
    filtered_properties = filter_properties(unique_properties, params)

    print(f"\n=== Total: {len(filtered_properties)} propiedades después de filtrar ===")

    return SearchResult(
        properties=filtered_properties,
        total=len(filtered_properties),
        location=params.location,
        platforms_searched=platforms_searched,
        errors=errors,
    )


@app.get("/api/search-urls")
async def get_search_urls(
    location: str = Query(..., description="Ubicación de búsqueda"),
    max_price: float = Query(2800),
    min_bedrooms: int = Query(2),
    min_bathrooms: int = Query(2),
    pets_allowed: bool = Query(True),
    need_elevator: bool = Query(True),
    prefer_terrace: bool = Query(True),
):
    """
    Retorna las URLs directas de búsqueda en cada plataforma.
    Útil como fallback si el scraping falla.
    """
    params = SearchParams(
        location=location,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        min_bathrooms=min_bathrooms,
        pets_allowed=pets_allowed,
        need_elevator=need_elevator,
        prefer_terrace=prefer_terrace,
    )

    urls = {}
    for name, scraper_class in SCRAPERS.items():
        scraper = scraper_class()
        urls[name] = scraper.get_direct_search_url(params)

    return urls


# ---------------------------------------------------------------------------
# Favoritos API (persistente en SQLite)
# ---------------------------------------------------------------------------

@app.get("/api/favorites/{session_id}")
async def list_favorites(session_id: str):
    """Devuelve las propiedades favoritas de una sesión."""
    if not session_id or len(session_id) < 8:
        raise HTTPException(status_code=400, detail="session_id inválido")
    props = get_favorites(session_id)
    ids = get_favorite_ids(session_id)
    return {"favorites": props, "ids": ids, "count": len(props)}


@app.post("/api/favorites/{session_id}")
async def save_favorite(session_id: str, prop: Property):
    """Añade o actualiza una propiedad en favoritos."""
    if not session_id or len(session_id) < 8:
        raise HTTPException(status_code=400, detail="session_id inválido")
    result = toggle_favorite(session_id, prop.model_dump())
    return result


@app.delete("/api/favorites/{session_id}/{prop_id}")
async def delete_favorite(session_id: str, prop_id: str):
    """Elimina una propiedad de favoritos."""
    if not session_id or len(session_id) < 8:
        raise HTTPException(status_code=400, detail="session_id inválido")
    removed = remove_favorite(session_id, prop_id)
    ids = get_favorite_ids(session_id)
    return {"removed": removed, "prop_id": prop_id, "count": len(ids)}


@app.delete("/api/favorites/{session_id}")
async def delete_all_favorites(session_id: str):
    """Elimina todos los favoritos de una sesión."""
    if not session_id or len(session_id) < 8:
        raise HTTPException(status_code=400, detail="session_id inválido")
    count = clear_favorites(session_id)
    return {"cleared": count}


@app.get("/api/is-coastal")
async def is_coastal_city(city: str = Query(..., description="Nombre de la ciudad")):
    """Verifica si una ciudad es costera (para mostrar filtro de vista al mar)."""
    city_norm = _normalize(city)

    is_coastal = any(
        city_norm in _normalize(c) or _normalize(c) in city_norm
        for c in COASTAL_CITIES
    )
    return {"city": city, "is_coastal": is_coastal}


# ---------------------------------------------------------------------------
# Auth API
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str   # puede ser email o username
    password: str

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email:    Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


@app.post("/api/auth/register")
async def auth_register(req: RegisterRequest):
    try:
        result = register_user(req.username, req.email, req.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
async def auth_login(req: LoginRequest):
    try:
        result = login_user(req.username, req.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/auth/logout")
async def auth_logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        logout_token(authorization[7:])
    return {"ok": True}


@app.get("/api/auth/me")
async def auth_me(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user


# ---- Admin: CRUD de usuarios ----

def _require_admin(authorization: Optional[str]) -> dict:
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return user


@app.get("/api/admin/users")
async def admin_list_users(authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    return list_users()


@app.post("/api/admin/users")
async def admin_create_user(req: RegisterRequest, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        result = register_user(req.username, req.email, req.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/admin/users/{user_id}")
async def admin_get_user(user_id: str, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    u = get_user(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return u


@app.put("/api/admin/users/{user_id}")
async def admin_update_user(user_id: str, req: UpdateUserRequest, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        data = {k: v for k, v in req.model_dump().items() if v is not None}
        return update_user(user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: str, authorization: Optional[str] = Header(None)):
    admin = _require_admin(authorization)
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    ok = delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=400, detail="No se puede eliminar (admin o no existe)")
    return {"deleted": user_id}


# ---------------------------------------------------------------------------
# Tracking API (pipeline de alquiler)
# ---------------------------------------------------------------------------

class TrackingAddRequest(BaseModel):
    prop_data: dict
    stage: str = "interesado"
    notes: str = ""

class TrackingUpdateRequest(BaseModel):
    stage: Optional[str] = None
    notes: Optional[str] = None


def _get_user_id(authorization: Optional[str], session_id: Optional[str]) -> str:
    """Devuelve el user_id autenticado o el session_id anónimo."""
    user = get_current_user(authorization)
    if user:
        return user["id"]
    if not session_id:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    return session_id


@app.get("/api/tracking")
async def tracking_get(
    session_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Devuelve el pipeline de seguimiento agrupado por etapa."""
    uid = _get_user_id(authorization, session_id)
    board = get_tracking(uid)
    return {"board": board, "stages": get_stages_info(), "user_id": uid}


@app.post("/api/tracking")
async def tracking_add(
    req: TrackingAddRequest,
    session_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    uid = _get_user_id(authorization, session_id)
    try:
        entry = add_to_tracking(uid, req.prop_data, req.stage, req.notes)
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/api/tracking/{tracking_id}")
async def tracking_update(
    tracking_id: str,
    req: TrackingUpdateRequest,
    session_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    uid = _get_user_id(authorization, session_id)
    try:
        if req.stage:
            return update_stage(tracking_id, uid, req.stage, req.notes)
        elif req.notes is not None:
            return update_notes(tracking_id, uid, req.notes)
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/tracking/{tracking_id}")
async def tracking_delete(
    tracking_id: str,
    session_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    uid = _get_user_id(authorization, session_id)
    ok = delete_from_tracking(tracking_id, uid)
    return {"deleted": ok}


@app.get("/api/tracking/stages")
async def tracking_stages():
    """Devuelve la lista de etapas disponibles."""
    return get_stages_info()


# ---------------------------------------------------------------------------
# Admin panel frontend
# ---------------------------------------------------------------------------

@app.get("/admin")
async def admin_panel():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return JSONResponse({"error": "Panel de administración no encontrado"}, status_code=404)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    purge_expired_sessions()
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
