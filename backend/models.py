"""
Modelos de datos para la plataforma de búsqueda de alquileres.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class PropertyType(str, Enum):
    PISO = "piso"
    CASA = "casa"
    DEPARTAMENTO = "departamento"
    ATICO = "ático"
    DUPLEX = "dúplex"
    ESTUDIO = "estudio"
    OTRO = "otro"


class Platform(str, Enum):
    IDEALISTA = "idealista"
    FOTOCASA = "fotocasa"
    HABITACLIA = "habitaclia"
    PISOS = "pisos.com"
    HOUSINGANYWHERE = "housinganywhere"


class Property(BaseModel):
    """Modelo de una propiedad en alquiler."""
    id: str = ""
    title: str = ""
    description: str = ""
    price: float = 0.0
    currency: str = "EUR"
    bedrooms: int = 0
    bathrooms: int = 0
    area_m2: float = 0.0
    floor: Optional[str] = None
    has_elevator: Optional[bool] = None
    has_terrace: bool = False
    has_balcony: bool = False
    pets_allowed: Optional[bool] = None
    address: str = ""
    neighborhood: str = ""
    city: str = ""
    province: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_precision: str = "approximate"
    availability: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    url: str = ""
    platform: str = ""
    property_type: str = ""
    has_parking: bool = False
    has_pool: bool = False
    has_air_conditioning: bool = False
    has_heating: bool = False
    furnished: Optional[bool] = None
    public_transport_nearby: Optional[bool] = None
    services_nearby: Optional[bool] = None
    energy_rating: Optional[str] = None
    allows_empadronamiento: Optional[bool] = None
    has_sea_view: bool = False
    is_long_stay: bool = False
    scam_score: float = 0.0  # 0 = seguro, 1 = probable estafa
    score: float = 0.0  # puntuación general de preferencia


class SearchParams(BaseModel):
    """Parámetros de búsqueda."""
    location: str
    max_price: float = 2800
    min_bedrooms: int = 2
    min_bathrooms: int = 2
    pets_allowed: bool = True
    strict_pets: bool = False  # Si True, excluye también propiedades donde pets=desconocido (None)
    need_elevator: bool = True
    available_from: Optional[str] = "2026-10-01"
    prefer_terrace: bool = True
    prefer_balcony: bool = True
    prefer_transport: bool = True
    prefer_services: bool = True
    property_type: Optional[str] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    long_stay: bool = False
    sea_view: Optional[bool] = None  # None = no filtrar, True = solo con vista mar
    platforms: List[str] = Field(
        default_factory=lambda: ["idealista", "fotocasa", "habitaclia", "pisos.com", "housinganywhere"]
    )


class SearchResult(BaseModel):
    """Resultado de una búsqueda."""
    properties: List[Property] = Field(default_factory=list)
    total: int = 0
    location: str = ""
    platforms_searched: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
