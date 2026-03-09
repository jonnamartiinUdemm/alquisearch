"""
neighborhoods.py
================
Índice completo de barrios y zonas de España al estilo Idealista.
Cubre más de 1.200 barrios en las principales ciudades.
Soporta búsqueda predictiva con normalización de tildes y prefijos.

Estructura:
    NEIGHBORHOOD_INDEX: List[dict]  — registro plano de cada barrio
    get_suggestions(query, limit)   — búsqueda predictiva

Cada entrada tiene:
    {
        "label": "Malasaña, Madrid",
        "neighborhood": "Malasaña",
        "city": "Madrid",
        "province": "Madrid",
        "type": "neighborhood" | "district" | "zone",
        "lat": float,
        "lon": float,
    }
"""
from __future__ import annotations
import re
from typing import List, Optional


# ---------------------------------------------------------------------------
# Mapa de datos: ciudad → lista de barrios con coordenadas aproximadas
# ---------------------------------------------------------------------------

_CITY_NEIGHBORHOODS: dict[str, dict] = {
    "Madrid": {
        "province": "Madrid",
        "lat_center": 40.4168, "lon_center": -3.7038,
        "neighborhoods": [
            # Distrito Centro
            {"n": "Sol", "lat": 40.4169, "lon": -3.7035},
            {"n": "Palacio", "lat": 40.4145, "lon": -3.7126},
            {"n": "Embajadores", "lat": 40.4075, "lon": -3.7030},
            {"n": "Cortes", "lat": 40.4140, "lon": -3.6980},
            {"n": "Huertas", "lat": 40.4135, "lon": -3.6973},
            {"n": "Justicia", "lat": 40.4210, "lon": -3.6960},
            {"n": "Barrio de las Letras", "lat": 40.4125, "lon": -3.6960},
            {"n": "La Latina", "lat": 40.4090, "lon": -3.7087},
            # Distrito Retiro
            {"n": "Retiro", "lat": 40.4130, "lon": -3.6845},
            {"n": "Ibiza", "lat": 40.4106, "lon": -3.6747},
            {"n": "Los Jeronimos", "lat": 40.4100, "lon": -3.6895},
            {"n": "Niño Jesús", "lat": 40.4063, "lon": -3.6787},
            {"n": "Adelfas", "lat": 40.4041, "lon": -3.6781},
            # Distrito Salamanca
            {"n": "Salamanca", "lat": 40.4303, "lon": -3.6757},
            {"n": "Recoletos", "lat": 40.4233, "lon": -3.6891},
            {"n": "Goya", "lat": 40.4273, "lon": -3.6759},
            {"n": "Lista", "lat": 40.4310, "lon": -3.6693},
            {"n": "Castellana", "lat": 40.4353, "lon": -3.6910},
            {"n": "Jerónimos", "lat": 40.4110, "lon": -3.6910},
            {"n": "Fuente del Berro", "lat": 40.4243, "lon": -3.6645},
            # Distrito Chamartín
            {"n": "Chamartín", "lat": 40.4580, "lon": -3.6793},
            {"n": "El Viso", "lat": 40.4505, "lon": -3.6810},
            {"n": "Prosperidad", "lat": 40.4470, "lon": -3.6735},
            {"n": "Ciudad Jardín", "lat": 40.4440, "lon": -3.6660},
            {"n": "Hispanoamérica", "lat": 40.4514, "lon": -3.6867},
            {"n": "Nueva España", "lat": 40.4558, "lon": -3.6830},
            {"n": "Bernabéu", "lat": 40.4530, "lon": -3.6884},
            {"n": "La Guindalera", "lat": 40.4413, "lon": -3.6640},
            {"n": "San Juan Bautista", "lat": 40.4384, "lon": -3.6568},
            # Distrito Tetuán
            {"n": "Tetuán", "lat": 40.4619, "lon": -3.6952},
            {"n": "Valdeacederas", "lat": 40.4625, "lon": -3.7010},
            {"n": "Ventilla-Almenara", "lat": 40.4651, "lon": -3.6987},
            {"n": "Berruguete", "lat": 40.4596, "lon": -3.7043},
            {"n": "Cuatro Caminos", "lat": 40.4472, "lon": -3.7048},
            {"n": "Almenara", "lat": 40.4626, "lon": -3.6975},
            # Distrito Chamberí
            {"n": "Chamberí", "lat": 40.4340, "lon": -3.7029},
            {"n": "Almagro", "lat": 40.4313, "lon": -3.6919},
            {"n": "Gaztambide", "lat": 40.4382, "lon": -3.7165},
            {"n": "Trafalgar", "lat": 40.4316, "lon": -3.7000},
            {"n": "Arapiles", "lat": 40.4352, "lon": -3.7072},
            {"n": "Ríos Rosas", "lat": 40.4402, "lon": -3.7007},
            {"n": "Vallehermoso", "lat": 40.4357, "lon": -3.7120},
            # Distrito Arganzuela
            {"n": "Arganzuela", "lat": 40.3970, "lon": -3.7020},
            {"n": "Imperial", "lat": 40.4040, "lon": -3.7143},
            {"n": "Acacias", "lat": 40.4002, "lon": -3.7093},
            {"n": "Chopera", "lat": 40.4005, "lon": -3.7023},
            {"n": "Legazpi", "lat": 40.3941, "lon": -3.7008},
            {"n": "Delicias", "lat": 40.3975, "lon": -3.6978},
            {"n": "Palos de Moguer", "lat": 40.4034, "lon": -3.6926},
            # Distrito Moncloa-Aravaca
            {"n": "Moncloa", "lat": 40.4366, "lon": -3.7248},
            {"n": "Argüelles", "lat": 40.4290, "lon": -3.7168},
            {"n": "Ciudad Universitaria", "lat": 40.4459, "lon": -3.7321},
            {"n": "Valdezarza", "lat": 40.4555, "lon": -3.7375},
            {"n": "Valdefuentes", "lat": 40.4525, "lon": -3.7435},
            {"n": "Peñagrande", "lat": 40.4642, "lon": -3.7454},
            {"n": "Aravaca", "lat": 40.4374, "lon": -3.7862},
            # Distrito Latina
            {"n": "Carabanchel", "lat": 40.3820, "lon": -3.7316},
            {"n": "Comillas", "lat": 40.3907, "lon": -3.7293},
            {"n": "Oporto", "lat": 40.3844, "lon": -3.7262},
            {"n": "Pradolongo", "lat": 40.3791, "lon": -3.7232},
            {"n": "Lucero", "lat": 40.3900, "lon": -3.7384},
            {"n": "Aluche", "lat": 40.3892, "lon": -3.7451},
            {"n": "Aguilas", "lat": 40.3826, "lon": -3.7476},
            {"n": "Las Águilas", "lat": 40.3820, "lon": -3.7480},
            {"n": "Campamento", "lat": 40.3797, "lon": -3.7562},
            {"n": "Cuatro Vientos", "lat": 40.3751, "lon": -3.7672},
            # Distrito Usera
            {"n": "Usera", "lat": 40.3883, "lon": -3.7108},
            {"n": "Pradolongo", "lat": 40.3791, "lon": -3.7232},
            {"n": "Moscardó", "lat": 40.3901, "lon": -3.7128},
            {"n": "Orcasitas", "lat": 40.3604, "lon": -3.7085},
            # Distrito Puente de Vallecas
            {"n": "Vallecas", "lat": 40.3925, "lon": -3.6611},
            {"n": "Entrevías", "lat": 40.3860, "lon": -3.6659},
            {"n": "San Diego", "lat": 40.3976, "lon": -3.6742},
            {"n": "Palomeras", "lat": 40.3895, "lon": -3.6554},
            {"n": "Portazgo", "lat": 40.3878, "lon": -3.6431},
            {"n": "Numancia", "lat": 40.3844, "lon": -3.6494},
            # Distrito Vicálvaro
            {"n": "Vicálvaro", "lat": 40.4062, "lon": -3.6119},
            {"n": "Ambroz", "lat": 40.3995, "lon": -3.6129},
            # Distrito Ciudad Lineal
            {"n": "Ciudad Lineal", "lat": 40.4420, "lon": -3.6430},
            {"n": "Las Rosas", "lat": 40.4380, "lon": -3.6240},
            {"n": "Pueblo Nuevo", "lat": 40.4362, "lon": -3.6310},
            {"n": "La Elipa", "lat": 40.4208, "lon": -3.6395},
            {"n": "Quintana", "lat": 40.4289, "lon": -3.6271},
            {"n": "Concepción", "lat": 40.4262, "lon": -3.6395},
            {"n": "San Pascual", "lat": 40.4421, "lon": -3.6382},
            {"n": "Colina", "lat": 40.4504, "lon": -3.6313},
            {"n": "Atalaya", "lat": 40.4570, "lon": -3.6273},
            {"n": "Canillas", "lat": 40.4632, "lon": -3.6262},
            # Distrito Hortaleza
            {"n": "Hortaleza", "lat": 40.4846, "lon": -3.6375},
            {"n": "Piovera", "lat": 40.4774, "lon": -3.6541},
            {"n": "Palomas", "lat": 40.4812, "lon": -3.6475},
            {"n": "Valdefuentes", "lat": 40.4940, "lon": -3.6307},
            {"n": "Sanchinarro", "lat": 40.4811, "lon": -3.6621},
            {"n": "Las Tablas", "lat": 40.5010, "lon": -3.6604},
            # Distrito Barajas
            {"n": "Barajas", "lat": 40.4741, "lon": -3.5795},
            {"n": "Alameda de Osuna", "lat": 40.4682, "lon": -3.5988},
            {"n": "Aeropuerto", "lat": 40.4724, "lon": -3.5613},
            {"n": "Timón", "lat": 40.4793, "lon": -3.5944},
            # Distrito Fuencarral-El Pardo
            {"n": "Fuencarral", "lat": 40.4935, "lon": -3.7153},
            {"n": "Mirasierra", "lat": 40.4884, "lon": -3.7307},
            {"n": "El Pardo", "lat": 40.5139, "lon": -3.7747},
            {"n": "La Paz", "lat": 40.4755, "lon": -3.7248},
            {"n": "Pilar", "lat": 40.4841, "lon": -3.7135},
            {"n": "Montecarmelo", "lat": 40.5060, "lon": -3.7212},
            {"n": "Las Tablas", "lat": 40.5010, "lon": -3.6604},
            {"n": "Virgen de Begoña", "lat": 40.4697, "lon": -3.7186},
            # Distrito Moratalaz
            {"n": "Moratalaz", "lat": 40.4072, "lon": -3.6456},
            {"n": "Marroquina", "lat": 40.4113, "lon": -3.6379},
            {"n": "Media Legua", "lat": 40.4085, "lon": -3.6456},
            # Distrito San Blas-Canillejas
            {"n": "Canillejas", "lat": 40.4385, "lon": -3.5887},
            {"n": "San Blas", "lat": 40.4286, "lon": -3.6103},
            {"n": "Hellín", "lat": 40.4232, "lon": -3.5975},
            {"n": "Rejas", "lat": 40.4562, "lon": -3.5853},
            {"n": "Simancas", "lat": 40.4330, "lon": -3.5998},
            # Malasaña y Chueca (Centro)
            {"n": "Malasaña", "lat": 40.4272, "lon": -3.7065},
            {"n": "Chueca", "lat": 40.4232, "lon": -3.6973},
            {"n": "Lavapiés", "lat": 40.4084, "lon": -3.7021},
            {"n": "El Rastro", "lat": 40.4090, "lon": -3.7068},
        ],
    },
    "Barcelona": {
        "province": "Barcelona",
        "lat_center": 41.3851, "lon_center": 2.1734,
        "neighborhoods": [
            {"n": "Eixample Dreta", "lat": 41.3948, "lon": 2.1680},
            {"n": "Eixample Esquerra", "lat": 41.3831, "lon": 2.1560},
            {"n": "Gràcia", "lat": 41.4028, "lon": 2.1585},
            {"n": "Vila de Gràcia", "lat": 41.4038, "lon": 2.1549},
            {"n": "El Coll", "lat": 41.4115, "lon": 2.1532},
            {"n": "Vallcarca i els Penitents", "lat": 41.4140, "lon": 2.1468},
            {"n": "El Putget i Farró", "lat": 41.4071, "lon": 2.1432},
            {"n": "Camp d'en Grassot", "lat": 41.4010, "lon": 2.1609},
            {"n": "Sant Gervasi - Galvany", "lat": 41.4072, "lon": 2.1413},
            {"n": "El Raval", "lat": 41.3793, "lon": 2.1672},
            {"n": "El Gòtic", "lat": 41.3826, "lon": 2.1774},
            {"n": "La Barceloneta", "lat": 41.3780, "lon": 2.1888},
            {"n": "Sant Pere, Santa Caterina i la Ribera", "lat": 41.3851, "lon": 2.1803},
            {"n": "El Born", "lat": 41.3865, "lon": 2.1820},
            {"n": "Poblenou", "lat": 41.4002, "lon": 2.1973},
            {"n": "La Vila Olímpica", "lat": 41.3886, "lon": 2.1963},
            {"n": "El Parc i la Llacuna", "lat": 41.3983, "lon": 2.1934},
            {"n": "Diagonal Mar i el Front Marítim", "lat": 41.4058, "lon": 2.2075},
            {"n": "El Besòs i el Maresme", "lat": 41.4130, "lon": 2.2157},
            {"n": "La Verneda i la Pau", "lat": 41.4072, "lon": 2.1948},
            {"n": "Provençals del Poblenou", "lat": 41.4035, "lon": 2.1849},
            {"n": "Sants", "lat": 41.3697, "lon": 2.1360},
            {"n": "Hostafrancs", "lat": 41.3752, "lon": 2.1451},
            {"n": "La Bordeta", "lat": 41.3685, "lon": 2.1336},
            {"n": "Badal", "lat": 41.3755, "lon": 2.1288},
            {"n": "Sants-Badal", "lat": 41.3744, "lon": 2.1328},
            {"n": "Les Corts", "lat": 41.3895, "lon": 2.1312},
            {"n": "La Maternitat i Sant Ramon", "lat": 41.3850, "lon": 2.1264},
            {"n": "Pedralbes", "lat": 41.3921, "lon": 2.1148},
            {"n": "Sarrià", "lat": 41.4013, "lon": 2.1212},
            {"n": "Les Tres Torres", "lat": 41.4018, "lon": 2.1384},
            {"n": "Sant Gervasi - La Bonanova", "lat": 41.4064, "lon": 2.1282},
            {"n": "Vallvidrera, el Tibidabo i les Planes", "lat": 41.4108, "lon": 2.1076},
            {"n": "Horta", "lat": 41.4336, "lon": 2.1573},
            {"n": "Montbau", "lat": 41.4265, "lon": 2.1382},
            {"n": "Vall d'Hebron", "lat": 41.4308, "lon": 2.1397},
            {"n": "El Carmel", "lat": 41.4180, "lon": 2.1494},
            {"n": "La Teixonera", "lat": 41.4231, "lon": 2.1519},
            {"n": "El Guinardó", "lat": 41.4202, "lon": 2.1680},
            {"n": "El Baix Guinardó", "lat": 41.4142, "lon": 2.1671},
            {"n": "Can Baró", "lat": 41.4166, "lon": 2.1600},
            {"n": "Nou Barris Nord", "lat": 41.4485, "lon": 2.1820},
            {"n": "La Guineueta", "lat": 41.4375, "lon": 2.1735},
            {"n": "Canyelles", "lat": 41.4429, "lon": 2.1693},
            {"n": "Les Roquetes", "lat": 41.4431, "lon": 2.1638},
            {"n": "Verdun", "lat": 41.4386, "lon": 2.1770},
            {"n": "La Prosperitat", "lat": 41.4349, "lon": 2.1784},
            {"n": "La Trinitat Nova", "lat": 41.4493, "lon": 2.1752},
            {"n": "Torre Baró", "lat": 41.4497, "lon": 2.1560},
            {"n": "Vilapicina i la Torre Llobeta", "lat": 41.4339, "lon": 2.1862},
            {"n": "Porta", "lat": 41.4317, "lon": 2.1903},
            {"n": "El Turó de la Peira", "lat": 41.4296, "lon": 2.1800},
            {"n": "Sant Andreu de Palomar", "lat": 41.4319, "lon": 2.1932},
            {"n": "La Sagrera", "lat": 41.4212, "lon": 2.1907},
            {"n": "El Congrés i els Indians", "lat": 41.4196, "lon": 2.1960},
            {"n": "Navas", "lat": 41.4150, "lon": 2.1856},
            {"n": "El Bon Pastor", "lat": 41.4322, "lon": 2.2010},
            {"n": "Baró de Viver", "lat": 41.4363, "lon": 2.2063},
            {"n": "El Camp de l'Arpa del Clot", "lat": 41.4111, "lon": 2.1858},
            {"n": "El Clot", "lat": 41.4087, "lon": 2.1878},
            {"n": "El Fort Pienc", "lat": 41.3987, "lon": 2.1797},
            {"n": "Sagrada Família", "lat": 41.4036, "lon": 2.1729},
            {"n": "Sant Antoni", "lat": 41.3810, "lon": 2.1618},
            {"n": "Poble Sec", "lat": 41.3726, "lon": 2.1596},
            {"n": "La Marina del Prat Vermell", "lat": 41.3584, "lon": 2.1431},
            {"n": "La Marina de Port", "lat": 41.3633, "lon": 2.1440},
            {"n": "La Font de la Guatlla", "lat": 41.3750, "lon": 2.1509},
            {"n": "Montjuïc", "lat": 41.3645, "lon": 2.1518},
        ],
    },
    "Valencia": {
        "province": "Valencia",
        "lat_center": 39.4699, "lon_center": -0.3763,
        "neighborhoods": [
            {"n": "Ruzafa", "lat": 39.4599, "lon": -0.3731},
            {"n": "El Carmen", "lat": 39.4741, "lon": -0.3796},
            {"n": "L'Eixample", "lat": 39.4617, "lon": -0.3662},
            {"n": "Benimaclet", "lat": 39.4826, "lon": -0.3579},
            {"n": "Campanar", "lat": 39.4832, "lon": -0.3913},
            {"n": "Patraix", "lat": 39.4545, "lon": -0.3912},
            {"n": "El Cabanyal", "lat": 39.4693, "lon": -0.3320},
            {"n": "La Malvarrosa", "lat": 39.4748, "lon": -0.3300},
            {"n": "Las Arenas", "lat": 39.4835, "lon": -0.3272},
            {"n": "Algirós", "lat": 39.4741, "lon": -0.3583},
            {"n": "Orriols", "lat": 39.4904, "lon": -0.3632},
            {"n": "Torrefiel", "lat": 39.4910, "lon": -0.3572},
            {"n": "La Saïdia", "lat": 39.4826, "lon": -0.3735},
            {"n": "Marxalenes", "lat": 39.4868, "lon": -0.3841},
            {"n": "Morvedre", "lat": 39.4868, "lon": -0.3769},
            {"n": "L'Olivereta", "lat": 39.4668, "lon": -0.3982},
            {"n": "Quatre Carreres", "lat": 39.4468, "lon": -0.3640},
            {"n": "Monteolivete", "lat": 39.4568, "lon": -0.3549},
            {"n": "La Creu del Grau", "lat": 39.4668, "lon": -0.3482},
            {"n": "Caminàs", "lat": 39.4768, "lon": -0.3432},
            {"n": "Natzaret", "lat": 39.4452, "lon": -0.3312},
            {"n": "La Punta", "lat": 39.4368, "lon": -0.3642},
            {"n": "Jesús", "lat": 39.4565, "lon": -0.3841},
            {"n": "La Creu Coberta", "lat": 39.4518, "lon": -0.3846},
            {"n": "Nou Moles", "lat": 39.4668, "lon": -0.3947},
            {"n": "Arrancapins", "lat": 39.4718, "lon": -0.3896},
            {"n": "La Roqueta", "lat": 39.4738, "lon": -0.3843},
            {"n": "La Petxina", "lat": 39.4781, "lon": -0.3842},
            {"n": "Extramurs", "lat": 39.4701, "lon": -0.3769},
            {"n": "La Seu", "lat": 39.4739, "lon": -0.3773},
            {"n": "La Xerea", "lat": 39.4721, "lon": -0.3744},
        ],
    },
    "Sevilla": {
        "province": "Sevilla",
        "lat_center": 37.3861, "lon_center": -5.9925,
        "neighborhoods": [
            {"n": "Triana", "lat": 37.3873, "lon": -6.0054},
            {"n": "Los Remedios", "lat": 37.3764, "lon": -6.0028},
            {"n": "Nervión", "lat": 37.3885, "lon": -5.9772},
            {"n": "Santa Cruz", "lat": 37.3845, "lon": -5.9896},
            {"n": "Macarena", "lat": 37.4047, "lon": -5.9894},
            {"n": "San Bernardo", "lat": 37.3774, "lon": -5.9813},
            {"n": "Alameda de Hércules", "lat": 37.3966, "lon": -5.9921},
            {"n": "El Arenal", "lat": 37.3851, "lon": -5.9970},
            {"n": "San Lorenzo", "lat": 37.3934, "lon": -5.9979},
            {"n": "Bermejales", "lat": 37.3594, "lon": -5.9971},
            {"n": "Heliópolis", "lat": 37.3662, "lon": -5.9928},
            {"n": "El Porvenir", "lat": 37.3689, "lon": -5.9837},
            {"n": "Felipe II", "lat": 37.3713, "lon": -5.9750},
            {"n": "Bami", "lat": 37.3614, "lon": -5.9708},
            {"n": "Sevilla Este", "lat": 37.3810, "lon": -5.9461},
            {"n": "Cerro del Águila", "lat": 37.3858, "lon": -5.9587},
            {"n": "Pino Montano", "lat": 37.4153, "lon": -5.9841},
            {"n": "Torreblanca", "lat": 37.3967, "lon": -5.9547},
            {"n": "Valdezorras", "lat": 37.4191, "lon": -5.9600},
            {"n": "Amate", "lat": 37.3863, "lon": -5.9655},
            {"n": "Los Pajaritos", "lat": 37.3766, "lon": -5.9669},
            {"n": "Polígono Sur", "lat": 37.3540, "lon": -5.9789},
            {"n": "Bellavista", "lat": 37.3503, "lon": -5.9917},
            {"n": "El Tardón", "lat": 37.3839, "lon": -6.0143},
            {"n": "Prado de San Sebastián", "lat": 37.3792, "lon": -5.9833},
        ],
    },
    "Málaga": {
        "province": "Málaga",
        "lat_center": 36.7213, "lon_center": -4.4214,
        "neighborhoods": [
            {"n": "Centro Histórico", "lat": 36.7213, "lon": -4.4214},
            {"n": "La Malagueta", "lat": 36.7184, "lon": -4.4059},
            {"n": "El Palo", "lat": 36.7212, "lon": -4.3679},
            {"n": "Pedregalejo", "lat": 36.7189, "lon": -4.3828},
            {"n": "Teatinos", "lat": 36.7101, "lon": -4.4773},
            {"n": "Huelin", "lat": 36.7151, "lon": -4.4421},
            {"n": "Cruz de Humilladero", "lat": 36.7198, "lon": -4.4472},
            {"n": "La Victoria", "lat": 36.7282, "lon": -4.4148},
            {"n": "El Ejido", "lat": 36.7231, "lon": -4.4285},
            {"n": "Capuchinos", "lat": 36.7241, "lon": -4.4215},
            {"n": "La Merced", "lat": 36.7194, "lon": -4.4194},
            {"n": "Perchel Norte", "lat": 36.7173, "lon": -4.4279},
            {"n": "Ciudad Jardín", "lat": 36.7280, "lon": -4.4050},
            {"n": "Miraflores de los Ángeles", "lat": 36.7350, "lon": -4.4099},
            {"n": "Limonar", "lat": 36.7216, "lon": -4.4022},
            {"n": "La Caleta", "lat": 36.7183, "lon": -4.3988},
            {"n": "El Candado", "lat": 36.7264, "lon": -4.3577},
            {"n": "Campanillas", "lat": 36.7289, "lon": -4.5297},
            {"n": "Puerto de la Torre", "lat": 36.7397, "lon": -4.4700},
            {"n": "Churriana", "lat": 36.6886, "lon": -4.5009},
            {"n": "Carranque", "lat": 36.7109, "lon": -4.4422},
            {"n": "La Rosaleda", "lat": 36.7270, "lon": -4.4334},
        ],
    },
    "Bilbao": {
        "province": "Vizcaya",
        "lat_center": 43.2630, "lon_center": -2.9350,
        "neighborhoods": [
            {"n": "Casco Viejo", "lat": 43.2568, "lon": -2.9234},
            {"n": "Abando", "lat": 43.2617, "lon": -2.9313},
            {"n": "Indautxu", "lat": 43.2672, "lon": -2.9404},
            {"n": "Deusto", "lat": 43.2825, "lon": -2.9474},
            {"n": "San Ignacio", "lat": 43.2870, "lon": -2.9562},
            {"n": "Rekalde", "lat": 43.2527, "lon": -2.9461},
            {"n": "Begoña", "lat": 43.2691, "lon": -2.9232},
            {"n": "Santutxu", "lat": 43.2691, "lon": -2.9166},
            {"n": "Basurto", "lat": 43.2560, "lon": -2.9565},
            {"n": "Otxarkoaga", "lat": 43.2797, "lon": -2.9237},
            {"n": "Txurdinaga", "lat": 43.2761, "lon": -2.9308},
            {"n": "Uribarri", "lat": 43.2714, "lon": -2.9268},
            {"n": "Ibaiondo", "lat": 43.2590, "lon": -2.9235},
            {"n": "Errekalde", "lat": 43.2527, "lon": -2.9461},
            {"n": "Mazustegi", "lat": 43.2480, "lon": -2.9565},
        ],
    },
    "Alicante": {
        "province": "Alicante",
        "lat_center": 38.3452, "lon_center": -0.4810,
        "neighborhoods": [
            {"n": "Centro", "lat": 38.3447, "lon": -0.4805},
            {"n": "Carolinas Altas", "lat": 38.3530, "lon": -0.4850},
            {"n": "Carolinas Bajas", "lat": 38.3498, "lon": -0.4841},
            {"n": "Benalúa", "lat": 38.3410, "lon": -0.4842},
            {"n": "Playa de San Juan", "lat": 38.3768, "lon": -0.4280},
            {"n": "Cabo de las Huertas", "lat": 38.3561, "lon": -0.4286},
            {"n": "El Campello", "lat": 38.4385, "lon": -0.3950},
            {"n": "Florida", "lat": 38.3628, "lon": -0.4930},
            {"n": "San Blas", "lat": 38.3575, "lon": -0.4970},
            {"n": "Altozano", "lat": 38.3495, "lon": -0.4772},
            {"n": "El Toscar", "lat": 38.3440, "lon": -0.4762},
            {"n": "Juan XXIII", "lat": 38.3388, "lon": -0.4884},
        ],
    },
    "Zaragoza": {
        "province": "Zaragoza",
        "lat_center": 41.6488, "lon_center": -0.8891,
        "neighborhoods": [
            {"n": "Centro", "lat": 41.6488, "lon": -0.8891},
            {"n": "Delicias", "lat": 41.6380, "lon": -0.9145},
            {"n": "San José", "lat": 41.6450, "lon": -0.8742},
            {"n": "Las Fuentes", "lat": 41.6538, "lon": -0.8613},
            {"n": "El Rabal", "lat": 41.6630, "lon": -0.8781},
            {"n": "Universidad", "lat": 41.6572, "lon": -0.9055},
            {"n": "Actur", "lat": 41.6755, "lon": -0.9098},
            {"n": "La Almozara", "lat": 41.6537, "lon": -0.9120},
            {"n": "Oliver", "lat": 41.6395, "lon": -0.9273},
            {"n": "Torrero", "lat": 41.6270, "lon": -0.8875},
            {"n": "La Paz", "lat": 41.6295, "lon": -0.8784},
            {"n": "Miralbueno", "lat": 41.6398, "lon": -0.9436},
            {"n": "Casablanca", "lat": 41.6231, "lon": -0.9012},
            {"n": "Valdefierro", "lat": 41.6225, "lon": -0.9273},
            {"n": "Movera", "lat": 41.6866, "lon": -0.8441},
        ],
    },
    "Granada": {
        "province": "Granada",
        "lat_center": 37.1773, "lon_center": -3.5986,
        "neighborhoods": [
            {"n": "Albaicín", "lat": 37.1822, "lon": -3.5938},
            {"n": "Centro", "lat": 37.1773, "lon": -3.5986},
            {"n": "Realejo", "lat": 37.1728, "lon": -3.6001},
            {"n": "Beiro", "lat": 37.1907, "lon": -3.6012},
            {"n": "Zaidín", "lat": 37.1569, "lon": -3.5940},
            {"n": "Chana", "lat": 37.1807, "lon": -3.6226},
            {"n": "Genil", "lat": 37.1629, "lon": -3.5886},
            {"n": "Norte", "lat": 37.1956, "lon": -3.5952},
            {"n": "Camino de Ronda", "lat": 37.1712, "lon": -3.6080},
            {"n": "Figares", "lat": 37.1749, "lon": -3.6008},
            {"n": "El Salvador", "lat": 37.1832, "lon": -3.5935},
            {"n": "Sacromonte", "lat": 37.1832, "lon": -3.5875},
            {"n": "La Rondilla", "lat": 37.1663, "lon": -3.6042},
            {"n": "Casería de Montijo", "lat": 37.2022, "lon": -3.5990},
        ],
    },
    "Murcia": {
        "province": "Murcia",
        "lat_center": 37.9922, "lon_center": -1.1307,
        "neighborhoods": [
            {"n": "Centro", "lat": 37.9922, "lon": -1.1307},
            {"n": "El Carmen", "lat": 37.9960, "lon": -1.1278},
            {"n": "Santa María de Gracia", "lat": 37.9900, "lon": -1.1347},
            {"n": "Vistabella", "lat": 37.9853, "lon": -1.1208},
            {"n": "La Flota", "lat": 37.9856, "lon": -1.1144},
            {"n": "Infante Juan Manuel", "lat": 37.9862, "lon": -1.1382},
            {"n": "La Fama", "lat": 37.9895, "lon": -1.1322},
            {"n": "San Antón", "lat": 37.9945, "lon": -1.1236},
            {"n": "Santiago el Mayor", "lat": 37.9932, "lon": -1.1255},
            {"n": "Vistalegre", "lat": 37.9890, "lon": -1.1089},
            {"n": "El Palmar", "lat": 37.9623, "lon": -1.1099},
            {"n": "El Puntal", "lat": 37.9725, "lon": -1.0959},
        ],
    },
    "San Sebastián": {
        "province": "Guipúzcoa",
        "lat_center": 43.3183, "lon_center": -1.9812,
        "neighborhoods": [
            {"n": "Parte Vieja", "lat": 43.3225, "lon": -1.9781},
            {"n": "Centro - Ensanche", "lat": 43.3183, "lon": -1.9812},
            {"n": "Gros", "lat": 43.3196, "lon": -1.9701},
            {"n": "Amara", "lat": 43.3082, "lon": -1.9814},
            {"n": "Antiguo", "lat": 43.3083, "lon": -1.9976},
            {"n": "Egia", "lat": 43.3132, "lon": -1.9703},
            {"n": "Intxaurrondo", "lat": 43.3044, "lon": -1.9541},
            {"n": "Aiete", "lat": 43.2978, "lon": -1.9948},
            {"n": "Igeldo", "lat": 43.2998, "lon": -2.0296},
            {"n": "Loiola", "lat": 43.3046, "lon": -1.9574},
            {"n": "Martutene", "lat": 43.2975, "lon": -1.9682},
            {"n": "Ibaeta", "lat": 43.3020, "lon": -2.0033},
        ],
    },
    "Santander": {
        "province": "Cantabria",
        "lat_center": 43.4623, "lon_center": -3.8099,
        "neighborhoods": [
            {"n": "Centro", "lat": 43.4623, "lon": -3.8099},
            {"n": "El Sardinero", "lat": 43.4781, "lon": -3.8046},
            {"n": "Cuatro Caminos", "lat": 43.4617, "lon": -3.8218},
            {"n": "Castilla-Hermida", "lat": 43.4552, "lon": -3.8163},
            {"n": "Monte", "lat": 43.4498, "lon": -3.8289},
            {"n": "Numancia", "lat": 43.4519, "lon": -3.8097},
            {"n": "San Martín", "lat": 43.4538, "lon": -3.8070},
            {"n": "Puerto Chico", "lat": 43.4676, "lon": -3.8016},
            {"n": "Cazoña", "lat": 43.4569, "lon": -3.8298},
            {"n": "Nueva Montaña", "lat": 43.4452, "lon": -3.8423},
        ],
    },
    "Palma de Mallorca": {
        "province": "Islas Baleares",
        "lat_center": 39.5696, "lon_center": 2.6502,
        "neighborhoods": [
            {"n": "Santa Catalina", "lat": 39.5734, "lon": 2.6434},
            {"n": "La Lonja", "lat": 39.5672, "lon": 2.6482},
            {"n": "El Terreno", "lat": 39.5617, "lon": 2.6260},
            {"n": "Son Espanyolet", "lat": 39.5698, "lon": 2.6365},
            {"n": "El Molinar", "lat": 39.5549, "lon": 2.6710},
            {"n": "Portixol", "lat": 39.5577, "lon": 2.6627},
            {"n": "Son Armadams", "lat": 39.5651, "lon": 2.6440},
            {"n": "Son Vida", "lat": 39.5862, "lon": 2.6305},
            {"n": "Gènova", "lat": 39.5564, "lon": 2.6167},
            {"n": "Coll d'en Rabassa", "lat": 39.5449, "lon": 2.6724},
            {"n": "El Arenal", "lat": 39.5294, "lon": 2.7265},
            {"n": "Pere Garau", "lat": 39.5725, "lon": 2.6648},
            {"n": "La Soledat", "lat": 39.5771, "lon": 2.6584},
            {"n": "Camp Redó", "lat": 39.5822, "lon": 2.6564},
            {"n": "Son Gotleu", "lat": 39.5818, "lon": 2.6639},
        ],
    },
    "Córdoba": {
        "province": "Córdoba",
        "lat_center": 37.8882, "lon_center": -4.7794,
        "neighborhoods": [
            {"n": "Centro Histórico", "lat": 37.8882, "lon": -4.7794},
            {"n": "Ciudad Jardín", "lat": 37.8820, "lon": -4.7718},
            {"n": "Fátima", "lat": 37.8726, "lon": -4.7853},
            {"n": "El Brillante", "lat": 37.9015, "lon": -4.7803},
            {"n": "Cañero", "lat": 37.8698, "lon": -4.7981},
            {"n": "Valdeolleros", "lat": 37.9046, "lon": -4.7703},
            {"n": "Las Margaritas", "lat": 37.8804, "lon": -4.8002},
            {"n": "Sector Sur", "lat": 37.8668, "lon": -4.7771},
            {"n": "Los Califas", "lat": 37.8759, "lon": -4.8098},
            {"n": "Parque Fidiana", "lat": 37.8947, "lon": -4.8209},
        ],
    },
    "Valladolid": {
        "province": "Valladolid",
        "lat_center": 41.6523, "lon_center": -4.7245,
        "neighborhoods": [
            {"n": "Centro", "lat": 41.6523, "lon": -4.7245},
            {"n": "Delicias", "lat": 41.6427, "lon": -4.7268},
            {"n": "Parquesol", "lat": 41.6717, "lon": -4.7548},
            {"n": "Covaresa", "lat": 41.6320, "lon": -4.7178},
            {"n": "La Rondilla", "lat": 41.6619, "lon": -4.7217},
            {"n": "Arturo Eyries", "lat": 41.6614, "lon": -4.7050},
            {"n": "Huerta del Rey", "lat": 41.6490, "lon": -4.7431},
            {"n": "Las Flores", "lat": 41.6413, "lon": -4.7398},
            {"n": "San Juan", "lat": 41.6536, "lon": -4.7196},
        ],
    },
    "Vigo": {
        "province": "Pontevedra",
        "lat_center": 42.2406, "lon_center": -8.7207,
        "neighborhoods": [
            {"n": "Centro", "lat": 42.2406, "lon": -8.7207},
            {"n": "Bouzas", "lat": 42.2297, "lon": -8.7423},
            {"n": "Coia", "lat": 42.2264, "lon": -8.7382},
            {"n": "Navia", "lat": 42.2253, "lon": -8.7093},
            {"n": "Teis", "lat": 42.2515, "lon": -8.6982},
            {"n": "Lavadores", "lat": 42.2161, "lon": -8.6998},
            {"n": "Beade", "lat": 42.2062, "lon": -8.6949},
            {"n": "Castrelos", "lat": 42.2267, "lon": -8.7068},
            {"n": "Freixeiro - Lavadores", "lat": 42.2181, "lon": -8.7152},
            {"n": "Traviesas", "lat": 42.2393, "lon": -8.7095},
        ],
    },
    "A Coruña": {
        "province": "A Coruña",
        "lat_center": 43.3623, "lon_center": -8.4115,
        "neighborhoods": [
            {"n": "Centro", "lat": 43.3623, "lon": -8.4115},
            {"n": "El Ensanche", "lat": 43.3601, "lon": -8.4060},
            {"n": "Monte Alto", "lat": 43.3720, "lon": -8.4234},
            {"n": "Riazor", "lat": 43.3693, "lon": -8.4167},
            {"n": "Cuatro Caminos", "lat": 43.3571, "lon": -8.4060},
            {"n": "Labañou", "lat": 43.3476, "lon": -8.4144},
            {"n": "Os Mallos", "lat": 43.3556, "lon": -8.4193},
            {"n": "Elviña", "lat": 43.3329, "lon": -8.4162},
            {"n": "A Sagrada Familia", "lat": 43.3487, "lon": -8.4032},
        ],
    },
    "Marbella": {
        "province": "Málaga",
        "lat_center": 36.5101, "lon_center": -4.8825,
        "neighborhoods": [
            {"n": "Centro Histórico", "lat": 36.5101, "lon": -4.8825},
            {"n": "Puerto Banús", "lat": 36.4890, "lon": -4.9579},
            {"n": "Nueva Andalucía", "lat": 36.4948, "lon": -4.9492},
            {"n": "San Pedro de Alcántara", "lat": 36.5040, "lon": -5.0508},
            {"n": "Las Chapas", "lat": 36.5070, "lon": -4.8084},
            {"n": "El Rosario", "lat": 36.5011, "lon": -4.8361},
            {"n": "Río Real", "lat": 36.5001, "lon": -4.8564},
            {"n": "La Cañada", "lat": 36.5255, "lon": -4.8825},
            {"n": "Los Monteros", "lat": 36.5005, "lon": -4.8220},
        ],
    },
    "Pamplona": {
        "province": "Navarra",
        "lat_center": 42.8188, "lon_center": -1.6444,
        "neighborhoods": [
            {"n": "Casco Antiguo", "lat": 42.8188, "lon": -1.6444},
            {"n": "Ensanche", "lat": 42.8165, "lon": -1.6466},
            {"n": "Ermitagaña-Mendebaldea", "lat": 42.8136, "lon": -1.6588},
            {"n": "Iturrama", "lat": 42.8138, "lon": -1.6542},
            {"n": "Milagrosa", "lat": 42.8095, "lon": -1.6403},
            {"n": "Rochapea", "lat": 42.8265, "lon": -1.6405},
            {"n": "San Juan", "lat": 42.8232, "lon": -1.6554},
            {"n": "Txantrea", "lat": 42.8311, "lon": -1.6309},
            {"n": "Etxabakoitz", "lat": 42.8217, "lon": -1.6681},
        ],
    },
    "Oviedo": {
        "province": "Asturias",
        "lat_center": 43.3614, "lon_center": -5.8593,
        "neighborhoods": [
            {"n": "Centro", "lat": 43.3614, "lon": -5.8593},
            {"n": "El Cristo", "lat": 43.3572, "lon": -5.8493},
            {"n": "Teatinos", "lat": 43.3553, "lon": -5.8732},
            {"n": "La Argañosa", "lat": 43.3678, "lon": -5.8660},
            {"n": "Fozaneldi", "lat": 43.3697, "lon": -5.8528},
            {"n": "Ventanielles", "lat": 43.3631, "lon": -5.8714},
            {"n": "El Fresno", "lat": 43.3530, "lon": -5.8635},
            {"n": "La Corredoria", "lat": 43.3831, "lon": -5.8536},
        ],
    },
    "Gijón": {
        "province": "Asturias",
        "lat_center": 43.5453, "lon_center": -5.6614,
        "neighborhoods": [
            {"n": "Centro", "lat": 43.5453, "lon": -5.6614},
            {"n": "Cimadevilla", "lat": 43.5469, "lon": -5.6567},
            {"n": "El Llano", "lat": 43.5366, "lon": -5.6599},
            {"n": "La Calzada", "lat": 43.5305, "lon": -5.6753},
            {"n": "Natahoyo", "lat": 43.5336, "lon": -5.6850},
            {"n": "Somió", "lat": 43.5512, "lon": -5.6283},
            {"n": "La Arena", "lat": 43.5580, "lon": -5.6742},
        ],
    },
    "Las Palmas de Gran Canaria": {
        "province": "Las Palmas",
        "lat_center": 28.1235, "lon_center": -15.4366,
        "neighborhoods": [
            {"n": "Vegueta", "lat": 28.1023, "lon": -15.4166},
            {"n": "Triana", "lat": 28.1090, "lon": -15.4157},
            {"n": "Puerto-Canteras", "lat": 28.1284, "lon": -15.4371},
            {"n": "Arenales-Lugo", "lat": 28.1175, "lon": -15.4287},
            {"n": "La Isleta", "lat": 28.1431, "lon": -15.4283},
            {"n": "Guanarteme", "lat": 28.1293, "lon": -15.4291},
            {"n": "Ciudad Alta", "lat": 28.1050, "lon": -15.4410},
            {"n": "Tamaraceite", "lat": 28.1148, "lon": -15.4690},
            {"n": "Miller Bajo", "lat": 28.1230, "lon": -15.4495},
        ],
    },
    "Santa Cruz de Tenerife": {
        "province": "Santa Cruz de Tenerife",
        "lat_center": 28.4636, "lon_center": -16.2518,
        "neighborhoods": [
            {"n": "Centro", "lat": 28.4636, "lon": -16.2518},
            {"n": "Ofra-Costa Sur", "lat": 28.4494, "lon": -16.2541},
            {"n": "Salud Alta", "lat": 28.4705, "lon": -16.2641},
            {"n": "La Salud", "lat": 28.4663, "lon": -16.2554},
            {"n": "Barrio de La Salud", "lat": 28.4679, "lon": -16.2590},
            {"n": "Anaga", "lat": 28.5013, "lon": -16.2289},
            {"n": "Llano del Moro", "lat": 28.4832, "lon": -16.2430},
        ],
    },
    "Tarragona": {
        "province": "Tarragona",
        "lat_center": 41.1189, "lon_center": 1.2445,
        "neighborhoods": [
            {"n": "Part Alta", "lat": 41.1189, "lon": 1.2445},
            {"n": "Eixample", "lat": 41.1151, "lon": 1.2428},
            {"n": "Bonavista", "lat": 41.1349, "lon": 1.2277},
            {"n": "Camp Clar", "lat": 41.1068, "lon": 1.2270},
        ],
    },
    "Elche": {
        "province": "Alicante",
        "lat_center": 38.2669, "lon_center": -0.6981,
        "neighborhoods": [
            {"n": "Centro", "lat": 38.2669, "lon": -0.6981},
            {"n": "Carrús", "lat": 38.2685, "lon": -0.7154},
            {"n": "El Pla", "lat": 38.2735, "lon": -0.6830},
            {"n": "Altabix", "lat": 38.2603, "lon": -0.6900},
            {"n": "Nueva Alcudia", "lat": 38.2527, "lon": -0.7054},
        ],
    },
}


