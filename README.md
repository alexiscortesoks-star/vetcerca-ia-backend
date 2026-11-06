# 🐾 TRABAJO PRÁCTICO INTEGRADOR (TPI)
**Asignatura:** Prácticas Profesionalizantes I: Aproximación al Campo Laboral / Desarrollo de Software  
**Institución:** Instituto de Formación Técnica Superior N° 12 (IFTS N° 12)  
**Carrera:** Técnico Superior en Ciencia de Datos e Inteligencia Artificial  

---

## 👥 Integrantes del Equipo
* **Caponi, Laura**
* **Cortes, Alexis**
* **Di Nucci, Lara**
* **Gazzola, Agostina**

---

# VetCerca IA: Sistema Inteligente de Triaje, Geolocalización y Recomendación Veterinaria por Barrio

---

## 1. DEFINICIÓN DEL PROBLEMA Y ALCANCE

### A. Contextualización
* **Sector Profesional:** Salud y bienestar de los animales de compañía en áreas urbanas de la Ciudad Autónoma de Buenos Aires (CABA) y zonas de influencia, abarcando la atención primaria, la categorización de síntomas y el despacho operativo de urgencias.
* **Actores Involucrados:**
  * **Tutores de mascotas:** Ciudadanos en situaciones de incertidumbre y estrés ante accidentes o sintomatologías agudas, que necesitan orientación inmediata y clara sin diagnósticos invasivos erróneos.
  * **Centros y Clínicas Veterinarias:** Red de atención heterogénea distribuida por comunas y barrios (consultorios diurnos vs. clínicas de guardia 24 horas y hospitales de alta complejidad).
* **Problema Central:**  
  La falta de orientación médica inicial ante urgencias veterinarias genera demoras críticas al intentar localizar clínicas con guardia 24hs abierta, o bien satura los centros de alta complejidad con afecciones leves. El sistema se enfoca estrictamente en **variables clínicas, técnicas, operativas y territoriales/geográficas**, excluyendo explícitamente variables comerciales o precios, priorizando el bienestar animal y la eficiencia en la atención.
* **Impacto Esperado:**
  1. Reducir los tiempos de respuesta y orientación inicial ante emergencias médicas veterinarias.
  2. Proveer contención estructurada mediante un asistente virtual empático con restricciones éticas rigurosas.
  3. Priorizar y despachar alertas en tiempo real hacia las guardias médicas ante cuadros críticos.
  4. Optimizar la canalización zonal y geolocalizada mediante la combinación de pertenencia barrial y cálculo geodésico preciso (**Fórmula de Haversine**).

---

### B. Objetivos del Proyecto

* **Objetivo General:**  
  Desarrollar una plataforma integral de software, análisis de datos e inteligencia artificial que clasifique el nivel de triaje veterinario a partir de síntomas clínicos, determine la urgencia mediante Machine Learning supervisado y recomiende las clínicas veterinarias disponibles más cercanas combinando análisis barrial y geolocalización GPS.

* **Objetivos Específicos:**
  1. **Pipeline y Curación de Datos:** Construir y mantener dos datasets tabulares curados: infraestructura veterinaria georreferenciada de CABA (`veterinarias_barrios.csv`) y casuística de triaje sintomático (`sintomas_triaje.csv`).
  2. **Modelado Supervisado (Triaje Clínico):** Entrenar y evaluar un clasificador multiclase (*Random Forest / Decision Tree*) para predecir el `nivel_urgencia` (*Baja, Moderada, Alta, Emergencia Crítica*), maximizando la métrica de **Recall** en cuadros críticos.
  3. **Modelado No Supervisado (Clustering Zonal):** Implementar *K-Means Clustering* para segmentar los barrios de CABA según densidad de veterinarias, presencia de guardias 24hs y niveles de complejidad operativa.
  4. **Geolocalización y Lógica de Contingencia Híbrida:** Desarrollar un motor de proximidad basado en la fórmula geodésica de **Haversine** combinado con matrices de adyacencia barrial para derivación inteligente ante ausencia de guardias locales.
  5. **Asistente Virtual y Restricciones Éticas:** Diseñar una arquitectura de prompts (Rol, Contexto, Tarea, Restricciones) que proporcione primeros auxilios orientativos y contención emocional sin emitir diagnósticos definitivos ni prescribir farmacología.
  6. **Arquitectura Backend y POO:** Implementar una API REST robusta en FastAPI con arquitectura limpia, principios de Programación Orientada a Objetos (POO), autenticación de usuarios y despacho de alertas.

---

