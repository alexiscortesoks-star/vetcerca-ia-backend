from datetime import date
from typing import Optional

from fastapi import APIRouter

from Services.asistente_ia import AsistenteIA
from Services.notificador import ServicioNotificacion
from models.mascotas import Especie, Mascota, Raza
from models.triaje import AlertaUrgencia, ConsultaTriaje
from models.veterinarias import Veterinaria
from schemas.triaje import TriajeRequest, TriajeResponse


router = APIRouter(prefix="/triaje", tags=["Triaje de Urgencia e IA"])
asistente_ia = AsistenteIA()
notificador = ServicioNotificacion(proveedor_api="WhatsApp / Twilio")

VETERINARIAS_CANDIDATAS = [
    Veterinaria(
        1,
        "Centro Médico Veterinario Belgrano 24h",
        "Amenábar 2214, Belgrano, CABA",
        -34.562069,
        -58.4596054,
        tiene_guardia_24h=True,
        telefono_guardia="+5491144445555",
        horario_informado="Guardia 24hs activa",
        fuente_datos="OpenStreetMap / Registro Oficial",
        fuente_url="https://www.openstreetmap.org/node/2276920088",
        atribucion_fuente="© OpenStreetMap contributors (ODbL)",
        estado_verificacion="VERIFICADA_24HS",
    ),
    Veterinaria(
        2,
        "Clínica Veterinaria Panda Guardia Urgencias",
        "Av. Ruiz Huidobro 4771, Saavedra, CABA",
        -34.5549092,
        -58.4945994,
        tiene_guardia_24h=True,
        telefono_guardia="+5491188889999",
        horario_informado="Guardia 24hs activa",
        fuente_datos="OpenStreetMap / Registro Oficial",
        fuente_url="https://www.openstreetmap.org/node/8067203564",
        atribucion_fuente="© OpenStreetMap contributors (ODbL)",
        estado_verificacion="VERIFICADA_24HS",
    ),
]
for candidata in VETERINARIAS_CANDIDATAS:
    candidata.actualizar_estado_guardia("DISPONIBLE")

contador_alertas = 900


@router.post("/evaluar", response_model=TriajeResponse)
def evaluar_triaje(datos: TriajeRequest) -> TriajeResponse:
    global contador_alertas

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

    if paciente is None:
        felino = Especie(1, "Felino", es_exotico=False)
        raza_generica = Raza(1, "Mestizo", felino)
        paciente = Mascota(
            id_mascota=1,
            nombre=datos.nombre_mascota,
            fecha_nacimiento=date.today(),
            sexo="Hembra",
            peso_kg=4.0,
            raza=raza_generica,
        )

    consulta = ConsultaTriaje(
        id_triaje=501,
        sintomas_ingresados=datos.sintomas,
        id_cliente=datos.id_cliente or 1,
        id_mascota=paciente.id_mascota,
        mascota=paciente,
        asistente_ia=asistente_ia,
    )
    consulta.ejecutar_triaje(asistente_ia)

    veterinaria_mas_cercana: Optional[Veterinaria] = None
    distancia_minima = float("inf")
    if datos.latitud_cliente is not None and datos.longitud_cliente is not None:
        for veterinaria in VETERINARIAS_CANDIDATAS:
            if veterinaria.esta_disponible() and veterinaria.tiene_guardia_24h:
                distancia = veterinaria.calcular_distancia_km(
                    datos.latitud_cliente,
                    datos.longitud_cliente,
                )
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    veterinaria_mas_cercana = veterinaria

    alerta_enviada = False
    id_alerta_generada = None
    estado_envio = None
    mensaje_texto = None
    tiempo_arribo = None

    if consulta.nivel_urgencia == "ALTA" and veterinaria_mas_cercana:
        contador_alertas += 1
        alerta = AlertaUrgencia(
            id_alerta=contador_alertas,
            consulta_triaje=consulta,
            veterinaria_destino=veterinaria_mas_cercana,
            servicio_notificacion=notificador,
            id_triaje=consulta.id_triaje,
            id_veterinaria_asignada=veterinaria_mas_cercana.id_veterinaria,
            tiempo_estimado_arribo_min=max(10, int(distancia_minima * 3)),
        )
        alerta.transmitir()
        alerta_enviada = True
        id_alerta_generada = alerta.id_alerta
        estado_envio = alerta.estado
        mensaje_texto = alerta.mensaje_texto
        tiempo_arribo = alerta.tiempo_estimado_arribo_min

    return TriajeResponse(
        paciente=paciente.nombre,
        sintomas_ingresados=datos.sintomas,
        nivel_urgencia=consulta.nivel_urgencia,
        diagnostico_preliminar=consulta.diagnostico_preliminar,
        especialidad_sugerida=consulta.especialidad_sugerida,
        primeros_auxilios=consulta.primeros_auxilios,
        veterinaria_cercana=(
            veterinaria_mas_cercana.nombre
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
        tiempo_estimado_arribo_min=tiempo_arribo,
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
