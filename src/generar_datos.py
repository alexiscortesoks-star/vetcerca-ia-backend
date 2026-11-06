"""
Generación y curación de datasets sintéticos para VetCerca IA (CABA)
1. data/veterinarias_barrios.csv: Infraestructura veterinaria georreferenciada en CABA.
2. data/sintomas_triaje.csv: Casuística clínica de triaje para entrenamiento supervisado.
"""

import os
import random
import pandas as pd
import numpy as np

# Semilla para reproducibilidad
np.random.seed(42)
random.seed(42)

# Crear directorio data si no existe
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------------------------------------------------------
# 1. GENERACIÓN DE VETERINARIAS POR BARRIO (CABA)
# -------------------------------------------------------------------------------------------------
BARRIOS_CABA = [
    {"barrio": "Palermo", "comuna": 14, "lat": -34.5800, "lon": -58.4200, "guardia_prob": 0.45},
    {"barrio": "Belgrano", "comuna": 13, "lat": -34.5620, "lon": -58.4560, "guardia_prob": 0.40},
    {"barrio": "Caballito", "comuna": 6, "lat": -34.6200, "lon": -58.4450, "guardia_prob": 0.35},
    {"barrio": "Recoleta", "comuna": 2, "lat": -34.5900, "lon": -58.3950, "guardia_prob": 0.35},
    {"barrio": "Flores", "comuna": 7, "lat": -34.6300, "lon": -58.4600, "guardia_prob": 0.25},
    {"barrio": "Villa Urquiza", "comuna": 12, "lat": -34.5750, "lon": -58.4850, "guardia_prob": 0.25},
    {"barrio": "Almagro", "comuna": 5, "lat": -34.6100, "lon": -58.4200, "guardia_prob": 0.25},
    {"barrio": "Saavedra", "comuna": 12, "lat": -34.5500, "lon": -58.4900, "guardia_prob": 0.30},
    {"barrio": "Villa Devoto", "comuna": 11, "lat": -34.6000, "lon": -58.5100, "guardia_prob": 0.20},
    {"barrio": "Balvanera", "comuna": 3, "lat": -34.6100, "lon": -58.4000, "guardia_prob": 0.20},
    {"barrio": "Colegiales", "comuna": 13, "lat": -34.5750, "lon": -58.4500, "guardia_prob": 0.25},
    {"barrio": "Núñez", "comuna": 13, "lat": -34.5450, "lon": -58.4650, "guardia_prob": 0.30},
    {"barrio": "Villa Crespo", "comuna": 15, "lat": -34.5950, "lon": -58.4400, "guardia_prob": 0.20},
    {"barrio": "San Telmo", "comuna": 1, "lat": -34.6200, "lon": -58.3700, "guardia_prob": 0.15},
    {"barrio": "Barracas", "comuna": 4, "lat": -34.6450, "lon": -58.3800, "guardia_prob": 0.10},
    {"barrio": "Parque Patricios", "comuna": 4, "lat": -34.6350, "lon": -58.4050, "guardia_prob": 0.10},
    {"barrio": "Villa Lugano", "comuna": 8, "lat": -34.6750, "lon": -58.4700, "guardia_prob": 0.05},
    {"barrio": "Mataderos", "comuna": 9, "lat": -34.6600, "lon": -58.5000, "guardia_prob": 0.10},
    {"barrio": "Chacarita", "comuna": 15, "lat": -34.5880, "lon": -58.4550, "guardia_prob": 0.20},
    {"barrio": "Boedo", "comuna": 5, "lat": -34.6300, "lon": -58.4150, "guardia_prob": 0.15},
]

NOMBRES_BASE = [
    "Hospital Veterinario Central", "Clínica Veterinaria San Francisco", "Centro Médico Veterinario",
    "Veterinaria Panda Guardia", "Clínica Veterinaria Las Mascotas", "Hospital Veterinario Integral",
    "Consultorio Veterinario del Sol", "Centro Veterinario CABA", "Veterinaria San Roque",
    "Clínica Veterinaria Norte", "Hospital Veterinario Buenos Aires", "Clínica de Pequeños Animales",
    "Centro Quirúrgico Veterinario", "Veterinaria San Martín", "Clínica Veterinaria Sur",
    "Consultorio Dr. Mascotas", "Centro Veterinario 24 Horas", "Clínica Médica Animal",
    "Hospital Veterinario Metropolitano", "Veterinaria La Huella"
]

