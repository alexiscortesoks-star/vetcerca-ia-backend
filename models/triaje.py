from datetime import datetime
from typing import Optional, Dict, Any


class ConsultaTriaje:
    def __init__(
        self,
        id_triaje: int,
        sintomas_ingresados: str,
        id_cliente: int = 1,
        id_mascota: int = 1,
        mascota=None,
        asistente_ia=None,
        id_consulta: Optional[int] = None,
        descripcion_sintomas: Optional[str] = None,
        especie: str = "Canino",
        tiempo_evolucion_hs: float = 2.0,
        estado_conciencia: str = "Alerta",
        presencia_hemorragia: int = 0
    ) -> None:
        self.id_triaje: int = id_consulta if id_consulta is not None else id_triaje
        self.id_cliente: int = id_cliente
        self.id_mascota: int = id_mascota
        self.fecha_hora: datetime = datetime.now()
        self.sintomas_ingresados: str = (
            descripcion_sintomas
            if descripcion_sintomas is not None
            else sintomas_ingresados
        )
        self.mascota = mascota
        self.asistente_ia = asistente_ia
        self.especie: str = especie
        self.tiempo_evolucion_hs: float = tiempo_evolucion_hs
        self.estado_conciencia: str = estado_conciencia
        self.presencia_hemorragia: int = presencia_hemorragia
        
        # Resultados de la evaluación del modelo
        self.nivel_urgencia: str = "Pendiente"
        self.confianza_prediccion: float = 0.0
        self.probabilidades: Dict[str, float] = {}
        self.diagnostico_preliminar: str = ""
        self.especialidad_sugerida: str = ""
        self.primeros_auxilios: str = ""
        self.pregunta_aclaratoria: Optional[str] = None
        self.alerta_despachada: bool = False

    # Alias para compatibilidad con llamadas anteriores
    @property
    def id_consulta(self) -> int:
        return self.id_triaje

    @id_consulta.setter
    def id_consulta(self, valor: int) -> None:
        self.id_triaje = valor

    @property
    def descripcion_sintomas(self) -> str:
        return self.sintomas_ingresados

    @descripcion_sintomas.setter
    def descripcion_sintomas(self, valor: str) -> None:
        self.sintomas_ingresados = valor

    def ejecutar_triaje(self, asistente_ia=None, **kwargs) -> None:
        """
        Ejecuta el triaje mediante el asistente de IA (Machine Learning + Prompt estructurado).
        Actualiza nivel_urgencia, diagnostico_preliminar, especialidad_sugerida y primeros_auxilios.
        """
        ia = asistente_ia or self.asistente_ia
        if not ia:
            raise ValueError("Se requiere un AsistenteIA para ejecutar el triaje.")

        especie_nombre = self.especie
        if self.mascota and hasattr(self.mascota, "raza") and hasattr(self.mascota.raza, "especie"):
            especie_nombre = getattr(self.mascota.raza.especie, "nombre", self.especie)

        tiempo_hs = kwargs.get("tiempo_evolucion_hs", self.tiempo_evolucion_hs)
        conciencia = kwargs.get("estado_conciencia", self.estado_conciencia)
        hemorragia = kwargs.get("presencia_hemorragia", self.presencia_hemorragia)

        resultado = ia.clasificar_urgencia(
            sintomas=self.sintomas_ingresados,
            especie=especie_nombre,
            tiempo_evolucion_hs=tiempo_hs,
            estado_conciencia=conciencia,
            presencia_hemorragia=hemorragia
        )
        self.nivel_urgencia = resultado.get("nivel_urgencia", "Moderada")
        self.confianza_prediccion = resultado.get("confianza", 0.0)
        self.probabilidades = resultado.get("probabilidades", {})
        self.diagnostico_preliminar = resultado.get(
            "diagnostico_preliminar", "Evaluación orientativa no concluyente."
        )
        self.especialidad_sugerida = resultado.get(
            "especialidad_sugerida", "Guardia General"
        )
        self.primeros_auxilios = resultado.get(
            "primeros_auxilios", "Mantener en calma y acudir a consulta presencial."
        )
        self.pregunta_aclaratoria = resultado.get("pregunta_aclaratoria")

    # Alias de compatibilidad
    def evaluar_sintomas(self) -> None:
        self.ejecutar_triaje()


class AlertaUrgencia:
    def __init__(
        self,
        id_alerta: int,
        consulta_triaje: ConsultaTriaje,
        veterinaria_destino,
        servicio_notificacion=None,
        id_triaje: Optional[int] = None,
        id_veterinaria_asignada: Optional[int] = None,
        tiempo_estimado_arribo_min: int = 15,
    ) -> None:
        self.id_alerta: int = id_alerta
        self.id_triaje: int = (
            id_triaje
            if id_triaje is not None
            else getattr(consulta_triaje, "id_triaje", 0)
        )
        self.id_veterinaria_asignada: int = (
            id_veterinaria_asignada
            if id_veterinaria_asignada is not None
            else getattr(veterinaria_destino, "id_veterinaria", 0)
        )
        self.fecha_hora: datetime = datetime.now()
        self.consulta_triaje: ConsultaTriaje = consulta_triaje
        self.veterinaria_destino = veterinaria_destino
        self.servicio_notificacion = servicio_notificacion
        # Máquina de estados: "EMITIDA", "NOTIFICADA", "EN_CURSO", "ATENDIDA"
        self.estado: str = "EMITIDA"
        self.tiempo_estimado_arribo_min: int = tiempo_estimado_arribo_min

        nombre_paciente = (
            consulta_triaje.mascota.nombre
            if consulta_triaje.mascota
            else f"Mascota #{consulta_triaje.id_mascota}"
        )
        self.mensaje_texto: str = (
            f"URGENCIA {consulta_triaje.nivel_urgencia.upper()}: Paciente "
            f"{nombre_paciente} ({consulta_triaje.sintomas_ingresados}) - "
            f"Arribo estimado en {tiempo_estimado_arribo_min} min."
        )

    @property
    def estado_envio(self) -> str:
        return self.estado

    @estado_envio.setter
    def estado_envio(self, valor: str) -> None:
        self.estado = valor

    def transmitir(self) -> bool:
        """Despacha la alerta vía el servicio de notificación y actualiza su estado."""
        if self.servicio_notificacion:
            exito = self.servicio_notificacion.despachar_alerta(self)
            self.estado = "NOTIFICADA"
            self.consulta_triaje.alerta_despachada = True
            return bool(exito)
        self.estado = "NOTIFICADA"
        self.consulta_triaje.alerta_despachada = True
        return True
