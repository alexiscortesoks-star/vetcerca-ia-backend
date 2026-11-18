from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class RegistroUsuarioRequest(BaseModel):
    rol: Literal["cliente", "veterinaria"]
    nombre_apellido: str = Field(min_length=2, max_length=100)
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    telefono: str = Field(default="", max_length=30)
    matricula_profesional: str = Field(default="", max_length=50)
    especialidad_principal: str = Field(default="", max_length=100)
    nombre_veterinaria: str = Field(default="", max_length=120)
    direccion_veterinaria: str = Field(default="", max_length=200)
    barrio: str = Field(default="", max_length=80)

    @field_validator("nombre_apellido")
    @classmethod
    def validar_nombre_apellido(cls, valor: str) -> str:
        nombre = valor.strip()
        if len(nombre) < 2:
            raise ValueError("Ingresá tu nombre y apellido.")
        return nombre

    @model_validator(mode="after")
    def validar_datos_profesionales(self) -> "RegistroUsuarioRequest":
        if self.rol == "veterinaria":
            campos = (
                self.matricula_profesional,
                self.especialidad_principal,
                self.nombre_veterinaria,
                self.direccion_veterinaria,
                self.barrio,
            )
            if any(not valor or not valor.strip() for valor in campos):
                raise ValueError(
                    "Completá matrícula, especialidad y los datos de la veterinaria."
                )
        return self


class LoginRequest(BaseModel):
    usuario_o_email: str = Field(
        ...,
        json_schema_extra={"example": "admin"},
        description=(
            "Ingresá tu usuario de cliente, email o usuario de veterinaria."
        ),
    )
    password: str = Field(..., json_schema_extra={"example": "1234"})
    rol: Optional[str] = Field(
        default=None,
        json_schema_extra={"example": "cliente"},
    )


class LoginResponse(BaseModel):
    mensaje: str
    id_cliente: int
    username: str
    nombre_cliente: str
    email: str
    avatar_url: Optional[str] = "https://ejemplo.com/avatars/maria.jpg"
    token_sesion: str


class LoginUnificadoResponse(BaseModel):
    tipo_usuario: Literal["cliente", "veterinaria", "administrador"]
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
    usuario: str = Field(..., json_schema_extra={"example": "admin"})
    password: str = Field(..., json_schema_extra={"example": "1234"})


class LoginVeterinariaResponse(BaseModel):
    mensaje: str
    id_veterinaria: int
    nombre_veterinaria: str
    token_sesion: str


class PerfilVeterinariaResponse(BaseModel):
    id_veterinaria: int
    nombre: str
    direccion: str
    telefono_guardia: Optional[str] = None
    es_24hs: bool
    estado_disponibilidad: str