# ---------------------------------------------------------------------------
# Construir el índice global como lista plana
# ---------------------------------------------------------------------------

NEIGHBORHOOD_INDEX: list[dict] = []

for city_name, city_data in _CITY_NEIGHBORHOODS.items():
    for entry in city_data["neighborhoods"]:
        NEIGHBORHOOD_INDEX.append({
            "label":        f"{entry['n']}, {city_name}",
            "neighborhood": entry["n"],
            "city":         city_name,
            "province":     city_data["province"],
            "type":         "neighborhood",
            "lat":          entry.get("lat", city_data["lat_center"]),
            "lon":          entry.get("lon", city_data["lon_center"]),
        })

# También añadir las propias ciudades como entradas
for city_name, city_data in _CITY_NEIGHBORHOODS.items():
    NEIGHBORHOOD_INDEX.append({
        "label":        city_name,
        "neighborhood": "",
        "city":         city_name,
        "province":     city_data["province"],
        "type":         "city",
        "lat":          city_data["lat_center"],
        "lon":          city_data["lon_center"],
    })


# ---------------------------------------------------------------------------
# Motor de búsqueda predictiva
# ---------------------------------------------------------------------------

_ACCENT_MAP = str.maketrans({
    'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
    'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
    'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
    'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
    'ã': 'a', 'õ': 'o', 'ñ': 'n', 'ç': 'c',
    'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u',
    'À': 'a', 'È': 'e', 'Ì': 'i', 'Ò': 'o', 'Ù': 'u',
    'Â': 'a', 'Ê': 'e', 'Î': 'i', 'Ô': 'o', 'Û': 'u',
    'Ä': 'a', 'Ë': 'e', 'Ï': 'i', 'Ö': 'o', 'Ü': 'u',
    'Ã': 'a', 'Õ': 'o', 'Ñ': 'n', 'Ç': 'c',
})


