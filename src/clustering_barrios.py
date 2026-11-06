"""
Clustering No Supervisado de Barrios de CABA - VetCerca IA
Algoritmo: K-Means Clustering
Objetivo: Segmentar los barrios según oferta veterinaria, cobertura de guardias 24hs y complejidad.
"""

import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_VETS = os.path.join(BASE_DIR, "data", "veterinarias_barrios.csv")

def obtener_metricas_por_barrio(df_vets=None):
    if df_vets is None:
        df_vets = pd.read_csv(DATA_VETS)
        
    # Agrupar por barrio
    resumen = df_vets.groupby("barrio").agg(
        comuna=("comuna", "first"),
        total_clinicas=("id_veterinaria", "count"),
        guardias_24hs=("guardia_24hs", "sum"),
        alta_complejidad=("nivel_complejidad", lambda s: (s == "Alta Complejidad/Quirófano").sum()),
        latitud_media=("latitud", "mean"),
        longitud_media=("longitud", "mean")
    ).reset_index()
    
    # Calcular ratios
    resumen["ratio_24hs"] = (resumen["guardias_24hs"] / resumen["total_clinicas"]).round(3)
    resumen["ratio_alta_complejidad"] = (resumen["alta_complejidad"] / resumen["total_clinicas"]).round(3)
    
    return resumen

def entrenar_clustering(k=3):
    resumen = obtener_metricas_por_barrio()
    
    features = ["total_clinicas", "guardias_24hs", "ratio_24hs", "alta_complejidad"]
    X = resumen[features]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    resumen["cluster_id"] = kmeans.fit_predict(X_scaled)
    
    # Etiquetar clústeres según promedio de guardias
    cluster_means = resumen.groupby("cluster_id")["guardias_24hs"].mean().sort_values()
    
    # Mapeo descriptivo: 0 -> Deficitaria, 1 -> Intermedia, 2 -> Alta
    etiquetas_map = {}
    nombres_ordenados = ["Zonas Críticas / Cobertura Deficitaria", "Cobertura Intermedia", "Alta Cobertura Zonal"]
    for idx, cluster_num in enumerate(cluster_means.index):
        etiquetas_map[cluster_num] = nombres_ordenados[min(idx, len(nombres_ordenados) - 1)]
        
    resumen["etiqueta_cobertura"] = resumen["cluster_id"].map(etiquetas_map)
    
    output_path = os.path.join(BASE_DIR, "data", "barrios_clusters.csv")
    resumen.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Resultados de clustering guardados en: {output_path}")
    
    return resumen

def obtener_diagnostico_barrio(nombre_barrio: str):
    path = os.path.join(BASE_DIR, "data", "barrios_clusters.csv")
    if not os.path.exists(path):
        entrenar_clustering()
    df = pd.read_csv(path)
    match = df[df["barrio"].str.lower() == nombre_barrio.strip().lower()]
    if not match.empty:
        return match.iloc[0].to_dict()
    return None

if __name__ == "__main__":
    print("Ejecutando K-Means Clustering para barrios de CABA...")
    resultado = entrenar_clustering(k=3)
    print("\nResumen por Clúster:")
    print(resultado[["barrio", "comuna", "total_clinicas", "guardias_24hs", "etiqueta_cobertura"]])
