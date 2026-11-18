import sqlite3
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "usuarios.db"


def _conectar() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(DATABASE_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes_registrados (
            id_cliente INTEGER PRIMARY KEY,
            username TEXT NOT NULL COLLATE NOCASE UNIQUE,
            email TEXT NOT NULL COLLATE NOCASE UNIQUE,
            nombre_apellido TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            telefono TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS solicitudes_veterinarias (
            id_veterinaria INTEGER PRIMARY KEY,
            username TEXT NOT NULL COLLATE NOCASE UNIQUE,
            email TEXT NOT NULL COLLATE NOCASE UNIQUE,
            nombre_apellido TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            telefono TEXT NOT NULL DEFAULT '',
            matricula_profesional TEXT NOT NULL,
            especialidad_principal TEXT NOT NULL,
            nombre_veterinaria TEXT NOT NULL,
            direccion_veterinaria TEXT NOT NULL,
            barrio TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'PENDIENTE'
        )
        """
    )
    return conexion


def cargar_clientes_registrados() -> list[dict[str, Any]]:
    with _conectar() as conexion:
        filas = conexion.execute(
            """
            SELECT id_cliente, username, email, nombre_apellido, password_hash,
                   telefono
            FROM clientes_registrados
            ORDER BY id_cliente
            """
        ).fetchall()
    return [dict(fila) for fila in filas]


def guardar_cliente_registrado(
    *,
    id_minimo: int,
    username: str,
    email: str,
    nombre_apellido: str,
    password_hash: str,
    telefono: str,
) -> int:
    with _conectar() as conexion:
        conexion.execute("BEGIN IMMEDIATE")
        ultimo_id = conexion.execute(
            "SELECT COALESCE(MAX(id_cliente), ?) FROM clientes_registrados",
            (id_minimo,),
        ).fetchone()[0]
        id_cliente = max(id_minimo, ultimo_id) + 1
        conexion.execute(
            """
            INSERT INTO clientes_registrados (
                id_cliente, username, email, nombre_apellido, password_hash,
                telefono
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                id_cliente,
                username,
                email,
                nombre_apellido,
                password_hash,
                telefono,
            ),
        )
    return id_cliente


def cargar_solicitudes_veterinarias() -> list[dict[str, Any]]:
    with _conectar() as conexion:
        filas = conexion.execute(
            """
            SELECT id_veterinaria, username, email, nombre_apellido, password_hash,
                   telefono, matricula_profesional, especialidad_principal,
                   nombre_veterinaria, direccion_veterinaria, barrio, estado
            FROM solicitudes_veterinarias
            ORDER BY id_veterinaria
            """
        ).fetchall()
    return [dict(fila) for fila in filas]


def guardar_solicitud_veterinaria(
    *,
    id_minimo: int,
    username: str,
    email: str,
    nombre_apellido: str,
    password_hash: str,
    telefono: str,
    matricula_profesional: str,
    especialidad_principal: str,
    nombre_veterinaria: str,
    direccion_veterinaria: str,
    barrio: str,
) -> int:
    with _conectar() as conexion:
        conexion.execute("BEGIN IMMEDIATE")
        ultimo_id = conexion.execute(
            "SELECT COALESCE(MAX(id_veterinaria), ?) "
            "FROM solicitudes_veterinarias",
            (id_minimo,),
        ).fetchone()[0]
        id_veterinaria = max(id_minimo, ultimo_id) + 1
        conexion.execute(
            """
            INSERT INTO solicitudes_veterinarias (
                id_veterinaria, username, email, nombre_apellido, password_hash,
                telefono, matricula_profesional, especialidad_principal,
                nombre_veterinaria, direccion_veterinaria, barrio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id_veterinaria,
                username,
                email,
                nombre_apellido,
                password_hash,
                telefono,
                matricula_profesional,
                especialidad_principal,
                nombre_veterinaria,
                direccion_veterinaria,
                barrio,
            ),
        )
    return id_veterinaria


def listar_solicitudes_veterinarias_pendientes() -> list[dict[str, Any]]:
    with _conectar() as conexion:
        filas = conexion.execute(
            """
            SELECT id_veterinaria, username, email, nombre_apellido, telefono,
                   matricula_profesional, especialidad_principal,
                   nombre_veterinaria, direccion_veterinaria, barrio, estado
            FROM solicitudes_veterinarias
            WHERE estado = 'PENDIENTE'
            ORDER BY id_veterinaria
            """
        ).fetchall()
    return [dict(fila) for fila in filas]


def actualizar_estado_solicitud_veterinaria(
    id_veterinaria: int,
    estado: str,
) -> bool:
    with _conectar() as conexion:
        resultado = conexion.execute(
            """
            UPDATE solicitudes_veterinarias
            SET estado = ?
            WHERE id_veterinaria = ? AND estado = 'PENDIENTE'
            """,
            (estado, id_veterinaria),
        )
    return resultado.rowcount == 1
