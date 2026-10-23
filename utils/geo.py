import math


def calcular_distancia_haversine(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calcula en kilómetros la distancia entre dos coordenadas GPS."""
    radio_tierra_km = 6371.0

    diferencia_latitud = math.radians(lat2 - lat1)
    diferencia_longitud = math.radians(lon2 - lon1)
    a = (
        math.sin(diferencia_latitud / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(diferencia_longitud / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distancia_km = radio_tierra_km * c
    return round(distancia_km, 2)