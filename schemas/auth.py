from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    usuario_o_email: str = Field(
        ...,
        example="maria_g2024",
        description=(
            "Ingresá tu Nombre de Usuario alfanumérico "
            "(ej: maria_g2024) O tu Email (ej: maria@email.com)"
        ),
    )
    password: str = Field(..., example="123456")


class LoginResponse(BaseModel):
    mensaje: str
    id_cliente: int
    username: str
    nombre_cliente: str
    email: str
    token_sesion: str