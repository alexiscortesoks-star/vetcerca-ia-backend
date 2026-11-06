"""
Test de Integración Directa de Funciones de VetCerca IA
"""

import sys
from app import inicio, obtener_veterinarias_cercanas
from routers.triaje import evaluar_triaje, consultar_contingencia_barrial, consultar_clustering_zonas
from schemas.triaje import TriajeRequest

def run_tests():
    print("--- 1. Probando Endpoint Raíz ---")
    res_inicio = inicio()
    print("OK:", res_inicio)

    print("\n--- 2. Probando Evaluación de Triaje (Emergencia Crítica con ML y Contingencia) ---")
    req_critico = TriajeRequest(
        nombre_mascota="Thor",
        especie="Canino",
        sintoma_principal="Dificultad respiratoria severa / Cianosis",
        tiempo_evolucion_hs=0.5,
        estado_conciencia="Estuporoso/Comatoso",
        presencia_hemorragia=1,
        barrio="Villa Lugano",
        latitud_cliente=-34.6750,
        longitud_cliente=-58.4700
    )
    res_critico = evaluar_triaje(req_critico)
    print("OK:")
    print(f"  Paciente: {res_critico.paciente}")
    print(f"  Nivel de Urgencia (Random Forest): {res_critico.nivel_urgencia}")
    print(f"  Confianza de predicción: {res_critico.confianza_prediccion}")
    print(f"  Clínica de guardia asignada: {res_critico.veterinaria_cercana} ({res_critico.distancia_km} km)")
    print(f"  ¿Contingencia activada?: {res_critico.contingencia_activada}")
    if res_critico.contingencia_activada:
        print(f"  Motivo contingencia: {res_critico.motivo_contingencia}")
        print(f"  Barrio derivación: {res_critico.barrio_derivacion}")
    print(f"  Alerta despachada en tiempo real: {res_critico.alerta_despachada}")
    print(f"  Primeros auxilios: {res_critico.primeros_auxilios[:90]}...")

    print("\n--- 3. Probando Evaluación de Triaje (Caso Leve / Baja) ---")
    req_leve = TriajeRequest(
        nombre_mascota="Michi",
        especie="Felino",
        sintoma_principal="Consulta de rutina / Plan de vacunación",
        tiempo_evolucion_hs=48.0,
        estado_conciencia="Alerta",
        presencia_hemorragia=0,
        barrio="Palermo",
        latitud_cliente=-34.5800,
        longitud_cliente=-58.4200
    )
    res_leve = evaluar_triaje(req_leve)
    print("OK:")
    print(f"  Paciente: {res_leve.paciente}")
    print(f"  Nivel de Urgencia (Random Forest): {res_leve.nivel_urgencia}")
    print(f"  Alerta despachada: {res_leve.alerta_despachada}")

    print("\n--- 4. Probando Consulta de Veterinarias Cercanas (Haversine GPS) ---")
    res_vets = obtener_veterinarias_cercanas(latitud=-34.5800, longitud=-58.4200, radio_km=3.0)
    print(f"OK: Encontradas {res_vets['cantidad']} veterinarias en radio de 3 km.")

    print("\n--- 5. Probando Clustering Zonal (K-Means) ---")
    res_clusters = consultar_clustering_zonas()
    print(f"OK: Se retornaron {len(res_clusters)} barrios segmentados por K-Means.")

    print("\nTODAS LAS PRUEBAS DE INTEGRACION PASARON EXITOSAMENTE!")

if __name__ == "__main__":
    run_tests()
