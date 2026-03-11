"""
Scraper para Pisos.com (pisos.com).
"""
import re
from typing import List, Optional
from bs4 import Tag

import sys
sys.path.insert(0, '..')
from models import Property, SearchParams
from scrapers.base import BaseScraper, _text_denies_pets


class PisosScraper(BaseScraper):
    PLATFORM_NAME = "pisos.com"
    BASE_URL = "https://www.pisos.com"

    LOCATION_MAP = {
        "madrid": "madrid",
        "barcelona": "barcelona",
        "valencia": "valencia",
        "sevilla": "sevilla",
        "malaga": "malaga",
        "zaragoza": "zaragoza",
        "bilbao": "bilbao",
        "alicante": "alicante",
        "cordoba": "cordoba",
        "valladolid": "valladolid",
        "granada": "granada",
        "murcia": "murcia",
        "palma": "palma_de_mallorca",
        "las palmas": "las_palmas_de_gran_canaria",
        "san sebastian": "san_sebastian",
        "santander": "santander",
        "gijon": "gijon",
        "oviedo": "oviedo",
        "vigo": "vigo",
        "a coruna": "a_coruna",
        "tarragona": "tarragona",
        "girona": "girona",
        "lleida": "lleida",
    }

    def _get_location_slug(self, location: str) -> str:
        loc = self._normalize_location(location)
        for key, slug in self.LOCATION_MAP.items():
            if key in loc or loc in key:
                return slug
        return loc.replace("-", "_")

    def _build_search_url(self, params: SearchParams) -> str:
        loc_slug = self._get_location_slug(params.location)
        url = f"{self.BASE_URL}/alquiler/pisos-{loc_slug}/"

        query_params = []
        if params.max_price:
            query_params.append(f"precio_max={int(params.max_price)}")
        if params.min_bedrooms:
            query_params.append(f"habitaciones_min={params.min_bedrooms}")
        if params.min_bathrooms:
            query_params.append(f"banos_min={params.min_bathrooms}")
        if params.pets_allowed:
            query_params.append("mascotas=1")
        if params.need_elevator:
            query_params.append("ascensor=1")

        if query_params:
            url += "?" + "&".join(query_params)

        return url

    def _parse_listing(self, element: Tag, base_url: str = "") -> Optional[Property]:
        try:
            prop = Property()
            prop.platform = self.PLATFORM_NAME

            # Título y enlace — confirmed: a.ad-preview__title
            link = element.select_one("a.ad-preview__title, a[class*='title'], a[href*='alquilar'], a[href*='alquiler']")
            if link:
                prop.title = link.get_text(strip=True)
                href = link.get("href", "")
                prop.url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                prop.id = self._generate_id(prop.url)

            # Precio
            price_el = element.select_one(".ad-preview__price, [class*='price']")
            if price_el:
                price_val = self._extract_number(price_el.get_text(strip=True))
                if price_val:
                    prop.price = price_val

            # Características
            features = element.select(".ad-preview__char, [class*='feature'], [class*='char']")
            for feat in features:
                text = feat.get_text(strip=True).lower()
                num = self._extract_number(text)
                if num:
                    if "hab" in text or "dorm" in text:
                        prop.bedrooms = int(num)
                    elif "baño" in text or "bano" in text:
                        prop.bathrooms = int(num)
                    elif "m²" in text or "m2" in text:
                        prop.area_m2 = num

            # Descripción
            desc_el = element.select_one(".ad-preview__description, [class*='description']")
            if desc_el:
                prop.description = desc_el.get_text(strip=True)
                self._extract_features_from_text(prop, prop.description.lower())

            # Imagen
            img = element.select_one("img")
            if img:
                src = img.get("src") or img.get("data-src") or ""
                if src and "static" not in src:
                    prop.images.append(src)

            # Dirección
            addr = element.select_one(".ad-preview__address, [class*='address'], [class*='location']")
            if addr:
                prop.address = addr.get_text(strip=True)

            return prop if prop.url else None

        except Exception as e:
            print(f"[Pisos.com] Error parseando listado: {e}")
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
        # pisos.com usa /pagina-N/ antes del query string
        if "?" in base_url:
            path, query = base_url.split("?", 1)
            return f"{path}{page}/?{query}"
        return f"{base_url}{page}/"

    async def search(self, params: SearchParams) -> List[Property]:
        properties = []
        base_url = self._build_search_url(params)
        seen_urls = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = self._build_page_url(base_url, page)
            print(f"[Pisos.com] Buscando página {page}: {url}")

            html = await self._fetch_page(url)
            if not html:
                print(f"[Pisos.com] No se pudo obtener la página {page}")
                break

            soup = self._parse_html(html)
            listings = soup.select(".ad-preview, .listing-item, article[class*='ad']")
            if not listings:
                listings = soup.select("article, [class*='card'], [class*='listing']")

            if not listings:
                print(f"[Pisos.com] Sin resultados en página {page}, fin de paginación")
                break

            print(f"[Pisos.com] Encontrados {len(listings)} listados en página {page}")

            new_count = 0
            for listing in listings:
                prop = self._parse_listing(listing)
                if prop and prop.url not in seen_urls:
                    prop.city = params.location
                    properties.append(prop)
                    seen_urls.add(prop.url)
                    new_count += 1

            # Si no hubo resultados nuevos, dejar de paginar
            if new_count == 0:
                break

        await self.close()
        print(f"[Pisos.com] Total: {len(properties)} propiedades")
        return properties
