from datetime import datetime


class ConsultaTriaje:
    def __init__(
        self, id_consulta: int, descripcion_sintomas: str, mascota, asistente_ia
    ) -> None:
        self.id_consulta = id_consulta
        self.fecha_hora = datetime.now()
        self.descripcion_sintomas = descripcion_sintomas
        self.mascota = mascota
        self.asistente_ia = asistente_ia
        self.nivel_urgencia = "PENDIENTE"
        self.especialidad_sugerida = ""

    def evaluar_sintomas(self) -> None:
        resultado = self.asistente_ia.procesar_triaje(
            self.descripcion_sintomas, self.mascota
        )
        self.nivel_urgencia = resultado["nivel_urgencia"]
        self.especialidad_sugerida = resultado["especialidad_sugerida"]


class AlertaUrgencia:
    def __init__(
        self,
        id_alerta: int,
        consulta_triaje: ConsultaTriaje,
        veterinaria_destino,
        servicio_notificacion,
    ) -> None:
        self.id_alerta = id_alerta
        self.fecha_hora = datetime.now()
        self.consulta_triaje = consulta_triaje
        self.veterinaria_destino = veterinaria_destino
        self.servicio_notificacion = servicio_notificacion
        self.estado_envio = "CREADA"
        self.mensaje_texto = (
            f"URGENCIA {consulta_triaje.nivel_urgencia}: Paciente "
            f"{consulta_triaje.mascota.nombre} "
            f"({consulta_triaje.descripcion_sintomas})"
        )

    def transmitir(self) -> bool:
        self.servicio_notificacion.despachar_alerta(self)
        return True