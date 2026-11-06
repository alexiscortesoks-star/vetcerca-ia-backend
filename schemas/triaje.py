from typing import Optional, Dict
from pydantic import BaseModel, Field


class TriajeRequest(BaseModel):
    id_cliente: Optional[int] = Field(default=1, example=1)
    nombre_mascota: str = Field(..., example="Mimi")
    sintomas: Optional[str] = Field(
        default=None, example="Dificultad respiratoria y decaimiento severo"
    )
    # Variables clínicas requeridas por el TPI de Ciencia de Datos
    especie: Optional[str] = Field(default="Canino", example="Felino")
    sintoma_principal: Optional[str] = Field(
        default=None, example="Dificultad respiratoria severa / Cianosis"
    )
    tiempo_evolucion_hs: Optional[float] = Field(default=2.0, example=2.5)
    estado_conciencia: Optional[str] = Field(
        default="Alerta", example="Deprimido"
    )
    presencia_hemorragia: Optional[int] = Field(default=0, example=0)
    
    # Geolocalización y zonificación barrial en CABA
    barrio: Optional[str] = Field(default="Palermo", example="Palermo")
    latitud_cliente: Optional[float] = Field(
        default=-34.6037, example=-34.6037
    )
    longitud_cliente: Optional[float] = Field(
        default=-58.3816, example=-58.3816
    )


class TriajeResponse(BaseModel):
    paciente: str
    especie: Optional[str] = "Canino"
    sintomas_ingresados: str
    nivel_urgencia: str  # "Baja", "Moderada", "Alta", "Emergencia Crítica"
    confianza_prediccion: Optional[float] = None
    probabilidades: Optional[Dict[str, float]] = None
    diagnostico_preliminar: Optional[str] = None
    especialidad_sugerida: str
    primeros_auxilios: str
    
    # Clínica asignada y geolocalización Haversine
    veterinaria_cercana: Optional[str] = None
    direccion_veterinaria: Optional[str] = None
    telefono_veterinaria: Optional[str] = None
    distancia_km: Optional[float] = None
    tiempo_estimado_arribo_min: Optional[int] = None
    
    # Información de zonificación y contingencia barrial
    barrio: Optional[str] = None
    contingencia_activada: bool = False
    motivo_contingencia: Optional[str] = None
    barrio_derivacion: Optional[str] = None
    
    # Despacho de alerta en tiempo real a guardia
    alerta_despachada: bool = False
    id_alerta: Optional[int] = None
    estado_notificacion: Optional[str] = None
    mensaje_alerta: Optional[str] = None
    
    # Coordenadas geográficas GPS
    latitud_cliente: Optional[float] = None
    longitud_cliente: Optional[float] = None
    latitud_veterinaria: Optional[float] = None
    longitud_veterinaria: Optional[float] = None
