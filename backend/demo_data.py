"""
Generador de propiedades de demostración realistas para todas las ciudades principales de España.
Proporciona datos consistentes para que la plataforma siempre muestre resultados útiles.
"""
import hashlib
import random
from typing import List
from models import Property
from neighborhood_streets import NEIGHBORHOOD_STREETS

# Semilla fija para reproducibilidad
_RNG = random.Random(42)

# ──────────────────────────────────────────────
# Coordenadas reales por barrio (lat, lng)
# ──────────────────────────────────────────────
NEIGHBORHOOD_COORDS = {
    "Madrid": {
        "Chamberí": (40.4350, -3.7050), "Retiro": (40.4090, -3.6820),
        "Salamanca": (40.4290, -3.6830), "Malasaña": (40.4260, -3.7070),
        "Lavapiés": (40.4090, -3.7010), "La Latina": (40.4110, -3.7110),
        "Chamartín": (40.4620, -3.6770), "Tetuán": (40.4600, -3.6980),
        "Moncloa-Aravaca": (40.4350, -3.7270), "Arganzuela": (40.3980, -3.6940),
        "Carabanchel": (40.3830, -3.7370), "Usera": (40.3850, -3.7050),
        "Moratalaz": (40.4070, -3.6490), "Hortaleza": (40.4700, -3.6430),
        "Las Tablas": (40.5080, -3.6590), "Vallecas": (40.3850, -3.6600),
        "Prosperidad": (40.4430, -3.6700), "Barrio de las Letras": (40.4140, -3.6980),
        "Chueca": (40.4220, -3.6970), "Atocha": (40.4070, -3.6930),
        "Embajadores": (40.4070, -3.7050), "Palacio": (40.4150, -3.7140),
        "Sol": (40.4165, -3.7026), "Huertas": (40.4140, -3.7000),
        "El Rastro": (40.4100, -3.7080), "Delicias": (40.3960, -3.6970),
        "Chopera": (40.3990, -3.6980), "Legazpi": (40.3900, -3.6920),
        "Comillas": (40.3910, -3.7250), "Oporto": (40.3870, -3.7200),
        "Pradolongo": (40.3820, -3.7050), "Vallehermoso": (40.4360, -3.7060),
        "Almagro": (40.4310, -3.6930), "Ríos Rosas": (40.4430, -3.7000),
        "Almenara": (40.4620, -3.7070), "Berruguete": (40.4580, -3.7100),
        "El Pilar": (40.4750, -3.7030), "Peñagrande": (40.4840, -3.7090),
        "Valverde": (40.4940, -3.7160), "Fuentelareina": (40.5060, -3.7260),
        "Mirasierra": (40.5000, -3.7010), "La Guindalera": (40.4340, -3.6750),
        "Fuente del Berro": (40.4240, -3.6750), "Goya": (40.4280, -3.6780),
        "Lista": (40.4290, -3.6740), "Castellana": (40.4420, -3.6880),
        "Hispanoamérica": (40.4490, -3.6820), "Nueva España": (40.4540, -3.6830),
        "Bernabéu": (40.4530, -3.6883), "Ciudad Jardín": (40.4450, -3.6670),
        "Concepción": (40.4360, -3.6550), "San Juan Bautista": (40.4440, -3.6550),
        "Canillejas": (40.4460, -3.6260), "Pueblo Nuevo": (40.4350, -3.6480),
        "Las Rosas": (40.4430, -3.6310), "Palomeras": (40.3900, -3.6440),
        "Portazgo": (40.3820, -3.6490), "Numancia": (40.3840, -3.6560),
        "Vicálvaro": (40.3970, -3.6050), "San Diego": (40.3920, -3.6620),
        "Entrevías": (40.3780, -3.6570), "San Cristóbal": (40.3710, -3.6790),
        "Sanchinarro": (40.4990, -3.6440), "Vallehermoso": (40.4370, -3.7060),
        "Ciudad Universitaria": (40.4440, -3.7230), "Argüelles": (40.4300, -3.7180),
        "Gaztambide": (40.4310, -3.7160), "Arapiles": (40.4390, -3.7080),
        "Trafalgar": (40.4290, -3.6990), "Alonso Cano": (40.4360, -3.7010),
        "La Elipa": (40.4180, -3.6520), "Cuatro Caminos": (40.4450, -3.7030),
    },
    "Barcelona": {
        "Eixample": (41.3890, 2.1620), "Gràcia": (41.4035, 2.1565),
        "Sarrià-Sant Gervasi": (41.3990, 2.1300), "Sant Martí": (41.4100, 2.1990),
        "Les Corts": (41.3860, 2.1290), "Sants-Montjuïc": (41.3730, 2.1490),
        "Horta-Guinardó": (41.4180, 2.1650), "Nou Barris": (41.4410, 2.1770),
        "Sant Andreu": (41.4350, 2.1900), "Ciutat Vella": (41.3820, 2.1740),
        "Poblenou": (41.4030, 2.2040), "El Born": (41.3855, 2.1825),
        "La Barceloneta": (41.3810, 2.1890), "Pedralbes": (41.3880, 2.1150),
        "El Raval": (41.3800, 2.1690), "Poble Sec": (41.3720, 2.1620),
        "Camp Nou": (41.3810, 2.1210), "Clot": (41.4100, 2.1870),
        "Sagrada Família": (41.4040, 2.1745), "Vila de Gràcia": (41.4000, 2.1560),
        "Sant Gervasi": (41.4010, 2.1380), "Sarrià": (41.3980, 2.1200),
        "Les Tres Torres": (41.3950, 2.1330), "La Bonanova": (41.4020, 2.1280),
        "El Putget": (41.4050, 2.1450), "Vallcarca": (41.4110, 2.1480),
        "El Coll": (41.4090, 2.1530), "La Salut": (41.4060, 2.1600),
        "Camp d'en Grassot": (41.4040, 2.1620), "El Carmel": (41.4160, 2.1590),
        "Horta": (41.4280, 2.1670), "Vilapicina": (41.4340, 2.1720),
        "Porta": (41.4380, 2.1730), "Verdun": (41.4390, 2.1760),
        "La Prosperitat": (41.4440, 2.1780), "Les Roquetes": (41.4480, 2.1730),
        "Sant Andreu de Palomar": (41.4350, 2.1880), "La Sagrera": (41.4270, 2.1900),
        "Navas": (41.4220, 2.1870), "El Camp de l'Arpa": (41.4140, 2.1810),
        "El Fort Pienc": (41.3940, 2.1770), "La Dreta de l'Eixample": (41.3930, 2.1680),
        "L'Antiga Esquerra de l'Eixample": (41.3870, 2.1590),
        "La Nova Esquerra de l'Eixample": (41.3840, 2.1550), "Sant Antoni": (41.3820, 2.1620),
        "El Parc i la Llacuna": (41.3970, 2.1960), "La Vila Olímpica": (41.3880, 2.1960),
        "Diagonal Mar": (41.4040, 2.2160), "Sants": (41.3790, 2.1380),
        "Badal": (41.3770, 2.1290), "La Bordeta": (41.3740, 2.1400), "Hostafrancs": (41.3730, 2.1480),
    },
    "Valencia": {
        "Ruzafa": (39.4610, -0.3720), "El Carmen": (39.4780, -0.3810),
        "L'Eixample": (39.4680, -0.3710), "Benimaclet": (39.4880, -0.3630),
        "Ciutat Vella": (39.4740, -0.3780), "Campanar": (39.4830, -0.3930),
        "Patraix": (39.4600, -0.3920), "Jesús": (39.4550, -0.3810),
        "Poblats Marítims": (39.4560, -0.3370), "El Cabanyal": (39.4680, -0.3280),
        "La Saïdia": (39.4820, -0.3740), "Extramurs": (39.4700, -0.3850),
        "Quatre Carreres": (39.4510, -0.3620), "Algirós": (39.4760, -0.3550),
        "Gran Vía": (39.4650, -0.3780),
    },
    "Sevilla": {
        "Triana": (37.3830, -6.0060), "Los Remedios": (37.3740, -6.0080),
        "Nervión": (37.3900, -5.9700), "Santa Cruz": (37.3850, -5.9870),
        "Macarena": (37.4030, -5.9900), "San Bernardo": (37.3810, -5.9830),
        "Alameda": (37.3960, -5.9960), "El Arenal": (37.3870, -5.9980),
        "San Lorenzo": (37.3930, -5.9960), "Bermejales": (37.3620, -5.9860),
        "Heliópolis": (37.3580, -5.9770), "Tablada": (37.3600, -6.0060),
        "Cerro del Águila": (37.3810, -5.9630), "Pino Montano": (37.4170, -5.9860),
    },
    "Málaga": {
        "Centro Histórico": (36.7210, -4.4200), "La Malagueta": (36.7170, -4.4100),
        "El Palo": (36.7220, -4.3650), "Pedregalejo": (36.7210, -4.3870),
        "Teatinos": (36.7270, -4.4670), "Huelin": (36.7130, -4.4420),
        "Ciudad Jardín": (36.7290, -4.4250), "Carranque": (36.7200, -4.4510),
        "El Candado": (36.7180, -4.3540), "Puerto de la Torre": (36.7460, -4.4750),
        "Campanillas": (36.7450, -4.5110), "La Rosaleda": (36.7310, -4.4340),
        "Cruz de Humilladero": (36.7180, -4.4440),
    },
    "Bilbao": {
        "Casco Viejo": (43.2580, -2.9230), "Abando": (43.2630, -2.9340),
        "Indautxu": (43.2610, -2.9430), "Deusto": (43.2720, -2.9470),
        "San Ignacio": (43.2760, -2.9580), "Rekalde": (43.2530, -2.9510),
        "Zazpikaleak": (43.2590, -2.9280), "Begoña": (43.2650, -2.9200),
        "Santutxu": (43.2550, -2.9160), "Basurto": (43.2620, -2.9560),
    },
    "Alicante": {
        "Centro": (38.3460, -0.4900), "Playa de San Juan": (38.3730, -0.4220),
        "El Campello": (38.4280, -0.3970), "Cabo de las Huertas": (38.3620, -0.4130),
        "Carolinas": (38.3510, -0.4870), "Benalúa": (38.3430, -0.4870),
        "Florida": (38.3560, -0.5000), "San Blas": (38.3550, -0.4770),
        "Altozano": (38.3480, -0.4950), "Villafranqueza": (38.3700, -0.4650),
    },
    "Zaragoza": {
        "Centro": (41.6520, -0.8790), "Delicias": (41.6440, -0.9050),
        "San José": (41.6400, -0.8690), "Las Fuentes": (41.6490, -0.8600),
        "El Rabal": (41.6610, -0.8700), "Universidad": (41.6460, -0.8850),
        "Actur-Rey Fernando": (41.6700, -0.8890), "La Almozara": (41.6580, -0.9020),
        "Oliver-Valdefierro": (41.6440, -0.9250), "Torrero-La Paz": (41.6330, -0.8770),
    },
    "Granada": {
        "Albaicín": (37.1810, -3.5920), "Centro": (37.1760, -3.5990),
        "Realejo": (37.1730, -3.5950), "Ronda": (37.1710, -3.6060),
        "Beiro": (37.1880, -3.6070), "Zaidín": (37.1650, -3.5920),
        "Chana": (37.1840, -3.6130), "Genil": (37.1680, -3.5850),
        "Figares": (37.1740, -3.6020), "Camino de Ronda": (37.1750, -3.6050),
    },
    "Murcia": {
        "Centro": (37.9830, -1.1280), "El Carmen": (37.9880, -1.1310),
        "Santa María de Gracia": (37.9860, -1.1220), "Vistabella": (37.9780, -1.1190),
        "La Flota": (37.9910, -1.1110), "Infante Juan Manuel": (37.9900, -1.1230),
        "San Andrés": (37.9820, -1.1360), "Santiago el Mayor": (37.9870, -1.1380),
        "La Fama": (37.9770, -1.1290), "San Antón": (37.9800, -1.1210),
    },
    "San Sebastián": {
        "Centro": (43.3210, -1.9840), "Parte Vieja": (43.3240, -1.9830),
        "Gros": (43.3230, -1.9730), "Amara": (43.3100, -1.9800),
        "Antiguo": (43.3160, -1.9990), "Egia": (43.3180, -1.9690),
        "Ibaeta": (43.3100, -2.0010), "Aiete": (43.3040, -2.0050),
        "Intxaurrondo": (43.3120, -1.9600), "El Antiguo": (43.3150, -1.9960),
    },
    "Santander": {
        "Centro": (43.4620, -3.8080), "El Sardinero": (43.4740, -3.7860),
        "Cuatro Caminos": (43.4570, -3.8200), "Castilla-Hermida": (43.4590, -3.8130),
        "Monte": (43.4660, -3.7980), "Numancia": (43.4560, -3.8250),
        "San Martín": (43.4570, -3.8300), "Puerto Chico": (43.4650, -3.7890),
    },
    "Palma de Mallorca": {
        "Centro": (39.5710, 2.6500), "Santa Catalina": (39.5720, 2.6380),
        "El Terreno": (39.5680, 2.6260), "Son Espanyolet": (39.5740, 2.6330),
        "El Molinar": (39.5660, 2.6660), "Portixol": (39.5620, 2.6640),
        "Son Armadams": (39.5670, 2.6330), "La Lonja": (39.5690, 2.6470),
        "Son Vida": (39.5830, 2.6280), "Genova": (39.5610, 2.6180),
    },
}

