from fastapi import FastAPI

from routers.triaje import VETERINARIAS_MOCK
from utils.geo import calcular_distancia_haversine


app = FastAPI(
    title="VetCerca IA - API Backend",
    description=(
        "API para triaje veterinario con Inteligencia Artificial "
        "y geolocalización de urgencias"
    ),
    version="1.1.0",
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


from routers import auth, mascotas, triaje

app.include_router(auth.router)
app.include_router(mascotas.router)
app.include_router(triaje.router)
