"""
Scraper para Habitaclia (habitaclia.com).

Habitaclia usa Cloudflare Lambda@Edge que bloquea httpx. Usamos cloudscraper
con firefox/darwin que puede bypasear esta protección. cloudscraper es síncrono
así que lo ejecutamos en ThreadPoolExecutor.
"""
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from bs4 import BeautifulSoup, Tag

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

import sys
sys.path.insert(0, '..')
from models import Property, SearchParams
from scrapers.base import BaseScraper, _text_denies_pets

_executor = ThreadPoolExecutor(max_workers=3)


class HabitacliaScraper(BaseScraper):
    PLATFORM_NAME = "habitaclia"
    BASE_URL = "https://www.habitaclia.com"

    LOCATION_MAP = {
        "madrid": "madrid",
        "barcelona": "barcelona-702",
        "valencia": "valencia",
        "sevilla": "sevilla",
        "malaga": "malaga",
        "zaragoza": "zaragoza",
        "bilbao": "bilbao",
        "alicante": "alicante-alacant",
        "granada": "granada",
        "murcia": "murcia",
        "palma": "palma-de-mallorca",
        "santander": "santander",
        "gijon": "gijon",
        "oviedo": "oviedo",
        "vigo": "vigo",
        "tarragona": "tarragona",
        "girona": "girona",
        "lleida": "lleida",
    }

    def _get_location_slug(self, location: str) -> str:
        loc = self._normalize_location(location)
        for key, slug in self.LOCATION_MAP.items():
            if key in loc or loc in key:
                return slug
        return loc

    def __init__(self):
        super().__init__()
        if HAS_CLOUDSCRAPER:
            self._scraper = cloudscraper.create_scraper(
                browser={"browser": "firefox", "platform": "darwin"}
            )
        else:
            self._scraper = None

    def _fetch_sync(self, url: str) -> Optional[str]:
        """Fetch síncrono con cloudscraper (para ejecutar en thread)."""
        if not self._scraper:
            return None
        try:
            import time
            time.sleep(1.5)  # Rate limiting
            resp = self._scraper.get(url, timeout=30)
            if resp.status_code == 200 and len(resp.text) > 15000:
                return resp.text
            if "pardon" in resp.text.lower() or "interruption" in resp.text.lower():
                print(f"[Habitaclia] Cloudflare challenge en: {url}")
                return None
            return resp.text if resp.status_code == 200 else None
        except Exception as e:
            print(f"[Habitaclia] Error fetch: {e}")
            return None

    async def _fetch_page(self, url: str) -> Optional[str]:
        """Override: usa cloudscraper en un thread para bypass Cloudflare."""
        if self._scraper:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(_executor, self._fetch_sync, url)
        # Fallback a httpx si no hay cloudscraper
        return await super()._fetch_page(url)

    def _build_search_url(self, params: SearchParams) -> str:
        loc_slug = self._get_location_slug(params.location)
        url = f"{self.BASE_URL}/alquiler-{loc_slug}.htm"

        # IMPORTANTE: Habitaclia bloquea con Cloudflare si usamos 2+ query params.
        # Solo usamos UN filtro (el más impactante: precio máximo) y filtramos el
        # resto client-side con filter_properties().
        if params.max_price:
            url += f"?preciohasta={int(params.max_price)}"

        return url

    def get_direct_search_url(self, params: SearchParams) -> str:
        """URL completa con todos los filtros para el usuario (no para scraping)."""
        loc_slug = self._get_location_slug(params.location)
        url = f"{self.BASE_URL}/alquiler-{loc_slug}.htm"
        query_parts = []
        if params.max_price:
            query_parts.append(f"preciohasta={int(params.max_price)}")
        if params.min_bedrooms and params.min_bedrooms > 0:
            query_parts.append(f"habdesde={params.min_bedrooms}")
        if getattr(params, 'pets_allowed', False):
            query_parts.append("mascotas=si")
        if getattr(params, 'need_elevator', False):
            query_parts.append("ascensor=si")
        if query_parts:
            url += "?" + "&".join(query_parts)
        return url

    def _parse_listing(self, element: Tag, base_url: str = "") -> Optional[Property]:
        try:
            prop = Property()
            prop.platform = self.PLATFORM_NAME

            # Título y enlace — confirmed: h3.list-item-title > a
            link = element.select_one("h3.list-item-title a")
            if not link:
                link = element.select_one("h3 a, a[href*='alquiler']")
            if link:
                prop.title = link.get_text(strip=True)
                href = link.get("href", "")
                prop.url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                prop.id = self._generate_id(prop.url)

            # Precio — confirmed: [itemprop='price'] => "2.500 €"
            price_el = element.select_one("[itemprop='price']")
            if not price_el:
                price_el = element.select_one(".list-item-price, [class*='price']")
            if price_el:
                price_val = self._extract_number(price_el.get_text(strip=True))
                if price_val:
                    prop.price = price_val

            # Características — confirmed: p.list-item-feature => "100m2- 3 habitaciones - 2 baños - 25,00€/m2"
            feat_el = element.select_one("p.list-item-feature")
            if feat_el:
                feat_text = feat_el.get_text(strip=True).lower()
                # Extraer habitaciones
                m = re.search(r'(\d+)\s*habitaci', feat_text)
                if m:
                    prop.bedrooms = int(m.group(1))
                # Extraer baños
                m = re.search(r'(\d+)\s*ba[ñn]o', feat_text)
                if m:
                    prop.bathrooms = int(m.group(1))
                # Extraer superficie — "100m2" o "100 m²"
                m = re.search(r'(\d+)\s*m[²2]?', feat_text)
                if m:
                    prop.area_m2 = float(m.group(1))

            # Ubicación — confirmed: p.list-item-location span => "Madrid - Ibiza"
            loc_el = element.select_one("p.list-item-location span")
            if not loc_el:
                loc_el = element.select_one("p.list-item-location")
            if loc_el:
                loc_text = loc_el.get_text(strip=True)
                prop.address = loc_text
                # Separar ciudad y barrio: "Madrid - Ibiza"
                if " - " in loc_text:
                    parts = loc_text.split(" - ", 1)
                    prop.city = parts[0].strip()
                    prop.neighborhood = parts[1].strip()

            # Descripción — confirmed: p.list-item-description
            desc_el = element.select_one("p.list-item-description")
            if desc_el:
                prop.description = desc_el.get_text(strip=True)
                self._extract_features_from_text(prop, prop.description.lower())

            # Imagen — confirmed: img[itemprop='image']
            img = element.select_one("img[itemprop='image']")
            if not img:
                img = element.select_one("img")
            if img:
                src = img.get("src") or img.get("data-src") or ""
                if src:
                    if src.startswith("//"):
                        src = f"https:{src}"
                    prop.images.append(src)

            return prop if prop.url else None

        except Exception as e:
            print(f"[Habitaclia] Error parseando listado: {e}")
            return None

    def _extract_features_from_text(self, prop: Property, text: str):
        if "terraza" in text:
            prop.has_terrace = True
        if "balcón" in text or "balcon" in text:
            prop.has_balcony = True
        if "mascota" in text or "animal" in text:
            if _text_denies_pets(text):
                prop.pets_allowed = False
            elif prop.pets_allowed is None:
                prop.pets_allowed = True
        if "ascensor" in text:
            prop.has_elevator = "sin ascensor" not in text
        if "empadron" in text:
            prop.allows_empadronamiento = True
        if "amueblad" in text:
            prop.furnished = True
        if "aire acondicionado" in text:
            prop.has_air_conditioning = True
        if "calefacción" in text or "calefaccion" in text:
            prop.has_heating = True
        if "garaje" in text or "parking" in text:
            prop.has_parking = True
        if "piscina" in text:
            prop.has_pool = True
        if any(t in text for t in ["metro", "bus", "transporte", "cercanías", "tren"]):
            prop.public_transport_nearby = True
        if any(s in text for s in ["supermercado", "farmacia", "colegio", "hospital"]):
            prop.services_nearby = True

    def _build_page_url(self, base_url: str, page: int) -> str:
        """Construye la URL para una página específica de resultados."""
        if page <= 1:
            return base_url
        # habitaclia usa ?pag=N como parámetro
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}pag={page}"

    async def search(self, params: SearchParams) -> List[Property]:
        properties = []
        base_url = self._build_search_url(params)
        seen_urls = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = self._build_page_url(base_url, page)
            print(f"[Habitaclia] Buscando página {page}: {url}")

            html = await self._fetch_page(url)
            if not html:
                print(f"[Habitaclia] No se pudo obtener la página {page}")
                break

            soup = self._parse_html(html)

            # Detectar Cloudflare challenge
            if "Pardon Our Interruption" in html or len(html) < 15000:
                print(f"[Habitaclia] Página bloqueada por Cloudflare en página {page}")
                break

            # Confirmed: article.js-list-item (15 per page)
            listings = soup.select("article.js-list-item")
            if not listings:
                listings = soup.select("article.list-item-container")
            if not listings:
                listings = soup.select("article")

            if not listings:
                print(f"[Habitaclia] Sin resultados en página {page}, fin de paginación")
                break

            print(f"[Habitaclia] Encontrados {len(listings)} listados en página {page}")

            new_count = 0
            for listing in listings:
                prop = self._parse_listing(listing)
                if prop and prop.url not in seen_urls:
                    prop.city = params.location
                    properties.append(prop)
                    seen_urls.add(prop.url)
                    new_count += 1

            if new_count == 0:
                break

        await self.close()
        print(f"[Habitaclia] Total: {len(properties)} propiedades")
        return properties
