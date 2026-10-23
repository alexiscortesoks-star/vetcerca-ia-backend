from typing import Dict


class AsistenteIA:
    def __init__(self, modelo_llm: str = "GPT-4o", timeout_ms: int = 3000) -> None:
        self.modelo_llm = modelo_llm
        self.timeout_ms = timeout_ms

    def procesar_triaje(self, sintomas: str, mascota) -> Dict[str, str]:
        sintomas_lower = sintomas.lower()
        if any(
            palabra in sintomas_lower
            for palabra in ["obstruccion", "convulsion", "sangrado", "dolor"]
        ):
            return {
                "nivel_urgencia": "ALTA",
                "especialidad_sugerida": "Urología / Urgencias",
                "primeros_auxilios": (
                    "Mantener al animal en calma y trasladar inmediatamente."
                ),
            }
        return {
            "nivel_urgencia": "MEDIA",
            "especialidad_sugerida": "Clínica General",
            "primeros_auxilios": "Observar evolución y pedir turno.",
        }

    def ejecutar_fallback(self, sintomas: str) -> Dict[str, str]:
        return {
            "nivel_urgencia": "MEDIA",
            "especialidad_sugerida": "Guardia General",
            "primeros_auxilios": "Acudir a la veterinaria más cercana.",
        }