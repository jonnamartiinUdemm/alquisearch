"""
Scraper para Fotocasa (fotocasa.es).
"""
import re
from typing import List, Optional
from bs4 import Tag

import sys
sys.path.insert(0, '..')
from models import Property, SearchParams
from scrapers.base import BaseScraper, _text_denies_pets


class FotocasaScraper(BaseScraper):
    PLATFORM_NAME = "fotocasa"
    BASE_URL = "https://www.fotocasa.es"

    LOCATION_MAP = {
        "madrid": "madrid-capital/todas-las-zonas/l",
        "barcelona": "barcelona-capital/todas-las-zonas/l",
        "valencia": "valencia-capital/todas-las-zonas/l",
        "sevilla": "sevilla-capital/todas-las-zonas/l",
        "malaga": "malaga-capital/todas-las-zonas/l",
        "zaragoza": "zaragoza-capital/todas-las-zonas/l",
        "bilbao": "bilbao/todas-las-zonas/l",
        "alicante": "alicante-alacant-capital/todas-las-zonas/l",
        "cordoba": "cordoba-capital/todas-las-zonas/l",
        "valladolid": "valladolid-capital/todas-las-zonas/l",
        "granada": "granada-capital/todas-las-zonas/l",
        "murcia": "murcia-capital/todas-las-zonas/l",
        "palma": "palma-de-mallorca/todas-las-zonas/l",
        "las palmas": "las-palmas-de-gran-canaria/todas-las-zonas/l",
        "san sebastian": "donostia-san-sebastian/todas-las-zonas/l",
        "santander": "santander/todas-las-zonas/l",
        "gijon": "gijon/todas-las-zonas/l",
        "oviedo": "oviedo/todas-las-zonas/l",
        "vigo": "vigo/todas-las-zonas/l",
        "a coruna": "a-coruna/todas-las-zonas/l",
    }

    def _get_location_slug(self, location: str) -> str:
        loc = self._normalize_location(location)
        for key, slug in self.LOCATION_MAP.items():
            if key in loc or loc in key:
                return slug
        return f"{loc}/todas-las-zonas/l"

    def _build_search_url(self, params: SearchParams) -> str:
        loc_slug = self._get_location_slug(params.location)
        url = f"{self.BASE_URL}/es/alquiler/viviendas/{loc_slug}"

        query_params = []
        if params.max_price:
            query_params.append(f"maxPrice={int(params.max_price)}")
        if params.min_bedrooms:
            query_params.append(f"minRooms={params.min_bedrooms}")
        if params.min_bathrooms:
            query_params.append(f"minBathrooms={params.min_bathrooms}")
        if params.pets_allowed:
            query_params.append("petsAllowed=true")
        if params.need_elevator:
            query_params.append("hasLift=true")
        if params.prefer_terrace:
            query_params.append("hasTerrace=true")

        if query_params:
            url += "?" + "&".join(query_params)

        return url

    def _parse_listing(self, element: Tag, base_url: str = "") -> Optional[Property]:
        """Parsea un article de Fotocasa usando extracción basada en texto.
        
        Fotocasa usa Tailwind CSS con clases dinámicas, así que no podemos
        depender de selectores CSS estables. Extraemos datos del texto.
        
        Texto de ejemplo de un article con contenido SSR:
        "Líder de zona•Olisson Club 1/24 14.000 €/mes Más de 3 meses 
         Piso con ascensor en Almagro 3 habs·3 baños·274 m²·6ª Planta
         ·Ascensor·Calefacción·Aire acondicionado·Trastero"
        """
        try:
            prop = Property()
            prop.platform = self.PLATFORM_NAME

            # Enlace — buscar link a detalle de vivienda
            link = element.select_one("a[href*='/vivienda/']")
            if not link:
                link = element.select_one("a[href*='/alquiler/']")
            if not link:
                return None

            href = link.get("href", "")
            prop.url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
            prop.id = self._generate_id(prop.url)

            # Extraer todo el texto del artículo
            text = element.get_text(strip=True)
            if len(text) < 30:
                return None  # Artículo vacío (skeleton loader)

            # Precio — "14.000 €/mes" o "1.200€" o "950 €"
            # Formato español: punto como separador de miles
            price_match = re.search(r'(\d[\d.]*)\s*€', text)
            if price_match:
                price_str = price_match.group(1).replace(".", "")
                try:
                    price_val = float(price_str)
                    # Sanity check: alquiler razonable (50€ - 30.000€/mes)
                    if 50 <= price_val <= 30000:
                        prop.price = price_val
                except ValueError:
                    pass

            # Título — buscar texto tipo "Piso en/con ..." o construirlo
            title_match = re.search(r'((?:Piso|Casa|Ático|Dúplex|Estudio|Apartamento|Chalet)[^·€\d]{5,80})', text)
            if title_match:
                prop.title = title_match.group(1).strip()
            else:
                # Usar la primera parte significativa del texto
                prop.title = text[:80].strip()

            # Habitaciones — "3 habs" o "3 hab."
            beds_match = re.search(r'(\d+)\s*hab', text, re.IGNORECASE)
            if beds_match:
                prop.bedrooms = int(beds_match.group(1))

            # Baños — "3 baños" o "2 baño"
            baths_match = re.search(r'(\d+)\s*ba[ñn]o', text, re.IGNORECASE)
            if baths_match:
                prop.bathrooms = int(baths_match.group(1))

            # Superficie — "274 m²" o "80m2"
            area_match = re.search(r'(\d+)\s*m[²2]', text)
            if area_match:
                prop.area_m2 = float(area_match.group(1))

            # Planta — "6ª Planta" o "3a planta"
            floor_match = re.search(r'(\d+)[ªa]?\s*[Pp]lanta', text)
            if floor_match:
                prop.floor = floor_match.group(1)

            # Features del texto
            text_lower = text.lower()
            self._extract_features_from_text(prop, text_lower)

            # Imagen
            img = element.select_one("img[src*='fotocasa'], img[src*='ccdn'], img[data-src]")
            if not img:
                img = element.select_one("img")
            if img:
                src = img.get("src") or img.get("data-src") or ""
                if src and "static" not in src and "placeholder" not in src:
                    prop.images.append(src)

            # Solo devolver si tiene datos reales (no skeleton)
            if prop.price > 0 or prop.bedrooms > 0:
                return prop
            return None

        except Exception as e:
            print(f"[Fotocasa] Error parseando listado: {e}")
            return None

    def _extract_features_from_text(self, prop: Property, text: str):
        """Extrae características del texto de descripción."""
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
        if "aire acondicionado" in text or "a/c" in text:
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
        # fotocasa usa ?combinedLocationIds=...&latitude=...&currentPage=N
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}currentPage={page}"

    async def search(self, params: SearchParams) -> List[Property]:
        properties = []
        base_url = self._build_search_url(params)
        seen_urls = set()

        # Fotocasa es SPA — solo 1-5 artículos SSR por página, el resto son skeletons.
        # Solo consultamos 2 páginas para no perder tiempo.
        max_pages = min(self.MAX_PAGES, 2)

        for page in range(1, max_pages + 1):
            url = self._build_page_url(base_url, page)
            print(f"[Fotocasa] Buscando página {page}: {url}")

            html = await self._fetch_page(url)
            if not html:
                print(f"[Fotocasa] No se pudo obtener la página {page}")
                break

            soup = self._parse_html(html)
            
            # Buscar artículos — algunos son skeletons sin contenido
            listings = soup.select("article")

            if not listings:
                print(f"[Fotocasa] Sin artículos en página {page}")
                break

            print(f"[Fotocasa] {len(listings)} artículos encontrados, extrayendo con contenido...")

            new_count = 0
            for listing in listings:
                prop = self._parse_listing(listing)
                if prop and prop.url not in seen_urls:
                    prop.city = params.location
                    properties.append(prop)
                    seen_urls.add(prop.url)
                    new_count += 1

            print(f"[Fotocasa] {new_count} propiedades con datos reales en página {page}")

            if new_count == 0:
                break

        await self.close()
        print(f"[Fotocasa] Total: {len(properties)} propiedades")
        return properties
