"""Inicialización del paquete de scrapers."""
from scrapers.base import BaseScraper
from scrapers.idealista import IdealistaScraper
from scrapers.fotocasa import FotocasaScraper
from scrapers.habitaclia import HabitacliaScraper
from scrapers.pisos import PisosScraper
from scrapers.housinganywhere import HousingAnywhereScraper

__all__ = [
    "BaseScraper",
    "IdealistaScraper",
    "FotocasaScraper",
    "HabitacliaScraper",
    "PisosScraper",
    "HousingAnywhereScraper",
]
