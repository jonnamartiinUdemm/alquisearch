"""
Scraper base con funcionalidad compartida.
"""
import re
import httpx
import asyncio
import random
import hashlib
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import sys
sys.path.insert(0, '..')
from models import Property, SearchParams


# Patrones negativos para detección de mascotas
_PET_DENY_PATTERNS = re.compile(
    r"no\s+(se\s+)?(admiten?|permiten?|aceptan?|permite)\s+(mascotas?|animales?|pets?)"
    r"|sin\s+mascotas?"
    r"|\bno\s+mascotas?\b"
    r"|\bno\s+pets?\b"
    r"|\bpets?\s+not\s+allowed\b"
    r"|\bmascotas?\s+no\b"
    r"|\banimales?\s+no\b"
    r"|\bprohibid[oa]s?\s+(mascotas?|animales?)\b"
    r"|\b(mascotas?|animales?)\s+prohibid[oa]s?\b",
    re.IGNORECASE
)


def _text_denies_pets(text: str) -> bool:
    """
    Detecta si un texto indica explícitamente que NO se admiten mascotas.
    Retorna True si el texto niega mascotas.
    """
    return bool(_PET_DENY_PATTERNS.search(text))


class BaseScraper(ABC):
    """Clase base para todos los scrapers de plataformas inmobiliarias."""

    PLATFORM_NAME: str = ""
    BASE_URL: str = ""
    MAX_PAGES: int = 5  # Número máximo de páginas a scrapear por plataforma

    # Mapa de provincias/ciudades a slugs de URL
    LOCATION_SLUGS: Dict[str, str] = {}

    def __init__(self):
        self.ua = UserAgent()
        self.client: Optional[httpx.AsyncClient] = None

    def _get_headers(self) -> dict:
        """Retorna headers HTTP realistas para evitar bloqueos."""
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP async."""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                headers=self._get_headers(),
                follow_redirects=True,
                timeout=30.0,
            )
        return self.client

    MAX_RETRIES: int = 3
    RETRY_DELAYS: tuple = (2.0, 5.0, 10.0)  # backoff exponencial

    async def _fetch_page(self, url: str) -> Optional[str]:
        """Descarga una página web con reintentos y back-off exponencial."""
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                client = await self._get_client()
                # Delay aleatorio para evitar rate limiting
                await asyncio.sleep(random.uniform(1.0, 3.0))

                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                last_error = e
                # No reintentar en errores 4xx (excepto 429 rate-limit)
                if 400 <= status < 500 and status != 429:
                    print(f"[{self.PLATFORM_NAME}] Error HTTP {status} (no reintentable): {url}")
                    return None
                print(f"[{self.PLATFORM_NAME}] Error HTTP {status} – intento {attempt + 1}/{self.MAX_RETRIES}: {url}")
            except httpx.RequestError as e:
                last_error = e
                print(f"[{self.PLATFORM_NAME}] Error de conexión – intento {attempt + 1}/{self.MAX_RETRIES}: {e}")
            except Exception as e:
                last_error = e
                print(f"[{self.PLATFORM_NAME}] Error inesperado – intento {attempt + 1}/{self.MAX_RETRIES}: {e}")

            # Esperar antes de reintentar (backoff)
            if attempt < self.MAX_RETRIES - 1:
                delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                jitter = random.uniform(0, delay * 0.3)
                print(f"[{self.PLATFORM_NAME}] Reintentando en {delay + jitter:.1f}s...")
                await asyncio.sleep(delay + jitter)

        print(f"[{self.PLATFORM_NAME}] Agotados {self.MAX_RETRIES} intentos para: {url}")
        return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parsea HTML a BeautifulSoup."""
        return BeautifulSoup(html, "lxml")

    def _generate_id(self, url: str) -> str:
        """Genera un ID único basado en la URL."""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def _normalize_location(self, location: str) -> str:
        """Normaliza el nombre de localización para búsqueda."""
        location = location.lower().strip()
        # Quitar tildes comunes
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
            "ñ": "n", "ü": "u"
        }
        for old, new in replacements.items():
            location = location.replace(old, new)
        return location.replace(" ", "-")

    def _extract_number(self, text: str) -> Optional[float]:
        """Extrae un número de un texto."""
        if not text:
            return None
        import re
        # Limpiar el texto
        text = text.replace(".", "").replace(",", ".").strip()
        match = re.search(r"[\d]+\.?\d*", text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    @abstractmethod
    def _build_search_url(self, params: SearchParams) -> str:
        """Construye la URL de búsqueda para la plataforma."""
        pass

    @abstractmethod
    def _parse_listing(self, element, base_url: str) -> Optional[Property]:
        """Parsea un elemento HTML de listado a un Property."""
        pass

    @abstractmethod
    async def search(self, params: SearchParams) -> List[Property]:
        """Ejecuta la búsqueda y retorna propiedades."""
        pass

    def get_direct_search_url(self, params: SearchParams) -> str:
        """Retorna la URL directa de búsqueda en la plataforma."""
        return self._build_search_url(params)

    async def close(self):
        """Cierra el cliente HTTP."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
