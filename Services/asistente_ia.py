import os
from typing import Any, Dict


class AsistenteIA:
    def __init__(
        self,
        api_key: str = "",
        modelo_principal: str = "Gemini 1.5 Pro / API",
        modo_fallback: bool = False,
        modelo_llm: str = "",
        timeout_ms: int = 3000,
    ) -> None:
        self.api_key: str = api_key or os.getenv("GEMINI_API_KEY", "")
        self.modelo_principal: str = modelo_llm or modelo_principal
        self.modo_fallback: bool = modo_fallback
        self.timeout_ms: int = timeout_ms

    # Alias para compatibilidad
    @property
    def modelo_llm(self) -> str:
        return self.modelo_principal

    @modelo_llm.setter
    def modelo_llm(self, valor: str) -> None:
        self.modelo_principal = valor

    def clasificar_urgencia(self, sintomas: str, especie: str = "Canino") -> Dict[str, str]:
        """
        Clasifica la urgencia en base a los síntomas y la especie.
        Retorna un dict con: nivel_urgencia, diagnostico_preliminar, especialidad_sugerida (y primeros_auxilios).
        """
        if self.modo_fallback:
            return self.ejecutar_fallback(sintomas)

        sintomas_lower = sintomas.lower()

        # Detección de patrones de urgencia alta
        if any(
            palabra in sintomas_lower
            for palabra in [
                "obstruccion",
                "convulsion",
                "sangrado",
                "dolor",
                "dificultad respiratoria",
                "inconsciente",
                "envenenamiento",
                "intoxicacion",
                "traumatismo",
            ]
        ):
            return {
                "nivel_urgencia": "ALTA",
                "diagnostico_preliminar": (
                    f"Posible cuadro crítico en {especie}. Requiere atención médica inmediata."
                ),
                "especialidad_sugerida": "Urología / Urgencias Quirúrgicas",
                "primeros_auxilios": (
                    "Mantener al animal en calma, evitar movimientos bruscos y trasladar de inmediato."
                ),
            }

        # Detección de patrones de urgencia media
        if any(
            palabra in sintomas_lower
            for palabra in ["vomito", "diarrea", "cojera", "inapetencia", "fiebre", "decaido"]
        ):
            return {
                "nivel_urgencia": "MEDIA",
                "diagnostico_preliminar": (
                    f"Sintomatología moderada en {especie}. Requiere evaluación clínica en el día."
                ),
                "especialidad_sugerida": "Clínica Médica General",
                "primeros_auxilios": (
                    "Ofrecer agua fresca en pequeñas cantidades, no medicar sin prescripción y monitorear."
                ),
            }

        # Urgencia baja por defecto
        return {
            "nivel_urgencia": "BAJA",
            "diagnostico_preliminar": (
                f"Cuadro no urgente en {especie}. Seguimiento clínico rutinario."
            ),
            "especialidad_sugerida": "Clínica General / Consulta Programada",
            "primeros_auxilios": "Observar evolución general y agendar turno veterinario regular.",
        }

    def procesar_triaje(self, sintomas: str, mascota: Any) -> Dict[str, str]:
        """Método de compatibilidad con llamados anteriores."""
        especie_nombre = "Animal"
        if hasattr(mascota, "raza") and hasattr(mascota.raza, "especie"):
            especie_nombre = getattr(mascota.raza.especie, "nombre", "Animal")
        return self.clasificar_urgencia(sintomas, especie_nombre)

    def ejecutar_fallback(self, sintomas: str) -> Dict[str, str]:
        """Motor heurístico de contingencia en caso de timeout o indisponibilidad del LLM."""
        return {
            "nivel_urgencia": "MEDIA",
            "diagnostico_preliminar": (
                "Evaluación de contingencia heurística por falla temporal de conectividad con IA."
            ),
            "especialidad_sugerida": "Guardia General",
            "primeros_auxilios": "Acudir a la veterinaria más cercana para revisión directa.",
        }
