"""
Entrenamiento y Evaluación del Clasificador de Triaje Clínico - VetCerca IA
Algoritmo: Random Forest Classifier
Métrica prioritaria: Recall (Sensibilidad) en clases 'Alta' y 'Emergencia Crítica'.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline

from src.pipeline_limpieza import (
    cargar_datos,
    crear_preprocesador,
    CAT_FEATURES,
    NUM_FEATURES,
    BIN_FEATURES,
    TARGET
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelo_triaje.joblib")

def entrenar_modelo():
    df = cargar_datos()
    
    X = df[CAT_FEATURES + NUM_FEATURES + BIN_FEATURES]
    y = df[TARGET]
    
    # División estratificada 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    preprocesador = crear_preprocesador()
    
    # Random Forest con balanceo de clases para penalizar errores en cuadros críticos
    clasificador = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        class_weight="balanced",
        random_state=42
    )
    
    pipeline_completo = Pipeline([
        ("preprocesador", preprocesador),
        ("clasificador", clasificador)
    ])
    
    print("Entrenando modelo Random Forest...")
    pipeline_completo.fit(X_train, y_train)
    
    # Evaluación en Test
    y_pred = pipeline_completo.predict(X_test)
    
    print("\n" + "=" * 60)
    print("REPORTE DE CLASIFICACIÓN (MÉTRICA PRIORITARIA: RECALL)")
    print("=" * 60)
    report = classification_report(y_test, y_pred, digits=4)
    print(report)
    
    print("\nMATRIZ DE CONFUSIÓN:")
    labels = ["Baja", "Moderada", "Alta", "Emergencia Crítica"]
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=[f"Real: {l}" for l in labels], columns=[f"Pred: {l}" for l in labels])
    print(cm_df)
    
    # Guardar modelo entrenado
    joblib.dump(pipeline_completo, MODEL_SAVE_PATH)
    print(f"\nModelo serializado exitosamente en: {MODEL_SAVE_PATH}")
    
    return pipeline_completo

def cargar_modelo(path=MODEL_SAVE_PATH):
    if not os.path.exists(path):
        print(f"Modelo no encontrado en {path}. Entrenando automáticamente...")
        return entrenar_modelo()
    return joblib.load(path)

def predecir_urgencia(especie: str, sintoma: str, horas: float, conciencia: str, hemorragia: int) -> dict:
    """
    Realiza la inferencia de nivel de urgencia a partir de variables clínicas individuales.
    """
    modelo = cargar_modelo()
    datos_df = pd.DataFrame([{
        "especie": especie,
        "sintoma_principal": sintoma,
        "tiempo_evolucion_hs": float(horas),
        "estado_conciencia": conciencia,
        "presencia_hemorragia": int(hemorragia)
    }])
    
    prediccion = modelo.predict(datos_df)[0]
    probabilidades = modelo.predict_proba(datos_df)[0]
    clases = list(modelo.classes_)
    prob_dict = {clase: round(float(prob), 4) for clase, prob in zip(clases, probabilidades)}
    
    return {
        "nivel_urgencia": prediccion,
        "probabilidades": prob_dict,
        "confianza": round(float(np.max(probabilidades)), 4)
    }

if __name__ == "__main__":
    entrenar_modelo()
