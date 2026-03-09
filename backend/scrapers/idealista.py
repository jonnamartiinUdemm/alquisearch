"""
Scraper para Idealista (idealista.com).
"""
import re
from typing import List, Optional
from bs4 import Tag

import sys
sys.path.insert(0, '..')
from models import Property, SearchParams
from scrapers.base import BaseScraper, _text_denies_pets


class IdealistaScraper(BaseScraper):
    PLATFORM_NAME = "idealista"
    BASE_URL = "https://www.idealista.com"

    # Mapeo de ciudades/provincias principales a slugs
    LOCATION_MAP = {
        "madrid": "madrid-madrid",
        "barcelona": "barcelona",
        "valencia": "valencia",
        "sevilla": "sevilla-sevilla",
        "malaga": "malaga-malaga",
        "zaragoza": "zaragoza-zaragoza",
        "bilbao": "bilbao-vizcaya",
        "alicante": "alicante-alacant",
        "cordoba": "cordoba-cordoba",
        "valladolid": "valladolid",
        "granada": "granada",
        "palma": "palma-de-mallorca-balears-illes",
        "murcia": "murcia-murcia",
        "las palmas": "las-palmas-de-gran-canaria",
        "santa cruz": "santa-cruz-de-tenerife",
        "san sebastian": "donostia-san-sebastian-guipuzcoa",
        "vitoria": "vitoria-gasteiz-alava",
        "pamplona": "pamplona-navarra",
        "santander": "santander-cantabria",
        "gijon": "gijon-asturias",
        "oviedo": "oviedo-asturias",
        "salamanca": "salamanca-salamanca",
        "burgos": "burgos",
        "leon": "leon",
        "tarragona": "tarragona",
        "girona": "girona-girona",
        "lleida": "lleida-lleida",
        "cadiz": "cadiz",
        "huelva": "huelva",
        "almeria": "almeria",
        "jaen": "jaen",
        "toledo": "toledo",
        "badajoz": "badajoz",
        "caceres": "caceres",
        "castellon": "castellon-castello",
        "logrono": "logrono-la-rioja",
        "huesca": "huesca",
        "teruel": "teruel",
        "soria": "soria",
        "segovia": "segovia",
        "avila": "avila",
        "zamora": "zamora",
        "palencia": "palencia",
        "cuenca": "cuenca",
        "guadalajara": "guadalajara",
        "ciudad real": "ciudad-real",
        "albacete": "albacete",
        "lugo": "lugo",
        "ourense": "ourense",
        "pontevedra": "pontevedra",
        "a coruna": "a-coruna",
        "vigo": "vigo-pontevedra",
    }

    def _get_location_slug(self, location: str) -> str:
        """Convierte una localización a slug de Idealista."""
        loc = self._normalize_location(location)
        # Buscar coincidencia en el mapa
        for key, slug in self.LOCATION_MAP.items():
            if key in loc or loc in key:
                return slug
        # Si no se encuentra, usar el formato genérico
        return loc

    def _build_search_url(self, params: SearchParams) -> str:
        """Construye URL de búsqueda en Idealista."""
        loc_slug = self._get_location_slug(params.location)

        # Construir filtros en la URL
        url = f"{self.BASE_URL}/alquiler-viviendas/{loc_slug}/"

        # Parámetros de filtro
        query_params = []

        if params.max_price:
            query_params.append(f"maxPrice={int(params.max_price)}")

        if params.min_bedrooms:
            query_params.append(f"minRooms={params.min_bedrooms}")

        if params.min_bathrooms:
            query_params.append(f"minBathrooms={params.min_bathrooms}")

        if params.pets_allowed:
            query_params.append("pets=yes")

        if params.prefer_terrace:
            query_params.append("terrace=true")

        if params.need_elevator:
            query_params.append("elevator=true")

        if query_params:
            url += "?" + "&".join(query_params)

        return url

    def _parse_listing(self, element: Tag, base_url: str = "") -> Optional[Property]:
        """Parsea un elemento de listado de Idealista."""
        try:
            prop = Property()
            prop.platform = self.PLATFORM_NAME

            # Título y enlace
            title_elem = element.select_one("a.item-link")
            if title_elem:
                prop.title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")
                prop.url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                prop.id = self._generate_id(prop.url)

            # Precio
            price_elem = element.select_one(".item-price, .price-row")
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_val = self._extract_number(price_text)
                if price_val:
                    prop.price = price_val

            # Detalles (habitaciones, baños, superficie)
            detail_items = element.select(".item-detail")
            for detail in detail_items:
                text = detail.get_text(strip=True).lower()
                num = self._extract_number(text)
                if num:
                    if "hab" in text or "dorm" in text:
                        prop.bedrooms = int(num)
                    elif "baño" in text or "bano" in text:
                        prop.bathrooms = int(num)
                    elif "m²" in text or "m2" in text:
                        prop.area_m2 = num

            # Planta y ascensor
            floor_elem = element.select_one(".item-parking, .item-detail")
            if floor_elem:
                text = floor_elem.get_text(strip=True).lower()
                if "planta" in text or "piso" in text:
                    floor_match = re.search(r"(\d+)[ºªa]?\s*planta", text)
                    if floor_match:
                        prop.floor = floor_match.group(1)
                    elif "bajo" in text:
                        prop.floor = "bajo"
                if "ascensor" in text:
                    prop.has_elevator = "sin ascensor" not in text
                if "con ascensor" in text:
                    prop.has_elevator = True

            # Descripción
            desc_elem = element.select_one(".item-description, .ellipsis")
            if desc_elem:
                prop.description = desc_elem.get_text(strip=True)
                desc_lower = prop.description.lower()

                # Detectar características en descripción
                if "terraza" in desc_lower:
                    prop.has_terrace = True
                if "balcón" in desc_lower or "balcon" in desc_lower:
                    prop.has_balcony = True
                if "mascota" in desc_lower or "animal" in desc_lower:
                    if _text_denies_pets(desc_lower):
                        prop.pets_allowed = False
                    elif prop.pets_allowed is None:
                        prop.pets_allowed = True
                if "ascensor" in desc_lower and prop.has_elevator is None:
                    prop.has_elevator = "sin ascensor" not in desc_lower
                if "empadron" in desc_lower:
                    prop.allows_empadronamiento = True
                if "amueblad" in desc_lower:
                    prop.furnished = True
                if "aire acondicionado" in desc_lower or "a/c" in desc_lower:
                    prop.has_air_conditioning = True
                if "calefacción" in desc_lower or "calefaccion" in desc_lower:
                    prop.has_heating = True
                if "garaje" in desc_lower or "parking" in desc_lower:
                    prop.has_parking = True
                if "piscina" in desc_lower:
                    prop.has_pool = True
                if any(t in desc_lower for t in ["metro", "bus", "transporte", "cercanías", "tren"]):
                    prop.public_transport_nearby = True
                if any(s in desc_lower for s in ["supermercado", "farmacia", "colegio", "hospital", "comercio"]):
                    prop.services_nearby = True

            # Imagen
            img_elem = element.select_one("img")
            if img_elem:
                src = img_elem.get("src") or img_elem.get("data-src") or ""
                if src and "static" not in src:
                    prop.images.append(src)

            # Tags/características
            tags = element.select(".item-tags span, .listing-tags span")
            for tag in tags:
                tag_text = tag.get_text(strip=True).lower()
                if "terraza" in tag_text:
                    prop.has_terrace = True
                if "ascensor" in tag_text:
                    prop.has_elevator = True
                if "mascota" in tag_text:
                    if _text_denies_pets(tag_text):
                        prop.pets_allowed = False
                    elif prop.pets_allowed is None:
                        prop.pets_allowed = True
                if "balcón" in tag_text or "balcon" in tag_text:
                    prop.has_balcony = True

            # Dirección
            addr_elem = element.select_one(".item-address, .item-location")
            if addr_elem:
                prop.address = addr_elem.get_text(strip=True)

            return prop if prop.url else None

        except Exception as e:
            print(f"[Idealista] Error parseando listado: {e}")
            return None

    def _build_page_url(self, base_url: str, page: int) -> str:
        """Construye la URL para una página específica de resultados."""
        if page <= 1:
            return base_url
        # idealista usa /pagina-N.htm en la ruta antes del query string
        if "?" in base_url:
            path, query = base_url.split("?", 1)
            # Quitar trailing slash si existe
            path = path.rstrip("/")
            return f"{path}/pagina-{page}.htm?{query}"
        path = base_url.rstrip("/")
        return f"{path}/pagina-{page}.htm"

    async def search(self, params: SearchParams) -> List[Property]:
        """Busca propiedades en Idealista."""
        properties = []
        base_url = self._build_search_url(params)
        seen_urls = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = self._build_page_url(base_url, page)
            print(f"[Idealista] Buscando página {page}: {url}")

            html = await self._fetch_page(url)
            if not html:
                print(f"[Idealista] No se pudo obtener la página {page}")
                break

            soup = self._parse_html(html)

            # Buscar elementos de listado
            listings = soup.select("article.item, .item-multimedia-container, div.item")
            if not listings:
                listings = soup.select("[data-element-id], .listing-item, .property-item")

            if not listings:
                print(f"[Idealista] Sin resultados en página {page}, fin de paginación")
                break

            print(f"[Idealista] Encontrados {len(listings)} listados en página {page}")

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
        print(f"[Idealista] Total: {len(properties)} propiedades")
        return properties
