from typing import Iterator
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from Services.asistente_ia import InterpretacionSintoma
from app import app
from routers import triaje as triaje_router
from routers.auth import SESIONES_ACTIVAS
from utils.geo import calcular_distancia_haversine

USUARIO_CLIENTE = "maria_g2024"
PASSWORD_CLIENTE = "123456"


@pytest.fixture
def client() -> Iterator[TestClient]:
    api_client = TestClient(app)
    try:
        yield api_client
    finally:
        SESIONES_ACTIVAS.discard(USUARIO_CLIENTE)
        api_client.close()


def _iniciar_sesion_cliente(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={
            "usuario_o_email": USUARIO_CLIENTE,
            "password": PASSWORD_CLIENTE,
        },
    )
    assert response.status_code == 200
    assert response.json()["token_sesion"]


def test_login_credenciales(client: TestClient) -> None:
    response_valido = client.post(
        "/auth/login",
        json={
            "usuario_o_email": USUARIO_CLIENTE,
            "password": PASSWORD_CLIENTE,
        },
    )

    assert response_valido.status_code == 200
    assert response_valido.json()["tipo_usuario"] == "cliente"
    assert response_valido.json()["token_sesion"]

    response_invalido = client.post(
        "/auth/login",
        json={
            "usuario_o_email": USUARIO_CLIENTE,
            "password": "clave-incorrecta",
        },
    )
    assert response_invalido.status_code == 401


def test_gestion_mascotas(client: TestClient) -> None:
    _iniciar_sesion_cliente(client)

    response_lista = client.get(f"/mascotas/cliente/{USUARIO_CLIENTE}")
    assert response_lista.status_code == 200
    mascotas = response_lista.json()
    assert isinstance(mascotas, list)
    assert any(mascota["nombre"] == "Mimi" for mascota in mascotas)

    nombre_prueba = f"Pytest-{uuid4().hex[:8]}"
    payload = {
        "username_cliente": USUARIO_CLIENTE,
        "nombre": nombre_prueba,
        "especie": "Canino",
        "raza": "Mestizo",
        "sexo": "Macho",
        "peso_kg": 8.4,
        "fecha_nacimiento": "2021-06-15",
    }

    id_mascota_creada = None
    try:
        response_alta = client.post("/mascotas/", json=payload)
        assert response_alta.status_code == 201
        mascota_creada = response_alta.json()
        id_mascota_creada = mascota_creada["id_mascota"]
        assert mascota_creada["nombre"] == nombre_prueba
        assert mascota_creada["username_cliente"] == USUARIO_CLIENTE
    finally:
        if id_mascota_creada is not None:
            response_baja = client.delete(
                f"/mascotas/{id_mascota_creada}",
                params={"username_cliente": USUARIO_CLIENTE},
            )
            assert response_baja.status_code == 200


def test_triaje_urgencia_normal(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    assistant = triaje_router.asistente_ia
    monkeypatch.setattr(assistant, "api_key", "test-api-key")

    def interpretar_sintoma(
        *, sintomas: str, especie: str
    ) -> InterpretacionSintoma:
        assert sintomas == "Dificultad para orinar y maullidos de dolor"
        assert especie == "Felino"
        return InterpretacionSintoma(
            sintoma_catalogo="Dificultad marcada para orinar con dolor intenso",
            confianza=0.95,
            pregunta_aclaratoria="",
        )

    monkeypatch.setattr(
        assistant,
        "_interpretar_sintoma_con_gemini",
        interpretar_sintoma,
    )
    payload = {
        "nombre_mascota": "Toby",
        "especie": "Felino",
        "sintoma_principal": "Dificultad para orinar y maullidos de dolor",
        "tiempo_evolucion_hs": 2.0,
        "estado_conciencia": "Alerta",
        "presencia_hemorragia": 0,
        "latitud_cliente": -34.562,
        "longitud_cliente": -58.455,
    }

    response = client.post(
        "/triaje/evaluar?despachar_alerta=false",
        json=payload,
    )

    assert response.status_code == 200
    resultado = response.json()
    assert resultado["nivel_urgencia"] == "Alta"
    assert resultado["diagnostico_preliminar"]
    assert resultado["veterinaria_cercana"] != "No disponible"
    assert resultado["distancia_km"] > 0
    assert resultado["alerta_despachada"] is False

    distancia_haversine = calcular_distancia_haversine(
        payload["latitud_cliente"],
        payload["longitud_cliente"],
        resultado["latitud_veterinaria"],
        resultado["longitud_veterinaria"],
    )
    assert resultado["distancia_km"] == pytest.approx(
        distancia_haversine,
        abs=0.01,
    )


def test_triaje_caso_adverso_fallback(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    assistant = triaje_router.asistente_ia
    monkeypatch.setattr(assistant, "api_key", "test-api-key")

    def falla_conexion_llm(*, sintomas: str, especie: str) -> InterpretacionSintoma:
        raise HTTPException(
            status_code=503,
            detail="Gemini no disponible durante la prueba.",
        )

    monkeypatch.setattr(
        assistant,
        "_interpretar_sintoma_con_gemini",
        falla_conexion_llm,
    )
    fallback_original = assistant.ejecutar_fallback

    with patch.object(
        assistant,
        "ejecutar_fallback",
        wraps=fallback_original,
    ) as fallback:
        response_con_senales = client.post(
            "/triaje/evaluar?despachar_alerta=false",
            json={
                "nombre_mascota": "Toby",
                "especie": "Felino",
                "sintoma_principal": (
                    "Dificultad para orinar y maullidos de dolor"
                ),
                "tiempo_evolucion_hs": 2.0,
                "estado_conciencia": "Alerta",
                "presencia_hemorragia": 0,
            },
        )

        assert response_con_senales.status_code == 200
        resultado_con_senales = response_con_senales.json()
        assert resultado_con_senales["nivel_urgencia"] == "Alta"
        assert "heurística local" in resultado_con_senales["diagnostico_preliminar"]
        fallback.assert_called_once()

        response_ambiguo = client.post(
            "/triaje/evaluar?despachar_alerta=false",
            json={
                "nombre_mascota": "Toby",
                "especie": "Felino",
                "sintomas": "Se siente raro",
                "tiempo_evolucion_hs": 2.0,
                "estado_conciencia": "Alerta",
                "presencia_hemorragia": 0,
            },
        )

        assert response_ambiguo.status_code == 200
        resultado_ambiguo = response_ambiguo.json()
        assert resultado_ambiguo["nivel_urgencia"] == "No concluyente"
        assert resultado_ambiguo["pregunta_aclaratoria"]
        assert fallback.call_count == 2
