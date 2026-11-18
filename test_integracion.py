"""
Test de Integración Directa de Funciones de VetCerca IA
"""

import sys
from unittest.mock import patch
from app import inicio, obtener_veterinarias_cercanas
from Services.asistente_ia import AsistenteIA, InterpretacionSintoma
from routers.triaje import (
    asistente_ia as asistente_router,
    evaluar_triaje,
    consultar_contingencia_barrial,
    consultar_clustering_zonas,
)
from schemas.triaje import TriajeRequest
from routers.auth import SESIONES_VETERINARIAS, VETERINARIA_DEMO
from routers.veterinaria import (
    agregar_evolucion_alerta,
    actualizar_estado_alerta,
    listar_alertas_veterinaria,
    listar_historial_alertas_veterinaria,
    obtener_historia_alerta,
    simular_alerta_veterinaria,
)
from schemas.veterinaria import EstadoAlertaRequest, EvolucionClinicaRequest

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

    SESIONES_VETERINARIAS["token-integracion-vet"] = VETERINARIA_DEMO.id_veterinaria
    alertas_veterinarias = listar_alertas_veterinaria(
        authorization="Bearer token-integracion-vet"
    )
    alerta_veterinaria = alertas_veterinarias[0]
    assert alerta_veterinaria["mascota"]["nombre"] == "Thor"
    assert alerta_veterinaria["nivel_urgencia"] == "Emergencia Crítica"
    assert alerta_veterinaria["tiempo_estimado_arribo_min"] > 0
    historia_inicial = obtener_historia_alerta(
        alerta_veterinaria["id_alerta"],
        authorization="Bearer token-integracion-vet",
    )
    registro_evolucion = agregar_evolucion_alerta(
        alerta_veterinaria["id_alerta"],
        EvolucionClinicaRequest(
            motivo="Atención inicial de urgencia",
            diagnostico="Paciente evaluado en guardia.",
            tratamiento="Evaluación y estabilización veterinaria.",
            observaciones="Registro de prueba de integración.",
        ),
        authorization="Bearer token-integracion-vet",
    )
    historia_actualizada = obtener_historia_alerta(
        alerta_veterinaria["id_alerta"],
        authorization="Bearer token-integracion-vet",
    )
    assert len(historia_actualizada["historial"]) == (
        historia_inicial["total_atenciones"] + 1
    )
    assert registro_evolucion["motivo"] == "Atención inicial de urgencia"
    estado_actualizado = actualizar_estado_alerta(
        alerta_veterinaria["id_alerta"],
        EstadoAlertaRequest(estado="EN_ATENCION"),
        authorization="Bearer token-integracion-vet",
    )
    assert estado_actualizado["estado"] == "EN_ATENCION"
    alerta_resuelta = actualizar_estado_alerta(
        alerta_veterinaria["id_alerta"],
        EstadoAlertaRequest(estado="RESUELTA"),
        authorization="Bearer token-integracion-vet",
    )
    alertas_activas = listar_alertas_veterinaria(
        authorization="Bearer token-integracion-vet"
    )
    historial_alertas = listar_historial_alertas_veterinaria(
        authorization="Bearer token-integracion-vet"
    )
    assert alerta_resuelta["estado"] == "RESUELTA"
    assert all(
        alerta["id_alerta"] != alerta_veterinaria["id_alerta"]
        for alerta in alertas_activas
    )
    assert historial_alertas[0]["id_alerta"] == alerta_veterinaria["id_alerta"]
    alerta_simulada = simular_alerta_veterinaria(
        authorization="Bearer token-integracion-vet"
    )
    assert alerta_simulada["es_demostracion"] is True
    assert alerta_simulada["estado"] == "RECIBIDA"
    print("OK: el portal veterinario lista, actualiza y agrega evoluciones a una alerta.")

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
    assert res_leve.nivel_urgencia == "Baja"
    assert res_leve.alerta_despachada is False

    print("\n--- 4. Probando síntoma no reconocido sin generar alarma ---")
    req_no_reconocido = TriajeRequest(
        nombre_mascota="Firulais",
        sintomas="Mi perro sonríe demasiado",
        tiempo_evolucion_hs=2.0,
        estado_conciencia="Alerta",
        presencia_hemorragia=0,
    )
    with patch.object(asistente_router, "api_key", ""):
        res_no_reconocido = evaluar_triaje(req_no_reconocido)
    assert res_no_reconocido.nivel_urgencia == "No concluyente"
    assert res_no_reconocido.alerta_despachada is False
    print(f"OK: {res_no_reconocido.nivel_urgencia}; no se despachó alerta.")

    resultado_sin_respuesta = asistente_router.clasificar_urgencia(
        sintomas="esta decaido y no responde",
        especie="Canino",
        tiempo_evolucion_hs=2.0,
        estado_conciencia="Estuporoso/Comatoso",
        presencia_hemorragia=0,
    )
    assert resultado_sin_respuesta["nivel_urgencia"] == "Emergencia Crítica"
    print("OK: pérdida de conciencia reportada activa orientación crítica aunque el síntoma sea libre.")

    print("\n--- 5. Priorizando sangrado abundante con texto no reconocido ---")
    req_sangrado_no_reconocido = TriajeRequest(
        nombre_mascota="Rocky",
        sintomas="asadas",
        tiempo_evolucion_hs=2.0,
        estado_conciencia="Deprimido",
        presencia_hemorragia=1,
    )
    with patch.object(asistente_router, "api_key", ""):
        res_sangrado = evaluar_triaje(req_sangrado_no_reconocido)
    assert res_sangrado.nivel_urgencia == "Emergencia Crítica"
    assert res_sangrado.alerta_despachada is True
    print("OK: el dato de sangrado abundante activa emergencia aunque el texto no se reconozca.")

    print("\n--- 6. Probando datos clínicos incompletos ---")
    req_incompleto = TriajeRequest(
        nombre_mascota="Firulais",
        sintoma_principal="Prurito y rascado auricular leve",
    )
    with patch.object(asistente_router, "api_key", ""):
        res_incompleto = evaluar_triaje(req_incompleto)
    assert res_incompleto.nivel_urgencia == "No concluyente"
    assert res_incompleto.alerta_despachada is False
    print(f"OK: {res_incompleto.nivel_urgencia} si faltan datos clínicos.")

    print("\n--- 7. Probando aclaración conversacional de un error tipográfico ---")
    asistente_chat = AsistenteIA(api_key="")
    with patch.object(asistente_chat, "api_key", ""):
        resultado_error = asistente_chat.clasificar_urgencia(
            sintomas="Sanngra",
            especie="Canino",
            tiempo_evolucion_hs=0.5,
            estado_conciencia="Alerta",
            presencia_hemorragia=0,
        )
    assert resultado_error["nivel_urgencia"] == "No concluyente"
    assert "sangrado" in resultado_error["pregunta_aclaratoria"].lower()
    assert "guardia" in resultado_error["pregunta_aclaratoria"].lower()

    asistente_chat.modo_fallback = True
    resultado_aclarado = asistente_chat.clasificar_urgencia(
        sintomas="Sanngra. Aclaración del tutor: sí, sangra mucho y no para",
        especie="Canino",
        tiempo_evolucion_hs=0.5,
        estado_conciencia="Alerta",
        presencia_hemorragia=0,
    )
    assert resultado_aclarado["nivel_urgencia"] == "Emergencia Crítica"
    print("OK: sugiere confirmar el síntoma y reconoce sangrado abundante como emergencia.")

    resultado_sin_sintomas = asistente_chat.clasificar_urgencia(
        sintomas="esta bien",
        especie="Canino",
        tiempo_evolucion_hs=2.0,
        estado_conciencia="Alerta",
        presencia_hemorragia=0,
    )
    assert resultado_sin_sintomas["nivel_urgencia"] == "No concluyente"
    assert resultado_sin_sintomas["confianza"] == 0.0
    print("OK: una expresión sin síntomas no se clasifica como emergencia.")

    resultado_alergia_cutanea = asistente_chat.clasificar_urgencia(
        sintomas="alergia en la piel",
        especie="Canino",
        tiempo_evolucion_hs=2.0,
        estado_conciencia="Alerta",
        presencia_hemorragia=0,
    )
    assert resultado_alergia_cutanea["nivel_urgencia"] == "Moderada"
    assert "dificultad para respirar" in resultado_alergia_cutanea["primeros_auxilios"]
    resultado_reaccion_alergica_grave = asistente_chat.clasificar_urgencia(
        sintomas="alergia en la piel, le cuesta respirar y tiene el hocico hinchado",
        especie="Canino",
        tiempo_evolucion_hs=2.0,
        estado_conciencia="Alerta",
        presencia_hemorragia=0,
    )
    assert resultado_reaccion_alergica_grave["nivel_urgencia"] == "Emergencia Crítica"
    resultado_alergia_sin_signos_cutaneos = asistente_chat.clasificar_urgencia(
        sintomas="alergia alimentaria sin síntomas cutáneos",
        especie="Canino",
        tiempo_evolucion_hs=2.0,
        estado_conciencia="Alerta",
        presencia_hemorragia=0,
    )
    assert resultado_alergia_sin_signos_cutaneos["nivel_urgencia"] == "No concluyente"
    print("OK: alergia cutánea sin Gemini recibe orientación moderada y detecta señales críticas.")

    print("\n--- 8. Probando interpretación Gemini sin llamada externa ---")
    asistente_prueba = AsistenteIA(api_key="clave-de-prueba")
    interpretacion_leve = InterpretacionSintoma(
        sintoma_catalogo="Prurito y rascado auricular leve",
        confianza=0.95,
        pregunta_aclaratoria="",
    )
    with patch.object(
        asistente_prueba,
        "_interpretar_sintoma_con_gemini",
        return_value=interpretacion_leve,
    ):
        resultado_interpretado = asistente_prueba.clasificar_urgencia(
            sintomas="se rasca mucho una oreja",
            especie="Canino",
            tiempo_evolucion_hs=48.0,
            estado_conciencia="Alerta",
            presencia_hemorragia=0,
        )
    assert resultado_interpretado["nivel_urgencia"] == "Baja"
    print(f"OK: descripción libre mapeada a {resultado_interpretado['nivel_urgencia']}.")

    interpretacion_ambigua = InterpretacionSintoma(
        sintoma_catalogo=None,
        confianza=0.2,
        pregunta_aclaratoria="¿Podés describir qué significa que sonríe?",
    )
    with patch.object(
        asistente_prueba,
        "_interpretar_sintoma_con_gemini",
        return_value=interpretacion_ambigua,
    ):
        resultado_ambiguo = asistente_prueba.clasificar_urgencia(
            sintomas="mi perro sonríe demasiado",
            especie="Canino",
            tiempo_evolucion_hs=2.0,
            estado_conciencia="Alerta",
            presencia_hemorragia=0,
        )
    assert resultado_ambiguo["nivel_urgencia"] == "No concluyente"
    assert resultado_ambiguo["pregunta_aclaratoria"]
    print("OK: descripción ambigua solicita una aclaración sin generar urgencia.")

    print("\n--- 9. Probando Consulta de Veterinarias Cercanas (Haversine GPS) ---")
    res_vets = obtener_veterinarias_cercanas(latitud=-34.5800, longitud=-58.4200, radio_km=3.0)
    print(f"OK: Encontradas {res_vets['cantidad']} veterinarias en radio de 3 km.")

    print("\n--- 10. Probando Clustering Zonal (K-Means) ---")
    res_clusters = consultar_clustering_zonas()
    print(f"OK: Se retornaron {len(res_clusters)} barrios segmentados por K-Means.")

    print("\nTODAS LAS PRUEBAS DE INTEGRACION PASARON EXITOSAMENTE!")

if __name__ == "__main__":
    run_tests()
