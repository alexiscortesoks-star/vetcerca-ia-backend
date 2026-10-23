from datetime import date

from fastapi import FastAPI

from Services.asistente_ia import AsistenteIA
from models.mascotas import Especie, Mascota, Raza
from models.veterinarias import Veterinaria
from schemas.triaje import TriajeRequest, TriajeResponse
from utils.geo import calcular_distancia_haversine


app = FastAPI(
    title="VetCerca IA - API Backend",
    description=(
        "API para triaje veterinario con Inteligencia Artificial "
        "y geolocalización de urgencias"
    ),
    version="1.1.0",
)

asistente_ia = AsistenteIA()

VETERINARIAS_MOCK = [
    Veterinaria(
        1,
        "Hospital Felino 24h",
        "Av. Corrientes 1234",
        -34.6037,
        -58.3816,
        "+5491199998888",
        True,
    ),
    Veterinaria(
        2,
        "Clínica Veterinaria Central",
        "Av. Belgrano 500",
        -34.6150,
        -58.3700,
        "+5491188887777",
        True,
    ),
    Veterinaria(
        3,
        "Guardia Veterinaria Sur",
        "Av. Santa Fe 2500",
        -34.5900,
        -58.4000,
        "+5491177776666",
        True,
    ),
]


@app.get("/")
def inicio() -> dict[str, str]:
    return {
        "mensaje": "¡Bienvenido a la API de VetCerca IA!",
        "estado": "Online",
        "version": "1.1.0",
        "documentacion_interactiva": "/docs",
    }


@app.post("/triaje/evaluar", response_model=TriajeResponse)
def evaluar_triaje(datos: TriajeRequest) -> TriajeResponse:
    felino = Especie(1, "Felino")
    raza_generica = Raza(1, "Mestizo", felino)
    paciente = Mascota(
        1,
        datos.nombre_mascota,
        date.today(),
        "Macho",
        4.0,
        raza_generica,
    )
    resultado = asistente_ia.procesar_triaje(datos.sintomas, paciente)

    veterinaria_mas_cercana = None
    distancia_minima = float("inf")
    if datos.latitud_cliente is not None and datos.longitud_cliente is not None:
        for veterinaria in VETERINARIAS_MOCK:
            if veterinaria.esta_disponible():
                distancia = calcular_distancia_haversine(
                    datos.latitud_cliente,
                    datos.longitud_cliente,
                    veterinaria.latitud,
                    veterinaria.longitud,
                )
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    veterinaria_mas_cercana = veterinaria

    return TriajeResponse(
        paciente=paciente.nombre,
        sintomas_ingresados=datos.sintomas,
        nivel_urgencia=resultado["nivel_urgencia"],
        especialidad_sugerida=resultado["especialidad_sugerida"],
        primeros_auxilios=resultado["primeros_auxilios"],
        veterinaria_cercana=(
            veterinaria_mas_cercana.nombre_fantasia
            if veterinaria_mas_cercana
            else "No disponible"
        ),
        distancia_km=(
            distancia_minima if veterinaria_mas_cercana else None
        ),
    )


@app.get("/veterinarias/cercanas")
def obtener_veterinarias_cercanas(
    latitud: float, longitud: float, radio_km: float = 10.0
) -> dict[str, object]:
    cercanas = []
    for veterinaria in VETERINARIAS_MOCK:
        distancia = calcular_distancia_haversine(
            latitud,
            longitud,
            veterinaria.latitud,
            veterinaria.longitud,
        )
        if distancia <= radio_km:
            cercanas.append(
                {
                    "id": veterinaria.id_veterinaria,
                    "nombre": veterinaria.nombre_fantasia,
                    "direccion": veterinaria.direccion,
                    "telefono": veterinaria.telefono_guardia,
                    "distancia_km": distancia,
                    "es_24hs": veterinaria.es_24hs,
                }
            )

    cercanas.sort(key=lambda veterinaria: veterinaria["distancia_km"])
    return {"cantidad": len(cercanas), "veterinarias": cercanas}


from routers import auth, mascotas

app.include_router(auth.router)
app.include_router(mascotas.router)