CALLES_CABA = [
    "Av. Cabildo", "Av. Santa Fe", "Av. Rivadavia", "Av. Corrientes", "Av. Córdoba",
    "Av. Belgrano", "Av. Montes de Oca", "Av. Triunvirato", "Av. San Martín", "Av. Directorio",
    "Amenábar", "Guatemala", "Av. Ruiz Huidobro", "Juramento", "Riobamba", "Malabia"
]

ESPECIALIDADES_LIST = [
    "Clínica Médica, Cirugía General",
    "Clínica Médica, Traumatología, Cirugía",
    "Clínica Médica, Ecografía, Guardia General",
    "Cirugía Compleja, Terapia Intensiva, Cardiología",
    "Clínica Médica, Dermatología, Odontología",
    "Guardia General, Laboratorio, Radiología Digital",
    "Terapia Intensiva, Cirugía, Ecografía, Traumatología"
]

def generar_dataset_veterinarias(n_total=80):
    veterinarias = []
    id_vet = 1

    for i in range(n_total):
        b_info = random.choice(BARRIOS_CABA)
        nombre = f"{random.choice(NOMBRES_BASE)} {b_info['barrio']}"
        calle = f"{random.choice(CALLES_CABA)} {random.randint(100, 5800)}"
        
        # Variación geográfica pequeña alrededor del centro del barrio
        lat = b_info["lat"] + np.random.uniform(-0.008, 0.008)
        lon = b_info["lon"] + np.random.uniform(-0.008, 0.008)
        
        es_guardia = 1 if (random.random() < b_info["guardia_prob"]) else 0
        
        if es_guardia:
            complejidad = random.choice(["Intermedio", "Alta Complejidad/Quirófano"])
            especialidad = random.choice([
                "Guardia General, Cirugía, Terapia Intensiva",
                "Cirugía Compleja, Terapia Intensiva, Cardiología",
                "Terapia Intensiva, Cirugía, Ecografía, Traumatología"
            ])
            tel = f"+54 9 11 {random.randint(4000, 9999)}-{random.randint(1000, 9999)}"
        else:
            complejidad = random.choice(["Básico", "Intermedio"])
            especialidad = random.choice([
                "Clínica Médica, Vacunación, Cirugía Menor",
                "Clínica Médica, Dermatología, Odontología",
                "Clínica Médica, Ecografía, Guardia General"
            ])
            tel = f"+54 11 {random.randint(4000, 4999)}-{random.randint(1000, 9999)}"
            
        veterinarias.append({
            "id_veterinaria": id_vet,
            "nombre_centro": nombre,
            "barrio": b_info["barrio"],
            "comuna": b_info["comuna"],
            "latitud": round(lat, 6),
            "longitud": round(lon, 6),
            "guardia_24hs": es_guardia,
            "nivel_complejidad": complejidad,
            "especialidades": especialidad,
            "direccion": f"{calle}, {b_info['barrio']}, CABA",
            "telefono_urgencias": tel
        })
        id_vet += 1

    df_vets = pd.DataFrame(veterinarias)
    path = os.path.join(DATA_DIR, "veterinarias_barrios.csv")
    df_vets.to_csv(path, index=False, encoding="utf-8")
    print(f"Dataset veterinarias guardado en: {path} ({len(df_vets)} registros)")
    return df_vets