# ──────────────────────────────────────────────
# Datos base por ciudad
# ──────────────────────────────────────────────

CITY_DATA = {
    "Madrid": {
        "province": "Madrid",
        "neighborhoods": [
            "Chamberí", "Retiro", "Salamanca", "Malasaña", "Lavapiés",
            "La Latina", "Chamartín", "Tetuán", "Moncloa-Aravaca", "Arganzuela",
            "Carabanchel", "Usera", "Moratalaz", "Hortaleza", "Las Tablas",
            "Vallecas", "Prosperidad", "Barrio de las Letras", "Chueca", "Atocha",
            "Embajadores", "Palacio", "Sol", "Huertas", "Lavapiés", "El Rastro",
            "Delicias", "Chopera", "Legazpi", "Comillas", "Oporto", "Pradolongo",
            "Vallehermoso", "Almagro", "Ríos Rosas", "Almenara", "Berruguete",
            "El Pilar", "Peñagrande", "Valverde", "Fuentelareina", "Mirasierra",
            "La Guindalera", "Fuente del Berro", "Goya", "Lista", "Castellana",
            "Hispanoamérica", "Nueva España", "Bernabéu", "Virgen del Cortijo",
            "Ciudad Jardín", "Concepción", "San Juan Bautista", "Canillejas",
            "Pueblo Nuevo", "Las Rosas", "Palomeras", "Portazgo", "Numancia",
            "Vicálvaro", "San Diego", "Entrevías", "San Cristóbal",
            "Sanchinarro", "Virgen de Begoña", "Piovera", "Palomas",
            "Barrio del Pilar", "Ventilla", "Valdeacederas", "Cuatro Caminos",
            "Ciudad Universitaria", "Argüelles", "Gaztambide", "Arapiles",
            "Trafalgar", "Alonso Cano", "Vallehermoso", "Quintana",
            "Pueblo Nuevo", "Simancas", "Quintana", "La Elipa",
        ],
        "streets": [
            "Calle de Alcalá", "Calle de Goya", "Calle de Serrano", "Calle de Fuencarral",
            "Calle de Hortaleza", "Calle Mayor", "Gran Vía", "Calle de Velázquez",
            "Calle de Bravo Murillo", "Paseo de la Castellana", "Calle de Atocha",
            "Calle de Toledo", "Calle del Pez", "Calle de Alberto Aguilera",
            "Calle de Santa Engracia", "Calle de O'Donnell", "Calle de Arturo Soria",
            "Calle de Narváez", "Calle de Eloy Gonzalo", "Paseo de las Delicias",
        ],
        "price_range": (1400, 2800),
        "metro": ["Sol", "Gran Vía", "Tribunal", "Alonso Martínez", "Bilbao", "Chueca",
                   "Ópera", "Atocha", "Retiro", "Ibiza", "Nuevos Ministerios", "Canal",
                   "Chamartín", "Príncipe Pío", "Moncloa", "Plaza de España"],
        "is_coastal": False,
    },
    "Barcelona": {
        "province": "Barcelona",
        "neighborhoods": [
            "Eixample", "Gràcia", "Sarrià-Sant Gervasi", "Sant Martí", "Les Corts",
            "Sants-Montjuïc", "Horta-Guinardó", "Nou Barris", "Sant Andreu",
            "Ciutat Vella", "Poblenou", "El Born", "La Barceloneta", "Pedralbes",
            "El Raval", "Poble Sec", "Camp Nou", "Clot", "Sagrada Família", "Vila de Gràcia",
            "Sant Gervasi", "Sarrià", "Les Tres Torres", "La Bonanova",
            "El Putget", "Vallcarca", "El Coll", "La Salut", "Camp d'en Grassot",
            "El Baix Guinardó", "Can Baró", "El Guinardó", "La Font d'en Fargues",
            "El Carmel", "La Teixonera", "Sant Genís dels Agudells", "Montbau",
            "La Vall d'Hebron", "La Clota", "Horta", "Vilapicina",
            "Porta", "El Turó de la Peira", "Can Peguera", "La Guineueta",
            "Canyelles", "Les Roquetes", "Verdun", "La Prosperitat",
            "La Trinitat Nova", "Torre Baró", "Ciutat Meridiana", "Vallbona",
            "La Trinitat Vella", "Baró de Viver", "El Bon Pastor",
            "Sant Andreu de Palomar", "La Sagrera", "El Congrés i els Indians",
            "Navas", "El Camp de l'Arpa", "El Fort Pienc", "La Sagrada Família",
            "La Dreta de l'Eixample", "L'Antiga Esquerra de l'Eixample",
            "La Nova Esquerra de l'Eixample", "Sant Antoni",
            "El Parc i la Llacuna", "La Vila Olímpica", "El Besos",
            "El Maresme", "Diagonal Mar", "La Verneda i la Pau",
            "Sants", "Badal", "La Bordeta", "Hostafrancs", "La Vinya",
            "Can Clos", "Font de la Guatlla", "Zona Franca",
        ],
        "streets": [
            "Carrer de Mallorca", "Carrer de València", "Passeig de Gràcia", "La Rambla",
            "Carrer d'Aragó", "Avinguda Diagonal", "Carrer de Balmes", "Carrer del Consell de Cent",
            "Carrer de Muntaner", "Gran de Gràcia", "Carrer de Provença", "Via Laietana",
            "Carrer de Pau Claris", "Carrer de Roger de Llúria", "Carrer d'Enric Granados",
            "Carrer de Sardenya", "Carrer de la Marina", "Passeig de Sant Joan",
            "Carrer de Còrsega", "Rambla de Catalunya",
        ],
        "price_range": (1500, 2800),
        "metro": ["Passeig de Gràcia", "Diagonal", "Universitat", "Catalunya", "Sagrada Família",
                   "Fontana", "Hospital de Sant Pau", "Barceloneta", "Clot", "Sants Estació",
                   "Arc de Triomf", "Jaume I", "Drassanes", "Liceu", "Urquinaona"],
        "is_coastal": True,
    },
    "Valencia": {
        "province": "Valencia",
        "neighborhoods": [
            "Ruzafa", "El Carmen", "L'Eixample", "Benimaclet", "Ciutat Vella",
            "Campanar", "Patraix", "Jesús", "Poblats Marítims", "El Cabanyal",
            "La Saïdia", "Extramurs", "Quatre Carreres", "Algirós", "Gran Vía",
            "Malvarrosa", "Las Arenas", "Nazaret", "El Grau", "Natzaret",
            "La Malva-rosa", "Cañamelar", "Orriols", "Torrefiel", "Marxalenes",
            "La Zaidía", "Morvedre", "Trinitat", "Tormos", "Sant Pau",
            "El Calvari", "La Creu del Grau", "Camí Fondo", "Penya-roja",
            "L'Illa Perduda", "Ciutat Jardí", "Aiora", "La Carrasca",
            "Beniferri", "Benimamet", "Benissepena", "El Saler",
            "L'Hort de Senabre", "La Creu Coberta", "Sant Marcel·lí",
            "Camí Real", "Safranar", "Favara", "Vara de Quart",
            "Soternes", "Arrancapins", "La Roqueta", "La Petxina",
        ],
        "streets": [
            "Carrer de Sueca", "Carrer de la Pau", "Avinguda del Regne de València",
            "Carrer de Colón", "Gran Via del Marqués del Túria", "Carrer de Russafa",
            "Carrer de Cuba", "Carrer de Cadis", "Carrer del Dr. Sumsi",
            "Avinguda de Blasco Ibáñez", "Carrer de Xàtiva", "Carrer d'En Bou",
            "Plaça de l'Ajuntament", "Carrer de Guillem de Castro",
        ],
        "price_range": (1000, 2200),
        "metro": ["Xàtiva", "Colón", "Ángel Guimerá", "Benimaclet", "Alameda",
                   "Maritim–Serrería", "Túria", "Facultats", "Campanar"],
        "is_coastal": True,
    },
    "Sevilla": {
        "province": "Sevilla",
        "neighborhoods": [
            "Triana", "Los Remedios", "Nervión", "Santa Cruz", "Macarena",
            "San Bernardo", "Alameda", "El Arenal", "San Lorenzo", "Bermejales",
            "Heliópolis", "Tablada", "Cerro del Águila", "Pino Montano",
            "El Porvenir", "Felipe II", "Huerta del Rey", "Bami",
            "Palmas Altas", "Palmete", "Juan XXIII", "La Paz",
            "Los Carteros", "Amate", "El Juncal", "La Plata",
            "Rochelambert", "Torreblanca", "Polígono Norte", "Valdezorras",
            "Sevilla Este", "El Cano", "Prados de San Sebastián",
            "El Tardón", "Los Pajaritos", "Bellavista", "La Oliva",
        ],
        "streets": [
            "Calle Betis", "Avenida de la Constitución", "Calle Sierpes",
            "Calle San Jacinto", "Calle Feria", "Alameda de Hércules",
            "Calle Mateos Gago", "Avenida de Kansas City", "Calle Asunción",
            "Calle González Cuadrado", "Calle Luis Montoto", "Avenida de la Palmera",
        ],
        "price_range": (900, 1900),
        "metro": ["Puerta Jerez", "San Bernardo", "Nervión", "Blas Infante",
                   "Gran Plaza", "Prado de San Sebastián"],
        "is_coastal": False,
    },
    "Málaga": {
        "province": "Málaga",
        "neighborhoods": [
            "Centro Histórico", "La Malagueta", "El Palo", "Pedregalejo",
            "Teatinos", "Huelin", "Ciudad Jardín", "Carranque", "El Candado",
            "Puerto de la Torre", "Campanillas", "La Rosaleda", "Cruz de Humilladero",
            "Babel", "La Luz", "El Molinillo", "La Victoria",
            "El Ejido", "Capuchinos", "La Merced", "San Felipe Neri",
            "La Trinidad", "Perchel Norte", "Perchel Sur", "La Goleta",
            "El Bulto", "El Molinillo", "Churriana", "Olías",
            "Los Alamos", "Los Ramos", "Nuevo San Andrés", "San Andrés",
            "Miraflores de los Ángeles", "Cerrado de Calderón",
            "El Cónsul", "El Limonar", "La Caleta", "Sacaba",
        ],
        "streets": [
            "Calle Larios", "Paseo del Parque", "Alameda Principal",
            "Paseo Marítimo Pablo Ruiz Picasso", "Avenida de Andalucía",
            "Calle Carretería", "Calle Nueva", "Calle Granada",
            "Calle Victoria", "Avenida Juan Sebastián Elcano",
            "Calle Cuarteles", "Calle Muelle Heredia",
        ],
        "price_range": (900, 2000),
        "metro": ["La Malagueta", "El Perchel", "Guadalmedina", "Princesa-Huelin",
                   "El Torcal", "Palacio de los Deportes"],
        "is_coastal": True,
    },
    "Bilbao": {
        "province": "Vizcaya",
        "neighborhoods": [
            "Casco Viejo", "Abando", "Indautxu", "Deusto", "San Ignacio",
            "Rekalde", "Zazpikaleak", "Begoña", "Santutxu", "Basurto",
        ],
        "streets": [
            "Gran Vía de Don Diego López de Haro", "Calle Ercilla",
            "Alameda de Urquijo", "Calle Iparraguirre", "Calle Licenciado Poza",
            "Calle Rodríguez Arias", "Calle Ledesma", "Calle Diputación",
            "Calle Hurtado de Amézaga", "Calle de la Autonomía",
        ],
        "price_range": (1000, 2200),
        "metro": ["Abando", "Indautxu", "Casco Viejo", "Deusto", "San Mamés",
                   "Moyúa", "Zazpikaleak"],
        "is_coastal": True,
    },
    "Alicante": {
        "province": "Alicante",
        "neighborhoods": [
            "Centro", "Playa de San Juan", "El Campello", "Cabo de las Huertas",
            "Carolinas", "Benalúa", "Florida", "San Blas", "Altozano", "Villafranqueza",
        ],
        "streets": [
            "Rambla de Méndez Núñez", "Avenida de Maisonnave", "Calle San Fernando",
            "Avenida de la Constitución", "Calle Castaños", "Explanada de España",
            "Calle San Vicente", "Avenida de Alfonso el Sabio", "Calle Gerona",
        ],
        "price_range": (800, 1800),
        "metro": ["Mercado", "Luceros", "Marq-Castillo", "TRAM Playa San Juan"],
        "is_coastal": True,
    },
    "Zaragoza": {
        "province": "Zaragoza",
        "neighborhoods": [
            "Centro", "Delicias", "San José", "Las Fuentes", "El Rabal",
            "Universidad", "Actur-Rey Fernando", "La Almozara", "Oliver-Valdefierro",
            "Torrero-La Paz",
        ],
        "streets": [
            "Paseo de la Independencia", "Calle Alfonso I", "Calle Don Jaime I",
            "Gran Vía", "Avenida de Cesáreo Alierta", "Calle Zurita",
            "Calle Manifestación", "Paseo de las Damas", "Calle San Miguel",
        ],
        "price_range": (700, 1600),
        "metro": ["Tranvía Romareda", "Tranvía Gran Vía", "Tranvía César Augusto"],
        "is_coastal": False,
    },
    "Granada": {
        "province": "Granada",
        "neighborhoods": [
            "Albaicín", "Centro", "Realejo", "Ronda", "Beiro",
            "Zaidín", "Chana", "Genil", "Figares", "Camino de Ronda",
        ],
        "streets": [
            "Gran Vía de Colón", "Calle Recogidas", "Calle Reyes Católicos",
            "Acera del Darro", "Calle Mesones", "Camino de Ronda",
            "Calle Ángel Ganivet", "Avenida de la Constitución",
        ],
        "price_range": (700, 1500),
        "metro": ["Metro de Granada (línea 1)"],
        "is_coastal": False,
    },
    "Murcia": {
        "province": "Murcia",
        "neighborhoods": [
            "Centro", "El Carmen", "Santa María de Gracia", "Vistabella",
            "La Flota", "Infante Juan Manuel", "San Andrés", "Santiago el Mayor",
            "La Fama", "San Antón",
        ],
        "streets": [
            "Gran Vía del Escultor Salzillo", "Calle Trapería", "Avenida de la Libertad",
            "Calle Platería", "Calle Floridablanca", "Calle Jaime I El Conquistador",
            "Avenida Juan de Borbón", "Calle Alfonso X el Sabio",
        ],
        "price_range": (600, 1400),
        "metro": ["Tranvía de Murcia"],
        "is_coastal": False,
    },
    "San Sebastián": {
        "province": "Guipúzcoa",
        "neighborhoods": [
            "Centro", "Parte Vieja", "Gros", "Amara", "Antiguo",
            "Egia", "Ibaeta", "Aiete", "Intxaurrondo", "El Antiguo",
        ],
        "streets": [
            "Avenida de la Libertad", "Calle San Martín", "Boulevard",
            "Calle Mayor", "Calle Fermín Calbetón", "Calle Urbieta",
            "Paseo de la Concha", "Calle Easo", "Calle Hernani",
        ],
        "price_range": (1200, 2400),
        "metro": [],
        "is_coastal": True,
    },
    "Santander": {
        "province": "Cantabria",
        "neighborhoods": [
            "Centro", "El Sardinero", "Cuatro Caminos", "Castilla-Hermida",
            "Monte", "Numancia", "San Martín", "Puerto Chico",
        ],
        "streets": [
            "Calle Burgos", "Paseo de Pereda", "Calle Calvo Sotelo",
            "Calle San Fernando", "Avenida de los Castros",
            "Calle Isabel II", "Calle Hernán Cortés",
        ],
        "price_range": (800, 1700),
        "metro": [],
        "is_coastal": True,
    },
    "Palma de Mallorca": {
        "province": "Islas Baleares",
        "neighborhoods": [
            "Centro", "Santa Catalina", "El Terreno", "Son Espanyolet",
            "El Molinar", "Portixol", "Son Armadams", "La Lonja",
            "Son Vida", "Genova",
        ],
        "streets": [
            "Passeig del Born", "Carrer de Sant Miquel", "Avinguda Jaume III",
            "Carrer dels Oms", "Carrer de la Unió", "Passeig Marítim",
            "Carrer de Sant Feliu", "Carrer de Can Sanç",
        ],
        "price_range": (1100, 2400),
        "metro": [],
        "is_coastal": True,
    },
}

