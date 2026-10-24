# 🐾 VetCerca IA - Backend &amp; Sistema de Triaje Veterinario

**VetCerca IA** es una plataforma backend desarrollada en Python y FastAPI que optimiza la atención veterinaria de urgencia. Combina evaluación de síntomas mediante **Inteligencia Artificial (LLM con sistema de contingencia/fallback)**, geolocalización precisa mediante la **fórmula de Haversine**, autenticación de usuarios y un módulo de **despacho automático de alertas de urgencia a clínicas de guardia** vía notificaciones en tiempo real.

---

## 🚀 Funcionalidades Principales

* 🩺 **Triaje Automatizado con IA (`AsistenteIA`)**:

  * Procesa los síntomas reportados por el cliente y determina el nivel de riesgo (`ALTA`, `MEDIA`, `BAJA`), sugiriendo la especialidad veterinaria y primeros auxilios.
  * Incluye mecanismo de **fallback determinista** en caso de timeout o falla en la API del LLM.
* 📍 **Geolocalización GPS (`Haversine`)**:

  * Calcula la distancia exacta en kilómetros entre la posición GPS actual del cliente y las veterinarias de guardia disponibles.
  * Ordena y filtra las clínicas más cercanas dentro de un radio configurable.
* 🚨 **Despacho de Alertas de Urgencia en Tiempo Real**:

  * Ante diagnósticos con urgencia **ALTA**, el sistema instancia `AlertaUrgencia` y ejecuta `ServicioNotificacion` para alertar inmediatamente a la guardia médica por WhatsApp/Push, evitando saturar clínicas con casos leves.
* 🔐 **Autenticación y Seguridad de Sesiones**:

  * Control de acceso basado en roles (`Cliente` y `UsuarioVeterinario`).
  * Bloqueo de seguridad (`401 Unauthorized`) que impide a usuarios no autenticados registrar o visualizar mascotas.
* 🐾 **Gestión de Pacientes e Historial Médico**:

  * Mapeo completo de especies (incluyendo especies exóticas autorizadas), razas y mascotas vinculadas a la cuenta del dueño.
  * Cálculo dinámico de la edad estimada y registro de atenciones en el historial clínico.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.12
* **Framework Web:** FastAPI
* **Servidor ASGI:** Uvicorn
* **Validación de Datos y Schemas:** Pydantic v2
* **Matemática y Geolocalización:** Módulo `math` (Fórmula de Haversine)
* **Arquitectura:** Programación Orientada a Objetos (POO), Clean Architecture y Routers de FastAPI.

---

## 📁 Estructura del Proyecto

```
vetcerca_ia_backend/
│
├── app.py                   # Punto de entrada principal e integración de la API FastAPI
├── requirements.txt         # Dependencias del proyecto (FastAPI, Uvicorn, Pydantic, httpx)
├── vetcerca-readme.md       # Documentación técnica y guía de ejecución
│
├── models/                  # Dominio y Lógica de Negocio (POO)
│   ├── usuarios.py          # Clase abstracta Usuario, Cliente y UsuarioVeterinario
│   ├── mascotas.py          # Clases Mascota, Especie, Raza e HistorialMedico
│   ├── veterinarias.py      # Clase Veterinaria y gestión de guardias 24hs
│   └── triaje.py            # Clases ConsultaTriaje y AlertaUrgencia
│
├── schemas/                 # Validación de Entradas/Salidas HTTP (Pydantic)
│   ├── auth.py              # LoginRequest y LoginResponse
│   ├── mascotas.py          # MascotaCreate y MascotaResponse
│   └── triaje.py            # TriajeRequest y TriajeResponse
│
├── routers/                 # Endpoints desacoplados de FastAPI
│   ├── auth.py              # Router /auth (Login y gestión de sesiones)
│   ├── mascotas.py          # Router /mascotas (ABM de pacientes y dueño)
│   └── triaje.py            # Router /triaje (Evaluación de IA y Alertas)
│
├── services/                # Servicios de Infraestructura
│   ├── asistente_ia.py      # Procesamiento con LLM y reglas de fallback
│   └── notificador.py       # ServicioNotificacion (Despacho WhatsApp / API)
│
└── utils/                   # Utilidades matemáticas e infraestructura
    └── geo.py               # Función de cálculo de distancia Haversine GPS

```

---

## ⚙️ Instalación y Ejecución Rápida

### 1\. Clonar o descargar el proyecto

Poscionarse en la carpeta raíz del backend `vetcerca_ia_backend`.

### 2\. Crear y activar el entorno virtual

```
# En Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# En Windows:
python -m venv venv
.\venv\Scripts\activate

```

### 3\. Instalar dependencias

```
pip install -r requirements.txt

```

### 4\. Iniciar el servidor de desarrollo

```
uvicorn app:app --reload

```

El servidor quedará ejecutándose localmente en: `127.0.0.1:8000`

---

## 📖 Documentación Interactiva de la API (Swagger UI)

Una vez iniciado el servidor, acceder a la documentación interactiva OpenAPI en:

👉 **`127.0.0.1:8000/docs`** o **`localhost:8000/docs`**

---

## 🖥️ Frontend local

Iniciá el backend con `uvicorn app:app --reload`. En otra terminal, desde la
raíz del proyecto, serví los archivos frontend:

```powershell
python -m http.server 5500 --directory frontend
```

Abrí `http://127.0.0.1:5500` para iniciar sesión y acceder al formulario de
triaje. CORS está habilitado para `localhost` y `127.0.0.1` en los puertos
5500 y 5501. La ubicación del triaje utiliza las coordenadas predeterminadas
de Buenos Aires mientras no se conecte la geolocalización del dispositivo.

---

## 📌 Resumen de Endpoints

| Método | Endpoint                         | Descripción                                                                              | Requiere Auth |
| ------ | -------------------------------- | ---------------------------------------------------------------------------------------- | ------------- |
| `POST` | `/auth/login`                    | Inicia sesión de cliente y activa la sesión en memoria                                   | ❌             |
| `GET`  | `/mascotas/cliente/{id_cliente}` | Devuelve la lista de mascotas del cliente autenticado                                    | 🌐 Sí         |
| `POST` | `/mascotas/`                     | Registra una nueva mascota vinculada al cliente logueado                                 | 🌐 Sí         |
| `POST` | `/triaje/evaluar`                | Evalúa síntomas con IA, calcula vet más cercana por GPS y despacha alerta si es **ALTA** | ❌             |
| `GET`  | `/veterinarias/cercanas`         | Busca y ordena clínicas por distancia GPS según un radio en km                           | ❌             |

---

## 🤖 Integración Dual de Inteligencia Artificial

1. **IA Integrada en el Producto (`AsistenteIA`)**:

  * Implementa procesamiento de lenguaje para clasificar síntomas veterinarios.
  * Cuenta con **sistema de resiliencia / fallback** para garantizar disponibilidad operativa continua.
2. **IA como Copiloto de Desarrollo**:

  * Asistencia en el diseño de arquitectura POO, encapsulamiento y refactorización a Clean Architecture.
  * Generación y optimización de algoritmos de geolocalización (Haversine).
  * Automatización de pruebas de integración con `httpx` y `TestClient`.