from abc import ABC
from typing import List


class Usuario(ABC):
    def __init__(
        self, id_usuario: int, email: str, password_hash: str, telefono: str
    ) -> None:
        self._id_usuario = id_usuario
        self._email = email
        self._password_hash = password_hash
        self._telefono = telefono

    def autenticar(self, password: str) -> bool:
        return self._password_hash == password

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, nuevo_email: str) -> None:
        if "@" in nuevo_email:
            self._email = nuevo_email

    @property
    def telefono(self) -> str:
        return self._telefono


class Cliente(Usuario):
    def __init__(
        self,
        id_usuario: int,
        email: str,
        password_hash: str,
        telefono: str,
        nombre_apellido: str,
    ) -> None:
        super().__init__(id_usuario, email, password_hash, telefono)
        self.nombre_apellido = nombre_apellido
        self.latitud_actual: float = 0.0
        self.longitud_actual: float = 0.0
        self._mascotas: List = []

    def agregar_mascota(self, mascota) -> None:
        self._mascotas.append(mascota)

    def get_mascotas(self) -> List:
        return self._mascotas

    def actualizar_gps(self, lat: float, lng: float) -> None:
        self.latitud_actual = lat
        self.longitud_actual = lng


class UsuarioVeterinario(Usuario):
    def __init__(
        self,
        id_usuario: int,
        email: str,
        password_hash: str,
        telefono: str,
        nombre_apellido: str,
        matricula: str,
        cargo: str,
        veterinaria=None,
    ) -> None:
        super().__init__(id_usuario, email, password_hash, telefono)
        self.nombre_apellido = nombre_apellido
        self.matricula_profesional = matricula
        self.cargo = cargo
        self.veterinaria = veterinaria

    def gestionar_estado_guardia(self, disponible: bool) -> None:
        if self.veterinaria:
            self.veterinaria.actualizar_estado_guardia(
                "ACTIVA" if disponible else "INACTIVA"
            )

    def recibir_alerta_urgencia(self, alerta) -> None:
        print(
            f"🚨 [NOTIFICACIÓN VET] {self.nombre_apellido} recibió alerta "
            f"#{alerta.id_alerta}: {alerta.mensaje_texto}"
        )