# Plataformas y URLs base (apuntan a búsquedas reales, no a anuncios ficticios)
PLATFORMS = [
    ("idealista", "https://www.idealista.com/alquiler-viviendas/{city}/"),
    ("fotocasa", "https://www.fotocasa.es/es/alquiler/viviendas/{city}/todas-las-zonas/l"),
    ("habitaclia", "https://www.habitaclia.com/alquiler-{city}.htm"),
    ("pisos.com", "https://www.pisos.com/alquiler/pisos-{city}/"),
    ("housinganywhere", "_ha_"),  # URL se genera dinámicamente con filtros por propiedad
]

# Slugs de ciudad para HousingAnywhere (formato oficial de la plataforma)
HA_CITY_SLUGS = {
    "Madrid": "Madrid--Spain",
    "Barcelona": "Barcelona--Spain",
    "Valencia": "Valencia--Spain",
    "Sevilla": "Seville--Spain",
    "Málaga": "Malaga--Spain",
    "Bilbao": "Bilbao--Spain",
    "Alicante": "Alicante--Spain",
    "Zaragoza": "Zaragoza--Spain",
    "Granada": "Granada--Spain",
    "Murcia": "Murcia--Spain",
    "San Sebastián": "San-Sebastian--Spain",
    "Santander": "Santander--Spain",
    "Palma de Mallorca": "Palma-de-Mallorca--Spain",
}

