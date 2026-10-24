from fastapi import APIRouter, HTTPException, status

from schemas.auth import LoginRequest, LoginResponse


router = APIRouter(prefix="/auth", tags=["Autenticación y Sesión"])

USUARIOS_DB = [
    {
        "id_cliente": 1,
        "nombre": "María González",
        "username": "maria_g2024",
        "email": "maria.gonzalez@email.com",
        "password": "123456",
    },
    {
        "id_cliente": 2,
        "nombre": "Juan Pérez",
        "username": "jperez99",
        "email": "juan.perez@email.com",
        "password": "123456",
    },
]

SESIONES_ACTIVAS = set()


def cliente_tiene_sesion(id_cliente: int) -> bool:
    return any(
        usuario["id_cliente"] == id_cliente
        and usuario["username"] in SESIONES_ACTIVAS
        for usuario in USUARIOS_DB
    )


@router.post("/login", response_model=LoginResponse)
def iniciar_sesion(datos: LoginRequest) -> LoginResponse:
    """Permite iniciar sesión con el nombre de usuario o el email."""
    identificador = datos.usuario_o_email.strip().lower()

    for usuario in USUARIOS_DB:
        if (
            identificador
            in (usuario["username"].lower(), usuario["email"].lower())
            and usuario["password"] == datos.password
        ):
            SESIONES_ACTIVAS.add(usuario["username"])
            return LoginResponse(
                mensaje="Inicio de sesión exitoso",
                id_cliente=usuario["id_cliente"],
                username=usuario["username"],
                nombre_cliente=usuario["nombre"],
                email=usuario["email"],
                token_sesion=f"token-sesion-{usuario['username']}",
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas (usuario/email o contraseña inválidos)",
    )