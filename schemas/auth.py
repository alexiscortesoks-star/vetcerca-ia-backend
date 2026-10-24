from typing import Optional

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
    avatar_url: Optional[str] = "https://ejemplo.com/avatars/maria.jpg"
    token_sesion: str


class LoginVeterinariaRequest(BaseModel):
    usuario: str = Field(..., example="admin")
    password: str = Field(..., example="1234")


class LoginVeterinariaResponse(BaseModel):
    mensaje: str
    id_veterinaria: int
    nombre_veterinaria: str
    token_sesion: str


class PerfilVeterinariaResponse(BaseModel):
    id_veterinaria: int
    nombre: str
    direccion: str
    telefono_guardia: str
    es_24hs: bool
    estado_disponibilidad: str