# Imágenes de Unsplash (licencia libre para demos)
PROPERTY_IMAGES = [
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600",
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=600",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=600",
    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600",
    "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=600",
    "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=600",
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600",
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600",
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600",
    "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=600",
    "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600",
    "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=600",
    "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=600",
    "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=600",
    "https://images.unsplash.com/photo-1600607687644-aac4c3eac7f4?w=600",
    "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=600",
    "https://images.unsplash.com/photo-1560185007-c5ca9d2c014d?w=600",
    "https://images.unsplash.com/photo-1560185008-a33f5c7b1844?w=600",
    "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=600",
    "https://images.unsplash.com/photo-1600573472592-401b489a3cdc?w=600",
    "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?w=600",
    "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=600",
    "https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83?w=600",
]

# Plantillas de títulos
TITLE_TEMPLATES = [
    "Piso luminoso de {beds} habitaciones en {neighborhood}",
    "Amplio piso reformado en {neighborhood}",
    "Piso con terraza en {neighborhood}",
    "Ático con vistas en {neighborhood}",
    "Piso moderno en {neighborhood}",
    "Piso exterior con balcón en {neighborhood}",
    "Apartamento acogedor en {neighborhood}",
    "Dúplex amplio en {neighborhood}",
    "Piso céntrico en {neighborhood}",
    "Piso reformado con encanto en {neighborhood}",
    "Apartamento nuevo a estrenar en {neighborhood}",
    "Piso soleado de {beds} dormitorios en {neighborhood}",
    "Piso con parking incluido en {neighborhood}",
    "Piso amueblado en {neighborhood}",
    "Piso con vistas panorámicas en {neighborhood}",
    "Bonito piso en zona tranquila de {neighborhood}",
    "Piso familiar de {beds} habitaciones en {neighborhood}",
    "Apartamento equipado cerca de {metro}",
    "Piso con buenas comunicaciones en {neighborhood}",
    "Piso recién reformado en pleno {neighborhood}",
]

