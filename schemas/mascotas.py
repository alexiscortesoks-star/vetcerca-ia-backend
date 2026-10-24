from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class MascotaCreate(BaseModel):
    username_cliente: str = Field(..., example="maria_g2024")
    nombre: str = Field(..., example="Mimi")
    especie: str = Field(..., example="Felino")
    raza: str = Field(..., example="Siamés")
    sexo: str = Field(..., example="Hembra")
    peso_kg: float = Field(..., example=3.8)
    fecha_nacimiento: Optional[date] = Field(
        default=None, example="2021-05-10"
    )
    foto_url: Optional[str] = Field(
        default="https://ejemplo.com/fotos/mimi.jpg",
        description="URL o ruta de la foto de la mascota",
    )


class MascotaResponse(BaseModel):
    id_mascota: int
    username_cliente: str
    nombre: str
    especie: str
    raza: str
    sexo: str
    peso_kg: float
    edad_estimada: str
    foto_url: Optional[str] = None