from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class MascotaCreate(BaseModel):
    id_cliente: int = Field(
        ..., example=1, description="ID del cliente logueado"
    )
    nombre: str = Field(..., example="Mimi")
    especie: str = Field(..., example="Felino")
    raza: str = Field(..., example="Siamés")
    sexo: str = Field(..., example="Hembra")
    peso_kg: float = Field(..., example=3.8)
    fecha_nacimiento: Optional[date] = Field(
        default=None, example="2021-05-10"
    )


class MascotaResponse(BaseModel):
    id_mascota: int
    id_cliente: int
    nombre: str
    especie: str
    raza: str
    sexo: str
    peso_kg: float
    edad_estimada: str