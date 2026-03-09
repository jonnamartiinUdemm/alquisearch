"""
Módulo de filtrado y puntuación de propiedades.
Aplica los criterios definidos en las instrucciones para filtrar y priorizar resultados.
"""
from typing import List
from models import Property, SearchParams
import re
from datetime import datetime


# Palabras clave que indican posible estafa
SCAM_KEYWORDS = [
    "western union", "transferencia internacional", "enviar dinero",
    "pago por adelantado sin visita", "no se puede visitar",
    "estoy en el extranjero", "envíe depósito", "urgente pago",
    "precio increíblemente bajo", "demasiado bueno para ser verdad",
    "contactar solo por email", "no llamar",
    "agencia no autorizada", "sin contrato",
]

# Zonas con alta criminalidad conocida (fuentes: Ministerio del Interior, prensa local)
HIGH_CRIME_AREAS = [
    # Madrid
    "valdemingómez", "cañada real",
    # Barcelona
    "la mina", "ciutat meridiana",
    # Sevilla
    "las 3000 viviendas", "los pajaritos", "su eminencia",
    # Málaga
    "la palmilla", "la corta",
    # Valencia
    "nazaret", "la coma",
    # Cádiz / Campo de Gibraltar
    "la línea de la concepción",
    # Alicante
    "virgen del remedio",
    # Murcia
    "espinardo polígono",
]

# Zonas con ruido excesivo conocido (aeropuertos, ocio nocturno, industria)
HIGH_NOISE_AREAS = [
    # Cercanías aeropuerto Madrid-Barajas
    "barajas", "alameda de osuna", "corralejos",
    # Cercanías aeropuerto Barcelona-El Prat
    "el prat de llobregat", "gavà mar",
    # Zonas de ocio nocturno intenso
    "malasaña", "huertas", "la latina",          # Madrid
    "barceloneta", "port olímpic", "gràcia",      # Barcelona
    "arenal", "alameda de hércules",               # Sevilla
    "puerto banús",                                 # Marbella
    # Cercanías industriales / puerto
    "zona franca", "polígono san pablo",
]


def detect_scam(prop: Property) -> float:
    """
    Detecta indicios de estafa en una propiedad.
    Retorna un score de 0 (seguro) a 1 (alta probabilidad de estafa).
    """
    score = 0.0
    text = f"{prop.title} {prop.description}".lower()

    # Verificar palabras clave de estafa
    for keyword in SCAM_KEYWORDS:
        if keyword.lower() in text:
            score += 0.3

    # Precio sospechosamente bajo para la zona
    if prop.price > 0 and prop.price < 300 and prop.bedrooms >= 2:
        score += 0.5

    # Sin imágenes o muy pocas
    if len(prop.images) == 0:
        score += 0.2
    elif len(prop.images) == 1:
        score += 0.1

    # Descripción muy corta o genérica
    if len(prop.description) < 20:
        score += 0.15

    # Sin dirección específica
    if not prop.address or prop.address.strip() == "":
        score += 0.1

    return min(score, 1.0)


def calculate_preference_score(prop: Property, params: SearchParams) -> float:
    """
    Calcula un score de preferencia para ordenar resultados.
    Mayor score = mejor coincidencia con preferencias.
    """
    score = 50.0  # Base

    # Preferencia por terraza o balcón
    if params.prefer_terrace and prop.has_terrace:
        score += 15
    if params.prefer_balcony and prop.has_balcony:
        score += 10

    # Preferencia por buena conexión de transporte
    if params.prefer_transport and prop.public_transport_nearby:
        score += 15

    # Preferencia por servicios cercanos
    if params.prefer_services and prop.services_nearby:
        score += 10

    # Mascotas permitidas explícitamente
    if prop.pets_allowed is True:
        score += 10
    elif prop.pets_allowed is None:
        score -= 5  # No se sabe, penalización menor

    # Ascensor cuando es necesario
    if prop.has_elevator is True:
        score += 5

    # Más habitaciones/baños de los mínimos
    if prop.bedrooms > params.min_bedrooms:
        score += (prop.bedrooms - params.min_bedrooms) * 3
    if prop.bathrooms > params.min_bathrooms:
        score += (prop.bathrooms - params.min_bathrooms) * 3

    # Precio más bajo es mejor (normalizado)
    if prop.price > 0 and params.max_price > 0:
        price_ratio = prop.price / params.max_price
        score += (1 - price_ratio) * 20

    # Penalizar por posible estafa
    score -= prop.scam_score * 50

    # Extras
    if prop.has_air_conditioning:
        score += 3
    if prop.has_heating:
        score += 3
    if prop.has_parking:
        score += 5
    if prop.has_pool:
        score += 5
    if prop.furnished is True:
        score += 2
    if prop.allows_empadronamiento is True:
        score += 10

    # Vista al mar
    if hasattr(params, 'sea_view') and params.sea_view and prop.has_sea_view:
        score += 15

    # Larga estancia
    if hasattr(params, 'long_stay') and params.long_stay and prop.is_long_stay:
        score += 10

    # Clasificación energética
    energy_scores = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0, "G": -1}
    if prop.energy_rating and prop.energy_rating.upper() in energy_scores:
        score += energy_scores[prop.energy_rating.upper()]

    return max(0, score)


