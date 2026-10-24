import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.triaje import VETERINARIAS_CANDIDATAS
from utils.geo import calcular_distancia_haversine


app = FastAPI(
    title="VetCerca IA - API Backend",
    description=(
        "API para triaje veterinario con Inteligencia Artificial "
        "y geolocalización de urgencias"
    ),
    version="1.1.0",
)

origins_permitidos = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5501",
    "http://127.0.0.1:5501",
]
origins_permitidos.extend(
    origen.strip()
    for origen in os.getenv("VETCERCA_CORS_ORIGINS", "").split(",")
    if origen.strip()
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_permitidos,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def inicio() -> dict[str, str]:
    return {
        "mensaje": "¡Bienvenido a la API de VetCerca IA!",
        "estado": "Online",
        "version": "1.1.0",
        "documentacion_interactiva": "/docs",
    }


@app.get("/veterinarias/cercanas")
def obtener_veterinarias_cercanas(
    latitud: float, longitud: float, radio_km: float = 10.0
) -> dict[str, object]:
    cercanas = []
    for veterinaria in VETERINARIAS_CANDIDATAS:
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
                    "latitud": veterinaria.latitud,
                    "longitud": veterinaria.longitud,
                    "distancia_km": distancia,
                    "es_24hs": veterinaria.es_24hs,
                    "horario_informado": veterinaria.horario_informado,
                    "estado_verificacion": veterinaria.estado_verificacion,
                    "fuente_datos": veterinaria.fuente_datos,
                    "fuente_url": veterinaria.fuente_url,
                    "atribucion_fuente": veterinaria.atribucion_fuente,
                }
            )

    cercanas.sort(key=lambda veterinaria: veterinaria["distancia_km"])
    return {"cantidad": len(cercanas), "veterinarias": cercanas}


from routers import auth, mascotas, triaje

app.include_router(auth.router)
app.include_router(mascotas.router)
app.include_router(triaje.router)
