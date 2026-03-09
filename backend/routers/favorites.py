"""
routers/favorites.py
====================
Rutas de gestión de favoritos (persistidos en SQLite por session_id).
"""
from fastapi import APIRouter, HTTPException

from models import Property
from favorites import get_favorites, remove_favorite, toggle_favorite, clear_favorites, get_favorite_ids

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


def _validate_session(session_id: str):
    if not session_id or len(session_id) < 8:
        raise HTTPException(status_code=400, detail="session_id inválido")


@router.get("/{session_id}")
async def list_favorites(session_id: str):
    """Devuelve las propiedades favoritas de una sesión."""
    _validate_session(session_id)
    props = get_favorites(session_id)
    ids = get_favorite_ids(session_id)
    return {"favorites": props, "ids": ids, "count": len(props)}


@router.post("/{session_id}")
async def save_favorite(session_id: str, prop: Property):
    """Alterna (añade/elimina) una propiedad de favoritos."""
    _validate_session(session_id)
    return toggle_favorite(session_id, prop.model_dump())


@router.delete("/{session_id}/{prop_id}")
async def delete_favorite(session_id: str, prop_id: str):
    """Elimina una propiedad concreta de favoritos."""
    _validate_session(session_id)
    removed = remove_favorite(session_id, prop_id)
    return {"removed": removed, "prop_id": prop_id, "count": len(get_favorite_ids(session_id))}


@router.delete("/{session_id}")
async def delete_all_favorites(session_id: str):
    """Elimina todos los favoritos de una sesión."""
    _validate_session(session_id)
    return {"cleared": clear_favorites(session_id)}
