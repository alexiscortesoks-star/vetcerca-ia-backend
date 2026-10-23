from typing import Optional

from pydantic import BaseModel, Field


class TriajeRequest(BaseModel):
    nombre_mascota: str = Field(..., example="Mimi")
    sintomas: str = Field(
        ..., example="Obstrucción urológica y maullidos de dolor"
    )
    latitud_cliente: Optional[float] = Field(
        default=-34.6037, example=-34.6037
    )
    longitud_cliente: Optional[float] = Field(
        default=-58.3816, example=-58.3816
    )


class TriajeResponse(BaseModel):
    paciente: str
    sintomas_ingresados: str
    nivel_urgencia: str
    especialidad_sugerida: str
    primeros_auxilios: str
    veterinaria_cercana: Optional[str] = None
    distancia_km: Optional[float] = None