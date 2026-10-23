class ServicioNotificacion:
    def __init__(self, proveedor_api: str = "Twilio/WhatsApp") -> None:
        self.proveedor_api = proveedor_api

    def despachar_alerta(self, alerta) -> None:
        telefono = alerta.veterinaria_destino.telefono_guardia
        print(f"📡 [DESPACHO API] Enviando mensaje WhatsApp a {telefono}...")
        self.enviar_mensaje_whatsapp(telefono, alerta.mensaje_texto)
        alerta.estado_envio = "ENVIADO"

    def enviar_mensaje_whatsapp(self, telefono: str, mensaje: str) -> None:
        print(f"💬 [WhatsApp -> {telefono}]: {mensaje}")