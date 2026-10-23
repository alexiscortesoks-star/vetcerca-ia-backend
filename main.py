from datetime import date

from Services.asistente_ia import AsistenteIA
from Services.notificador import ServicioNotificacion
from models.mascotas import Especie, HistorialMedico, Mascota, Raza
from models.triaje import AlertaUrgencia, ConsultaTriaje
from models.usuarios import Cliente, UsuarioVeterinario
from models.veterinarias import Veterinaria


def main() -> None:
    print("=== INICIANDO SISTEMA VETCERCA IA ===\n")

    # 1. Crear especie, raza y mascota.
    felino = Especie(1, "Felino", es_exotica=False)
    siames = Raza(1, "Siamés", felino)
    mimi = Mascota(101, "Mimi", date(2021, 5, 10), "Hembra", 3.8, siames)

    # 2. Crear cliente y asignar mascota.
    cliente = Cliente(
        1, "maria@email.com", "pass123", "1122334455", "María González"
    )
    cliente.agregar_mascota(mimi)

    # 3. Crear veterinaria y veterinario.
    hospital = Veterinaria(
        1,
        "Hospital Felino 24h",
        "Av. Corrientes 1234",
        -34.60,
        -58.38,
        "+5491199998888",
        True,
    )
    dr_roberto = UsuarioVeterinario(
        2,
        "vet@hospital.com",
        "vetpass",
        "1188887777",
        "Dr. Roberto Gómez",
        "MN-8492",
        "Jefe de Guardia",
        hospital,
    )

    # 4. Simular triaje con IA.
    ia = AsistenteIA()
    consulta = ConsultaTriaje(
        501,
        "Obstrucción urológica y maullidos de dolor",
        mimi,
        ia,
    )
    consulta.evaluar_sintomas()
    print(
        f"📋 Resultado Triaje: Urgencia = {consulta.nivel_urgencia} | "
        f"Especialidad = {consulta.especialidad_sugerida}"
    )

    # 5. Si la urgencia es alta, enviar alerta.
    if consulta.nivel_urgencia == "ALTA":
        notificador = ServicioNotificacion()
        alerta = AlertaUrgencia(901, consulta, hospital, notificador)
        alerta.transmitir()
        dr_roberto.recibir_alerta_urgencia(alerta)

    # 6. Registrar en el historial médico.
    historial = HistorialMedico(
        1,
        date.today(),
        "Obstrucción uretral",
        "Cateterismo de urgencia",
        "Evolución favorable",
        hospital,
        dr_roberto,
    )
    hospital.registrar_atencion_historial(mimi, historial)
    print(
        f"\n✅ Historial registrado en {mimi.nombre}: "
        f"{mimi._historial_medico[0].diagnostico} "
        f"(Firmado por {historial.veterinario_firmante.nombre_apellido})"
    )


if __name__ == "__main__":
    main()