### C. Preguntas de Investigación y Desarrollo
1. **Pregunta Predictiva (Supervisada):**  
   Dada una combinación de síntomas físicos, especie, tiempo de evolución y estado de conciencia, ¿con qué sensibilidad (Recall) el modelo supervisado clasifica los casos de *Alta* y *Emergencia Crítica* para evitar falsos negativos letales?
2. **Pregunta Espacial y de Segmentación (No Supervisada / Zonal):**  
   ¿Qué patrones de disparidad territorial surgen al agrupar los barrios de CABA según la disponibilidad de guardias 24hs y cómo optimiza la fórmula de Haversine la derivación a centros limítrofes?
3. **Pregunta de Interacción y Operatividad (Asistente IA & Backend):**  
   ¿Cómo coordinar el modelo predictivo, la geolocalización y el asistente conversacional para emitir una respuesta estructurada en menos de 2 segundos y despachar alertas tempranas a la guardia médica?

---

## 2. ARQUITECTURA INTEGRAL DEL SISTEMA

```text
 ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   ARQUITECTURA VETCERCA IA                                     │
 └────────────────────────────────────────────────────────────────────────────────────────────────┘

  [ FUENTES DE DATOS ]              [ PIPELINE ML / CIENCIA DE DATOS ]
  ┌──────────────────────┐          ┌────────────────────────────────────────────────────────┐
  │ veterinarias_barrios │─────────▶│ Preprocesamiento, Limpieza y One-Hot Encoding (Pandas)  │
  │      (.csv)          │          └──────────────────────────┬─────────────────────────────┘
  └──────────────────────┘                                     │
  ┌──────────────────────┐                     ┌───────────────┴───────────────┐
  │   sintomas_triaje    │                     ▼                               ▼
  │      (.csv)          │─────────▶┌─────────────────────┐         ┌─────────────────────┐
  └──────────────────────┘          │   K-Means Zonal     │         │    Random Forest    │
                                    │ (Clustering Barrios)│         │(Clasificador Triaje)│
                                    └──────────┬──────────┘         └──────────┬──────────┘
                                               │                               │
                                               ▼                               ▼
                                    ┌─────────────────────┐         ┌─────────────────────┐
                                    │  Clusters Zonal CABA│         │ modelo_triaje.joblib│
                                    └──────────┬──────────┘         └──────────┬──────────┘
                                               │                               │
 ──────────────────────────────────────────────┼───────────────────────────────┼───────────────────
  [ BACKEND FASTAPI & POO ]                    │                               │
                                               ▼                               ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                             API REST & SERVICIOS DE INFRAESTRUCTURA                            │
 │                                                                                                │
 │   ┌───────────────────────┐   ┌───────────────────────────┐   ┌────────────────────────────┐   │
 │   │  utils/geo.py         │   │  services/asistente_ia.py │   │ services/notificador.py    │   │
 │   │  • Haversine GPS (km) │   │  • Inferencia ML (Joblib) │   │ • Despacho en tiempo real  │   │
 │   │  • Matriz Contingencia│   │  • Prompting Ético        │   │ • Alertas WhatsApp / API   │   │
 │   └───────────┬───────────┘   └─────────────┬─────────────┘   └─────────────┬──────────────┘   │
 │               │                             │                               │                  │
 │               └─────────────────────────────┼───────────────────────────────┘                  │
 │                                             ▼                                                  │
 │                              ┌─────────────────────────────┐                                   │
 │                              │     routers/triaje.py       │                                   │
 │                              │  • Evaluación de Urgencia   │                                   │
 │                              │  • Geoconsulta de Guardias  │                                   │
 │                              └──────────────┬──────────────┘                                   │
 └─────────────────────────────────────────────┼──────────────────────────────────────────────────┘
                                               ▼
  [ CAPA DE PRESENTACIÓN ]       ┌─────────────────────────────┐
                                 │   Frontend Web Interactivo  │
                                 │ • Mapa / GPS del Tutor      │
                                 │ • Formulario Clínico Triaje │
                                 │ • Panel de Guardia Médica   │
                                 └─────────────────────────────┘
```

---

## 3. PIPELINE DE DATOS Y ANÁLISIS EXPLORATORIO (EDA)

### A. Estructura de los Datasets

