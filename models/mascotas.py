from datetime import date
from typing import List, Optional


class Especie:
    def __init__(
        self,
        id_especie: int,
        nombre: str,
        es_exotico: bool = False,
        requiere_permiso_senasa: bool = False,
    ) -> None:
        self.id_especie: int = id_especie
        self.nombre: str = nombre
        self.es_exotico: bool = es_exotico
        self.requiere_permiso_senasa: bool = requiere_permiso_senasa

    # Propiedades para compatibilidad con código existente
    @property
    def nombre_especie(self) -> str:
        return self.nombre

    @nombre_especie.setter
    def nombre_especie(self, valor: str) -> None:
        self.nombre = valor

    @property
    def es_exotica(self) -> bool:
        return self.es_exotico

    @es_exotica.setter
    def es_exotica(self, valor: bool) -> None:
        self.es_exotico = valor


class Raza:
    def __init__(
        self,
        id_raza: int,
        nombre: str,
        especie: Especie,
        descripcion: str = "",
    ) -> None:
        self.id_raza: int = id_raza
        self.nombre: str = nombre
        self.especie: Especie = especie
        self.descripcion: str = descripcion

    # Propiedad para compatibilidad
    @property
    def nombre_raza(self) -> str:
        return self.nombre

    @nombre_raza.setter
    def nombre_raza(self, valor: str) -> None:
        self.nombre = valor


class HistorialClinico:
    def __init__(
        self,
        id_registro: int,
        id_mascota: int,
        fecha: date,
        motivo: str,
        diagnostico: str,
        tratamiento: str,
        veterinario_firmante: str,
        observaciones: Optional[str] = None,
        veterinaria_emisora=None,
    ) -> None:
        self.id_registro: int = id_registro
        self.id_mascota: int = id_mascota
        self.fecha: date = fecha
        self.motivo: str = motivo
        self.diagnostico: str = diagnostico
        self.tratamiento: str = tratamiento
        self.veterinario_firmante: str = veterinario_firmante
        self.observaciones: str = observaciones or ""
        self.veterinaria_emisora = veterinaria_emisora

    # Alias de compatibilidad previa
    @property
    def id_historial(self) -> int:
        return self.id_registro

    def es_modificable_por(self, usuario_vet) -> bool:
        matricula = getattr(usuario_vet, "matricula_profesional", "")
        nombre = getattr(usuario_vet, "nombre_apellido", str(usuario_vet))
        firmante_coincide = (
            self.veterinario_firmante in (matricula, nombre, str(usuario_vet))
        )
        return firmante_coincide or self.veterinaria_emisora == getattr(
            usuario_vet, "veterinaria", None
        )


# Alias para compatibilidad con importaciones previas
HistorialMedico = HistorialClinico


class Mascota:
    def __init__(
        self,
        id_mascota: int,
        nombre: str,
        fecha_nacimiento: Optional[date],
        sexo: str,
        peso_kg: float,
        raza: Raza,
        foto_url: Optional[str] = None,
    ) -> None:
        self.id_mascota: int = id_mascota
        self.nombre: str = nombre
        self.fecha_nacimiento: Optional[date] = fecha_nacimiento
        self.sexo: str = sexo
        if peso_kg <= 0:
            raise ValueError("El peso debe ser mayor a 0 kg.")
        self._peso_kg: float = float(peso_kg)
        self.raza: Raza = raza
        self.foto_url: Optional[str] = (
            foto_url or "https://via.placeholder.com/150?text=Mascota"
        )
        self._historial_clinico: List[HistorialClinico] = []

    # Métodos explícitos según especificación técnica
    def get_peso(self) -> float:
        """Retorna el peso en kg de la mascota."""
        return self._peso_kg

    def set_peso(self, nuevo_peso: float) -> None:
        """Establece un nuevo peso con validación > 0."""
        if nuevo_peso <= 0:
            raise ValueError("El peso de la mascota debe ser mayor a 0.")
        self._peso_kg = float(nuevo_peso)

    # Estilo Python property para soporte en librerías / Pydantic
    @property
    def peso_kg(self) -> float:
        return self.get_peso()

    @peso_kg.setter
    def peso_kg(self, nuevo_peso: float) -> None:
        self.set_peso(nuevo_peso)

    def es_exotica(self) -> bool:
        return self.raza.especie.es_exotico

    def calcular_edad_formateada(self) -> str:
        """Calcula la edad en formato legible según la fecha de nacimiento."""
        if not self.fecha_nacimiento:
            return "Edad no especificada"
        hoy = date.today()
        edad_anios = hoy.year - self.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (
            self.fecha_nacimiento.month,
            self.fecha_nacimiento.day,
        ):
            edad_anios -= 1
        return f"{edad_anios} años" if edad_anios > 0 else "Menos de un año"

    # Alias de compatibilidad previa
    def obtener_edad_formateada(self) -> str:
        return self.calcular_edad_formateada()

    def agregar_historial(self, historial: HistorialClinico) -> None:
        self._historial_clinico.append(historial)

    @property
    def _historial_medico(self) -> List[HistorialClinico]:
        return self._historial_clinico
