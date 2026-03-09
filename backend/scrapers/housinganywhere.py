"""
Scraper para HousingAnywhere (housinganywhere.com).
Plataforma especializada en alquileres de media y larga estancia en Europa.
"""
import re
import json
from typing import List, Optional
from bs4 import Tag

import sys
sys.path.insert(0, '..')
from models import Property, SearchParams
from scrapers.base import BaseScraper, _text_denies_pets


class HousingAnywhereScraper(BaseScraper):
    PLATFORM_NAME = "housinganywhere"
    BASE_URL = "https://housinganywhere.com"

    LOCATION_MAP = {
        "madrid": "Madrid--Spain",
        "barcelona": "Barcelona--Spain",
        "valencia": "Valencia--Spain",
        "sevilla": "Seville--Spain",
        "malaga": "Malaga--Spain",
        "zaragoza": "Zaragoza--Spain",
        "bilbao": "Bilbao--Spain",
        "alicante": "Alicante--Spain",
        "cordoba": "Cordoba--Spain",
        "valladolid": "Valladolid--Spain",
        "granada": "Granada--Spain",
        "murcia": "Murcia--Spain",
        "palma": "Palma-de-Mallorca--Spain",
        "las palmas": "Las-Palmas-de-Gran-Canaria--Spain",
        "san sebastian": "San-Sebastian--Spain",
        "santander": "Santander--Spain",
        "gijon": "Gijon--Spain",
        "oviedo": "Oviedo--Spain",
        "vigo": "Vigo--Spain",
        "a coruna": "A-Coruna--Spain",
        "tarragona": "Tarragona--Spain",
        "girona": "Girona--Spain",
        "lleida": "Lleida--Spain",
        "cadiz": "Cadiz--Spain",
        "marbella": "Marbella--Spain",
        "salamanca": "Salamanca--Spain",
        "pamplona": "Pamplona--Spain",
        "leon": "Leon--Spain",
        "toledo": "Toledo--Spain",
    }

    def _get_location_slug(self, location: str) -> str:
        """Obtiene el slug de HousingAnywhere para la ubicación."""
        loc = self._normalize_location(location)
        for key, slug in self.LOCATION_MAP.items():
            if key in loc or loc in key:
                return slug
        # Intentar construir slug genérico
        city_name = location.strip().replace(" ", "-")
        return f"{city_name}--Spain"

    def _build_search_url(self, params: SearchParams) -> str:
        """Construye la URL de búsqueda para HousingAnywhere."""
        loc_slug = self._get_location_slug(params.location)
        url = f"{self.BASE_URL}/s/{loc_slug}"

        query_params = []

        # Tipo: apartment (por defecto buscamos pisos)
        query_params.append("categories=apartment")

        # Precio máximo
        if params.max_price:
            query_params.append(f"priceMax={int(params.max_price)}")

        # Larga estancia (mínimo 6 meses)
        if hasattr(params, 'long_stay') and params.long_stay:
            query_params.append("minDuration=6")

        if query_params:
            url += "?" + "&".join(query_params)

        return url

    def _parse_listing(self, element: Tag, base_url: str = "") -> Optional[Property]:
        """Parsea un elemento HTML de listado de HousingAnywhere."""
        try:
            prop = Property()
            prop.platform = self.PLATFORM_NAME

            # Título y enlace
            link = element.select_one("a[href*='/rent/'], a[href*='/listing/'], a[class*='title'], h2 a, h3 a")
            if link:
                prop.title = link.get_text(strip=True)
                href = link.get("href", "")
                if href.startswith("/"):
                    prop.url = f"{self.BASE_URL}{href}"
                elif href.startswith("http"):
                    prop.url = href
                else:
                    prop.url = f"{self.BASE_URL}/{href}"
                prop.id = self._generate_id(prop.url)

            # Precio
            price_el = element.select_one("[class*='price'], [class*='Price'], [data-test*='price']")
            if price_el:
                price_val = self._extract_number(price_el.get_text(strip=True))
                if price_val:
                    prop.price = price_val

            # Características (habitaciones, baños, superficie)
            features = element.select("[class*='feature'], [class*='detail'], [class*='spec'], [class*='property-info'] span")
            for feat in features:
                text = feat.get_text(strip=True).lower()
                num = self._extract_number(text)
                if num:
                    if any(kw in text for kw in ["bedroom", "habitaci", "room", "bed"]):
                        prop.bedrooms = int(num)
                    elif any(kw in text for kw in ["bathroom", "baño", "bath"]):
                        prop.bathrooms = int(num)
                    elif any(kw in text for kw in ["m²", "m2", "sqm", "square"]):
                        prop.area_m2 = num

            # Descripción
            desc_el = element.select_one("[class*='description'], [class*='subtitle']")
            if desc_el:
                prop.description = desc_el.get_text(strip=True)
                self._extract_features_from_text(prop, prop.description.lower())

            # Imagen
            img = element.select_one("img")
            if img:
                src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
                if src and "static" not in src and "placeholder" not in src:
                    prop.images.append(src)

            # Dirección/ubicación
            addr = element.select_one("[class*='location'], [class*='address'], [class*='area']")
            if addr:
                prop.address = addr.get_text(strip=True)

            # HousingAnywhere generalmente es larga estancia
            prop.is_long_stay = True

            return prop if prop.url else None

        except Exception as e:
            print(f"[HousingAnywhere] Error parseando listado: {e}")
            return None

    def _extract_features_from_text(self, prop: Property, text: str):
        """Extrae características del texto de descripción."""
        if "terraza" in text or "terrace" in text:
            prop.has_terrace = True
        if "balcón" in text or "balcon" in text or "balcony" in text:
            prop.has_balcony = True
        if "mascota" in text or "animal" in text or "pet" in text:
            if _text_denies_pets(text):
                prop.pets_allowed = False
            elif prop.pets_allowed is None:
                prop.pets_allowed = True
        if "ascensor" in text or "elevator" in text or "lift" in text:
            prop.has_elevator = "sin ascensor" not in text and "no elevator" not in text
        if "amueblad" in text or "furnished" in text:
            prop.furnished = True
        if "aire acondicionado" in text or "air conditioning" in text or "a/c" in text:
            prop.has_air_conditioning = True
        if "calefacción" in text or "calefaccion" in text or "heating" in text:
            prop.has_heating = True
        if "garaje" in text or "parking" in text or "garage" in text:
            prop.has_parking = True
        if "piscina" in text or "pool" in text:
            prop.has_pool = True
        if "vista" in text and "mar" in text or "sea view" in text or "ocean view" in text:
            prop.has_sea_view = True
        if any(t in text for t in ["metro", "bus", "transporte", "transport", "cercanías", "tren", "train"]):
            prop.public_transport_nearby = True
        if any(s in text for s in ["supermercado", "farmacia", "colegio", "hospital", "supermarket", "pharmacy"]):
            prop.services_nearby = True

    def _build_page_url(self, base_url: str, page: int) -> str:
        """Construye la URL para una página específica de resultados."""
        if page <= 1:
            return base_url
        # housinganywhere usa ?page=N como parámetro
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}page={page}"

    async def search(self, params: SearchParams) -> List[Property]:
        """Ejecuta la búsqueda en HousingAnywhere."""
        properties = []
        base_url = self._build_search_url(params)
        seen_urls = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = self._build_page_url(base_url, page)
            print(f"[HousingAnywhere] Buscando página {page}: {url}")

            html = await self._fetch_page(url)
            if not html:
                print(f"[HousingAnywhere] No se pudo obtener la página {page}")
                break

            soup = self._parse_html(html)
            page_properties = []

            # Intentar parsear datos JSON embebidos (HousingAnywhere usa SSR/React)
            scripts = soup.select("script[type='application/ld+json'], script[type='application/json']")
            for script in scripts:
                try:
                    data = json.loads(script.string or "")
                    if isinstance(data, list):
                        for item in data:
                            prop = self._parse_json_listing(item, params)
                            if prop:
                                page_properties.append(prop)
                    elif isinstance(data, dict):
                        items = data.get("itemListElement", data.get("listings", data.get("results", [])))
                        if isinstance(items, list):
                            for item in items:
                                prop = self._parse_json_listing(item, params)
                                if prop:
                                    page_properties.append(prop)
                except (json.JSONDecodeError, TypeError):
                    continue

            # Si no se encontraron datos JSON, intentar parsing HTML directamente
            if not page_properties:
                listings = soup.select(
                    "[class*='listing-card'], [class*='ListingCard'], "
                    "[class*='property-card'], article[class*='card'], "
                    "[data-test*='listing'], [class*='SearchResult']"
                )
                if not listings:
                    listings = soup.select("article, [class*='card'], [role='listitem']")

                if not listings:
                    print(f"[HousingAnywhere] Sin resultados en página {page}, fin de paginación")
                    break

                print(f"[HousingAnywhere] Encontrados {len(listings)} listados HTML en página {page}")

                for listing in listings:
                    prop = self._parse_listing(listing)
                    if prop:
                        prop.city = params.location
                        prop.is_long_stay = True
                        page_properties.append(prop)

            new_count = 0
            for prop in page_properties:
                if prop.url not in seen_urls:
                    properties.append(prop)
                    seen_urls.add(prop.url)
                    new_count += 1

            if new_count == 0:
                break

        print(f"[HousingAnywhere] Total: {len(properties)} propiedades")
        await self.close()
        return properties

    def _parse_json_listing(self, item: dict, params: SearchParams) -> Optional[Property]:
        """Parsea un listado desde datos JSON estructurados."""
        try:
            if not isinstance(item, dict):
                return None

            prop = Property()
            prop.platform = self.PLATFORM_NAME
            prop.is_long_stay = True

            # Datos básicos
            prop.title = item.get("name", item.get("title", ""))
            prop.description = item.get("description", "")

            # URL
            url = item.get("url", item.get("link", ""))
            if url:
                if url.startswith("/"):
                    prop.url = f"{self.BASE_URL}{url}"
                else:
                    prop.url = url
                prop.id = self._generate_id(prop.url)
            else:
                return None

            # Precio
            price_data = item.get("offers", item.get("price", {}))
            if isinstance(price_data, dict):
                prop.price = float(price_data.get("price", price_data.get("amount", 0)))
            elif isinstance(price_data, (int, float)):
                prop.price = float(price_data)

            # Ubicación
            geo = item.get("geo", item.get("location", {}))
            if isinstance(geo, dict):
                prop.latitude = geo.get("latitude", geo.get("lat"))
                prop.longitude = geo.get("longitude", geo.get("lng", geo.get("lon")))
                prop.address = geo.get("address", "")

            # Características
            prop.bedrooms = int(item.get("numberOfBedrooms", item.get("bedrooms", 0)))
            prop.bathrooms = int(item.get("numberOfBathooms", item.get("bathrooms", 1)))
            area = item.get("floorSize", item.get("area", item.get("size", {})))
            if isinstance(area, dict):
                prop.area_m2 = float(area.get("value", 0))
            elif isinstance(area, (int, float)):
                prop.area_m2 = float(area)

            # Imágenes
            images = item.get("image", item.get("images", item.get("photos", [])))
            if isinstance(images, list):
                for img in images[:5]:
                    if isinstance(img, str):
                        prop.images.append(img)
                    elif isinstance(img, dict):
                        prop.images.append(img.get("url", img.get("contentUrl", "")))
            elif isinstance(images, str):
                prop.images.append(images)

            prop.city = params.location

            # Extraer features del texto
            if prop.description:
                self._extract_features_from_text(prop, prop.description.lower())

            return prop if prop.url and prop.title else None

        except Exception as e:
            print(f"[HousingAnywhere] Error parseando JSON listing: {e}")
            return None
