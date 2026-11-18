from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, status

from Services.alertas_veterinaria import (
    ALERTAS_VETERINARIAS,
    MASCOTAS_POR_ALERTA,
    generar_id_alerta,
    registrar_alerta_veterinaria,
)
from models.mascotas import HistorialClinico
from routers.auth import SESIONES_VETERINARIAS, USUARIOS_DB, VETERINARIA_DEMO
from routers.mascotas import HISTORIALES_DB, MASCOTAS_DB
from schemas.veterinaria import EstadoAlertaRequest, EvolucionClinicaRequest


router = APIRouter(prefix="/veterinaria", tags=["Portal veterinario"])


def _obtener_id_veterinaria(authorization: Optional[str]) -> int:
    esquema, _, token = (authorization or "").partition(" ")
    id_veterinaria = SESIONES_VETERINARIAS.get(token)
    if esquema.lower() != "bearer" or id_veterinaria is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Iniciá sesión como veterinaria para acceder a las alertas.",
        )
    return id_veterinaria


def _obtener_alerta_veterinaria(
    id_alerta: int, id_veterinaria: int
) -> dict[str, Any]:
    alerta = next(
        (
            item
            for item in ALERTAS_VETERINARIAS
            if item["id_alerta"] == id_alerta
            and item["id_veterinaria"] == id_veterinaria
        ),
        None,
    )
    if alerta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la alerta para esta veterinaria.",
        )
    return alerta


def _obtener_mascota(id_alerta: int, id_mascota: int):
    mascota_alerta = MASCOTAS_POR_ALERTA.get(id_alerta)
    if mascota_alerta is not None:
        return mascota_alerta

    item = next(
        (
            registro
            for registro in MASCOTAS_DB
            if registro["mascota"].id_mascota == id_mascota
        ),
        None,
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la mascota asociada a la alerta.",
        )
    return item["mascota"]


def _serializar_historial(registro: HistorialClinico) -> dict[str, str]:
    fecha = (
        registro.fecha.strftime("%Y-%m-%d")
        if hasattr(registro.fecha, "strftime")
        else str(registro.fecha)
    )
    return {
        "fecha": fecha,
        "motivo": registro.motivo,
        "diagnostico": registro.diagnostico,
        "tratamiento": registro.tratamiento,
        "observaciones": registro.observaciones,
        "veterinario": registro.veterinario_firmante,
    }


@router.get("/alertas")
def listar_alertas_veterinaria(
    authorization: Optional[str] = Header(default=None),
) -> list[dict[str, Any]]:
    id_veterinaria = _obtener_id_veterinaria(authorization)
    return [
        alerta
        for alerta in ALERTAS_VETERINARIAS
        if alerta["id_veterinaria"] == id_veterinaria
        and alerta["estado"] != "RESUELTA"
    ]


@router.get("/alertas/historial")
def listar_historial_alertas_veterinaria(
    authorization: Optional[str] = Header(default=None),
) -> list[dict[str, Any]]:
    id_veterinaria = _obtener_id_veterinaria(authorization)
    return [
        alerta
        for alerta in ALERTAS_VETERINARIAS
        if alerta["id_veterinaria"] == id_veterinaria
        and alerta["estado"] == "RESUELTA"
    ]


