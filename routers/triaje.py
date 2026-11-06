from datetime import date
from typing import Optional, Dict, Any, List

from fastapi import APIRouter

from Services.asistente_ia import AsistenteIA
from Services.notificador import ServicioNotificacion
from models.mascotas import Especie, Mascota, Raza
from models.triaje import AlertaUrgencia, ConsultaTriaje
from models.veterinarias import Veterinaria
from schemas.triaje import TriajeRequest, TriajeResponse
from utils.contingencia_barrios import resolver_contingencia_zonal, cargar_catalogo_veterinarias
from src.clustering_barrios import obtener_metricas_por_barrio, obtener_diagnostico_barrio


router = APIRouter(prefix="/triaje", tags=["Triaje de Urgencia e IA"])
asistente_ia = AsistenteIA()
notificador = ServicioNotificacion(proveedor_api="WhatsApp / Twilio")

contador_alertas = 900


@router.post("/evaluar", response_model=TriajeResponse)
def evaluar_triaje(datos: TriajeRequest) -> TriajeResponse:
    global contador_alertas

    # Normalizar síntomas de entrada
    sintomas_texto = datos.sintoma_principal or datos.sintomas or "Decaimiento general"

    # Intentar asociar a una mascota registrada en memoria si existe
    from routers.mascotas import MASCOTAS_DB

    paciente: Optional[Mascota] = None
    for item in MASCOTAS_DB:
        m = item["mascota"]
        if (
            m.nombre.strip().lower() == datos.nombre_mascota.strip().lower()
            and (datos.id_cliente is None or item["id_cliente"] == datos.id_cliente)
        ):
            paciente = m
            break

    especie_nombre = datos.especie or "Canino"
    if paciente is None:
        especie_obj = Especie(1, especie_nombre, es_exotico=False)
        raza_generica = Raza(1, "Mestizo", especie_obj)
        paciente = Mascota(
            id_mascota=1,
            nombre=datos.nombre_mascota,
            fecha_nacimiento=date.today(),
            sexo="Hembra",
            peso_kg=4.0,
            raza=raza_generica,
        )
    elif hasattr(paciente, "raza") and hasattr(paciente.raza, "especie"):
        especie_nombre = paciente.raza.especie.nombre

    # Instanciar ConsultaTriaje con variables clínicas del modelo supervisado
    consulta = ConsultaTriaje(
        id_triaje=501,
        sintomas_ingresados=sintomas_texto,
        id_cliente=datos.id_cliente or 1,
        id_mascota=paciente.id_mascota,
        mascota=paciente,
        asistente_ia=asistente_ia,
        especie=especie_nombre,
        tiempo_evolucion_hs=datos.tiempo_evolucion_hs,
        estado_conciencia=datos.estado_conciencia,
        presencia_hemorragia=datos.presencia_hemorragia
    )
    
    # Ejecutar inferencia predictiva con Machine Learning + Prompt estructurado
    consulta.ejecutar_triaje(
        asistente_ia,
        tiempo_evolucion_hs=datos.tiempo_evolucion_hs,
        estado_conciencia=datos.estado_conciencia,
        presencia_hemorragia=datos.presencia_hemorragia
    )

    es_urgencia_critica = consulta.nivel_urgencia in ["Alta", "Emergencia Crítica"]

    # Resolver recomendación barrial y contingencia combinada con Haversine GPS
    barrio_solicitado = datos.barrio or "Palermo"
    contingencia_res = resolver_contingencia_zonal(
        barrio_usuario=barrio_solicitado,
        lat_cliente=datos.latitud_cliente,
        lon_cliente=datos.longitud_cliente,
        requiere_24hs=es_urgencia_critica
    )

    vet_info = contingencia_res.get("veterinaria_recomendada")
    veterinaria_obj = None

    if vet_info:
        veterinaria_obj = Veterinaria(
            id_veterinaria=vet_info["id_veterinaria"],
            nombre=vet_info["nombre_centro"],
            direccion=vet_info["direccion"],
            latitud=vet_info["latitud"],
            longitud=vet_info["longitud"],
            tiene_guardia_24h=vet_info["guardia_24hs"],
            telefono_guardia=vet_info["telefono"],
            barrio=vet_info["barrio"],
            comuna=vet_info["comuna"],
            nivel_complejidad=vet_info["nivel_complejidad"],
            especialidades=vet_info["especialidades"]
        )

    # Despacho de alerta en tiempo real ante casos de severidad Alta o Emergencia Crítica
    alerta_enviada = False
    id_alerta_generada = None
    estado_envio = None
    mensaje_texto = None
    tiempo_arribo = vet_info.get("tiempo_estimado_min", 15) if vet_info else None

    if es_urgencia_critica and veterinaria_obj:
        contador_alertas += 1
        alerta = AlertaUrgencia(
            id_alerta=contador_alertas,
            consulta_triaje=consulta,
            veterinaria_destino=veterinaria_obj,
            servicio_notificacion=notificador,
            id_triaje=consulta.id_triaje,
            id_veterinaria_asignada=veterinaria_obj.id_veterinaria,
            tiempo_estimado_arribo_min=tiempo_arribo or 15,
        )
        alerta.transmitir()
        alerta_enviada = True
        id_alerta_generada = alerta.id_alerta
        estado_envio = alerta.estado
        mensaje_texto = alerta.mensaje_texto

    return TriajeResponse(
        paciente=paciente.nombre,
        especie=especie_nombre,
        sintomas_ingresados=sintomas_texto,
        nivel_urgencia=consulta.nivel_urgencia,
        confianza_prediccion=consulta.confianza_prediccion,
        probabilidades=consulta.probabilidades,
        diagnostico_preliminar=consulta.diagnostico_preliminar,
        especialidad_sugerida=consulta.especialidad_sugerida,
        primeros_auxilios=consulta.primeros_auxilios,
        pregunta_aclaratoria=consulta.pregunta_aclaratoria,
        veterinaria_cercana=vet_info["nombre_centro"] if vet_info else "No disponible",
        direccion_veterinaria=vet_info["direccion"] if vet_info else None,
        telefono_veterinaria=vet_info["telefono"] if vet_info else None,
        distancia_km=vet_info.get("distancia_km") if vet_info else None,
        tiempo_estimado_arribo_min=tiempo_arribo,
        barrio=barrio_solicitado,
        contingencia_activada=contingencia_res.get("contingencia_activada", False),
        motivo_contingencia=contingencia_res.get("motivo_contingencia"),
        barrio_derivacion=contingencia_res.get("barrio_derivacion"),
        alerta_despachada=alerta_enviada,
        id_alerta=id_alerta_generada,
        estado_notificacion=estado_envio,
        mensaje_alerta=mensaje_texto,
        latitud_cliente=datos.latitud_cliente,
        longitud_cliente=datos.longitud_cliente,
        latitud_veterinaria=vet_info["latitud"] if vet_info else None,
        longitud_veterinaria=vet_info["longitud"] if vet_info else None,
    )


@router.get("/contingencia/{barrio}")
def consultar_contingencia_barrial(
    barrio: str,
    latitud: Optional[float] = None,
    longitud: Optional[float] = None,
    solo_24hs: bool = True
) -> Dict[str, Any]:
    """
    Consulta directa de cobertura de guardia y derivación por contingencia geográfica.
    """
    return resolver_contingencia_zonal(
        barrio_usuario=barrio,
        lat_cliente=latitud,
        lon_cliente=longitud,
        requiere_24hs=solo_24hs
    )


@router.get("/clustering/zonas")
def consultar_clustering_zonas() -> List[Dict[str, Any]]:
    """
    Expone los resultados de segmentación no supervisada (K-Means) de los barrios de CABA.
    """
    df_clusters = obtener_metricas_por_barrio()
    from src.clustering_barrios import entrenar_clustering
    resultado = entrenar_clustering(k=3)
    return resultado.to_dict(orient="records")
