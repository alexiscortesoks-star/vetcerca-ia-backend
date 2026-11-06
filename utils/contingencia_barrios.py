"""
Lógica de Contingencia Zonal y Matriz de Adyacencia de Barrios de CABA - VetCerca IA
Combina el límite territorial de comunas/barrios con el cálculo geodésico Haversine.
"""

import os
from typing import Dict, List, Optional
import pandas as pd
from utils.geo import calcular_distancia_haversine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_VETS_PATH = os.path.join(BASE_DIR, "data", "veterinarias_barrios.csv")

# Centroides aproximados de barrios para fallback cuando el usuario no envía GPS exacto
CENTROIDES_BARRIOS: Dict[str, Dict[str, float]] = {
    "palermo": {"lat": -34.5800, "lon": -58.4200},
    "belgrano": {"lat": -34.5620, "lon": -58.4560},
    "caballito": {"lat": -34.6200, "lon": -58.4450},
    "recoleta": {"lat": -34.5900, "lon": -58.3950},
    "flores": {"lat": -34.6300, "lon": -58.4600},
    "villa urquiza": {"lat": -34.5750, "lon": -58.4850},
    "almagro": {"lat": -34.6100, "lon": -58.4200},
    "saavedra": {"lat": -34.5500, "lon": -58.4900},
    "villa devoto": {"lat": -34.6000, "lon": -58.5100},
    "balvanera": {"lat": -34.6100, "lon": -58.4000},
    "colegiales": {"lat": -34.5750, "lon": -58.4500},
    "núñez": {"lat": -34.5450, "lon": -58.4650},
    "nunez": {"lat": -34.5450, "lon": -58.4650},
    "villa crespo": {"lat": -34.5950, "lon": -58.4400},
    "san telmo": {"lat": -34.6200, "lon": -58.3700},
    "barracas": {"lat": -34.6450, "lon": -58.3800},
    "parque patricios": {"lat": -34.6350, "lon": -58.4050},
    "villa lugano": {"lat": -34.6750, "lon": -58.4700},
    "mataderos": {"lat": -34.6600, "lon": -58.5000},
    "chacarita": {"lat": -34.5880, "lon": -58.4550},
    "boedo": {"lat": -34.6300, "lon": -58.4150},
}

# Matriz de adyacencia geográfica entre barrios de CABA
ADYACENCIA_BARRIOS: Dict[str, List[str]] = {
    "palermo": ["recoleta", "almagro", "villa crespo", "chacarita", "colegiales", "belgrano"],
    "belgrano": ["núñez", "saavedra", "villa urquiza", "colegiales", "palermo"],
    "caballito": ["almagro", "boedo", "flores", "villa crespo"],
    "recoleta": ["palermo", "balvanera", "san telmo"],
    "flores": ["caballito", "parque patricios", "mataderos", "villa lugano"],
    "villa urquiza": ["saavedra", "belgrano", "colegiales", "villa devoto", "chacarita"],
    "almagro": ["palermo", "recoleta", "balvanera", "boedo", "caballito", "villa crespo"],
    "saavedra": ["núñez", "belgrano", "villa urquiza"],
    "villa devoto": ["villa urquiza", "flores", "mataderos"],
    "balvanera": ["recoleta", "almagro", "san telmo", "boedo"],
    "colegiales": ["belgrano", "palermo", "chacarita", "villa urquiza"],
    "núñez": ["saavedra", "belgrano"],
    "nunez": ["saavedra", "belgrano"],
    "villa crespo": ["palermo", "almagro", "caballito", "chacarita"],
    "san telmo": ["recoleta", "balvanera", "barracas", "parque patricios"],
    "barracas": ["san telmo", "parque patricios", "boedo"],
    "parque patricios": ["barracas", "san telmo", "boedo", "flores"],
    "villa lugano": ["flores", "mataderos"],
    "mataderos": ["flores", "villa lugano", "villa devoto"],
    "chacarita": ["palermo", "colegiales", "villa urquiza", "villa crespo"],
    "boedo": ["almagro", "balvanera", "caballito", "parque patricios", "barracas"],
}

def cargar_catalogo_veterinarias() -> pd.DataFrame:
    if os.path.exists(DATA_VETS_PATH):
        return pd.read_csv(DATA_VETS_PATH)
    return pd.DataFrame()

