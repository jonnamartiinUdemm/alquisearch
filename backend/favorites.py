"""
favorites.py
============
Persistencia de favoritos en SQLite.
Usa session_id (cookie UUID) para identificar al usuario sin autenticación.
Cada favorito almacena el JSON completo de la propiedad para que funcione
aunque la búsqueda original ya no esté en caché.
"""
import json
import sqlite3
import pathlib
from datetime import datetime
from typing import List, Optional

import os
_db_dir = pathlib.Path(os.environ.get("DB_DIR", str(pathlib.Path(__file__).parent)))
_db_dir.mkdir(parents=True, exist_ok=True)
DB_PATH = _db_dir / "favorites.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table() -> None:
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                session_id  TEXT NOT NULL,
                prop_id     TEXT NOT NULL,
                prop_data   TEXT NOT NULL,     -- JSON completo de la propiedad
                added_at    TEXT NOT NULL,
                PRIMARY KEY (session_id, prop_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fav_session ON favorites(session_id)")
        conn.commit()


_ensure_table()


def get_favorites(session_id: str) -> List[dict]:
    """Devuelve todas las propiedades favoritas de una sesión."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT prop_data FROM favorites WHERE session_id = ? ORDER BY added_at DESC",
            (session_id,)
        ).fetchall()
    return [json.loads(row["prop_data"]) for row in rows]


def get_favorite_ids(session_id: str) -> List[str]:
    """Devuelve solo los IDs de las propiedades favoritas."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT prop_id FROM favorites WHERE session_id = ?",
            (session_id,)
        ).fetchall()
    return [row["prop_id"] for row in rows]


def add_favorite(session_id: str, prop_data: dict) -> bool:
    """
    Añade una propiedad a favoritos. Devuelve True si se añadió, False si ya existía.
    """
    prop_id = prop_data.get("id", "")
    if not prop_id:
        return False
    now = datetime.utcnow().isoformat()
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO favorites (session_id, prop_id, prop_data, added_at) VALUES (?, ?, ?, ?)",
                (session_id, prop_id, json.dumps(prop_data, ensure_ascii=False), now)
            )
            conn.commit()
        return True
    except Exception:
        return False


def remove_favorite(session_id: str, prop_id: str) -> bool:
    """Elimina una propiedad de favoritos. Devuelve True si existía."""
    with _get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM favorites WHERE session_id = ? AND prop_id = ?",
            (session_id, prop_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def toggle_favorite(session_id: str, prop_data: dict) -> dict:
    """
    Alterna el estado favorito de una propiedad.
    Devuelve {'action': 'added'|'removed', 'prop_id': str, 'count': int}
    """
    prop_id = prop_data.get("id", "")
    ids = get_favorite_ids(session_id)
    if prop_id in ids:
        remove_favorite(session_id, prop_id)
        action = "removed"
    else:
        add_favorite(session_id, prop_data)
        action = "added"
    count = len(get_favorite_ids(session_id))
    return {"action": action, "prop_id": prop_id, "count": count}


def clear_favorites(session_id: str) -> int:
    """Elimina todos los favoritos de una sesión. Devuelve cuántos se eliminaron."""
    with _get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM favorites WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        return cursor.rowcount
