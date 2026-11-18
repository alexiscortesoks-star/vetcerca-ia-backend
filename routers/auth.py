import os
import secrets
import sqlite3
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status

from models.usuarios import Cliente, hashear_contrasena, verificar_contrasena
from models.veterinarias import Veterinaria
from schemas.auth import (
    LoginRequest,
    LoginUnificadoResponse,
    LoginVeterinariaRequest,
    LoginVeterinariaResponse,
    PerfilVeterinariaResponse,
    RegistroUsuarioRequest,
)
from utils.usuarios_store import (
    actualizar_estado_solicitud_veterinaria,
    cargar_clientes_registrados,
    cargar_solicitudes_veterinarias,
    guardar_cliente_registrado,
    guardar_solicitud_veterinaria,
    listar_solicitudes_veterinarias_pendientes,
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


def _crear_veterinaria_registrada(datos: dict) -> Veterinaria:
    return Veterinaria(
        id_veterinaria=datos["id_veterinaria"],
        nombre=datos["nombre_veterinaria"],
        direccion=datos["direccion_veterinaria"],
        latitud=0.0,
        longitud=0.0,
        tiene_guardia_24h=False,
        telefono_guardia=datos["telefono"],
        barrio=datos["barrio"],
        especialidades=datos["especialidad_principal"],
    )


CLIENTES_DB_OBJ: list[Cliente] = [
    # Cuenta de demostración con la mascota Rocky asociada al id 3.
    Cliente(
        id_usuario=3,
        username="demo",
        email="demo@vetcerca.com",
        contrasena_hash="1234",
        direccion="Av. Santa Fe 3200, Palermo, CABA",
        latitud=-34.588,
        longitud=-58.410,
        telefono="1144445555",
        nombre_apellido="Cliente Demo",
        avatar_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&q=80",
    ),
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

for registro in cargar_clientes_registrados():
    CLIENTES_DB_OBJ.append(
        Cliente(
            id_usuario=registro["id_cliente"],
            username=registro["username"],
            email=registro["email"],
            contrasena_hash=registro["password_hash"],
            telefono=registro["telefono"],
            nombre_apellido=registro["nombre_apellido"],
        )
    )

SOLICITUDES_VETERINARIAS = cargar_solicitudes_veterinarias()
VETERINARIAS_REGISTRADAS = {
    registro["id_veterinaria"]: _crear_veterinaria_registrada(registro)
    for registro in SOLICITUDES_VETERINARIAS
    if registro["estado"] == "APROBADA"
}

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
SESIONES_ADMINISTRADORES: set[str] = set()
USUARIO_ADMINISTRADOR = os.getenv("VETCERCA_ADMIN_USER", "admin")
PASSWORD_ADMINISTRADOR = hashear_contrasena(
    os.getenv("VETCERCA_ADMIN_PASSWORD", "1234")
)
USUARIO_VETERINARIA = os.getenv("VETCERCA_VET_ADMIN_USER", "admin_vet")
PASSWORD_VETERINARIA = os.getenv("VETCERCA_VET_ADMIN_PASSWORD", "1234")


def obtener_veterinaria_por_id(id_veterinaria: int) -> Optional[Veterinaria]:
    if id_veterinaria == VETERINARIA_DEMO.id_veterinaria:
        return VETERINARIA_DEMO
    return VETERINARIAS_REGISTRADAS.get(id_veterinaria)


def cliente_tiene_sesion(id_cliente: int) -> bool:
    return any(
        usuario["id_cliente"] == id_cliente
        and usuario["username"] in SESIONES_ACTIVAS
        for usuario in USUARIOS_DB
    )


@router.post(
    "/registro",
    status_code=status.HTTP_201_CREATED,
)
def registrar_usuario(datos: RegistroUsuarioRequest) -> dict[str, object]:
    username = datos.username.strip().lower()
    email = str(datos.email).strip().lower()
    nombre_apellido = datos.nombre_apellido.strip()

    usernames_reservados = {
        USUARIO_ADMINISTRADOR.lower(),
        USUARIO_VETERINARIA.lower(),
        "admin_vet",
        "veterinaria",
    }
    if username in usernames_reservados:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese nombre de usuario está reservado.",
        )

    if any(
        cliente.username.casefold() == username.casefold()
        or cliente.email.casefold() == email.casefold()
        for cliente in CLIENTES_DB_OBJ
    ) or any(
        registro["username"].casefold() == username.casefold()
        or registro["email"].casefold() == email.casefold()
        for registro in SOLICITUDES_VETERINARIAS
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese usuario o email ya está registrado.",
        )

    password_hash = hashear_contrasena(datos.password)
    if datos.rol == "veterinaria":
        matricula = datos.matricula_profesional
        especialidad = datos.especialidad_principal
        nombre_veterinaria = datos.nombre_veterinaria
        direccion_veterinaria = datos.direccion_veterinaria
        barrio = datos.barrio
        if not all(
            (matricula, especialidad, nombre_veterinaria, direccion_veterinaria, barrio)
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Completá todos los datos profesionales requeridos.",
            )
        try:
            id_veterinaria = guardar_solicitud_veterinaria(
                id_minimo=max(
                    (registro["id_veterinaria"] for registro in SOLICITUDES_VETERINARIAS),
                    default=VETERINARIA_DEMO.id_veterinaria,
                ),
                username=username,
                email=email,
                nombre_apellido=nombre_apellido,
                password_hash=password_hash,
                telefono=datos.telefono.strip(),
                matricula_profesional=matricula.strip(),
                especialidad_principal=especialidad.strip(),
                nombre_veterinaria=nombre_veterinaria.strip(),
                direccion_veterinaria=direccion_veterinaria.strip(),
                barrio=barrio.strip(),
            )
        except sqlite3.IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ese usuario o email ya está registrado.",
            ) from error

        SOLICITUDES_VETERINARIAS.append(
            {
                "id_veterinaria": id_veterinaria,
                "username": username,
                "email": email,
                "nombre_apellido": nombre_apellido,
                "password_hash": password_hash,
                "telefono": datos.telefono.strip(),
                "matricula_profesional": matricula.strip(),
                "especialidad_principal": especialidad.strip(),
                "nombre_veterinaria": nombre_veterinaria.strip(),
                "direccion_veterinaria": direccion_veterinaria.strip(),
                "barrio": barrio.strip(),
                "estado": "PENDIENTE",
            }
        )
        return {
            "tipo_usuario": "veterinaria",
            "estado_solicitud": "PENDIENTE",
            "mensaje": "Solicitud enviada. Vas a poder ingresar cuando sea aprobada.",
        }

    try:
        id_cliente = guardar_cliente_registrado(
            id_minimo=max(cliente.id_usuario for cliente in CLIENTES_DB_OBJ),
            username=username,
            email=email,
            nombre_apellido=nombre_apellido,
            password_hash=password_hash,
            telefono=datos.telefono.strip(),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario o email ya está registrado.",
        ) from error

    cliente = Cliente(
        id_usuario=id_cliente,
        username=username,
        email=email,
        contrasena_hash=password_hash,
        telefono=datos.telefono.strip(),
        nombre_apellido=nombre_apellido,
    )
    CLIENTES_DB_OBJ.append(cliente)
    USUARIOS_DB.append(
        {
            "id_cliente": cliente.id_usuario,
            "nombre": cliente.nombre_apellido,
            "username": cliente.username,
            "email": cliente.email,
            "password": cliente.contrasena_hash,
            "cliente_obj": cliente,
        }
    )
    SESIONES_ACTIVAS.add(cliente.username)

    return {
        "tipo_usuario": "cliente",
        "mensaje": "Cuenta creada correctamente.",
        "id_cliente": cliente.id_usuario,
        "username": cliente.username,
        "nombre_cliente": cliente.nombre_apellido,
        "email": cliente.email,
        "avatar_url": cliente.avatar_url,
        "token_sesion": f"token-sesion-{cliente.username}",
    }