1. **Dataset de Infraestructura Veterinaria (`data/veterinarias_barrios.csv`):**
   * `id_veterinaria`: Identificador único numérico.
   * `nombre_centro`: Razón social o denominación del establecimiento.
   * `barrio`: Barrio de CABA (ej. *Palermo, Belgrano, Flores, Caballito, Saavedra*).
   * `comuna`: Comuna administrativa (1 a 15).
   * `latitud`: Coordenada geográfica GPS (-34.xxxx).
   * `longitud`: Coordenada geográfica GPS (-58.xxxx).
   * `guardia_24hs`: Indicador binario (`1`: Servicio continuo ininterrumpido; `0`: Horario comercial).
   * `nivel_complejidad`: Nivel operativo (*Básico, Intermedio, Alta Complejidad/Quirófano*).
   * `especialidades`: Prestaciones (*Clínica Médica, Cirugía, Traumatología, Ecografía, Terapia Intensiva*).
   * `direccion`: Ubicación física normalizada en CABA.
   * `telefono_urgencias`: Línea de contacto directo de guardia.

2. **Dataset Clínico de Triaje (`data/sintomas_triaje.csv`):**
   * `id_caso`: Identificador único del caso clínico.
   * `especie`: Especie del paciente (*Canino / Felino*).
   * `sintoma_principal`: Cuadro presentado (ej. *Dificultad respiratoria, Convulsiones, Vómitos reiterados, Traumatismo agudo, Inapetencia*).
   * `tiempo_evolucion_hs`: Horas transcurridas desde el inicio de los signos.
   * `estado_conciencia`: Evaluación neurológica (*Alerta, Deprimido, Estuporoso/Comatoso*).
   * `presencia_hemorragia`: Indicador binario (`1`: Presente; `0`: Ausente).
   * `nivel_urgencia` (**Target**): 4 clases ordenadas (*Baja, Moderada, Alta, Emergencia Crítica*).

### B. Análisis Exploratorio de Datos (EDA en Notebook)
El notebook interactivo `notebooks/01_analisis_exploratorio_eda.ipynb` analiza:
* **Cobertura Territorial:** Concentración de guardias 24hs frente a clínicas diurnas por Comuna y Barrio.
* **Correlación Clínica:** Heatmaps entre horas de evolución, estado de conciencia, presencia de hemorragia y nivel de severidad.
* **Distribución de Especies:** Frecuencia cruzada de síntomas críticos según especie canina o felina.
* **Análisis de Dispersión Espacial:** Densidad de cobertura por coordenadas geográficas lat/long.

---

## 4. MODELADO DE MACHINE LEARNING E INTELIGENCIA ARTIFICIAL

### A. Clasificación Supervisada (Triaje Clínico)
* **Algoritmo:** *Random Forest Classifier* con balanceo de clases.
* **Preprocesamiento:** Pipeline con imputación, codificación One-Hot para categóricas y escalado estándar para variables temporales.
* **Métrica Clave:** **Recall (Sensibilidad)** en las clases *Alta* y *Emergencia Crítica* ($\ge 0.95$), minimizando los falsos negativos donde la vida del paciente corre peligro inminente.
* **Serialización:** Exportación del estimador a `src/modelo_triaje.joblib` para consumo directo en la API FastAPI.

### B. Segmentación No Supervisada (Clustering Zonal CABA)
* **Algoritmo:** *K-Means Clustering* analizando variables territoriales por barrio (oferta total de clínicas, proporción de guardias 24hs, densidad de alta complejidad y centroides geográficos).
* **Clústeres Resultantes:**
  * **Clúster 0 (Alta Cobertura):** Barrios con alta densidad de centros y guardias 24hs activas (ej. Palermo, Recoleta).
  * **Clúster 1 (Cobertura Intermedia):** Barrios con atención primaria diurna y guardias limitadas.
  * **Clúster 2 (Zonas Deficitarias/Críticas):** Barrios sin cobertura nocturna directa, requiriendo activación automática de derivación.

### C. Asistente Virtual e Ingeniería de Prompts
Implementación de un agente conversacional de contención con arquitectura de prompts estricta:
* **Rol:** Orientador empático y copiloto de triaje veterinario.
* **Contexto:** Tutor experimentando angustia ante el malestar o accidente de su mascota.
* **Entrada:** Diagnóstico del clasificador supervisado (`nivel_urgencia`), datos del paciente y la veterinaria de guardia asignada.
* **Formato de Respuesta:** 
  1. *Nivel de Urgencia y Tiempo de Acción Recomendado.*
  2. *Primeros Auxilios orientativos en viaje (qué hacer y qué NO hacer).*
  3. *Datos de la Clínica de Guardia más cercana (distancia exacta, dirección y teléfono).*
