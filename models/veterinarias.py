class Especialidad:
    def __init__(self, id_especialidad: int, nombre_especialidad: str) -> None:
        self.id_especialidad = id_especialidad
        self.nombre_especialidad = nombre_especialidad


class Veterinaria:
    def __init__(
        self,
        id_veterinaria: int,
        nombre_fantasia: str,
        direccion: str,
        latitud: float,
        longitud: float,
        telefono_guardia: str,
        es_24hs: bool,
    ) -> None:
        self.id_veterinaria = id_veterinaria
        self.nombre_fantasia = nombre_fantasia
        self.direccion = direccion
        self.latitud = latitud
        self.longitud = longitud
        self.telefono_guardia = telefono_guardia
        self.es_24hs = es_24hs
        self.estado_disponibilidad = "DISPONIBLE"

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