@router.post("/login", response_model=LoginUnificadoResponse)
def iniciar_sesion(datos: LoginRequest) -> LoginUnificadoResponse:
    """
    Autentica clientes, veterinarias y administradores desde el formulario unificado.
    """
    identificador = datos.usuario_o_email.strip().lower()
    rol_solicitado = (getattr(datos, "rol", None) or "").strip().lower()

    if (
        identificador == USUARIO_ADMINISTRADOR.lower()
        and verificar_contrasena(datos.password, PASSWORD_ADMINISTRADOR)
    ):
        token = secrets.token_urlsafe(32)
        SESIONES_ADMINISTRADORES.add(token)
        return LoginUnificadoResponse(
            tipo_usuario="administrador",
            mensaje="Inicio de sesión administrativo exitoso.",
            token_sesion=token,
        )

    # Si se pide explícitamente rol veterinaria o usa los alias exclusivos de veterinaria:
    if rol_solicitado == "veterinaria" or identificador in ["admin_vet", "veterinaria"]:
        if datos.password == PASSWORD_VETERINARIA:
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

    registro_veterinario = next(
        (
            registro
            for registro in SOLICITUDES_VETERINARIAS
            if identificador
            in (registro["username"].lower(), registro["email"].lower())
        ),
        None,
    )
    if registro_veterinario and verificar_contrasena(
        datos.password,
        registro_veterinario["password_hash"],
    ):
        if registro_veterinario["estado"] != "APROBADA":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "La solicitud veterinaria sigue pendiente de aprobación."
                    if registro_veterinario["estado"] == "PENDIENTE"
                    else "La solicitud veterinaria fue rechazada."
                ),
            )
        veterinaria = obtener_veterinaria_por_id(
            registro_veterinario["id_veterinaria"]
        )
        if veterinaria is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo cargar el perfil de la veterinaria.",
            )
        token = secrets.token_urlsafe(32)
        SESIONES_VETERINARIAS[token] = veterinaria.id_veterinaria
        return LoginUnificadoResponse(
            tipo_usuario="veterinaria",
            mensaje="Inicio de sesión veterinario exitoso.",
            id_veterinaria=veterinaria.id_veterinaria,
            nombre_veterinaria=veterinaria.nombre_fantasia,
            token_sesion=token,
        )

    # Autenticación de clientes
    for cliente in CLIENTES_DB_OBJ:
        if cliente.verificar_credenciales(datos.usuario_o_email, datos.password):
            SESIONES_ACTIVAS.add(cliente.username)
            return LoginUnificadoResponse(
                tipo_usuario="cliente",
                mensaje="Inicio de sesión exitoso como cliente.",
                id_cliente=cliente.id_usuario,
                username=cliente.username,
                nombre_cliente=cliente.nombre_apellido,
                email=cliente.email,
                avatar_url=cliente.avatar_url or "https://ejemplo.com/avatars/maria.jpg",
                token_sesion=f"token-sesion-{cliente.username}",
            )

    # Acceso compatible con la cuenta veterinaria demo configurada por entorno
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
    usuario_ingresado = datos.usuario.strip().lower()
    if (
        usuario_ingresado not in [USUARIO_VETERINARIA.lower(), "admin_vet", "veterinaria"]
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


def _verificar_sesion_administrador(
    authorization: Optional[str],
) -> None:
    esquema, _, token = (authorization or "").partition(" ")
    if esquema.lower() != "bearer" or token not in SESIONES_ADMINISTRADORES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Iniciá sesión como administrador para continuar.",
        )


