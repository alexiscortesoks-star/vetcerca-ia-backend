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

Abrí `http://127.0.0.1:5500` para ver la portada y consultar clínicas cercanas.
Para cargar síntomas y recibir una orientación de triaje primero hay que iniciar
sesión desde la portada. Después vas a encontrar un espacio privado para cargar
y gestionar tus mascotas, ver sus datos generales e iniciar el triaje por separado.
El resultado se presenta en lenguaje claro e incluye la urgencia estimada, los
pasos sugeridos, la guardia cercana y su ubicación. Desde el dashboard también
podés consultar el historial clínico.
El navegador solicitará permiso para compartir la
ubicación; si no está disponible, se usarán coordenadas predeterminadas de
Buenos Aires. CORS está habilitado para `localhost` y `127.0.0.1` en los
puertos 5500 y 5501.

### Acceso de veterinarias (demostración)

El mismo formulario de acceso identifica si la cuenta es de cliente o
veterinaria y abre el panel correspondiente. Las credenciales locales de
demostración de veterinaria son `admin` / `1234`.
El perfil de demostración muestra la clínica configurada en el backend.
Podés reemplazar estas credenciales configurando `VETCERCA_VET_ADMIN_USER` y
`VETCERCA_VET_ADMIN_PASSWORD` antes de iniciar FastAPI. Este acceso usa datos
en memoria y no debe publicarse en Internet con las credenciales por defecto.

### Compartir la demo en una red local

Para que tus compañeros la prueben conectados a la misma red Wi-Fi:

1. Averiguá la IP local de tu computadora con `ipconfig` (por ejemplo,
   `192.168.1.50`).
2. En PowerShell, iniciá el backend permitiendo el origen de la página:

   ```powershell
   $env:VETCERCA_CORS_ORIGINS = "http://192.168.1.50:5500"
   python -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```

3. En otra terminal iniciá el frontend para la red local:

   ```powershell
   python -m http.server 5500 --bind 0.0.0.0 --directory frontend
   ```

4. Compartí `http://192.168.1.50:5500` con tus compañeros. Si Windows muestra
   un aviso del firewall, permití el acceso en la red privada.

Esto es solo para una prueba en una red de confianza. No abras los puertos del
router ni publiques la demo directamente en Internet: los usuarios y datos son
de demostración y la autenticación aún no es adecuada para producción.

---

## 📌 Resumen de Endpoints

| Método | Endpoint                         | Descripción                                                                              | Requiere Auth |
| ------ | -------------------------------- | ---------------------------------------------------------------------------------------- | ------------- |
| `POST` | `/auth/login`                    | Inicia sesión unificada y devuelve el tipo de perfil (cliente o veterinaria)             | ❌             |
| `POST` | `/auth/veterinaria/login`        | Inicia sesión de demostración de una veterinaria                                        | ❌             |
| `GET`  | `/auth/veterinaria/perfil`       | Consulta el perfil de la veterinaria usando token Bearer                                 | 🌐 Sí         |
| `GET`  | `/mascotas/cliente/{identificador_cliente}` | Devuelve mascotas usando ID o username del cliente autenticado                  | 🌐 Sí         |
| `POST` | `/mascotas/`                     | Registra una nueva mascota vinculada al cliente logueado                                 | 🌐 Sí         |
| `PUT`  | `/mascotas/{id_mascota}`         | Actualiza una mascota del usuario autenticado                                             | 🌐 Sí         |
| `DELETE` | `/mascotas/{id_mascota}?username_cliente={username}` | Elimina una mascota propia                         | 🌐 Sí         |
| `GET`  | `/mascotas/{id_mascota}/historial?username_cliente={username}` | Consulta historial clínico propio       | 🌐 Sí         |
| `POST` | `/triaje/evaluar`                | Evalúa síntomas con IA, calcula vet más cercana por GPS y despacha alerta si es **ALTA** | ❌             |
| `GET`  | `/veterinarias/cercanas`         | Busca y ordena clínicas por distancia GPS según un radio en km                           | ❌             |

### Datos de clínicas

El catálogo incluye dos candidatos de CABA con horario `24/7` indicado en
OpenStreetMap, pero pendiente de confirmación directa:

- Centro Médico Veterinario Belgrano, Amenábar 2214, Belgrano ([ficha OSM](https://www.openstreetmap.org/node/2276920088)).
- Panda, Av. Ruiz Huidobro 4771, Saavedra ([ficha OSM](https://www.openstreetmap.org/node/8067203564), [sitio oficial](https://www.veterinariapanda.com.ar/)).

La API los muestra como candidatos, pero no los trata como guardias disponibles
para asignación de triaje. No se encontró un teléfono verificable en las fuentes
consultadas. Los datos de ubicación y horario proceden de OpenStreetMap bajo
ODbL. Atribución: © OpenStreetMap contributors
([licencia](https://www.openstreetmap.org/copyright)).

---

## 🤖 Integración Dual de Inteligencia Artificial

1. **IA Integrada en el Producto (`AsistenteIA`)**:

  * Implementa procesamiento de lenguaje para clasificar síntomas veterinarios.
  * Cuenta con **sistema de resiliencia / fallback** para garantizar disponibilidad operativa continua.
2. **IA como Copiloto de Desarrollo**:

  * Asistencia en el diseño de arquitectura POO, encapsulamiento y refactorización a Clean Architecture.
  * Generación y optimización de algoritmos de geolocalización (Haversine).
  * Automatización de pruebas de integración con `httpx` y `TestClient`.

---

## 🏛️ ESPECIFICACIÓN TÉCNICA FORMAL: VETCERCA IA (POO + CASOS DE USO)

### 1. Diagrama de Clases (Arquitectura Orientada a Objetos)

#### Módulo: Autenticación y Usuarios (Herencia)
* **`Usuario` (Clase Base / Abstracta `ABC`):**
  * **Atributos privados:**
    * `- _id_usuario: int`
    * `- _username: str` (alfanumérico único)
    * `- _email: str` (único)
    * `- _contrasena_hash: str`
    * `- _fecha_registro: datetime`
    * `- _avatar_url: Optional[str]`
    * `- _telefono: str`
  * **Métodos públicos:**
    * `+ verificar_credenciales(usuario_o_email: str, password: str) -> bool`
    * `+ cambiar_contrasena(nueva_contrasena: str) -> None`
* **`Cliente` (Especialización de `Usuario`):**
  * **Atributos privados:**
    * `- _direccion: str`
    * `- _latitud: float`
    * `- _longitud: float`
    * `- _telefono: str`
  * **Relaciones:**
    * Composición con `Mascota` (1 a 1..*): Un cliente posee una o varias mascotas registradas (`_mascotas: List[Mascota]`).
* **`UsuarioVeterinario` (Especialización de `Usuario`):**
  * **Atributos privados:**
    * `- _matricula_profesional: str`
    * `- _especialidad_principal: str`
  * **Relaciones:**
    * Pertenece a una `Veterinaria` (* a 1).
  * **Métodos:**
    * `+ gestionar_estado_guardia(disponible: bool) -> None`
    * `+ recibir_alerta_urgencia(alerta) -> None`

#### Módulo: Pacientes e Historial Médico
* **`Mascota`:**
  * **Atributos privados:**
    * `- id_mascota: int`
    * `- nombre: str`
    * `- fecha_nacimiento: Optional[date]`
    * `- sexo: str` ("Macho" | "Hembra")
    * `- _peso_kg: float` (encapsulado con validación > 0)
    * `- foto_url: Optional[str]`
  * **Métodos públicos:**
    * `+ get_peso() -> float`
    * `+ set_peso(nuevo_peso: float) -> None`
    * `+ calcular_edad_formateada() -> str`
  * **Relaciones:**
    * Asociación con `Raza` (* a 1).
    * Agregación con `HistorialClinico` (1 a 0..*) vía `_historial_clinico`.
* **`Especie`:**
  * `- id_especie: int`
  * `- nombre: str` ("Felino", "Canino", "Ave Exótica")
  * `- es_exotico: bool`
  * `- requiere_permiso_senasa: bool`
* **`Raza`:**
  * `- id_raza: int`
  * `- nombre: str`
  * `- descripcion: str`
  * Relación: Pertenece a una `Especie` (* a 1).
* **`HistorialClinico`:**
  * `- id_registro: int`
  * `- id_mascota: int`
  * `- fecha: date`
  * `- motivo: str`
  * `- diagnostico: str`
  * `- tratamiento: str`
  * `- veterinario_firmante: str`
  * `- observaciones: str`
  * `- veterinaria_emisora: Optional[Veterinaria]`

#### Módulo: Triaje Inteligente y Georreferenciación
* **`ConsultaTriaje`:**
  * `- id_triaje: int`
  * `- id_cliente: int`
  * `- id_mascota: int`
  * `- fecha_hora: datetime`
  * `- sintomas_ingresados: str`
  * `- nivel_urgencia: str` ("ALTA", "MEDIA", "BAJA")
  * `- diagnostico_preliminar: str`
  * `- especialidad_sugerida: str`
  * `- alerta_despachada: bool`
  * **Métodos:**
    * `+ ejecutar_triaje(asistente_ia: AsistenteIA) -> None`
* **`AsistenteIA` (Servicio de Inferencia):**
  * `- api_key: str`
  * `- modelo_principal: str` (LLM / Gemini 1.5 Pro API)
  * `- modo_fallback: bool` (Motor heurístico de contingencia)
  * **Métodos:**
    * `+ clasificar_urgencia(sintomas: str, especie: str) -> dict`: Retorna `{nivel_urgencia, diagnostico_preliminar, especialidad_sugerida, primeros_auxilios}`.
    * `+ ejecutar_fallback(sintomas: str) -> dict`
* **`Veterinaria`:**
  * `- id_veterinaria: int`
  * `- nombre: str`
  * `- direccion: str`
  * `- latitud: float`
  * `- longitud: float`
  * `- tiene_guardia_24h: bool`
  * `- telefono_guardia: Optional[str]`
  * **Métodos:**
    * `+ calcular_distancia_km(lat_origen: float, lng_origen: float) -> float` (Fórmula de Haversine encapsulada en la clase)
    * `+ esta_disponible() -> bool`
    * `+ actualizar_estado_guardia(estado: str) -> None`
* **`AlertaUrgencia`:**
  * `- id_alerta: int`
  * `- id_triaje: int`
  * `- id_veterinaria_asignada: int`
  * `- fecha_hora: datetime`
  * `- estado: str` ("EMITIDA", "NOTIFICADA", "EN_CURSO", "ATENDIDA")
  * `- tiempo_estimado_arribo_min: int`
  * **Métodos:**
    * `+ transmitir() -> bool`
* **`ServicioNotificacion`:**
  * **Métodos:**
    * `+ despachar_whatsapp(telefono_destino: str, mensaje: str) -> bool`
    * `+ despachar_alerta(alerta: AlertaUrgencia) -> bool`

---

### 2. Especificación Formal de Casos de Uso (UML)

#### Actores
1. **Cliente (Dueño de Mascota):** Actor humano primario.
2. **Veterinario de Guardia:** Actor humano secundario/receptor.
3. **Asistente IA:** Actor del sistema externo (procesamiento de lenguaje natural / Gemini API).
4. **Servicio Notificación (WhatsApp API):** Actor del sistema externo.

#### CU-01: Iniciar Sesión (Autenticación Dual)
* **Actor Primario:** Cliente / Veterinario.
* **Tipo:** Primario, Esencial.
* **Precondición:** El usuario debe estar registrado en el sistema.
* **Poscondición:** Sesión iniciada y token devuelto al cliente.
* **Flujo Principal:**
  1. El usuario ingresa `usuario_o_email` y `password`.
  2. El sistema busca coincidencias por username o por email invocando `Usuario.verificar_credenciales()`.
  3. El sistema valida el hash de la contraseña.
  4. El sistema registra la sesión en `SESIONES_ACTIVAS` y retorna token y perfil.
* **Flujo Alternativo (Credenciales inválidas):**
  * 3a. El sistema emite error HTTP 401 ("Credenciales incorrectas") y deniega el acceso.

#### CU-02: Gestionar Mascotas (CRUD)
* **Actor Primario:** Cliente.
* **Tipo:** Primario, Esencial.
* **Precondición:** Sesión activa válida.
* **Flujos:**
  * **Alta (`POST /mascotas/`):** Cliente ingresa nombre, especie, raza, sexo, peso_kg (>0) y foto_url opcional. Se asocia al cliente logueado.
  * **Lectura (`GET /mascotas/cliente/{username}`):** Sistema lista las mascotas del usuario con edad calculada (`calcular_edad_formateada()`).
  * **Modificación (`PUT /mascotas/{id}`):** Cliente actualiza peso (`set_peso()`) o nombre; se validan permisos de dueño.
  * **Baja (`DELETE /mascotas/{id}`):** Se elimina la mascota de la cuenta del cliente.

#### CU-03: Consultar Historial Clínico
* **Actor:** Cliente / Veterinario.
* **Tipo:** Secundario, Esencial.
* **Precondición:** Mascota registrada con identificador válido.
* **Flujo Principal:**
  1. El usuario solicita el historial médico de una mascota (`GET /mascotas/{id_mascota}/historial`).
  2. El sistema recupera la lista cronológica de atenciones del objeto `Mascota._historial_clinico` (fecha, motivo, diagnóstico, tratamiento y veterinario firmante).
  3. El frontend renderiza las fichas clínicas en un timeline modal.

#### CU-04: Realizar Triaje de Urgencia con IA (Caso Central)
* **Actor Primario:** Cliente.
* **Actores Secundarios:** Asistente IA, Servicio Notificación.
* **Precondición:** Mascota y cliente identificados; síntomas reportados.
* **Flujo Principal:**
  1. El cliente envía síntomas y coordenadas GPS del móvil (`POST /triaje/evaluar`).
  2. Se instancia `ConsultaTriaje` y se invoca `ejecutar_triaje(asistente_ia)`.
  3. El `AsistenteIA` clasifica la urgencia (`ALTA`, `MEDIA`, `BAJA`), generando diagnóstico preliminar y especialidad sugerida.
  4. Si la urgencia es **ALTA**:
     * El sistema filtra las veterinarias disponibles con guardia 24h activa (`tiene_guardia_24h == True` y `esta_disponible() == True`).
     * Calcula la distancia con `Veterinaria.calcular_distancia_km()` y selecciona la más cercana.
     * Instancia `AlertaUrgencia` con tiempo estimado de arribo y estado `"EMITIDA"`.
     * Ejecuta `alerta.transmitir()`, notificando al veterinario de guardia vía `ServicioNotificacion.despachar_whatsapp()`.
     * El estado de la alerta cambia a `"NOTIFICADA"`.
  5. Se retorna `TriajeResponse` al cliente con semáforo, primeros auxilios, clínica asignada y confirmación de alerta despachada.
* **Flujo Alternativo (Contingencia de IA):**
  * 3a. Si el LLM tiene timeout o no responde, se activa `modo_fallback = True` y se ejecuta `ejecutar_fallback()`, emitiendo una recomendación heurística sin interrumpir el flujo.

---

## 📑 REPORTE DE ACTUALIZACIÓN TÉCNICA (NOTEBOOKLM EXPORT)

| Requerimiento POO / UML | Estado | Archivo / Componente |
| :--- | :---: | :--- |
| **`Usuario`** (Username, fecha_registro, avatar, verificar_credenciales, cambiar_contrasena) | ✅ Implementado | [`models/usuarios.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/models/usuarios.py) |
| **`Cliente`** (Dirección, latitud, longitud, teléfono, composición Mascota) | ✅ Implementado | [`models/usuarios.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/models/usuarios.py) |
| **`UsuarioVeterinario`** (Matrícula, especialidad principal, asociación Veterinaria) | ✅ Implementado | [`models/usuarios.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/models/usuarios.py) |
| **`Mascota`** (get_peso, set_peso > 0, calcular_edad_formateada, agregación HistorialClinico) | ✅ Implementado | [`models/mascotas.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/models/mascotas.py) |
| **`Especie` y `Raza`** (Permiso SENASA, descripción, relaciones) | ✅ Implementado | [`models/mascotas.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/models/mascotas.py) |
| **`HistorialClinico`** (id_registro, id_mascota, motivo, diagnóstico, tratamiento, firmante) | ✅ Implementado | [`models/mascotas.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/models/mascotas.py) |
| **`Veterinaria`** (calcular_distancia_km Haversine en la clase, tiene_guardia_24h) | ✅ Implementado | [`models/veterinarias.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/models/veterinarias.py) |
| **`ConsultaTriaje`** (ejecutar_triaje, diagnostico_preliminar, alerta_despachada) | ✅ Implementado | [`models/triaje.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/models/triaje.py) |
| **`AsistenteIA`** (api_key, modelo Gemini, clasificar_urgencia, motor fallback) | ✅ Implementado | [`Services/asistente_ia.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/Services/asistente_ia.py) |
| **`AlertaUrgencia`** (Máquina de estados EMITIDA->NOTIFICADA, tiempo arribo, transmitir) | ✅ Implementado | [`models/triaje.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/models/triaje.py) |
| **`ServicioNotificacion`** (despachar_whatsapp) | ✅ Implementado | [`Services/notificador.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/Services/notificador.py) |
| **Activación de Guardias 24h (Bug Fix)** | ✅ Corregido | [`routers/triaje.py`](file:///d:/TP%20DES/VetCercaIA-Backend/vetcerca-ia-backend-1/routers/triaje.py) |
