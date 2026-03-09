"""
auth.py
=======
Gestión de usuarios y sesiones para AlquiSearch España.
Usa SQLite + PBKDF2-SHA256 (stdlib) sin dependencias externas.

Tablas:
    users    — id, username, email, password_hash, salt, is_admin, created_at, is_active
    sessions — token, user_id, created_at, expires_at, last_seen
"""
from __future__ import annotations
import hashlib
import os
import pathlib
import re
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

_db_dir = pathlib.Path(os.environ.get("DB_DIR", str(pathlib.Path(__file__).parent)))
_db_dir.mkdir(parents=True, exist_ok=True)
DB_PATH = _db_dir / "users.db"
SESSION_HOURS = 720   # 30 días
PBKDF2_ITER   = 260_000
SALT_BYTES    = 32
TOKEN_BYTES   = 48


# ── helpers de DB ──────────────────────────────────────────────────────────
def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init_db() -> None:
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
                email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                salt          TEXT NOT NULL,
                is_admin      INTEGER NOT NULL DEFAULT 0,
                is_active     INTEGER NOT NULL DEFAULT 1,
                created_at    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token       TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                expires_at  TEXT NOT NULL,
                last_seen   TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_exp  ON sessions(expires_at);
        """)
        # Crear admin por defecto si no existe
        if not c.execute("SELECT 1 FROM users WHERE is_admin=1").fetchone():
            _create_user_tx(c, "admin", "admin@alquisearch.es", "Admin1234!", is_admin=True)
        c.commit()


# ── contraseñas ────────────────────────────────────────────────────────────
def _hash_password(password: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITER,
    )
    return dk.hex()


def _verify_password(password: str, salt: str, stored_hash: str) -> bool:
    return secrets.compare_digest(_hash_password(password, salt), stored_hash)


def _validate_password(password: str) -> Optional[str]:
    if len(password) < 8:
        return "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r"[A-Z]", password):
        return "Debe contener al menos una mayúscula"
    if not re.search(r"\d", password):
        return "Debe contener al menos un número"
    return None


# ── creación de usuario (helper interno) ──────────────────────────────────
def _create_user_tx(conn: sqlite3.Connection, username: str, email: str, password: str, is_admin: bool = False) -> dict:
    uid   = "u_" + secrets.token_hex(12)
    salt  = secrets.token_bytes(SALT_BYTES).hex()
    ph    = _hash_password(password, salt)
    now   = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO users (id, username, email, password_hash, salt, is_admin, is_active, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
        (uid, username, email, ph, salt, int(is_admin), now),
    )
    return {"id": uid, "username": username, "email": email, "is_admin": is_admin}


# ── API pública ────────────────────────────────────────────────────────────
def register_user(username: str, email: str, password: str) -> dict:
    """
    Registra un nuevo usuario.
    Devuelve dict con datos del usuario + token de sesión o lanza ValueError.
    """
    err = _validate_password(password)
    if err:
        raise ValueError(err)
    if not re.match(r"^[a-zA-Z0-9_.-]{3,40}$", username):
        raise ValueError("Usuario inválido (3–40 caracteres alfanuméricos)")
    try:
        with _conn() as c:
            user = _create_user_tx(c, username, email, password)
            c.commit()
        token = create_session(user["id"])
        return {**user, "token": token}
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            raise ValueError("Ese nombre de usuario ya está en uso")
        raise ValueError("Ese email ya está registrado")


def login_user(username_or_email: str, password: str) -> dict:
    """Autentica al usuario. Devuelve user + token o lanza ValueError."""
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM users WHERE (username=? OR email=?) AND is_active=1",
            (username_or_email, username_or_email),
        ).fetchone()
    if not row:
        raise ValueError("Credenciales incorrectas")
    if not _verify_password(password, row["salt"], row["password_hash"]):
        raise ValueError("Credenciales incorrectas")
    token = create_session(row["id"])
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "is_admin": bool(row["is_admin"]),
        "token": token,
    }


def create_session(user_id: str) -> str:
    """Crea una sesión y devuelve el token."""
    token = secrets.token_urlsafe(TOKEN_BYTES)
    now   = datetime.utcnow()
    exp   = now + timedelta(hours=SESSION_HOURS)
    with _conn() as c:
        c.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at, last_seen) VALUES (?, ?, ?, ?, ?)",
            (token, user_id, now.isoformat(), exp.isoformat(), now.isoformat()),
        )
        c.commit()
    return token


def validate_token(token: str) -> Optional[dict]:
    """
    Valida un token de sesión.
    Devuelve datos del usuario o None si el token es inválido/expirado.
    """
    if not token:
        return None
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        row = c.execute(
            """SELECT u.id, u.username, u.email, u.is_admin
               FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token=? AND s.expires_at > ? AND u.is_active=1""",
            (token, now),
        ).fetchone()
        if row:
            c.execute("UPDATE sessions SET last_seen=? WHERE token=?", (now, token))
            c.commit()
    return dict(row) if row else None


def logout_token(token: str) -> None:
    """Elimina la sesión activa."""
    with _conn() as c:
        c.execute("DELETE FROM sessions WHERE token=?", (token,))
        c.commit()


def get_current_user(authorization: Optional[str]) -> Optional[dict]:
    """Extrae y valida el token del header Authorization: Bearer <token>."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return validate_token(authorization[7:])


# ── CRUD de usuarios (admin) ───────────────────────────────────────────────
def list_users() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, username, email, is_admin, is_active, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_user(user_id: str) -> Optional[dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT id, username, email, is_admin, is_active, created_at FROM users WHERE id=?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def update_user(user_id: str, data: dict) -> dict:
    """Actualiza username, email, is_admin, is_active y opcionalmente password."""
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            raise ValueError("Usuario no encontrado")
        fields, vals = [], []
        for col in ("username", "email", "is_admin", "is_active"):
            if col in data:
                fields.append(f"{col}=?")
                vals.append(data[col])
        if "password" in data:
            err = _validate_password(data["password"])
            if err:
                raise ValueError(err)
            new_salt = secrets.token_bytes(SALT_BYTES).hex()
            fields.append("password_hash=?")
            fields.append("salt=?")
            vals.append(_hash_password(data["password"], new_salt))
            vals.append(new_salt)
        if fields:
            vals.append(user_id)
            c.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", vals)
            c.commit()
    return get_user(user_id)


def delete_user(user_id: str) -> bool:
    with _conn() as c:
        result = c.execute("DELETE FROM users WHERE id=? AND is_admin=0", (user_id,))
        c.commit()
        return result.rowcount > 0


def purge_expired_sessions() -> int:
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        r = c.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
        c.commit()
        return r.rowcount


# Inicializar DB al importar
init_db()
