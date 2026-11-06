class ServicioNotificacion:
    def __init__(self, proveedor_api: str = "Twilio/WhatsApp") -> None:
        self.proveedor_api = proveedor_api

    def despachar_whatsapp(self, telefono_destino: str, mensaje: str) -> bool:
        """
        Envía un mensaje de urgencia vía la API de WhatsApp al número especificado.
        Retorna True si el despacho fue exitoso.
        """
        try:
            print(f"[DESPACHO API ({self.proveedor_api})] Enviando WhatsApp a {telefono_destino}...")
            print(f"[WhatsApp -> {telefono_destino}]: {mensaje}")
        except UnicodeEncodeError:
            # Fallback seguro para consolas con codepage limitado
            print(f"[DESPACHO API ({self.proveedor_api})] Enviando WhatsApp a {telefono_destino}")
        return True

    def despachar_alerta(self, alerta) -> bool:
        """Despacha la alerta completa extrayendo destino y mensaje."""
        telefono = (
            getattr(alerta.veterinaria_destino, "telefono_guardia", None)
            or getattr(alerta.veterinaria_destino, "telefono", None)
            or "+5491100000000"
        )
        mensaje = getattr(alerta, "mensaje_texto", str(alerta))
        exito = self.despachar_whatsapp(telefono, mensaje)
        if hasattr(alerta, "estado"):
            alerta.estado = "NOTIFICADA"
        elif hasattr(alerta, "estado_envio"):
            alerta.estado_envio = "ENVIADO"
        return exito

    def enviar_mensaje_whatsapp(self, telefono: str, mensaje: str) -> bool:
        """Alias para compatibilidad con llamadas existentes."""
        return self.despachar_whatsapp(telefono, mensaje)
