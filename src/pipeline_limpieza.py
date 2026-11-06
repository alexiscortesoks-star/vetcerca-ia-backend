"""
Pipeline de Preprocesamiento y Limpieza de Datos - VetCerca IA
Carga, normaliza, codifica e imputa variables para el modelado supervisado.
"""

import os
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "sintomas_triaje.csv")

# Definición de columnas
CAT_FEATURES = ["especie", "sintoma_principal", "estado_conciencia"]
NUM_FEATURES = ["tiempo_evolucion_hs"]
BIN_FEATURES = ["presencia_hemorragia"]
TARGET = "nivel_urgencia"

def cargar_datos(path=DATA_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el dataset en: {path}")
    df = pd.read_csv(path)
    return df

def crear_preprocesador():
    """
    Crea un ColumnTransformer con:
    - OneHotEncoder para variables categóricas (especie, sintoma, estado_conciencia)
    - StandardScaler e imputación mediana para variables numéricas (tiempo_evolucion_hs)
    - Passthrough para variables binarias
    """
    pipeline_num = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    
    pipeline_cat = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", pipeline_num, NUM_FEATURES),
            ("cat", pipeline_cat, CAT_FEATURES),
            ("bin", "passthrough", BIN_FEATURES)
        ]
    )
    return preprocessor

if __name__ == "__main__":
    df = cargar_datos()
    print("Muestra de datos de triaje:")
    print(df.head())
    print("\nDistribución del target:")
    print(df[TARGET].value_counts())
