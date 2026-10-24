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

HISTORIALES_DB = {
    1: [
        {
            "fecha": "2024-09-15",
            "motivo": "Control anual y vacunación",
            "diagnostico": (
                "Paciente felino saludable. Se aplica vacuna Triple Felina."
            ),
            "veterinario": "Dr. Roberto Gómez (MP 4512)",
        },
        {
            "fecha": "2024-03-10",
            "motivo": "Consulta por inapetencia",
            "diagnostico": (
                "Indigestión leve. Tratamiento con dieta blanda por 48 hs."
            ),
            "veterinario": "Dra. Laura Martínez (MP 5890)",
        },
    ]
}


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
        fecha_nacimiento=mascota.fecha_nacimiento,
        foto_url=mascota.foto_url,
    )


@router.get(
    "/cliente/{identificador_cliente}", response_model=List[MascotaResponse]
)
def obtener_mascotas_por_cliente(
    identificador_cliente: str,
) -> List[MascotaResponse]:
    usuario = next(
        (
            usuario
            for usuario in USUARIOS_DB
            if usuario["username"].lower() == identificador_cliente.lower()
        ),
        None,
    )
    if usuario is None and identificador_cliente.isdecimal():
        id_cliente = int(identificador_cliente)
        usuario = next(
            (
                usuario
                for usuario in USUARIOS_DB
                if usuario["id_cliente"] == id_cliente
            ),
            None,
        )

    if usuario is None or not cliente_tiene_sesion(usuario["id_cliente"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Acceso denegado: Debe iniciar sesión previamente "
                "para ver sus mascotas."
            ),
        )

    id_cliente = usuario["id_cliente"]

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


@router.put("/{id_mascota}", response_model=MascotaResponse)
def actualizar_mascota(
    id_mascota: int, datos: MascotaCreate
) -> MascotaResponse:
    usuario = next(
        (
            usuario
            for usuario in USUARIOS_DB
            if usuario["username"].lower() == datos.username_cliente.lower()
        ),
        None,
    )
    if usuario is None or not cliente_tiene_sesion(usuario["id_cliente"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso denegado: se requiere una sesión activa.",
        )

    item = next(
        (
            item
            for item in MASCOTAS_DB
            if item["mascota"].id_mascota == id_mascota
            and item["id_cliente"] == usuario["id_cliente"]
        ),
        None,
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mascota no encontrada o no pertenece al usuario.",
        )

    mascota = item["mascota"]
    mascota.nombre = datos.nombre
    mascota.peso_kg = datos.peso_kg
    mascota.sexo = datos.sexo
    mascota.raza = Raza(
        mascota.raza.id_raza,
        datos.raza,
        Especie(
            mascota.raza.especie.id_especie,
            datos.especie,
            mascota.raza.especie.es_exotica,
        ),
    )
    if datos.fecha_nacimiento is not None:
        mascota.fecha_nacimiento = datos.fecha_nacimiento
    if datos.foto_url is not None:
        mascota.foto_url = datos.foto_url

    return _crear_respuesta(mascota, usuario["id_cliente"])


@router.delete("/{id_mascota}")
def eliminar_mascota(id_mascota: int, username_cliente: str) -> dict[str, str]:
    usuario = next(
        (
            usuario
            for usuario in USUARIOS_DB
            if usuario["username"].lower() == username_cliente.lower()
        ),
        None,
    )
    if usuario is None or not cliente_tiene_sesion(usuario["id_cliente"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso denegado: se requiere una sesión activa.",
        )

    for index, item in enumerate(MASCOTAS_DB):
        if (
            item["mascota"].id_mascota == id_mascota
            and item["id_cliente"] == usuario["id_cliente"]
        ):
            mascota_eliminada = MASCOTAS_DB.pop(index)["mascota"]
            return {
                "mensaje": (
                    f"La mascota '{mascota_eliminada.nombre}' "
                    "fue eliminada correctamente."
                )
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Mascota no encontrada o no pertenece al usuario.",
    )


@router.get("/{id_mascota}/historial")
def obtener_historial_medico(
    id_mascota: int, username_cliente: str
) -> dict[str, object]:
    usuario = next(
        (
            usuario
            for usuario in USUARIOS_DB
            if usuario["username"].lower() == username_cliente.lower()
        ),
        None,
    )
    if usuario is None or not cliente_tiene_sesion(usuario["id_cliente"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso denegado: se requiere una sesión activa.",
        )

    item = next(
        (
            item
            for item in MASCOTAS_DB
            if item["mascota"].id_mascota == id_mascota
            and item["id_cliente"] == usuario["id_cliente"]
        ),
        None,
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mascota no encontrada o no pertenece al usuario.",
        )

    historial = HISTORIALES_DB.get(id_mascota, [])
    return {
        "id_mascota": id_mascota,
        "total_atenciones": len(historial),
        "historial": historial,
    }