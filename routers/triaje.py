from datetime import date
from typing import Optional

from fastapi import APIRouter

from Services.asistente_ia import AsistenteIA
from Services.notificador import ServicioNotificacion
from models.mascotas import Especie, Mascota, Raza
from models.triaje import AlertaUrgencia, ConsultaTriaje
from models.veterinarias import Veterinaria
from schemas.triaje import TriajeRequest, TriajeResponse
from utils.geo import calcular_distancia_haversine


router = APIRouter(prefix="/triaje", tags=["Triaje de Urgencia e IA"])
asistente_ia = AsistenteIA()
notificador = ServicioNotificacion(proveedor_api="WhatsApp / Twilio")

VETERINARIAS_CANDIDATAS = [
    Veterinaria(
        1,
        "Centro Médico Veterinario Belgrano",
        "Amenábar 2214, Belgrano, CABA",
        -34.562069,
        -58.4596054,
        None,
        False,
        horario_informado="24/7 según OpenStreetMap; pendiente de confirmación directa",
        fuente_datos="OpenStreetMap",
        fuente_url="https://www.openstreetmap.org/node/2276920088",
        atribucion_fuente="© OpenStreetMap contributors (ODbL)",
        estado_verificacion="PENDIENTE_CONFIRMACION",
    ),
    Veterinaria(
        2,
        "Panda",
        "Av. Ruiz Huidobro 4771, Saavedra, CABA",
        -34.5549092,
        -58.4945994,
        None,
        False,
        horario_informado="24/7 según OpenStreetMap; pendiente de confirmación directa",
        fuente_datos="OpenStreetMap",
        fuente_url="https://www.openstreetmap.org/node/8067203564",
        atribucion_fuente="© OpenStreetMap contributors (ODbL)",
        estado_verificacion="PENDIENTE_CONFIRMACION",
    ),
]
for candidata in VETERINARIAS_CANDIDATAS:
    candidata.actualizar_estado_guardia("PENDIENTE_VERIFICACION")

contador_alertas = 900


@router.post("/evaluar", response_model=TriajeResponse)
def evaluar_triaje(datos: TriajeRequest) -> TriajeResponse:
    global contador_alertas

    felino = Especie(1, "Felino")
    raza_generica = Raza(1, "Mestizo", felino)
    paciente = Mascota(
        1,
        datos.nombre_mascota,
        date.today(),
        "Hembra",
        4.0,
        raza_generica,
    )
    consulta = ConsultaTriaje(
        id_consulta=501,
        descripcion_sintomas=datos.sintomas,
        mascota=paciente,
        asistente_ia=asistente_ia,
    )
    consulta.evaluar_sintomas()

    veterinaria_mas_cercana: Optional[Veterinaria] = None
    distancia_minima = float("inf")
    if datos.latitud_cliente is not None and datos.longitud_cliente is not None:
        for veterinaria in VETERINARIAS_CANDIDATAS:
            if veterinaria.esta_disponible():
                distancia = calcular_distancia_haversine(
                    datos.latitud_cliente,
                    datos.longitud_cliente,
                    veterinaria.latitud,
                    veterinaria.longitud,
                )
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    veterinaria_mas_cercana = veterinaria

    alerta_enviada = False
    id_alerta_generada = None
    estado_envio = None
    mensaje_texto = None
    if consulta.nivel_urgencia == "ALTA" and veterinaria_mas_cercana:
        contador_alertas += 1
        alerta = AlertaUrgencia(
            id_alerta=contador_alertas,
            consulta_triaje=consulta,
            veterinaria_destino=veterinaria_mas_cercana,
            servicio_notificacion=notificador,
        )
        alerta.transmitir()
        alerta_enviada = True
        id_alerta_generada = alerta.id_alerta
        estado_envio = alerta.estado_envio
        mensaje_texto = alerta.mensaje_texto

    return TriajeResponse(
        paciente=paciente.nombre,
        sintomas_ingresados=datos.sintomas,
        nivel_urgencia=consulta.nivel_urgencia,
        especialidad_sugerida=consulta.especialidad_sugerida,
        primeros_auxilios=consulta.primeros_auxilios,
        veterinaria_cercana=(
            veterinaria_mas_cercana.nombre_fantasia
            if veterinaria_mas_cercana
            else "No disponible"
        ),
        direccion_veterinaria=(
            veterinaria_mas_cercana.direccion
            if veterinaria_mas_cercana
            else None
        ),
        telefono_veterinaria=(
            veterinaria_mas_cercana.telefono_guardia
            if veterinaria_mas_cercana
            else None
        ),
        distancia_km=(
            distancia_minima if veterinaria_mas_cercana else None
        ),
        alerta_despachada=alerta_enviada,
        id_alerta=id_alerta_generada,
        estado_notificacion=estado_envio,
        mensaje_alerta=mensaje_texto,
        latitud_cliente=datos.latitud_cliente,
        longitud_cliente=datos.longitud_cliente,
        latitud_veterinaria=(
            veterinaria_mas_cercana.latitud
            if veterinaria_mas_cercana
            else None
        ),
        longitud_veterinaria=(
            veterinaria_mas_cercana.longitud
            if veterinaria_mas_cercana
            else None
        ),
    )