def check_availability(prop: Property, available_from: str) -> bool:
    """
    Verifica si la disponibilidad de la propiedad es compatible.
    Acepta: no indicada, inmediata, o a partir de la fecha dada.
    """
    if not prop.availability or prop.availability.strip() == "":
        return True  # No indicada -> aceptar

    avail_lower = prop.availability.lower().strip()

    if avail_lower in ["no indicada", "sin especificar", "disponible", "inmediata",
                        "ya disponible", "disponibilidad inmediata", "ahora"]:
        return True

    # Intentar parsear fecha
    try:
        target_date = datetime.strptime(available_from, "%Y-%m-%d")
        # Buscar patrones de fecha en el texto
        date_patterns = [
            r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})",
            r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, avail_lower)
            if match:
                groups = match.groups()
                if len(groups[0]) == 4:
                    avail_date = datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                else:
                    avail_date = datetime(int(groups[2]), int(groups[1]), int(groups[0]))
                return avail_date <= target_date
    except (ValueError, IndexError):
        pass

    # Si contiene "octubre" o "10/2026" o similar
    if "octubre" in avail_lower or "10/2026" in avail_lower or "10-2026" in avail_lower:
        return True

    # Si contiene meses anteriores a octubre 2026
    months_before = ["enero 2026", "febrero 2026", "marzo 2026", "abril 2026",
                     "mayo 2026", "junio 2026", "julio 2026", "agosto 2026",
                     "septiembre 2026"]
    for m in months_before:
        if m in avail_lower:
            return True

    return True  # En caso de duda, incluir


def needs_elevator(prop: Property) -> bool:
    """
    Determina si una propiedad necesita ascensor.
    Solo pisos/departamentos en planta superior a PB.
    """
    if prop.property_type.lower() in ["casa", "chalet", "adosado", "pareado"]:
        return False

    if prop.floor is None or prop.floor.strip() == "":
        return False

    floor_lower = prop.floor.lower().strip()
    if floor_lower in ["bajo", "baja", "planta baja", "pb", "0", "entreplanta", "entresuelo"]:
        return False

    # Si es planta 1 o superior, necesita ascensor
    try:
        floor_num = int(re.search(r"(\d+)", floor_lower).group(1))
        if floor_num >= 1:
            return True
    except (ValueError, AttributeError):
        pass

    if any(x in floor_lower for x in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]):
        return True

    return False


def filter_properties(properties: List[Property], params: SearchParams) -> List[Property]:
    """
    Filtra y ordena propiedades según los criterios del usuario.
    """
    filtered = []

    for prop in properties:
        # 1. Filtrar por precio máximo (solo si el precio se pudo extraer)
        if prop.price > 0 and prop.price > params.max_price:
            continue

        # 2. Filtrar por habitaciones mínimas (0 = desconocido, no filtrar)
        if prop.bedrooms > 0 and prop.bedrooms < params.min_bedrooms:
            continue

        # 3. Filtrar por baños mínimos (0 = desconocido, no filtrar)
        if prop.bathrooms > 0 and prop.bathrooms < params.min_bathrooms:
            continue

        # 4. Verificar disponibilidad
        if params.available_from and not check_availability(prop, params.available_from):
            continue

        # 5. Filtrar por superficie mínima / máxima
        if params.min_area and prop.area_m2 > 0 and prop.area_m2 < params.min_area:
            continue
        if params.max_area and prop.area_m2 > 0 and prop.area_m2 > params.max_area:
            continue

        # 5a. Filtrar por tipo de propiedad
        if params.property_type:
            if prop.property_type and prop.property_type.lower() != params.property_type.lower():
                continue

        # 6. Ascensor obligatorio si es planta alta
        if params.need_elevator and needs_elevator(prop) and prop.has_elevator is False:
            continue

        # 6a. Mascotas obligatorias: excluir si explícitamente no admite mascotas
        if params.pets_allowed and prop.pets_allowed is False:
            continue
        # 6b. Modo estricto: excluir también las propiedades donde se desconoce si admiten mascotas
        if params.pets_allowed and getattr(params, 'strict_pets', False) and prop.pets_allowed is None:
            continue

        # 5b. Filtrar por larga estancia si se solicita
        if hasattr(params, 'long_stay') and params.long_stay and not prop.is_long_stay:
            continue

        # 5c. Filtrar por vista al mar si se solicita
        if hasattr(params, 'sea_view') and params.sea_view and not prop.has_sea_view:
            continue

        # 6. Detectar estafas
        prop.scam_score = detect_scam(prop)
        if prop.scam_score >= 0.7:
            continue  # Excluir estafas obvias

        # 7. Excluir zonas peligrosas
        location_text = f"{prop.neighborhood} {prop.address}".lower()
        if any(zone.lower() in location_text for zone in HIGH_CRIME_AREAS):
            continue
        if any(zone.lower() in location_text for zone in HIGH_NOISE_AREAS):
            continue

        # 8. Calcular puntuación de preferencia
        prop.score = calculate_preference_score(prop, params)

        filtered.append(prop)

    # Ordenar por puntuación de mayor a menor
    filtered.sort(key=lambda p: p.score, reverse=True)

    return filtered
