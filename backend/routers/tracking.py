"""
routers/tracking.py
===================
Rutas del pipeline kanban de seguimiento del proceso de alquiler.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel

from auth import get_current_user
from tracking import (
    get_tracking, add_to_tracking, update_stage, update_notes,
    delete_from_tracking, get_stages_info,
)

router = APIRouter(prefix="/api/tracking", tags=["tracking"])


# ── Modelos de petición ────────────────────────────────────────────────────

class TrackingAddRequest(BaseModel):
    prop_data: dict
    stage: str = "interesado"
    notes: str = ""


class TrackingUpdateRequest(BaseModel):
    stage: Optional[str] = None
    notes: Optional[str] = None


# ── Dependencia: usuario autenticado o anónimo por session_id ─────────────

def _resolve_user(authorization: Optional[str], session_id: Optional[str]) -> str:
    user = get_current_user(authorization)
    if user:
        return user["id"]
    if not session_id:
        raise HTTPException(status_code=401, detail="Autenticación o session_id requeridos")
    return session_id


# ── Rutas ─────────────────────────────────────────────────────────────────

@router.get("")
async def tracking_get(
    session_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Devuelve el pipeline agrupado por etapa."""
    uid = _resolve_user(authorization, session_id)
    return {"board": get_tracking(uid), "stages": get_stages_info(), "user_id": uid}


@router.post("")
async def tracking_add(
    req: TrackingAddRequest,
    session_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Añade o actualiza una propiedad en el pipeline."""
    uid = _resolve_user(authorization, session_id)
    try:
        return add_to_tracking(uid, req.prop_data, req.stage, req.notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{tracking_id}")
async def tracking_update(
    tracking_id: str,
    req: TrackingUpdateRequest,
    session_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Actualiza etapa y/o notas de una entrada del pipeline."""
    uid = _resolve_user(authorization, session_id)
    try:
        if req.stage:
            return update_stage(tracking_id, uid, req.stage, req.notes)
        if req.notes is not None:
            return update_notes(tracking_id, uid, req.notes)
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tracking_id}")
async def tracking_delete(
    tracking_id: str,
    session_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """Elimina una entrada del pipeline."""
    uid = _resolve_user(authorization, session_id)
    return {"deleted": delete_from_tracking(tracking_id, uid)}


@router.get("/stages")
async def tracking_stages():
    """Devuelve la lista de etapas disponibles."""
    return get_stages_info()