def resolver_contingencia_zonal(
    barrio_usuario: str,
    lat_cliente: Optional[float] = None,
    lon_cliente: Optional[float] = None,
    requiere_24hs: bool = True
) -> Dict[str, object]:
    """
    Busca veterinarias disponibles para el usuario aplicando la lógica:
    1. Si hay clínicas de guardia 24hs en el barrio seleccionado, calcula Haversine a cada una.
    2. Si no hay guardia 24hs activa en ese barrio, activa protocolo de contingencia a barrios limítrofes
       y selecciona la clínica de guardia vecina con menor distancia Haversine.
    """
    df_vets = cargar_catalogo_veterinarias()
    if df_vets.empty:
        return {
            "encontrada": False,
            "contingencia_activada": False,
            "mensaje": "No se encontraron clínicas cargadas en la base de datos."
        }
    
    b_limpio = barrio_usuario.strip().lower()
    
    # Determinar coordenadas de referencia para el cálculo geodésico
    if lat_cliente is None or lon_cliente is None:
        coords = CENTROIDES_BARRIOS.get(b_limpio, {"lat": -34.6037, "lon": -58.3816})
        lat_ref = coords["lat"]
        lon_ref = coords["lon"]
    else:
        lat_ref = float(lat_cliente)
        lon_ref = float(lon_cliente)
        
    # Filtrar en barrio de origen
    vets_origen = df_vets[df_vets["barrio"].str.lower() == b_limpio]
    if requiere_24hs:
        vets_candidatas = vets_origen[vets_origen["guardia_24hs"] == 1]
    else:
        vets_candidatas = vets_origen

    contingencia_activada = False
    barrio_derivado = None
    motivo_contingencia = None

    if vets_candidatas.empty and requiere_24hs:
        # Activar Contingencia Zonal
        contingencia_activada = True
        barrios_vecinos = ADYACENCIA_BARRIOS.get(b_limpio, [])
        motivo_contingencia = (
            f"El barrio {barrio_usuario.title()} no dispone de guardia activa de 24hs. "
            f"Se activó el protocolo de derivación zonal hacia barrios limítrofes."
        )
        
        # Buscar en barrios vecinos con guardia 24hs
        vets_candidatas = df_vets[
            (df_vets["barrio"].str.lower().isin(barrios_vecinos)) &
            (df_vets["guardia_24hs"] == 1)
        ]
        
        # Si aún estuviese vacío, buscar en toda la ciudad la guardia más cercana
        if vets_candidatas.empty:
            vets_candidatas = df_vets[df_vets["guardia_24hs"] == 1]
            motivo_contingencia = (
                f"Sin guardias directas en {barrio_usuario.title()} ni adyacentes. "
                "Derivación global a la guardia 24hs de CABA más cercana."
            )

    if vets_candidatas.empty:
        # Fallback a cualquier veterinaria
        vets_candidatas = df_vets

    # Calcular distancia Haversine a cada clínica candidata
    resultados = []
    for _, row in vets_candidatas.iterrows():
        dist_km = calcular_distancia_haversine(lat_ref, lon_ref, row["latitud"], row["longitud"])
        # Estimación de tiempo de arribo (asumiendo velocidad urbana de 30 km/h + 5 min fijos)
        tiempo_min = max(5, int(round((dist_km / 30.0) * 60) + 5))
        
        resultados.append({
            "id_veterinaria": int(row["id_veterinaria"]),
            "nombre_centro": row["nombre_centro"],
            "barrio": row["barrio"],
            "comuna": int(row["comuna"]),
            "direccion": row["direccion"],
            "telefono": row["telefono_urgencias"],
            "latitud": float(row["latitud"]),
            "longitud": float(row["longitud"]),
            "guardia_24hs": bool(row["guardia_24hs"] == 1),
            "nivel_complejidad": row["nivel_complejidad"],
            "especialidades": row["especialidades"],
            "distancia_km": dist_km,
            "tiempo_estimado_min": tiempo_min
        })

    # Ordenar por menor distancia geodésica
    resultados.sort(key=lambda x: x["distancia_km"])
    mejor_opcion = resultados[0] if resultados else None

    if contingencia_activada and mejor_opcion:
        barrio_derivado = mejor_opcion["barrio"]

    return {
        "encontrada": mejor_opcion is not None,
        "contingencia_activada": contingencia_activada,
        "barrio_origen": barrio_usuario,
        "barrio_derivacion": barrio_derivado,
        "motivo_contingencia": motivo_contingencia,
        "veterinaria_recomendada": mejor_opcion,
        "total_opciones_disponibles": len(resultados),
        "todas_las_opciones": resultados[:5] # Top 5 más cercanas
    }
