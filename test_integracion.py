from typing import Iterator
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from Services.asistente_ia import InterpretacionSintoma
from app import app
from models.usuarios import verificar_contrasena
from routers import auth as auth_router
from routers import triaje as triaje_router
from routers.auth import (
    SESIONES_ACTIVAS,
    SESIONES_ADMINISTRADORES,
    SESIONES_VETERINARIAS,
)
from utils.geo import calcular_distancia_haversine
from utils import usuarios_store

USUARIO_CLIENTE = "maria_g2024"
PASSWORD_CLIENTE = "123456"


@pytest.fixture
def client() -> Iterator[TestClient]:
    api_client = TestClient(app)
    try:
        yield api_client
    finally:
        SESIONES_ACTIVAS.discard(USUARIO_CLIENTE)
        SESIONES_ACTIVAS.discard("demo")
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


def test_cliente_demo_con_mascota_y_login_admin(client: TestClient) -> None:
    response_cliente = client.post(
        "/auth/login",
        json={"usuario_o_email": "demo", "password": "1234"},
    )
    assert response_cliente.status_code == 200
    assert response_cliente.json()["tipo_usuario"] == "cliente"
    assert response_cliente.json()["id_cliente"] == 3

    mascotas = client.get("/mascotas/cliente/demo")
    assert mascotas.status_code == 200
    assert any(item["nombre"] == "Rocky" for item in mascotas.json())

    response_admin = client.post(
        "/auth/login",
        json={"usuario_o_email": "admin", "password": "1234"},
    )
    assert response_admin.status_code == 200
    assert response_admin.json()["tipo_usuario"] == "administrador"
    SESIONES_ADMINISTRADORES.discard(response_admin.json()["token_sesion"])


def test_registro_cliente_y_login(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        usuarios_store,
        "DATABASE_PATH",
        tmp_path / "usuarios.db",
    )
    username = f"alta_{uuid4().hex[:8]}"
    nombre = f"Usuario {username}"
    email = f"{username}@example.com"
    password = "ClaveSegura123"
    payload = {
        "rol": "cliente",
        "nombre_apellido": nombre,
        "username": username,
        "email": email,
        "password": password,
        "telefono": "",
    }
    cliente_creado = None

    try:
        response_registro = client.post("/auth/registro", json=payload)

        assert response_registro.status_code == 201
        cuenta = response_registro.json()
        assert cuenta["tipo_usuario"] == "cliente"
        assert cuenta["username"] == username
        cliente_creado = next(
            cliente
            for cliente in auth_router.CLIENTES_DB_OBJ
            if cliente.username == username
        )
        assert cliente_creado.contrasena_hash != password
        assert verificar_contrasena(password, cliente_creado.contrasena_hash)
        persistidos = usuarios_store.cargar_clientes_registrados()
        assert any(
            registro["username"] == username
            and registro["password_hash"] == cliente_creado.contrasena_hash
            for registro in persistidos
        )

        response_duplicado = client.post("/auth/registro", json=payload)
        assert response_duplicado.status_code == 409

        response_login = client.post(
            "/auth/login",
            json={"usuario_o_email": email, "password": password},
        )
        assert response_login.status_code == 200
        assert response_login.json()["username"] == username
    finally:
        if cliente_creado:
            auth_router.CLIENTES_DB_OBJ.remove(cliente_creado)
            auth_router.USUARIOS_DB[:] = [
                usuario
                for usuario in auth_router.USUARIOS_DB
                if usuario["username"] != username
            ]
            SESIONES_ACTIVAS.discard(username)


def test_alta_y_aprobacion_veterinaria(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        usuarios_store,
        "DATABASE_PATH",
        tmp_path / "usuarios.db",
    )
    username = f"vet_{uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "ClaveVeterinaria123"
    payload = {
        "rol": "veterinaria",
        "nombre_apellido": "Profesional de prueba",
        "username": username,
        "email": email,
        "password": password,
        "telefono": "1100000000",
        "matricula_profesional": "MP-12345",
        "especialidad_principal": "Clínica médica",
        "nombre_veterinaria": "Clínica de prueba",
        "direccion_veterinaria": "Av. Siempre Viva 123",
        "barrio": "Palermo",
    }
    id_veterinaria = None
    token_admin = None
    token_veterinaria = None

    try:
        response_registro = client.post("/auth/registro", json=payload)
        assert response_registro.status_code == 201
        assert response_registro.json()["estado_solicitud"] == "PENDIENTE"
        id_veterinaria = next(
            solicitud["id_veterinaria"]
            for solicitud in auth_router.SOLICITUDES_VETERINARIAS
            if solicitud["username"] == username
        )

        response_login_pendiente = client.post(
            "/auth/login",
            json={"usuario_o_email": username, "password": password},
        )
        assert response_login_pendiente.status_code == 403

        response_admin = client.post(
            "/auth/login",
            json={"usuario_o_email": "admin", "password": "1234"},
        )
        assert response_admin.status_code == 200
        token_admin = response_admin.json()["token_sesion"]
        headers_admin = {"Authorization": f"Bearer {token_admin}"}

        response_listado = client.get(
            "/auth/administracion/solicitudes-veterinarias",
            headers=headers_admin,
        )
        assert response_listado.status_code == 200
        assert any(
            item["username"] == username for item in response_listado.json()
        )
        assert "password_hash" not in response_listado.json()[0]

        response_aprobacion = client.post(
            f"/auth/administracion/solicitudes-veterinarias/{id_veterinaria}/aprobar",
            headers=headers_admin,
        )
        assert response_aprobacion.status_code == 200

        response_login_veterinaria = client.post(
            "/auth/login",
            json={"usuario_o_email": email, "password": password},
        )
        assert response_login_veterinaria.status_code == 200
        token_veterinaria = response_login_veterinaria.json()["token_sesion"]
        response_perfil = client.get(
            "/auth/veterinaria/perfil",
            headers={"Authorization": f"Bearer {token_veterinaria}"},
        )
        assert response_perfil.status_code == 200
        assert response_perfil.json()["nombre"] == "Clínica de prueba"
    finally:
        if id_veterinaria is not None:
            auth_router.SOLICITUDES_VETERINARIAS[:] = [
                solicitud
                for solicitud in auth_router.SOLICITUDES_VETERINARIAS
                if solicitud["id_veterinaria"] != id_veterinaria
            ]
            auth_router.VETERINARIAS_REGISTRADAS.pop(id_veterinaria, None)
        if token_admin:
            SESIONES_ADMINISTRADORES.discard(token_admin)
        if token_veterinaria:
            SESIONES_VETERINARIAS.pop(token_veterinaria, None)


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
