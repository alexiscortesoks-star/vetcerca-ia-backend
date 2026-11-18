from typing import Literal, Optional

from pydantic import BaseModel, Field


class EvolucionClinicaRequest(BaseModel):
    motivo: str = Field(min_length=3, max_length=300)
    diagnostico: str = Field(min_length=3, max_length=1000)
    tratamiento: str = Field(min_length=3, max_length=1000)
    observaciones: Optional[str] = Field(default=None, max_length=2000)


class EstadoAlertaRequest(BaseModel):
    estado: Literal["EN_ATENCION", "RESUELTA"]