* **Restricciones Éticas Mandatorias:** 
  * Prohibición absoluta de emitir diagnósticos patológicos conclusivos.
  * Prohibición terminante de indicar fármacos, dosis o remedios caseros.
  * Obligatoriedad de instar a la atención presencial inmediata en casos de urgencia alta o crítica.

---

## 5. GEOLOCALIZACIÓN Y LÓGICA DE CONTINGENCIA HÍBRIDA

El sistema combina el criterio político-territorial (barrios/comunas) con la distancia geodésica real en kilómetros calculada mediante la **Fórmula de Haversine**:

$$\Delta\sigma = 2 \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)} \right)$$

$$d = R \cdot \Delta\sigma \quad \text{donde } R = 6.371\text{ km}$$

### Protocolo de Contingencia Zonal Inteligente:
1. El usuario ingresa su ubicación (por selección de **Barrio** de CABA o por **GPS del navegador**).
2. Si el caso se clasifica como `Alta` o `Emergencia Crítica`:
   * **Caso Directo:** Si el barrio seleccionado posee clínicas con `guardia_24hs == 1`, se ordenan por distancia geodésica Haversine y se asigna la más cercana.
   * **Caso de Contingencia:** Si el barrio seleccionado carece de guardia 24hs activa, el algoritmo activa la **matriz de adyacencia de comunas limítrofes**, busca las clínicas 24hs de los barrios vecinos y recomienda la que posea menor distancia Haversine, informando la derivación al tutor y estimando el tiempo de arribo.

---

## 6. ARQUITECTURA DE SOFTWARE, POO Y DESPACHO EN TIEMPO REAL

El backend se estructura bajo los principios de **Clean Architecture** y **Programación Orientada a Objetos (POO)**:

### A. Modelo de Dominio (POO)
* **`Usuario` (Clase Abstracta / ABC):** Encapsula identidad, credenciales hash, contacto y roles.
  * `Cliente`: Tutor de mascotas con dirección y coordenadas geográficas.
  * `UsuarioVeterinario`: Personal médico vinculado a una clínica de guardia.
* **`Mascota`:** Entidad del paciente asociada a `Especie`, `Raza` e `HistorialMedico`.
* **`Veterinaria`:** Entidad del centro de salud con atributos geográficos, cálculo de distancia Haversine (`calcular_distancia_km`), estado operativo y acreditación de guardia 24hs.
* **`ConsultaTriaje`:** Registra la sintomatología, ejecuta la inferencia con el modelo supervisado (`ejecutar_triaje`) y coordina las recomendaciones del asistente.
* **`AlertaUrgencia`:** Ante clasificaciones de `Alta` o `Emergencia Crítica`, despacha una notificación en tiempo real (`ServicioNotificacion`) informando a la guardia médica receptora la llegada estimada del paciente.

### B. Endpoints de la API REST (FastAPI)

| Método | Endpoint | Descripción | Componente |
| :--- | :--- | :--- | :--- |
| `POST` | `/triaje/evaluar` | Evalúa síntomas con Random Forest, geolocaliza guardia por Haversine y despacha alerta si es crítica | ML + Geo + Alertas |
| `GET` | `/veterinarias/cercanas` | Filtra clínicas por radio en km según coordenadas GPS | Haversine GPS |
| `GET` | `/triaje/contingencia/{barrio}` | Retorna centros del barrio con protocolo de contingencia a limítrofes | Territorial / Contingencia |
| `GET` | `/triaje/clustering/zonas` | Expone los clústeres de cobertura zonal de CABA generados por K-Means | ML No Supervisado |
| `POST` | `/auth/login` | Autenticación unificada de clientes y veterinarias | Seguridad / Sesión |
| `GET/POST`| `/mascotas/` | Gestión de fichas clínicas y pacientes del tutor | Dominio POO |

---

## 7. ESTRUCTURA UNIFICADA DEL REPOSITORIO

