import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.contingencia_barrios import cargar_catalogo_veterinarias
from utils.geo import calcular_distancia_haversine


app = FastAPI(
    title="VetCerca IA - API Backend & Sistema de Triaje",
    description=(
        "API para triaje veterinario con Inteligencia Artificial (Random Forest), "
        "geolocalización de urgencias (Haversine), segmentación barrial (K-Means) "
        "y lógica de contingencia zonal en CABA."
    ),
    version="2.0.0",
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
        "mensaje": "¡Bienvenido a la API unificada de VetCerca IA!",
        "estado": "Online",
        "version": "2.0.0",
        "enfoque": "Ciencia de Datos + Backend POO",
        "documentacion_interactiva": "/docs",
    }


@app.get("/veterinarias/cercanas")
def obtener_veterinarias_cercanas(
    latitud: float, longitud: float, radio_km: float = 10.0, solo_24hs: bool = False
) -> dict[str, object]:
    df_vets = cargar_catalogo_veterinarias()
    cercanas = []
    
    if not df_vets.empty:
        if solo_24hs:
            df_vets = df_vets[df_vets["guardia_24hs"] == 1]

        for _, row in df_vets.iterrows():
            distancia = calcular_distancia_haversine(
                latitud,
                longitud,
                float(row["latitud"]),
                float(row["longitud"]),
            )
            if distancia <= radio_km:
                cercanas.append(
                    {
                        "id": int(row["id_veterinaria"]),
                        "nombre": row["nombre_centro"],
                        "barrio": row["barrio"],
                        "comuna": int(row["comuna"]),
                        "direccion": row["direccion"],
                        "telefono": row["telefono_urgencias"],
                        "latitud": float(row["latitud"]),
                        "longitud": float(row["longitud"]),
                        "distancia_km": distancia,
                        "es_24hs": bool(row["guardia_24hs"] == 1),
                        "nivel_complejidad": row["nivel_complejidad"],
                        "especialidades": row["especialidades"],
                        "horario_informado": "Guardia 24hs activa" if row["guardia_24hs"] == 1 else "Atención diurna",
                        "estado_verificacion": "VERIFICADA_CABA",
                        "fuente_datos": "Catálogo Oficial CABA",
                    }
                )

    cercanas.sort(key=lambda veterinaria: veterinaria["distancia_km"])
    return {"cantidad": len(cercanas), "veterinarias": cercanas}


from routers import auth, mascotas, triaje

app.include_router(auth.router)
app.include_router(mascotas.router)
app.include_router(triaje.router)