@router.get("/administracion/solicitudes-veterinarias")
def listar_solicitudes_veterinarias(
    authorization: Optional[str] = Header(default=None),
) -> list[dict[str, object]]:
    _verificar_sesion_administrador(authorization)
    return listar_solicitudes_veterinarias_pendientes()


def _resolver_solicitud_veterinaria(
    id_veterinaria: int,
    estado: str,
) -> dict[str, str]:
    registro = next(
        (
            solicitud
            for solicitud in SOLICITUDES_VETERINARIAS
            if solicitud["id_veterinaria"] == id_veterinaria
        ),
        None,
    )
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la solicitud veterinaria.",
        )
    if registro["estado"] != "PENDIENTE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya fue resuelta.",
        )
    if not actualizar_estado_solicitud_veterinaria(id_veterinaria, estado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya fue resuelta.",
        )

    registro["estado"] = estado
    if estado == "APROBADA":
        VETERINARIAS_REGISTRADAS[id_veterinaria] = _crear_veterinaria_registrada(
            registro
        )
    return {"mensaje": f"Solicitud {estado.lower()} correctamente."}


@router.post("/administracion/solicitudes-veterinarias/{id_veterinaria}/aprobar")
def aprobar_solicitud_veterinaria(
    id_veterinaria: int,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, str]:
    _verificar_sesion_administrador(authorization)
    return _resolver_solicitud_veterinaria(id_veterinaria, "APROBADA")


@router.post("/administracion/solicitudes-veterinarias/{id_veterinaria}/rechazar")
def rechazar_solicitud_veterinaria(
    id_veterinaria: int,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, str]:
    _verificar_sesion_administrador(authorization)
    return _resolver_solicitud_veterinaria(id_veterinaria, "RECHAZADA")


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
    if esquema.lower() != "bearer" or id_veterinaria is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Iniciá sesión como veterinaria para acceder al portal.",
        )

    veterinaria = obtener_veterinaria_por_id(id_veterinaria)
    if veterinaria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el perfil de la veterinaria.",
        )
    return PerfilVeterinariaResponse(
        id_veterinaria=veterinaria.id_veterinaria,
        nombre=veterinaria.nombre_fantasia,
        direccion=veterinaria.direccion,
        telefono_guardia=veterinaria.telefono_guardia,
        es_24hs=veterinaria.es_24hs,
        estado_disponibilidad=veterinaria.estado_disponibilidad,
    )