```text
vetcerca-ia-backend/
├── data/
│   ├── veterinarias_barrios.csv       # Catálogo georreferenciado de clínicas de CABA
│   ├── sintomas_triaje.csv            # Casuística clínica de entrenamiento de triaje
│   └── barrios_clusters.csv           # Segmentación de barrios por K-Means
├── notebooks/
│   └── 01_analisis_exploratorio_eda.ipynb # EDA, gráficos de cobertura y correlaciones
├── src/                               # Módulos de Ciencia de Datos y Machine Learning
│   ├── generar_datos.py               # Generación y validación de datasets sintéticos CABA
│   ├── pipeline_limpieza.py           # Preprocesamiento, OHE y estandarización
│   ├── modelo_clasificador.py         # Entrenamiento y validación de Random Forest
│   ├── clustering_barrios.py          # K-Means de segmentación territorial
│   └── modelo_triaje.joblib           # Estimador supervisado serializado
├── models/                            # Clases de Dominio POO
│   ├── usuarios.py                    # Usuario (ABC), Cliente, UsuarioVeterinario
│   ├── mascotas.py                    # Mascota, Especie, Raza, HistorialMedico
│   ├── veterinarias.py                # Veterinaria, Especialidad, cálculo Haversine
│   └── triaje.py                      # ConsultaTriaje, AlertaUrgencia
├── schemas/                           # Validación de contratos de datos (Pydantic v2)
│   ├── auth.py                        # LoginRequest, LoginResponse
│   ├── mascotas.py                    # MascotaCreate, MascotaResponse
│   └── triaje.py                      # TriajeRequest (variables clínicas), TriajeResponse
├── routers/                           # Endpoints modulares FastAPI
│   ├── auth.py                        # Sesiones y autenticación
│   ├── mascotas.py                    # CRUD de mascotas y dueños
│   └── triaje.py                      # Endpoint principal de triaje y contingencia
├── services/                          # Lógica de negocio y servicios
│   ├── asistente_ia.py                # Inferencia con Random Forest + Prompting ético
│   └── notificador.py                 # Despacho de alertas a clínicas de guardia
├── utils/                             # Utilidades matemáticas y geográficas
│   ├── geo.py                         # Fórmula geodésica de Haversine
│   └── contingencia_barrios.py        # Matriz de adyacencia de barrios y comunas de CABA
├── frontend/                          # Interfaz web interactiva (HTML5 / CSS3 / Vanilla JS)
│   ├── index.html                     # Portada y geolocalización de clínicas
│   ├── dashboard.html                 # Carga de triaje, perfil de mascotas e historial
│   └── assets/                        # Estilos y scripts clientes
├── docs/
│   └── arquitectura_sistema.md        # Especificación técnica y diagramas formales
├── app.py                             # Punto de entrada principal de FastAPI
├── requirements.txt                   # Dependencias completas del ecosistema
└── README.md                          # Documento unificado del proyecto
```

---

## 8. GUÍA DE INSTALACIÓN Y EJECUCIÓN

### 1. Clonar el repositorio y configurar el entorno virtual
```bash
# Crear el entorno virtual con Python 3.10+
python -m venv venv

# Activar en Windows:
.\venv\Scripts\activate

# Activar en Linux/macOS:
source venv/bin/activate
```

### 2. Instalar dependencias completas
```bash
pip install -r requirements.txt
```

### 3. Generar datasets y entrenar los modelos de Machine Learning
```bash
# Genera los CSVs sintéticos curados de CABA
python src/generar_datos.py

# Ejecuta el preprocesamiento y entrena el clasificador supervisado
python src/modelo_clasificador.py

# Ejecuta el clustering territorial K-Means
python src/clustering_barrios.py
```

### 4. Iniciar el servidor backend (FastAPI)
```bash
uvicorn app:app --reload
```
* La API estará activa en: `http://127.0.0.1:8000`
* Documentación interactiva Swagger: `http://127.0.0.1:8000/docs`

#### Configurar Gemini para interpretar descripciones libres del triaje

Creá una clave en [Google AI Studio](https://aistudio.google.com/apikey) y configurala
en la misma terminal antes de iniciar el servidor:

```powershell
$env:GEMINI_API_KEY = "TU_CLAVE"
```

Gemini recibe únicamente la especie y la descripción de síntomas para relacionarla
con el catálogo clínico local; no recibe el nombre ni identificadores de la mascota
o su dueño. La urgencia sigue siendo calculada por el clasificador local. Si Gemini
no puede relacionar el texto con claridad, la API solicita una aclaración y no asigna
una urgencia. Sin esta clave, solo se procesan frases del catálogo.

### 5. Iniciar la interfaz frontend
En otra terminal dentro de la raíz del proyecto:
```bash
python -m http.server 5500 --directory frontend
```
* Acceder a la plataforma desde el navegador en: `http://127.0.0.1:5500`

---

## 9. CONCLUSIONES Y TRABAJO FUTURO
El proyecto unifica con éxito la rigurosidad estadística y predictiva de la Ciencia de Datos con las buenas prácticas de la Ingeniería de Software. La inclusión del cálculo de Haversine junto con la matriz de contingencia barrial resuelve el problema operativo de derivación nocturna, mientras que el clasificador supervisado y el asistente empático ofrecen una herramienta de triaje ágil, segura y con estricta adherencia a la ética veterinaria.
