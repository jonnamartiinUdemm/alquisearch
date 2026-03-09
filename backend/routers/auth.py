"""
routers/auth.py
===============
Rutas de autenticación y panel de administración de usuarios (CRUD).
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from auth import (
    register_user, login_user, logout_token, get_current_user,
    list_users, get_user, update_user, delete_user,
)

router = APIRouter(tags=["auth"])


# ── Modelos de petición ────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str = ""
    password: str


class LoginRequest(BaseModel):
    username: str   # puede ser email o username
    password: str


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


# ── Dependencia de administrador ──────────────────────────────────────────

def _require_admin(authorization: Optional[str]) -> dict:
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return user


# ── Auth pública ──────────────────────────────────────────────────────────

@router.post("/api/auth/register")
async def auth_register(req: RegisterRequest):
    try:
        return register_user(req.username, req.email, req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/auth/login")
async def auth_login(req: LoginRequest):
    try:
        return login_user(req.username, req.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/api/auth/logout")
async def auth_logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        logout_token(authorization[7:])
    return {"ok": True}


@router.get("/api/auth/me")
async def auth_me(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user


# ── Admin: CRUD de usuarios ────────────────────────────────────────────────

@router.get("/api/admin/users")
async def admin_list_users(authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    return list_users()


@router.post("/api/admin/users")
async def admin_create_user(req: RegisterRequest, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        return register_user(req.username, req.email, req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/admin/users/{user_id}")
async def admin_get_user(user_id: str, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    u = get_user(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return u


@router.put("/api/admin/users/{user_id}")
async def admin_update_user(user_id: str, req: UpdateUserRequest, authorization: Optional[str] = Header(None)):
    _require_admin(authorization)
    try:
        data = {k: v for k, v in req.model_dump().items() if v is not None}
        return update_user(user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: str, authorization: Optional[str] = Header(None)):
    admin = _require_admin(authorization)
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    if not delete_user(user_id):
        raise HTTPException(status_code=400, detail="No se puede eliminar (admin o no existe)")
    return {"deleted": user_id}