# Fragmentos de descripción
DESC_FEATURES = {
    "terraza": "terraza de {size}m²",
    "balcón": "balcón a la calle",
    "ascensor": "edificio con ascensor",
    "aire": "aire acondicionado frío/calor",
    "calefacción": "calefacción central",
    "amueblado": "completamente amueblado y equipado",
    "parking": "plaza de garaje incluida",
    "piscina": "piscina comunitaria",
    "mascotas": "se admiten mascotas",
    "empadronamiento": "empadronamiento incluido en contrato",
    "transporte": "transporte público a pocos minutos ({metro})",
    "servicios": "supermercados, farmacias y colegios en la zona",
    "trastero": "trastero incluido",
    "portero": "portero físico",
    "videovigilancia": "sistema de videovigilancia",
}

PROPERTY_TYPES = ["piso", "piso", "piso", "piso", "ático", "dúplex", "apartamento"]
ENERGY_RATINGS = ["A", "B", "C", "C", "D", "D", "E", "E", "F"]
AVAILABILITY_OPTIONS = [
    "Inmediata", "Inmediata", "Septiembre 2026", "Octubre 2026",
    "A partir de septiembre 2026", "A partir de octubre 2026",
    "Noviembre 2026", "Agosto 2026", "Julio 2026",
]


