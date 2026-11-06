import math
from typing import Optional, List


class Especialidad:
    def __init__(self, id_especialidad: int, nombre_especialidad: str) -> None:
        self.id_especialidad = id_especialidad
        self.nombre_especialidad = nombre_especialidad


class Veterinaria:
    def __init__(
        self,
        id_veterinaria: int,
        nombre: str,
        direccion: str,
        latitud: float,
        longitud: float,
        tiene_guardia_24h: bool = True,
        telefono_guardia: Optional[str] = None,
        horario_informado: Optional[str] = None,
        fuente_datos: Optional[str] = None,
        fuente_url: Optional[str] = None,
        atribucion_fuente: Optional[str] = None,
        estado_verificacion: str = "VERIFICADA_24HS",
        nombre_fantasia: Optional[str] = None,
        es_24hs: Optional[bool] = None,
        barrio: str = "Palermo",
        comuna: int = 14,
        nivel_complejidad: str = "Intermedio",
        especialidades: Optional[str] = None,
    ) -> None:
        self.id_veterinaria: int = id_veterinaria
        self.nombre: str = nombre or (nombre_fantasia or "")
        self.direccion: str = direccion
        self.latitud: float = latitud
        self.longitud: float = longitud
        self.tiene_guardia_24h: bool = (
            es_24hs if es_24hs is not None else tiene_guardia_24h
        )
        self.telefono_guardia: Optional[str] = telefono_guardia
        self.horario_informado: Optional[str] = (
            horario_informado
            if horario_informado
            else ("Guardia 24hs activa" if self.tiene_guardia_24h else "Horario diurno")
        )
        self.fuente_datos: Optional[str] = fuente_datos or "Catálogo Oficial CABA"
        self.fuente_url: Optional[str] = fuente_url
        self.atribucion_fuente: Optional[str] = atribucion_fuente
        self.estado_verificacion: str = estado_verificacion
        self.estado_disponibilidad: str = "DISPONIBLE"
        self.barrio: str = barrio
        self.comuna: int = comuna
        self.nivel_complejidad: str = nivel_complejidad
        self.especialidades_texto: str = especialidades or "Clínica Médica General"

    # Alias y propiedades para compatibilidad
    @property
    def nombre_fantasia(self) -> str:
        return self.nombre

    @nombre_fantasia.setter
    def nombre_fantasia(self, valor: str) -> None:
        self.nombre = valor

    @property
    def es_24hs(self) -> bool:
        return self.tiene_guardia_24h

    @es_24hs.setter
    def es_24hs(self, valor: bool) -> None:
        self.tiene_guardia_24h = valor

    def calcular_distancia_km(self, lat_origen: float, lng_origen: float) -> float:
        """
        Calcula la distancia geodésica en kilómetros entre las coordenadas de origen
        y la ubicación de esta veterinaria mediante la fórmula de Haversine.
        """
        radio_tierra_km = 6371.0

        diferencia_latitud = math.radians(self.latitud - lat_origen)
        diferencia_longitud = math.radians(self.longitud - lng_origen)
        a = (
            math.sin(diferencia_latitud / 2) ** 2
            + math.cos(math.radians(lat_origen))
            * math.cos(math.radians(self.latitud))
            * math.sin(diferencia_longitud / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(radio_tierra_km * c, 2)

    def esta_disponible(self) -> bool:
        return self.estado_disponibilidad == "DISPONIBLE"

    def actualizar_estado_guardia(self, estado: str) -> None:
        self.estado_disponibilidad = estado

    def registrar_atencion_historial(self, mascota, historial) -> None:
        historial.veterinaria_emisora = self
        mascota.agregar_historial(historial)


class VeterinariaEspecialidad:
    def __init__(
        self,
        veterinaria: Veterinaria,
        especialidad: Especialidad,
        disponible_en_guardia: bool = True,
    ) -> None:
        self.veterinaria = veterinaria
        self.especialidad = especialidad
        self.disponible_en_guardia = disponible_en_guardia
