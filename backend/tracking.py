"""
tracking.py
===========
Pipeline de seguimiento del proceso de alquiler.
Cada propiedad puede estar en una única etapa del proceso.

Etapas:
    interesado       → Guardé la propiedad, me parece interesante
    contactado       → He contactado con el propietario/agencia
    visita_programada→ He acordado una visita
    visitado         → Ya he visto el piso
    oferta_enviada   → He hecho una oferta
    negociacion      → Estamos negociando condiciones
    contrato         → He firmado / pendiente de firma
    alquilado        → Ya es mío 🎉
    descartado       → Lo descarté por algún motivo
"""
from __future__ import annotations
import json
import pathlib
import secrets
import sqlite3
from datetime import datetime
from typing import Optional

import os
_db_dir = pathlib.Path(os.environ.get("DB_DIR", str(pathlib.Path(__file__).parent)))
_db_dir.mkdir(parents=True, exist_ok=True)
DB_PATH = _db_dir / "tracking.db"

STAGES = [
    "interesado",
    "contactado",
    "visita_programada",
    "visitado",
    "oferta_enviada",
    "negociacion",
    "contrato",
    "alquilado",
    "descartado",
]

STAGE_LABELS = {
    "interesado":        "Interesado",
    "contactado":        "Contactado",
    "visita_programada": "Visita Programada",
    "visitado":          "Visitado",
    "oferta_enviada":    "Oferta Enviada",
    "negociacion":       "Negociación",
    "contrato":          "Contrato",
    "alquilado":         "Alquilado ✓",
    "descartado":        "Descartado",
}


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init_db() -> None:
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS tracking (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                prop_id     TEXT NOT NULL,
                prop_data   TEXT NOT NULL,
                stage       TEXT NOT NULL DEFAULT 'interesado',
                notes       TEXT NOT NULL DEFAULT '',
                priority    INTEGER NOT NULL DEFAULT 0,
                updated_at  TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                UNIQUE (user_id, prop_id)
            );
            CREATE INDEX IF NOT EXISTS idx_track_user  ON tracking(user_id);
            CREATE INDEX IF NOT EXISTS idx_track_stage ON tracking(stage);
        """)
        c.commit()


# ── API pública ────────────────────────────────────────────────────────────

def get_tracking(user_id: str) -> dict:
    """
    Devuelve el pipeline completo agrupado por etapa.
    { stage: [entry, ...], ... }
    """
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM tracking WHERE user_id=? ORDER BY priority DESC, updated_at DESC",
            (user_id,),
        ).fetchall()

    board: dict = {s: [] for s in STAGES}
    for row in rows:
        entry = _row_to_dict(row)
        board[entry["stage"]].append(entry)
    return board


def get_tracking_flat(user_id: str) -> list[dict]:
    """Devuelve todos los entries sin agrupar."""
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM tracking WHERE user_id=? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def add_to_tracking(user_id: str, prop_data: dict, stage: str = "interesado", notes: str = "") -> dict:
    """
    Añade o actualiza una propiedad en el pipeline.
    Si ya existe, actualiza la etapa y notas.
    """
    if stage not in STAGES:
        stage = "interesado"
    prop_id = prop_data.get("id", "")
    if not prop_id:
        raise ValueError("La propiedad no tiene ID")
    now = datetime.utcnow().isoformat()
    tid = "t_" + secrets.token_hex(10)
    with _conn() as c:
        existing = c.execute(
            "SELECT id FROM tracking WHERE user_id=? AND prop_id=?",
            (user_id, prop_id),
        ).fetchone()
        if existing:
            c.execute(
                "UPDATE tracking SET stage=?, notes=?, prop_data=?, updated_at=? WHERE user_id=? AND prop_id=?",
                (stage, notes, json.dumps(prop_data, ensure_ascii=False), now, user_id, prop_id),
            )
            tid = existing["id"]
        else:
            c.execute(
                "INSERT INTO tracking (id, user_id, prop_id, prop_data, stage, notes, priority, updated_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
                (tid, user_id, prop_id, json.dumps(prop_data, ensure_ascii=False), stage, notes, now, now),
            )
        c.commit()
    return get_entry(tid)


def update_stage(tracking_id: str, user_id: str, stage: str, notes: Optional[str] = None) -> dict:
    """Mueve una entrada a otra etapa."""
    if stage not in STAGES:
        raise ValueError(f"Etapa inválida. Opciones: {STAGES}")
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        row = c.execute(
            "SELECT id FROM tracking WHERE id=? AND user_id=?",
            (tracking_id, user_id),
        ).fetchone()
        if not row:
            raise ValueError("Seguimiento no encontrado")
        if notes is not None:
            c.execute(
                "UPDATE tracking SET stage=?, notes=?, updated_at=? WHERE id=?",
                (stage, notes, now, tracking_id),
            )
        else:
            c.execute(
                "UPDATE tracking SET stage=?, updated_at=? WHERE id=?",
                (stage, now, tracking_id),
            )
        c.commit()
    return get_entry(tracking_id)


def update_notes(tracking_id: str, user_id: str, notes: str) -> dict:
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        c.execute(
            "UPDATE tracking SET notes=?, updated_at=? WHERE id=? AND user_id=?",
            (notes, now, tracking_id, user_id),
        )
        c.commit()
    return get_entry(tracking_id)


def delete_from_tracking(tracking_id: str, user_id: str) -> bool:
    with _conn() as c:
        r = c.execute(
            "DELETE FROM tracking WHERE id=? AND user_id=?",
            (tracking_id, user_id),
        )
        c.commit()
        return r.rowcount > 0


def get_entry(tracking_id: str) -> Optional[dict]:
    with _conn() as c:
        row = c.execute("SELECT * FROM tracking WHERE id=?", (tracking_id,)).fetchone()
    return _row_to_dict(row) if row else None


def get_stages_info() -> list[dict]:
    return [{"id": s, "label": STAGE_LABELS[s]} for s in STAGES]


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    try:
        d["prop_data"] = json.loads(d["prop_data"])
    except Exception:
        d["prop_data"] = {}
    d["stage_label"] = STAGE_LABELS.get(d["stage"], d["stage"])
    return d


# Inicializar al importar
init_db()