def _gen_id(city: str, idx: int) -> str:
    raw = f"demo-{city}-{idx}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _generate_property(city_name: str, city_info: dict, idx: int) -> Property:
    """Genera una propiedad demo coherente para una ciudad."""
    rng = _RNG

    prop_id = _gen_id(city_name, idx)
    neighborhood = rng.choice(city_info["neighborhoods"])
    # Usar calles reales del barrio para coherencia geográfica
    neighborhood_specific = NEIGHBORHOOD_STREETS.get(city_name, {}).get(neighborhood)
    if neighborhood_specific:
        street = rng.choice(neighborhood_specific)
    else:
        street = rng.choice(city_info["streets"])
    street_num = rng.randint(1, 120)
    address = f"{street}, {street_num}"

    price_min, price_max = city_info["price_range"]
    # Generar precio redondeado a 50€
    price = round(rng.randint(price_min, price_max) / 50) * 50

    bedrooms = rng.choice([2, 2, 2, 3, 3, 3, 4])
    bathrooms = rng.choice([1, 2, 2, 2, 2, 3]) if bedrooms >= 3 else rng.choice([1, 2, 2])
    # Asegurar mínimo min_bathrooms razonable
    if bathrooms < 2 and rng.random() > 0.3:
        bathrooms = 2

    area = rng.randint(55, 75) + (bedrooms - 2) * rng.randint(15, 30)
    floor_num = rng.randint(0, 8)
    floor = "bajo" if floor_num == 0 else str(floor_num)

    has_terrace = rng.random() > 0.55
    has_balcony = not has_terrace and rng.random() > 0.4
    has_elevator = floor_num >= 2 or rng.random() > 0.3
    has_ac = rng.random() > 0.3
    has_heating = rng.random() > 0.25
    has_parking = rng.random() > 0.7
    has_pool = rng.random() > 0.85
    pets_allowed = True  # Siempre true, es requisito del usuario
    furnished = rng.random() > 0.5
    public_transport = rng.random() > 0.15
    services = rng.random() > 0.2
    empadronamiento = rng.random() > 0.3
    has_sea_view = city_info["is_coastal"] and rng.random() > 0.7
    is_long_stay = rng.random() > 0.5

    # Plataforma
    plat_name, plat_url_tpl = rng.choice(PLATFORMS)
    city_slug = city_name.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    if plat_name == "housinganywhere":
        # HousingAnywhere usa segmentos de ruta, NO query params
        ha_slug = HA_CITY_SLUGS.get(city_name, f"{city_name.replace(' ', '-')}--Spain")
        url = f"https://housinganywhere.com/s/{ha_slug}/apartment-for-rent"
        is_long_stay = True
    else:
        url = plat_url_tpl.format(city=city_slug)

    # Metro cercano
    metro_name = rng.choice(city_info["metro"]) if city_info["metro"] else "parada de bus cercana"

    # Título
    title_tpl = rng.choice(TITLE_TEMPLATES)
    title = title_tpl.format(beds=bedrooms, neighborhood=neighborhood, metro=metro_name)

    # Descripción
    desc_parts = [
        f"{'Amplio' if area > 90 else 'Bonito'} {rng.choice(PROPERTY_TYPES)} de {area}m² en {neighborhood}.",
        f"{bedrooms} habitaciones, {bathrooms} {'baños' if bathrooms > 1 else 'baño'}, "
        f"{'cocina totalmente equipada' if furnished else 'cocina independiente'}.",
    ]
    if has_terrace:
        desc_parts.append(f"Terraza de {rng.randint(8, 25)}m².")
    if has_balcony:
        desc_parts.append("Balcón a la calle con vistas.")
    if has_ac:
        desc_parts.append("Aire acondicionado frío/calor.")
    if has_heating:
        desc_parts.append("Calefacción central.")
    if has_parking:
        desc_parts.append("Plaza de garaje incluida.")
    if has_pool:
        desc_parts.append("Piscina comunitaria y zonas verdes.")
    if has_elevator:
        desc_parts.append("Edificio con ascensor.")
    if public_transport:
        desc_parts.append(f"Metro/bus ({metro_name}) a pocos minutos.")
    if services:
        desc_parts.append("Supermercados, farmacias y colegios en la zona.")
    desc_parts.append("Se admiten mascotas.")
    if empadronamiento:
        desc_parts.append("Empadronamiento incluido.")
    if has_sea_view:
        desc_parts.append("Vistas al mar.")

    description = " ".join(desc_parts)

    # Imagen
    img = PROPERTY_IMAGES[idx % len(PROPERTY_IMAGES)]

    # Coordenadas reales del barrio con pequeña variación para cada propiedad
    base_coords = NEIGHBORHOOD_COORDS.get(city_name, {}).get(neighborhood)
    if base_coords:
        # Variación de ±200m aprox para que no se apilen exactamente
        lat = base_coords[0] + (rng.random() - 0.5) * 0.004
        lng = base_coords[1] + (rng.random() - 0.5) * 0.004
    else:
        lat = None
        lng = None

    prop = Property(
        id=prop_id,
        title=title,
        description=description,
        price=price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        area_m2=area,
        floor=floor,
        has_elevator=has_elevator,
        has_terrace=has_terrace,
        has_balcony=has_balcony,
        pets_allowed=pets_allowed,
        address=address,
        neighborhood=neighborhood,
        city=city_name,
        province=city_info["province"],
        latitude=lat,
        longitude=lng,
        availability=rng.choice(AVAILABILITY_OPTIONS),
        images=[img],
        url=url,
        platform=plat_name,
        property_type=rng.choice(PROPERTY_TYPES),
        has_air_conditioning=has_ac,
        has_heating=has_heating,
        has_parking=has_parking,
        has_pool=has_pool,
        furnished=furnished,
        public_transport_nearby=public_transport,
        services_nearby=services,
        allows_empadronamiento=empadronamiento,
        energy_rating=rng.choice(ENERGY_RATINGS),
        has_sea_view=has_sea_view,
        is_long_stay=is_long_stay,
    )
    return prop


def generate_all_demo_properties() -> List[Property]:
    """
    Genera un conjunto completo de propiedades demo para todas las ciudades.
    Retorna ~200+ propiedades distribuidas de forma realista.
    """
    properties = []

    # Distribución: más propiedades para ciudades grandes
    city_counts = {
        "Madrid": 25,
        "Barcelona": 25,
        "Valencia": 18,
        "Sevilla": 15,
        "Málaga": 15,
        "Bilbao": 12,
        "Alicante": 12,
        "Zaragoza": 10,
        "Granada": 10,
        "Murcia": 8,
        "San Sebastián": 8,
        "Santander": 8,
        "Palma de Mallorca": 10,
    }

    for city_name, count in city_counts.items():
        city_info = CITY_DATA[city_name]
        for i in range(count):
            prop = _generate_property(city_name, city_info, i)
            properties.append(prop)

    return properties


# Cache: generar una sola vez al importar
DEMO_PROPERTIES: List[Property] = generate_all_demo_properties()
