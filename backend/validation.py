"""
Validaciones de integridad para propiedades scrapeadas.
"""
from __future__ import annotations

from urllib.parse import urlparse

from models import Property


PLATFORM_DOMAINS = {
    "idealista": "idealista.com",
    "fotocasa": "fotocasa.es",
    "habitaclia": "habitaclia.com",
    "pisos.com": "pisos.com",
    "housinganywhere": "housinganywhere.com",
}


def _host_from_url(url: str) -> str:
    if not url:
        return ""
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def has_valid_platform_url(prop: Property) -> bool:
    """Valida que la URL de la propiedad coincida con el dominio esperado de la plataforma."""
    expected_domain = PLATFORM_DOMAINS.get((prop.platform or "").lower())
    if not expected_domain:
        return False

    host = _host_from_url(prop.url)
    return bool(host) and (host == expected_domain or host.endswith(f".{expected_domain}"))


def normalize_coordinates(prop: Property) -> None:
    """Normaliza coordenadas inválidas y marca precisión de ubicación."""
    lat = prop.latitude
    lng = prop.longitude

    has_valid_lat = lat is not None and -90 <= lat <= 90
    has_valid_lng = lng is not None and -180 <= lng <= 180

    if has_valid_lat and has_valid_lng:
        prop.location_precision = "exact"
    else:
        prop.latitude = None
        prop.longitude = None
        prop.location_precision = "approximate"