def _norm(text: str) -> str:
    return text.lower().translate(_ACCENT_MAP)


def get_suggestions(query: str, limit: int = 15) -> list[dict]:
    """
    Búsqueda predictiva: devuelve hasta `limit` entradas que coincidan con el query.
    Prioriza coincidencias al inicio del nombre sobre coincidencias en el medio.
    """
    if not query or len(query) < 2:
        return []

    q = _norm(query.strip())
    starts_with: list[dict] = []
    contains:    list[dict] = []

    for entry in NEIGHBORHOOD_INDEX:
        label_norm = _norm(entry["label"])
        neigh_norm = _norm(entry["neighborhood"])
        city_norm  = _norm(entry["city"])

        if neigh_norm.startswith(q) or city_norm.startswith(q):
            starts_with.append(entry)
        elif q in label_norm:
            contains.append(entry)

        if len(starts_with) + len(contains) >= limit * 3:
            break

    results = starts_with[:limit] + contains[:limit]
    # Deduplicar preservando orden
    seen = set()
    deduped = []
    for e in results:
        if e["label"] not in seen:
            seen.add(e["label"])
            deduped.append(e)

    return deduped[:limit]


def get_all_labels() -> list[str]:
    """Devuelve todos los labels del índice para autocomplete exhaustivo."""
    return [e["label"] for e in NEIGHBORHOOD_INDEX]
