from datetime import date
from typing import List, Optional


class Especie:
    def __init__(
        self, id_especie: int, nombre_especie: str, es_exotica: bool = False
    ) -> None:
        self.id_especie = id_especie
        self.nombre_especie = nombre_especie
        self.es_exotica = es_exotica


class Raza:
    def __init__(self, id_raza: int, nombre_raza: str, especie: Especie) -> None:
        self.id_raza = id_raza
        self.nombre_raza = nombre_raza
        self.especie = especie


class HistorialMedico:
    def __init__(
        self,
        id_historial: int,
        fecha: date,
        diagnostico: str,
        tratamiento: str,
        observaciones: str,
        veterinaria_emisora=None,
        veterinario_firmante=None,
    ) -> None:
        self.id_historial = id_historial
        self.fecha = fecha
        self.diagnostico = diagnostico
        self.tratamiento = tratamiento
        self.observaciones = observaciones
        self.veterinaria_emisora = veterinaria_emisora
        self.veterinario_firmante = veterinario_firmante

    def es_modificable_por(self, usuario_vet) -> bool:
        return self.veterinario_firmante == usuario_vet or self.veterinaria_emisora == getattr(
            usuario_vet, "veterinaria", None
        )


class Mascota:
    def __init__(
        self,
        id_mascota: int,
        nombre: str,
        fecha_nacimiento: date,
        sexo: str,
        peso_kg: float,
        raza: Raza,
        foto_url: Optional[str] = None,
    ) -> None:
        self.id_mascota = id_mascota
        self.nombre = nombre
        self.fecha_nacimiento = fecha_nacimiento
        self.sexo = sexo
        self._peso_kg = peso_kg
        self.raza = raza
        self.foto_url = (
            foto_url or "https://via.placeholder.com/150?text=Mascota"
        )
        self._historial_medico: List[HistorialMedico] = []

    @property
    def peso_kg(self) -> float:
        return self._peso_kg

    @peso_kg.setter
    def peso_kg(self, nuevo_peso: float) -> None:
        if nuevo_peso > 0:
            self._peso_kg = nuevo_peso

    def es_exotica(self) -> bool:
        return self.raza.especie.es_exotica

    def obtener_edad_formateada(self) -> str:
        hoy = date.today()
        edad_anios = hoy.year - self.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (
            self.fecha_nacimiento.month,
            self.fecha_nacimiento.day,
        ):
            edad_anios -= 1
        return f"{edad_anios} años" if edad_anios else "Menos de un año"

    def agregar_historial(self, historial: HistorialMedico) -> None:
        self._historial_medico.append(historial)