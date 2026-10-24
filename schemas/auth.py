from typing import Literal, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    usuario_o_email: str = Field(
        ...,
        example="maria_g2024",
        description=(
            "Ingresá tu usuario de cliente, email o usuario de veterinaria."
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


class LoginUnificadoResponse(BaseModel):
    tipo_usuario: Literal["cliente", "veterinaria"]
    mensaje: str
    token_sesion: str
    id_cliente: Optional[int] = None
    username: Optional[str] = None
    nombre_cliente: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    id_veterinaria: Optional[int] = None
    nombre_veterinaria: Optional[str] = None


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