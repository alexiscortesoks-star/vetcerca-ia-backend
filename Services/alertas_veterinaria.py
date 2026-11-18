from typing import Any


ALERTAS_VETERINARIAS: list[dict[str, Any]] = []
MASCOTAS_POR_ALERTA: dict[int, Any] = {}
_ultimo_id_alerta = 900


def registrar_alerta_veterinaria(alerta: dict[str, Any], mascota: Any) -> None:
    ALERTAS_VETERINARIAS.insert(0, alerta)
    MASCOTAS_POR_ALERTA[alerta["id_alerta"]] = mascota


def generar_id_alerta() -> int:
    global _ultimo_id_alerta
    ultimo_registrado = max(
        (alerta["id_alerta"] for alerta in ALERTAS_VETERINARIAS),
        default=900,
    )
    _ultimo_id_alerta = max(_ultimo_id_alerta, ultimo_registrado) + 1
    return _ultimo_id_alerta
