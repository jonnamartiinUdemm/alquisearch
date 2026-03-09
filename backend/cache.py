"""
Módulo de caché SQLite para resultados de búsqueda.
TTL configurable (por defecto 6 horas).
"""
import sqlite3
import json
import hashlib
import time
import os
from typing import Optional, List
from models import Property


_db_dir = os.environ.get("DB_DIR", os.path.dirname(__file__))
os.makedirs(_db_dir, exist_ok=True)
DB_PATH = os.path.join(_db_dir, "search_cache.db")
DEFAULT_TTL = 6 * 3600  # 6 horas en segundos


def _get_connection() -> sqlite3.Connection:
    """Conecta a la base de datos (creándola si no existe)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            cache_key TEXT PRIMARY KEY,
            data      TEXT NOT NULL,
            created   REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def _make_key(location: str, params_hash: str) -> str:
    """Genera una clave de caché determinista."""
    raw = f"{location.lower().strip()}|{params_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()


def params_to_hash(params_dict: dict) -> str:
    """Convierte parámetros de búsqueda en un hash estable."""
    # Excluir campos que no afectan los resultados del scraping
    relevant = {
        "max_price": params_dict.get("max_price"),
        "min_bedrooms": params_dict.get("min_bedrooms"),
        "min_bathrooms": params_dict.get("min_bathrooms"),
        "pets_allowed": params_dict.get("pets_allowed"),
        "platforms": sorted(params_dict.get("platforms", [])),
    }
    raw = json.dumps(relevant, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached(location: str, params_hash: str, ttl: int = DEFAULT_TTL) -> Optional[List[dict]]:
    """
    Busca resultados en caché.
    Retorna lista de dicts (serialización de Property) o None si no hay hit o expiró.
    """
    key = _make_key(location, params_hash)
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT data, created FROM search_cache WHERE cache_key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        data, created = row
        if time.time() - created > ttl:
            # Expirado — limpiar
            conn.execute("DELETE FROM search_cache WHERE cache_key = ?", (key,))
            conn.commit()
            return None
        return json.loads(data)
    finally:
        conn.close()


def set_cached(location: str, params_hash: str, properties: List[dict]) -> None:
    """Guarda resultados en caché."""
    key = _make_key(location, params_hash)
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO search_cache (cache_key, data, created) VALUES (?, ?, ?)",
            (key, json.dumps(properties, ensure_ascii=False), time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def clear_expired(ttl: int = DEFAULT_TTL) -> int:
    """Limpia entradas expiradas. Retorna número de filas eliminadas."""
    cutoff = time.time() - ttl
    conn = _get_connection()
    try:
        cursor = conn.execute("DELETE FROM search_cache WHERE created < ?", (cutoff,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def clear_all() -> int:
    """Limpia toda la caché."""
    conn = _get_connection()
    try:
        cursor = conn.execute("DELETE FROM search_cache")
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()
