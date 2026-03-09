"""
config.py
=========
Constantes compartidas y configuración de la aplicación.
"""

from scrapers import IdealistaScraper, FotocasaScraper, HabitacliaScraper, PisosScraper, HousingAnywhereScraper

# Mapa de scrapers disponibles por plataforma
SCRAPERS = {
    "idealista": IdealistaScraper,
    "fotocasa": FotocasaScraper,
    "habitaclia": HabitacliaScraper,
    "pisos.com": PisosScraper,
    "housinganywhere": HousingAnywhereScraper,
}

# Ciudades costeras de España (para filtro de vista al mar)
COASTAL_CITIES = [
    "barcelona", "valencia", "málaga", "malaga", "alicante", "cádiz", "cadiz",
    "bilbao", "santander", "gijón", "gijon", "vigo", "a coruña", "a coruna",
    "san sebastián", "san sebastian", "tarragona", "castellón", "castellon",
    "almería", "almeria", "huelva", "marbella", "palma de mallorca", "palma",
    "las palmas de gran canaria", "las palmas", "santa cruz de tenerife",
    "ibiza", "menorca", "cartagena", "benidorm", "torrevieja", "estepona",
    "fuengirola", "nerja", "lloret de mar", "sitges", "roses", "salou",
    "dénia", "denia", "gandía", "gandia", "badalona", "el puerto de santa maría",
    "rota", "chipiona", "conil", "zahara", "pontevedra",
]

# Ciudades principales para autocompletado
SPANISH_CITIES = [
    "Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga", "Zaragoza",
    "Bilbao", "Alicante", "Córdoba", "Valladolid", "Granada", "Murcia",
    "Palma de Mallorca", "Las Palmas de Gran Canaria", "San Sebastián",
    "Vitoria-Gasteiz", "Pamplona", "Santander", "Gijón", "Oviedo",
    "Santa Cruz de Tenerife", "Salamanca", "Burgos", "León", "Tarragona",
    "Girona", "Lleida", "Cádiz", "Huelva", "Almería", "Jaén",
    "Toledo", "Badajoz", "Cáceres", "Logroño", "Huesca", "Teruel",
    "Soria", "Segovia", "Ávila", "Zamora", "Palencia", "Cuenca",
    "Guadalajara", "Ciudad Real", "Albacete", "Lugo", "Ourense",
    "Pontevedra", "A Coruña", "Vigo", "Marbella", "Elche",
    "Sabadell", "Terrassa", "Hospitalet de Llobregat", "Badalona",
    "Getafe", "Alcalá de Henares", "Fuenlabrada", "Leganés",
    "Torrejón de Ardoz", "Alcorcón", "Móstoles", "Reus",
    "Sant Cugat del Vallès", "Castellón de la Plana",
]


def normalize(text: str) -> str:
    """Normaliza texto eliminando tildes para búsqueda aproximada."""
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n", "ü": "u", "à": "a", "è": "e", "ì": "i",
        "ò": "o", "ù": "u", "ï": "i", "ç": "c",
    }
    result = text.lower()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result
