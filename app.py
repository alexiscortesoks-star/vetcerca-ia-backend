from datetime import date

from fastapi import FastAPI

from Services.asistente_ia import AsistenteIA
from models.mascotas import Especie, Mascota, Raza


app = FastAPI(
    title="VetCerca IA - API Backend",
    description=(
        "API para triaje veterinario con Inteligencia Artificial "
        "y gestión de urgencias"
    ),
    version="1.0.0",
)

asistente_ia = AsistenteIA()


@app.get("/")
def inicio() -> dict[str, str]:
    return {
        "mensaje": "¡Bienvenido a la API de VetCerca IA!",
        "estado": "Online",
        "documentacion_interactiva": "/docs",
    }


@app.get("/triaje/evaluar")
def evaluar_triaje(
    sintomas: str, nombre_mascota: str = "Mascota"
) -> dict[str, str]:
    felino = Especie(1, "Felino")
    raza_generica = Raza(1, "Mestizo", felino)
    paciente = Mascota(
        1, nombre_mascota, date.today(), "Macho", 4.0, raza_generica
    )
    resultado = asistente_ia.procesar_triaje(sintomas, paciente)
    return {
        "paciente": paciente.nombre,
        "sintomas_ingresados": sintomas,
        "nivel_urgencia": resultado["nivel_urgencia"],
        "especialidad_sugerida": resultado["especialidad_sugerida"],
        "primeros_auxilios": resultado["primeros_auxilios"],
    }