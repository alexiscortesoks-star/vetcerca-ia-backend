from datetime import date

from Services.asistente_ia import AsistenteIA
from Services.notificador import ServicioNotificacion
from models.mascotas import Especie, HistorialClinico, Mascota, Raza
from models.triaje import AlertaUrgencia, ConsultaTriaje
from models.usuarios import Cliente, UsuarioVeterinario
from models.veterinarias import Veterinaria


def main() -> None:
    print("=== INICIANDO SISTEMA VETCERCA IA (POO + CASOS DE USO) ===\n")

    # 1. Crear especie, raza y mascota con encapsulamiento
    felino = Especie(
        id_especie=1,
        nombre="Felino",
        es_exotico=False,
        requiere_permiso_senasa=False,
    )
    siames = Raza(
        id_raza=1,
        nombre="Siamés",
        especie=felino,
        descripcion="Felino doméstico de pelaje corto y extremidades oscuras",
    )
    mimi = Mascota(
        id_mascota=101,
        nombre="Mimi",
        fecha_nacimiento=date(2021, 5, 10),
        sexo="Hembra",
        peso_kg=3.8,
        raza=siames,
    )
    print(
        f"🐾 Paciente Creado: {mimi.nombre} | Raza: {mimi.raza.nombre} | "
        f"Edad: {mimi.calcular_edad_formateada()} | Peso: {mimi.get_peso()} kg"
    )

    # 2. Crear cliente (herencia de Usuario) y asociar mascota (composición)
    cliente = Cliente(
        id_usuario=1,
        username="maria_g2024",
        email="maria@email.com",
        contrasena_hash="pass123",
        direccion="Av. Corrientes 1500, CABA",
        latitud=-34.6037,
        longitud=-58.3816,
        telefono="1122334455",
        nombre_apellido="María González",
    )
    cliente.agregar_mascota(mimi)

    # Test CU-01: Verificación de credenciales
    login_ok = cliente.verificar_credenciales("maria_g2024", "pass123")
    print(f"🔐 CU-01 Autenticación para '{cliente.username}': {'Exitosa' if login_ok else 'Fallida'}")

    # 3. Crear veterinaria y veterinario
    hospital = Veterinaria(
        id_veterinaria=1,
        nombre="Hospital Felino 24h",
        direccion="Av. Corrientes 1234, CABA",
        latitud=-34.6030,
        longitud=-58.3820,
        tiene_guardia_24h=True,
        telefono_guardia="+5491199998888",
    )
    distancia = hospital.calcular_distancia_km(cliente.latitud, cliente.longitud)
    print(
        f"📍 Veterinaria de Guardia: {hospital.nombre} | "
        f"Distancia al cliente (Haversine en POO): {distancia} km"
    )

    dr_roberto = UsuarioVeterinario(
        id_usuario=2,
        username="dr_roberto",
        email="vet@hospital.com",
        contrasena_hash="vetpass",
        matricula_profesional="MN-8492",
        especialidad_principal="Urgencias Quirúrgicas / Urología",
        telefono="1188887777",
        nombre_apellido="Dr. Roberto Gómez",
        veterinaria=hospital,
    )

    # 4. CU-04: Simular Triaje Inteligente con IA
    ia = AsistenteIA(modelo_principal="Gemini 1.5 Pro / API")
    consulta = ConsultaTriaje(
        id_triaje=501,
        sintomas_ingresados="Obstrucción urológica, maullidos agudos de dolor y abdomen distendido",
        id_cliente=cliente.id_usuario,
        id_mascota=mimi.id_mascota,
        mascota=mimi,
        asistente_ia=ia,
    )
    consulta.ejecutar_triaje(ia)
    print(
        f"\n📋 Resultado Triaje IA: Urgencia = {consulta.nivel_urgencia} | "
        f"Especialidad = {consulta.especialidad_sugerida}\n"
        f"   Diagnóstico Preliminar: {consulta.diagnostico_preliminar}\n"
        f"   Primeros Auxilios: {consulta.primeros_auxilios}"
    )

    # 5. Despacho de alerta de urgencia si la urgencia es ALTA
    if consulta.nivel_urgencia == "ALTA":
        notificador = ServicioNotificacion(proveedor_api="WhatsApp API")
        alerta = AlertaUrgencia(
            id_alerta=901,
            consulta_triaje=consulta,
            veterinaria_destino=hospital,
            servicio_notificacion=notificador,
            id_triaje=consulta.id_triaje,
            id_veterinaria_asignada=hospital.id_veterinaria,
            tiempo_estimado_arribo_min=15,
        )
        alerta.transmitir()
        dr_roberto.recibir_alerta_urgencia(alerta)
        print(f"🚨 Estado de la alerta: {alerta.estado} | Tiempo estimado arribo: {alerta.tiempo_estimado_arribo_min} min")

    # 6. CU-03: Registrar en el Historial Clínico
    historial = HistorialClinico(
        id_registro=1,
        id_mascota=mimi.id_mascota,
        fecha=date.today(),
        motivo="Obstrucción urinaria y dolor agudo",
        diagnostico="Obstrucción uretral felina grave",
        tratamiento="Sondaje uretral de urgencia y fluidoterapia",
        veterinario_firmante=dr_roberto.nombre_apellido,
        veterinaria_emisora=hospital,
    )
    hospital.registrar_atencion_historial(mimi, historial)
    print(
        f"\n✅ Historial Clínico registrado en {mimi.nombre}: "
        f"'{historial.diagnostico}' (Firmado por {historial.veterinario_firmante})"
    )


if __name__ == "__main__":
    main()