@router.post("/alertas/simular", status_code=status.HTTP_201_CREATED)
def simular_alerta_veterinaria(
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    id_veterinaria = _obtener_id_veterinaria(authorization)
    item_mascota = next(
        (
            item
            for item in MASCOTAS_DB
            if item["id_cliente"] == 3
        ),
        MASCOTAS_DB[0] if MASCOTAS_DB else None,
    )
    usuario = next(
        (
            item
            for item in USUARIOS_DB
            if item["id_cliente"] == item_mascota["id_cliente"]
        ),
        None,
    ) if item_mascota else None
    if item_mascota is None or usuario is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No hay datos de demostración disponibles para crear la alerta.",
        )

    mascota = item_mascota["mascota"]
    cliente = usuario["cliente_obj"]
    alerta = {
        "id_alerta": generar_id_alerta(),
        "id_triaje": 0,
        "id_veterinaria": id_veterinaria,
        "id_veterinaria_destino": id_veterinaria,
        "fecha_hora": datetime.now().isoformat(timespec="seconds"),
        "estado": "RECIBIDA",
        "es_demostracion": True,
        "nivel_urgencia": "Emergencia Crítica",
        "sintomas": (
            "Dificultad para respirar y decaimiento; "
            "simulación para demostración del panel."
        ),
        "tiempo_estimado_arribo_min": 8,
        "id_mascota": mascota.id_mascota,
        "mascota": {
            "nombre": mascota.nombre,
            "especie": mascota.raza.especie.nombre,
            "raza": mascota.raza.nombre,
            "sexo": mascota.sexo,
            "edad": mascota.calcular_edad_formateada(),
            "peso_kg": mascota.peso_kg,
        },
        "tutor": {
            "id_cliente": usuario["id_cliente"],
            "nombre": cliente.nombre_apellido,
            "username": usuario["username"],
            "email": cliente.email,
            "telefono": cliente.telefono,
        },
        "veterinaria": {
            "nombre": VETERINARIA_DEMO.nombre_fantasia,
            "direccion": VETERINARIA_DEMO.direccion,
            "telefono": VETERINARIA_DEMO.telefono_guardia,
        },
    }
    registrar_alerta_veterinaria(alerta, mascota)
    return alerta


@router.get("/alertas/{id_alerta}")
def obtener_alerta_veterinaria(
    id_alerta: int,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    id_veterinaria = _obtener_id_veterinaria(authorization)
    return _obtener_alerta_veterinaria(id_alerta, id_veterinaria)


@router.patch("/alertas/{id_alerta}/estado")
def actualizar_estado_alerta(
    id_alerta: int,
    datos: EstadoAlertaRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    id_veterinaria = _obtener_id_veterinaria(authorization)
    alerta = _obtener_alerta_veterinaria(id_alerta, id_veterinaria)
    alerta["estado"] = datos.estado
    alerta["actualizada_en"] = datetime.now().isoformat(timespec="seconds")
    return alerta


@router.get("/alertas/{id_alerta}/historia")
def obtener_historia_alerta(
    id_alerta: int,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    id_veterinaria = _obtener_id_veterinaria(authorization)
    alerta = _obtener_alerta_veterinaria(id_alerta, id_veterinaria)
    mascota = _obtener_mascota(id_alerta, alerta["id_mascota"])
    registros = getattr(mascota, "_historial_clinico", [])
    esta_registrada = any(item["mascota"] is mascota for item in MASCOTAS_DB)
    if registros:
        historia = [_serializar_historial(registro) for registro in registros]
    elif esta_registrada:
        historia = HISTORIALES_DB.get(alerta["id_mascota"], [])
    else:
        historia = []
    return {
        "id_mascota": alerta["id_mascota"],
        "nombre_mascota": mascota.nombre,
        "total_atenciones": len(historia),
        "historial": historia,
    }


@router.post("/alertas/{id_alerta}/historia", status_code=status.HTTP_201_CREATED)
def agregar_evolucion_alerta(
    id_alerta: int,
    datos: EvolucionClinicaRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    id_veterinaria = _obtener_id_veterinaria(authorization)
    alerta = _obtener_alerta_veterinaria(id_alerta, id_veterinaria)
    mascota = _obtener_mascota(id_alerta, alerta["id_mascota"])

    registros = getattr(mascota, "_historial_clinico", [])
    nuevo_id = max(
        (getattr(registro, "id_registro", 0) for registro in registros),
        default=0,
    ) + 1
    registro = HistorialClinico(
        id_registro=nuevo_id,
        id_mascota=mascota.id_mascota,
        fecha=date.today(),
        motivo=datos.motivo,
        diagnostico=datos.diagnostico,
        tratamiento=datos.tratamiento,
        veterinario_firmante=VETERINARIA_DEMO.nombre_fantasia,
        observaciones=datos.observaciones,
        veterinaria_emisora=VETERINARIA_DEMO,
    )
    mascota.agregar_historial(registro)
    if any(item["mascota"] is mascota for item in MASCOTAS_DB):
        HISTORIALES_DB[mascota.id_mascota] = [
            _serializar_historial(item)
            for item in mascota._historial_clinico
        ]
    return _serializar_historial(registro)
