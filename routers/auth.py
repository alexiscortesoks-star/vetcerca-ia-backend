from fastapi import APIRouter, HTTPException, status

from schemas.auth import LoginRequest, LoginResponse


router = APIRouter(prefix="/auth", tags=["Autenticación y Sesión"])

USUARIOS_DB = [
    {
        "id_cliente": 1,
        "nombre": "María González",
        "email": "maria.gonzalez@email.com",
        "password": "123456",
    },
    {
        "id_cliente": 2,
        "nombre": "Juan Pérez",
        "email": "juan.perez@email.com",
        "password": "123456",
    },
]

SESIONES_ACTIVAS = set()


@router.post("/login", response_model=LoginResponse)
def iniciar_sesion(datos: LoginRequest) -> LoginResponse:
    for usuario in USUARIOS_DB:
        if (
            usuario["email"] == datos.email
            and usuario["password"] == datos.password
        ):
            SESIONES_ACTIVAS.add(usuario["id_cliente"])
            return LoginResponse(
                mensaje="Inicio de sesión exitoso",
                id_cliente=usuario["id_cliente"],
                nombre_cliente=usuario["nombre"],
                email=usuario["email"],
                token_sesion=f"token-sesion-{usuario['id_cliente']}",
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas (email o contraseña inválidos)",
    )