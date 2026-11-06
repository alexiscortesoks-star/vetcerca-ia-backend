from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional


class Usuario(ABC):
    def __init__(
        self,
        id_usuario: int,
        username: str,
        email: str,
        contrasena_hash: str,
        fecha_registro: Optional[datetime] = None,
        avatar_url: Optional[str] = None,
        telefono: str = "",
    ) -> None:
        self._id_usuario: int = id_usuario
        self._username: str = username
        self._email: str = email
        self._contrasena_hash: str = contrasena_hash
        self._fecha_registro: datetime = fecha_registro or datetime.now()
        self._avatar_url: Optional[str] = avatar_url
        self._telefono: str = telefono

    @property
    def id_usuario(self) -> int:
        return self._id_usuario

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, nuevo_email: str) -> None:
        if "@" in nuevo_email:
            self._email = nuevo_email

    @property
    def contrasena_hash(self) -> str:
        return self._contrasena_hash

    # Compatibilidad con código previo
    @property
    def _password_hash(self) -> str:
        return self._contrasena_hash

    @property
    def fecha_registro(self) -> datetime:
        return self._fecha_registro

    @property
    def avatar_url(self) -> Optional[str]:
        return self._avatar_url

    @property
    def telefono(self) -> str:
        return self._telefono

    def verificar_credenciales(self, usuario_o_email: str, password: str) -> bool:
        """Verifica si el usuario/email coincide y si la contraseña hash es válida."""
        coincide_identificador = (
            usuario_o_email.strip().lower() in (self._username.lower(), self._email.lower())
        )
        return coincide_identificador and self._contrasena_hash == password

    def cambiar_contrasena(self, nueva_contrasena: str) -> None:
        """Actualiza la contraseña hash del usuario."""
        if not nueva_contrasena:
            raise ValueError("La nueva contraseña no puede estar vacía.")
        self._contrasena_hash = nueva_contrasena

    # Alias de compatibilidad
    def autenticar(self, password: str) -> bool:
        return self._contrasena_hash == password


class Cliente(Usuario):
    def __init__(
        self,
        id_usuario: int,
        username: str,
        email: str,
        contrasena_hash: str,
        direccion: str = "",
        latitud: float = 0.0,
        longitud: float = 0.0,
        telefono: str = "",
        nombre_apellido: str = "",
        fecha_registro: Optional[datetime] = None,
        avatar_url: Optional[str] = None,
    ) -> None:
        super().__init__(
            id_usuario=id_usuario,
            username=username,
            email=email,
            contrasena_hash=contrasena_hash,
            fecha_registro=fecha_registro,
            avatar_url=avatar_url,
            telefono=telefono,
        )
        self._direccion: str = direccion
        self._latitud: float = latitud
        self._longitud: float = longitud
        self.nombre_apellido: str = nombre_apellido or username
        self._mascotas: List = []

    @property
    def direccion(self) -> str:
        return self._direccion

    @direccion.setter
    def direccion(self, nueva_direccion: str) -> None:
        self._direccion = nueva_direccion

    @property
    def latitud(self) -> float:
        return self._latitud

    @property
    def longitud(self) -> float:
        return self._longitud

    # Compatibilidad con accesos directos existentes
    @property
    def latitud_actual(self) -> float:
        return self._latitud

    @latitud_actual.setter
    def latitud_actual(self, valor: float) -> None:
        self._latitud = valor

    @property
    def longitud_actual(self) -> float:
        return self._longitud

    @longitud_actual.setter
    def longitud_actual(self, valor: float) -> None:
        self._longitud = valor

    def agregar_mascota(self, mascota) -> None:
        self._mascotas.append(mascota)

    def get_mascotas(self) -> List:
        return self._mascotas

    def actualizar_gps(self, lat: float, lng: float) -> None:
        self._latitud = lat
        self._longitud = lng


class UsuarioVeterinario(Usuario):
    def __init__(
        self,
        id_usuario: int,
        username: str,
        email: str,
        contrasena_hash: str,
        matricula_profesional: str,
        especialidad_principal: str,
        telefono: str = "",
        nombre_apellido: str = "",
        cargo: str = "",
        veterinaria=None,
        fecha_registro: Optional[datetime] = None,
        avatar_url: Optional[str] = None,
    ) -> None:
        super().__init__(
            id_usuario=id_usuario,
            username=username,
            email=email,
            contrasena_hash=contrasena_hash,
            fecha_registro=fecha_registro,
            avatar_url=avatar_url,
            telefono=telefono,
        )
        self._matricula_profesional: str = matricula_profesional
        self._especialidad_principal: str = especialidad_principal
        self.nombre_apellido: str = nombre_apellido or username
        self.cargo: str = cargo or especialidad_principal
        self._veterinaria = veterinaria

    @property
    def matricula_profesional(self) -> str:
        return self._matricula_profesional

    @property
    def especialidad_principal(self) -> str:
        return self._especialidad_principal

    @property
    def veterinaria(self):
        return self._veterinaria

    @veterinaria.setter
    def veterinaria(self, vet) -> None:
        self._veterinaria = vet

    def gestionar_estado_guardia(self, disponible: bool) -> None:
        if self._veterinaria:
            self._veterinaria.actualizar_estado_guardia(
                "DISPONIBLE" if disponible else "NO_DISPONIBLE"
            )

    def recibir_alerta_urgencia(self, alerta) -> None:
        mensaje = getattr(alerta, "mensaje_texto", str(alerta))
        id_alerta = getattr(alerta, "id_alerta", "?")
        print(
            f"🚨 [NOTIFICACIÓN VET] {self.nombre_apellido} recibió alerta "
            f"#{id_alerta}: {mensaje}"
        )
