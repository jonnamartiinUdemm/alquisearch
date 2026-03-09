# AlquiSearch España 🏠

Plataforma web integrada para buscar viviendas en alquiler en España. Busca simultáneamente en **Idealista**, **Fotocasa**, **Habitaclia**, **Pisos.com** y **HousingAnywhere**, aplicando filtros inteligentes para encontrar las mejores opciones.

## Características

- **Búsqueda integrada** en 5 plataformas inmobiliarias (incluyendo HousingAnywhere para larga estancia)
- **Vista de mapa** interactivo: visualiza propiedades por zonas con marcadores de precio y clustering
- **Filtro de larga estancia**: para alquileres de duración extendida (6+ meses)
- **Filtro de vista al mar**: aparece automáticamente al buscar en ciudades costeras
- **Filtros automáticos**: mascotas, ascensor, precio máx, habitaciones, baños
- **Detección de estafas**: identifica y excluye anuncios sospechosos
- **Puntuación inteligente**: prioriza propiedades según preferencias (terraza, transporte, servicios)
- **URLs directas**: enlace directo a cada anuncio en su plataforma original
- **Interfaz moderna**: UI responsive con búsqueda autocompletada
- **Verificación de disponibilidad**: filtra por fecha de disponibilidad
- **Detección de ciudades costeras**: API integrada para habilitar filtros específicos

## Criterios de filtrado

| Criterio | Detalle |
|----------|---------|
| Mascotas | Admite mascotas |
| Ascensor | Obligatorio en plantas superiores a PB |
| Precio | Máximo 2.800 €/mes |
| Habitaciones | 2 o más |
| Baños | 2 o más |
| Disponibilidad | A partir de 1 de octubre de 2026 |
| Terraza/balcón | Preferencia (mayor puntuación) |
| Transporte público | Preferencia por buena conexión |
| Servicios | Supermercados, farmacias, etc. cercanos |
| Empadronamiento | Se favorecen anuncios que lo permitan |
| Larga estancia | Filtro para alquileres de 6+ meses |
| Vista al mar | Disponible automáticamente en ciudades costeras |
| Anti-estafa | Excluye anuncios sospechosos automáticamente |

## Inicio rápido

```bash
# Iniciar la aplicación
./start.sh

# Solo ejecutar tests
./start.sh --test

# Reinstalar dependencias
./start.sh --install
```

La aplicación estará disponible en **http://localhost:8000**

## Requisitos

- Python 3.8+
- pip (gestor de paquetes de Python)

## Estructura del proyecto

```
Rent/
├── start.sh                    # Script de arranque
├── Instructions.MD             # Requisitos del proyecto
├── README.md                   # Esta documentación
├── backend/
│   ├── main.py                 # API FastAPI principal
│   ├── models.py               # Modelos de datos (Property, SearchParams)
│   ├── filters.py              # Lógica de filtrado y puntuación
│   ├── tests.py                # Tests automatizados
│   ├── requirements.txt        # Dependencias Python
│   └── scrapers/
│       ├── __init__.py
│       ├── base.py             # Scraper base (compartido)
│       ├── idealista.py        # Scraper Idealista
│       ├── fotocasa.py         # Scraper Fotocasa
│       ├── habitaclia.py       # Scraper Habitaclia
│       ├── pisos.py            # Scraper Pisos.com
│       └── housinganywhere.py  # Scraper HousingAnywhere
└── frontend/
    ├── index.html              # Página principal
    ├── styles.css              # Estilos CSS
    └── app.js                  # Lógica del frontend
```

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Página web principal |
| GET | `/api/health` | Health check |
| GET | `/api/cities?q=` | Autocompletado de ciudades |
| POST | `/api/search` | Búsqueda de propiedades |
| GET | `/api/search-urls?location=` | URLs directas de búsqueda |
| GET | `/api/is-coastal?city=` | Verifica si una ciudad es costera |

## Tecnologías

- **Backend**: Python, FastAPI, httpx, BeautifulSoup4
- **Frontend**: HTML5, CSS3, JavaScript vanilla, Leaflet.js (mapas)
- **Scraping**: httpx + BeautifulSoup4 + lxml
- **Mapas**: Leaflet + MarkerCluster + OpenStreetMap
