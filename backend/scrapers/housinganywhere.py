"""
Scraper para HousingAnywhere (housinganywhere.com).
Plataforma especializada en alquileres de media y larga estancia en Europa.

Estrategia: HousingAnywhere es una SPA React que incluye datos de listados en
un tag <script> con window.__staticRouterHydrationData = JSON.parse("...").
Extraemos esos datos JSON directamente (23+ listings por página), con fallback
a parsing HTML de tarjetas.
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

    # Mapeo de propertyType de HA a tipos legibles
    PROPERTY_TYPE_MAP = {
        "apartment": "piso",
        "studio": "estudio",
        "room": "habitación",
        "house": "casa",
    }

    def _get_location_slug(self, location: str) -> str:
        loc = self._normalize_location(location)
        for key, slug in self.LOCATION_MAP.items():
            if key in loc or loc in key:
                return slug
        city_name = location.strip().replace(" ", "-")
        return f"{city_name}--Spain"

    def _build_search_url(self, params: SearchParams) -> str:
        loc_slug = self._get_location_slug(params.location)
        if getattr(params, 'long_stay', False):
            path_filter = "/long-term-rentals"
        else:
            path_filter = "/apartment-for-rent"
        url = f"{self.BASE_URL}/s/{loc_slug}{path_filter}"
        return url

    def get_direct_search_url(self, params: SearchParams) -> str:
        return self._build_search_url(params)

    def _extract_hydration_listings(self, html: str) -> List[dict]:
        """Extrae listings del JSON de hidratación React.

        El HTML contiene:
        window.__staticRouterHydrationData = JSON.parse("{...}");

        Los listings están en loaderData[key]["listings"].
        """
        idx = html.find("window.__staticRouterHydrationData")
        if idx < 0:
            return []

        eq_idx = html.find("=", idx)
        if eq_idx < 0:
            return []

        end_script = html.find("</script>", eq_idx)
        if end_script < 0:
            return []

        raw = html[eq_idx + 1:end_script].strip().rstrip(";").strip()

        # Manejar JSON.parse("...") wrapper
        if raw.startswith("JSON.parse("):
            inner = raw[len("JSON.parse("):-1]
            if inner.startswith('"') and inner.endswith('"'):
                inner = inner[1:-1]
            inner = inner.replace('\\"', '"').replace('\\\\', '\\')
            raw = inner

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"[HousingAnywhere] Error parseando JSON de hidratación: {e}")
            return []

        loader_data = data.get("loaderData", {})

        for key, value in loader_data.items():
            if isinstance(value, dict) and "listings" in value:
                listings = value["listings"]
                if isinstance(listings, list) and len(listings) > 0:
                    print(f"[HousingAnywhere] Encontrados {len(listings)} listings en hidratación (key='{key}')")
                    return listings

        return []

    def _parse_hydration_listing(self, item: dict, params: SearchParams) -> Optional[Property]:
        """Parsea un listing del JSON de hidratación de HA.

        Campos confirmados: price (centimos), city, street, neighborhood,
        facility_bedroom_count, facility_total_size, listingPath,
        _geoloc.{lat,lng}, photos[], thumbnailURL, propertyType,
        facility_registration_possible (empadronamiento).
        """
        try:
            prop = Property()
            prop.platform = self.PLATFORM_NAME
            prop.is_long_stay = True

            listing_path = item.get("listingPath", "")
            if not listing_path:
                return None
            prop.url = f"{self.BASE_URL}{listing_path}"
            prop.id = self._generate_id(prop.url)

            street = item.get("street", "")
            neighborhood = item.get("neighborhood", "")
            prop_type = item.get("propertyType", "apartment")
            type_name = self.PROPERTY_TYPE_MAP.get(prop_type, prop_type)
            prop.property_type = type_name

            if street and neighborhood:
                prop.title = f"{type_name.capitalize()} en {street}, {neighborhood}"
            elif street:
                prop.title = f"{type_name.capitalize()} en {street}"
            elif neighborhood:
                prop.title = f"{type_name.capitalize()} en {neighborhood}"
            else:
                prop.title = f"{type_name.capitalize()} en {item.get('city', params.location)}"

            price_cents = item.get("price", 0)
            if isinstance(price_cents, (int, float)) and price_cents > 0:
                prop.price = price_cents / 100.0

            prop.city = item.get("city", params.location)
            prop.neighborhood = neighborhood
            prop.address = street

            geoloc = item.get("_geoloc", {})
            if isinstance(geoloc, dict):
                prop.latitude = geoloc.get("lat")
                prop.longitude = geoloc.get("lng")

            prop.bedrooms = int(item.get("facility_bedroom_count", 0))
            prop.area_m2 = float(item.get("facility_total_size", 0))
            prop.bathrooms = int(item.get("facility_bathroom_count", 1))

            photos = item.get("photos", [])
            if isinstance(photos, list):
                for photo in photos[:8]:
                    if isinstance(photo, str):
                        prop.images.append(photo)
                    elif isinstance(photo, dict):
                        url = photo.get("url", photo.get("src", ""))
                        if url:
                            prop.images.append(url)

            thumbnail = item.get("thumbnailURL", "")
            if thumbnail and thumbnail not in prop.images:
                prop.images.insert(0, thumbnail)

            if item.get("facility_registration_possible"):
                prop.allows_empadronamiento = True
            if item.get("facility_bedroom_furnished"):
                prop.furnished = True

            return prop

        except Exception as e:
            print(f"[HousingAnywhere] Error parseando listing JSON: {e}")
            return None

    def _parse_listing(self, element: Tag, base_url: str = "") -> Optional[Property]:
        """Fallback: parsea una tarjeta HTML de HA."""
        try:
            prop = Property()
            prop.platform = self.PLATFORM_NAME
            prop.is_long_stay = True

            link = element if element.name == "a" else element.select_one("a[href]")
            if link:
                href = link.get("href", "")
                if href.startswith("/"):
                    prop.url = f"{self.BASE_URL}{href}"
                elif href.startswith("http"):
                    prop.url = href
                else:
                    return None
                prop.id = self._generate_id(prop.url)
                prop.title = link.get_text(strip=True) or "Listing en HousingAnywhere"

            text = element.get_text(strip=True)
            price_match = re.search(r'€\s*([\d.,]+)|(\d[\d.,]+)\s*€', text)
            if price_match:
                price_str = (price_match.group(1) or price_match.group(2)).replace(".", "").replace(",", ".")
                try:
                    prop.price = float(price_str)
                except ValueError:
                    pass

            return prop if prop.url else None

        except Exception as e:
            print(f"[HousingAnywhere] Error parseando HTML: {e}")
            return None

    def _build_page_url(self, base_url: str, page: int) -> str:
        if page <= 1:
            return base_url
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}page={page}"

    async def search(self, params: SearchParams) -> List[Property]:
        properties = []
        base_url = self._build_search_url(params)
        seen_urls = set()

        print(f"[HousingAnywhere] Buscando: {base_url}")

        html = await self._fetch_page(base_url)
        if not html:
            print("[HousingAnywhere] No se pudo obtener la página")
            await self.close()
            return []

        # Estrategia 1: JSON de hidratación (preferida — datos completos)
        json_listings = self._extract_hydration_listings(html)
        if json_listings:
            for item in json_listings:
                prop = self._parse_hydration_listing(item, params)
                if prop and prop.url not in seen_urls:
                    properties.append(prop)
                    seen_urls.add(prop.url)

        # Estrategia 2: Fallback a tarjetas HTML
        if not properties:
            print("[HousingAnywhere] JSON no disponible, intentando HTML...")
            soup = self._parse_html(html)
            cards = soup.select("a[data-test-locator='ListingCard/Anchor'], a[class*='cardLink']")
            if not cards:
                cards = soup.select("a[href*='/room/'], a[href*='/apartment/']")

            print(f"[HousingAnywhere] Encontradas {len(cards)} tarjetas HTML")
            for card in cards:
                prop = self._parse_listing(card)
                if prop and prop.url not in seen_urls:
                    prop.city = params.location
                    properties.append(prop)
                    seen_urls.add(prop.url)

        print(f"[HousingAnywhere] Total: {len(properties)} propiedades")
        await self.close()
        return properties