# -------------------------------------------------------------------------------------------------
# 2. GENERACIÓN DE DATASET DE SÍNTOMAS Y TRIAJE CLÍNICO
# -------------------------------------------------------------------------------------------------
CASOS_CLINICOS_PATRONES = [
    # Emergencia Crítica
    {
        "urgencia": "Emergencia Crítica",
        "sintomas": [
            "Dificultad respiratoria severa / Cianosis",
            "Convulsiones continuas / Status epiléptico",
            "Paro cardiorrespiratorio inminente",
            "Hemorragia arterial profusa no controlada",
            "Traumatismo agudo por atropello con shock",
            "Pérdida de conciencia / Estado comatoso",
            "Obstrucción uretral completa con dilatación vesical",
            "Intoxicación sobreaguda por rodenticidas / Sangrado activo"
        ],
        "horas_rango": (0.2, 4.0),
        "conciencia_pesos": [0.05, 0.20, 0.75], # Alerta, Deprimido, Estuporoso/Comatoso
        "hemorragia_prob": 0.65
    },
    # Alta
    {
        "urgencia": "Alta",
        "sintomas": [
            "Vómitos reiterados con contenido hemorrágico",
            "Dificultad marcada para orinar con dolor intenso",
            "Herida profunda penetrante o mordedura",
            "Dolor abdominal agudo / Abdomen distendido y duro",
            "Letargo extremo post-traumatismo",
            "Quemadura grave por calor o cáusticos",
            "Reacción anafiláctica aguda / Angioedema facial severo",
            "Prolapso o traumatismo ocular grave"
        ],
        "horas_rango": (0.5, 12.0),
        "conciencia_pesos": [0.25, 0.60, 0.15],
        "hemorragia_prob": 0.40
    },
    # Moderada
    {
        "urgencia": "Moderada",
        "sintomas": [
            "Vómitos y diarrea persistente sin sangre por más de 24 horas",
            "Cojera severa / Claudicación aguda sin fractura expuesta",
            "Inapetencia y letargo de más de 48 horas",
            "Fiebre persistente con decaimiento notable",
            "Tos paroxística frecuente",
            "Secreción ocular purulenta y blefaroespasmo",
            "Herida superficial lacerante"
        ],
        "horas_rango": (12.0, 72.0),
        "conciencia_pesos": [0.70, 0.28, 0.02],
        "hemorragia_prob": 0.08
    },
    # Baja
    {
        "urgencia": "Baja",
        "sintomas": [
            "Prurito y rascado auricular leve",
            "Consulta de rutina / Plan de vacunación",
            "Estornudos aislados sin secreción mucopurulenta",
            "Alopecia focalizada sin prurito intenso",
            "Halitosis y sarro dental sin dificultad de masticación",
            "Control de peso y chequeo preventivo",
            "Lagrimeo leve transparente"
        ],
        "horas_rango": (24.0, 168.0),
        "conciencia_pesos": [0.95, 0.05, 0.00],
        "hemorragia_prob": 0.00
    }
]

ESTADOS_CONCIENCIA = ["Alerta", "Deprimido", "Estuporoso/Comatoso"]
ESPECIES = ["Canino", "Felino"]

def generar_dataset_triaje(n_registros=1200):
    casos = []
    id_caso = 1
    
    # Generar casos balanceados/ponderados
    for patron in CASOS_CLINICOS_PATRONES:
        n_cat = n_registros // len(CASOS_CLINICOS_PATRONES)
        for _ in range(n_cat):
            especie = random.choice(ESPECIES)
            sintoma = random.choice(patron["sintomas"])
            horas = round(random.uniform(*patron["horas_rango"]), 1)
            conciencia = np.random.choice(ESTADOS_CONCIENCIA, p=patron["conciencia_pesos"])
            hemorragia = 1 if (random.random() < patron["hemorragia_prob"]) else 0
            
            casos.append({
                "id_caso": id_caso,
                "especie": especie,
                "sintoma_principal": sintoma,
                "tiempo_evolucion_hs": horas,
                "estado_conciencia": conciencia,
                "presencia_hemorragia": hemorragia,
                "nivel_urgencia": patron["urgencia"]
            })
            id_caso += 1
            
    df_triaje = pd.DataFrame(casos)
    # Desordenar aleatoriamente
    df_triaje = df_triaje.sample(frac=1.0, random_state=42).reset_index(drop=True)
    df_triaje["id_caso"] = range(1, len(df_triaje) + 1)
    
    path = os.path.join(DATA_DIR, "sintomas_triaje.csv")
    df_triaje.to_csv(path, index=False, encoding="utf-8")
    print(f"Dataset triaje guardado en: {path} ({len(df_triaje)} registros)")
    return df_triaje

if __name__ == "__main__":
    print("Iniciando generación de datos para VetCerca IA...")
    generar_dataset_veterinarias(100)
    generar_dataset_triaje(1500)
    print("¡Generación completada exitosamente!")
