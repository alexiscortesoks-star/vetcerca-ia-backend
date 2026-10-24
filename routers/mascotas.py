from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException, status

from models.mascotas import Especie, Mascota, Raza
from routers.auth import USUARIOS_DB, cliente_tiene_sesion
from schemas.mascotas import MascotaCreate, MascotaResponse


router = APIRouter(prefix="/mascotas", tags=["Mascotas y Pacientes"])

MASCOTAS_DB = [
    {
        "id_cliente": 1,
        "mascota": Mascota(
            1,
            "Mimi",
            date(2021, 5, 10),
            "Hembra",
            3.8,
            Raza(1, "Siamés", Especie(1, "Felino")),
        ),
    },
    {
        "id_cliente": 2,
        "mascota": Mascota(
            2,
            "Thor",
            date(2019, 8, 15),
            "Macho",
            28.0,
            Raza(2, "Ovejero Alemán", Especie(2, "Canino")),
        ),
    },
]


def _crear_respuesta(
    mascota: Mascota, id_cliente: int
) -> MascotaResponse:
    username_cliente = next(
        usuario["username"]
        for usuario in USUARIOS_DB
        if usuario["id_cliente"] == id_cliente
    )
    return MascotaResponse(
        id_mascota=mascota.id_mascota,
        username_cliente=username_cliente,
        nombre=mascota.nombre,
        especie=mascota.raza.especie.nombre_especie,
        raza=mascota.raza.nombre_raza,
        sexo=mascota.sexo,
        peso_kg=mascota.peso_kg,
        edad_estimada=mascota.obtener_edad_formateada(),
        foto_url=mascota.foto_url,
    )


@router.get(
    "/cliente/{id_cliente}", response_model=List[MascotaResponse]
)
def obtener_mascotas_por_cliente(id_cliente: int) -> List[MascotaResponse]:
    if not cliente_tiene_sesion(id_cliente):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Acceso denegado: Debe iniciar sesión previamente "
                "para ver sus mascotas."
            ),
        )

    return [
        _crear_respuesta(item["mascota"], id_cliente)
        for item in MASCOTAS_DB
        if item["id_cliente"] == id_cliente
    ]


@router.post(
    "/", response_model=MascotaResponse, status_code=status.HTTP_201_CREATED
)
def registrar_mascota(datos: MascotaCreate) -> MascotaResponse:
    usuario = next(
        (
            usuario
            for usuario in USUARIOS_DB
            if usuario["username"] == datos.username_cliente
        ),
        None,
    )
    if usuario is None or not cliente_tiene_sesion(usuario["id_cliente"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Acceso denegado: Debe iniciar sesión previamente "
                "para poder registrar una mascota."
            ),
        )

    nueva_id = max(
        (item["mascota"].id_mascota for item in MASCOTAS_DB),
        default=0,
    ) + 1
    especie = Especie(nueva_id, datos.especie)
    raza = Raza(nueva_id, datos.raza, especie)
    mascota = Mascota(
        id_mascota=nueva_id,
        nombre=datos.nombre,
        fecha_nacimiento=datos.fecha_nacimiento or date.today(),
        sexo=datos.sexo,
        peso_kg=datos.peso_kg,
        raza=raza,
        foto_url=datos.foto_url,
    )
    id_cliente = usuario["id_cliente"]
    MASCOTAS_DB.append({"id_cliente": id_cliente, "mascota": mascota})
    return _crear_respuesta(mascota, id_cliente)