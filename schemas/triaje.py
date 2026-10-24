from typing import Optional

from pydantic import BaseModel, Field


class TriajeRequest(BaseModel):
    id_cliente: Optional[int] = Field(default=1, example=1)
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
    direccion_veterinaria: Optional[str] = None
    telefono_veterinaria: Optional[str] = None
    distancia_km: Optional[float] = None
    alerta_despachada: bool = False
    id_alerta: Optional[int] = None
    estado_notificacion: Optional[str] = None
    mensaje_alerta: Optional[str] = None
    latitud_cliente: Optional[float] = None
    longitud_cliente: Optional[float] = None
    latitud_veterinaria: Optional[float] = None
    longitud_veterinaria: Optional[float] = None