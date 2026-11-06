import os
import secrets
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status

from models.usuarios import Cliente
from models.veterinarias import Veterinaria
from schemas.auth import (
    LoginRequest,
    LoginUnificadoResponse,
    LoginVeterinariaRequest,
    LoginVeterinariaResponse,
    PerfilVeterinariaResponse,
)


router = APIRouter(prefix="/auth", tags=["Autenticación y Sesión"])

VETERINARIA_DEMO = Veterinaria(
    0,
    "Cuenta veterinaria de demostración",
    "Sin sede registrada (demo)",
    0.0,
    0.0,
    tiene_guardia_24h=False,
    telefono_guardia="No disponible",
)
VETERINARIA_DEMO.actualizar_estado_guardia("DEMO")

CLIENTES_DB_OBJ: list[Cliente] = [
    Cliente(
        id_usuario=1,
        username="maria_g2024",
        email="maria.gonzalez@email.com",
        contrasena_hash="123456",
        direccion="Av. Cabildo 1500, Belgrano, CABA",
        latitud=-34.562,
        longitud=-58.455,
        telefono="1122334455",
        nombre_apellido="María González",
        avatar_url="https://ejemplo.com/avatars/maria.jpg",
    ),
    Cliente(
        id_usuario=2,
        username="jperez99",
        email="juan.perez@email.com",
        contrasena_hash="123456",
        direccion="Av. Juramento 2500, CABA",
        latitud=-34.561,
        longitud=-58.459,
        telefono="1155667788",
        nombre_apellido="Juan Pérez",
        avatar_url="https://ejemplo.com/avatars/juan.jpg",
    ),
]

USUARIOS_DB = [
    {
        "id_cliente": c.id_usuario,
        "nombre": c.nombre_apellido,
        "username": c.username,
        "email": c.email,
        "password": c.contrasena_hash,
        "cliente_obj": c,
    }
    for c in CLIENTES_DB_OBJ
]

SESIONES_ACTIVAS = set()
SESIONES_VETERINARIAS: dict[str, int] = {}
USUARIO_VETERINARIA = os.getenv("VETCERCA_VET_ADMIN_USER", "admin")
PASSWORD_VETERINARIA = os.getenv("VETCERCA_VET_ADMIN_PASSWORD", "1234")


def cliente_tiene_sesion(id_cliente: int) -> bool:
    return any(
        usuario["id_cliente"] == id_cliente
        and usuario["username"] in SESIONES_ACTIVAS
        for usuario in USUARIOS_DB
    )


@router.post("/login", response_model=LoginUnificadoResponse)
def iniciar_sesion(datos: LoginRequest) -> LoginUnificadoResponse:
    """Autentica clientes o veterinarias desde el mismo formulario mediante POO."""
    identificador = datos.usuario_o_email.strip().lower()

    if (
        identificador == USUARIO_VETERINARIA.lower()
        and datos.password == PASSWORD_VETERINARIA
    ):
        veterinaria = VETERINARIA_DEMO
        token = secrets.token_urlsafe(32)
        SESIONES_VETERINARIAS[token] = veterinaria.id_veterinaria
        return LoginUnificadoResponse(
            tipo_usuario="veterinaria",
            mensaje="Inicio de sesión de veterinaria exitoso.",
            id_veterinaria=veterinaria.id_veterinaria,
            nombre_veterinaria=veterinaria.nombre_fantasia,
            token_sesion=token,
        )

    # Autenticación de Cliente invocando el método de POO verificar_credenciales
    for cliente in CLIENTES_DB_OBJ:
        if cliente.verificar_credenciales(datos.usuario_o_email, datos.password):
            SESIONES_ACTIVAS.add(cliente.username)
            return LoginUnificadoResponse(
                tipo_usuario="cliente",
                mensaje="Inicio de sesión exitoso",
                id_cliente=cliente.id_usuario,
                username=cliente.username,
                nombre_cliente=cliente.nombre_apellido,
                email=cliente.email,
                avatar_url=cliente.avatar_url or "https://ejemplo.com/avatars/maria.jpg",
                token_sesion=f"token-sesion-{cliente.username}",
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas (usuario/email o contraseña inválidos)",
    )


@router.post(
    "/veterinaria/login",
    response_model=LoginVeterinariaResponse,
    tags=["Acceso de Veterinarias"],
)
def iniciar_sesion_veterinaria(
    datos: LoginVeterinariaRequest,
) -> LoginVeterinariaResponse:
    """Inicia la sesión de demostración del portal veterinario."""
    if (
        datos.usuario.strip() != USUARIO_VETERINARIA
        or datos.password != PASSWORD_VETERINARIA
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña de veterinaria incorrectos.",
        )

    veterinaria = VETERINARIA_DEMO
    token = secrets.token_urlsafe(32)
    SESIONES_VETERINARIAS[token] = veterinaria.id_veterinaria
    return LoginVeterinariaResponse(
        mensaje="Inicio de sesión de veterinaria exitoso.",
        id_veterinaria=veterinaria.id_veterinaria,
        nombre_veterinaria=veterinaria.nombre_fantasia,
        token_sesion=token,
    )


@router.get(
    "/veterinaria/perfil",
    response_model=PerfilVeterinariaResponse,
    tags=["Acceso de Veterinarias"],
)
def obtener_perfil_veterinaria(
    authorization: Optional[str] = Header(default=None),
) -> PerfilVeterinariaResponse:
    esquema, _, token = (authorization or "").partition(" ")
    id_veterinaria = SESIONES_VETERINARIAS.get(token)
    if (
        esquema.lower() != "bearer"
        or id_veterinaria != VETERINARIA_DEMO.id_veterinaria
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Iniciá sesión como veterinaria para acceder al portal.",
        )

    veterinaria = VETERINARIA_DEMO
    return PerfilVeterinariaResponse(
        id_veterinaria=veterinaria.id_veterinaria,
        nombre=veterinaria.nombre_fantasia,
        direccion=veterinaria.direccion,
        telefono_guardia=veterinaria.telefono_guardia,
        es_24hs=veterinaria.es_24hs,
        estado_disponibilidad=veterinaria.estado_disponibilidad,
    )