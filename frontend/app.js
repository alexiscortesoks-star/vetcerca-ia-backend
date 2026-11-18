const API_URL = `${window.location.protocol}//${window.location.hostname}:8000`;
let mapaInstancia = null;
const mascotasPorId = new Map();
let mascotaEnEdicionId = null;
let ultimoResultadoTriaje = null;
let ultimoNombreMascotaTriaje = null;
let ultimoDatosTriaje = null;
let consultaGuiada = null;
let suspenderReinicioConsulta = false;
let alertaVeterinariaSeleccionada = null;
const alertasVeterinariasMostradas = new Set();
const colaAlertasVeterinarias = [];
let cargandoAlertasVeterinarias = false;

async function leerRespuesta(response) {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "No se pudo completar la solicitud.");
  }
  return data;
}

function mostrarMensaje(elemento, mensaje, esError = false) {
  if (!elemento) return;
  elemento.textContent = mensaje;
  elemento.classList.toggle("text-danger", esError);
  elemento.classList.toggle("text-success", !esError);
}

async function iniciarSesion(usuarioOEmail, password) {
  const submitButton = document.querySelector(
    "#loginForm button[type='submit']",
  );
  if (submitButton) submitButton.disabled = true;

  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        usuario_o_email: usuarioOEmail,
        password,
      }),
    });
    const data = await leerRespuesta(response);

    if (data.tipo_usuario === "veterinaria") {
      localStorage.removeItem("username");
      localStorage.removeItem("id_cliente");
      localStorage.removeItem("token");
      localStorage.setItem("vet_username", usuarioOEmail);
      localStorage.setItem("vet_id", String(data.id_veterinaria));
      localStorage.setItem("vet_token", data.token_sesion);
      window.location.href = "veterinaria-dashboard.html";
      return;
    }

    if (data.tipo_usuario !== "cliente" || !data.username || !data.id_cliente) {
      throw new Error("La respuesta de acceso no contiene un perfil válido.");
    }
    localStorage.setItem("username", data.username);
    localStorage.setItem("id_cliente", String(data.id_cliente));
    localStorage.setItem("token", data.token_sesion);
    localStorage.removeItem("vet_username");
    localStorage.removeItem("vet_id");
    localStorage.removeItem("vet_token");
    window.location.href = "dashboard.html";
  } catch (error) {
    console.error("Error al iniciar sesión:", error);
    mostrarMensaje(document.getElementById("loginMessage"), error.message, true);
  } finally {
    if (submitButton) submitButton.disabled = false;
  }
}

async function iniciarSesionVeterinaria(usuario, password) {
  const form = document.getElementById("veterinaryLoginForm");
  const submitButton = form?.querySelector("button[type='submit']");
  const message = document.getElementById("veterinaryLoginMessage");
  if (submitButton) submitButton.disabled = true;

  try {
    const response = await fetch(`${API_URL}/auth/veterinaria/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ usuario, password }),
    });
    const data = await leerRespuesta(response);

    localStorage.removeItem("username");
    localStorage.removeItem("id_cliente");
    localStorage.removeItem("token");
    localStorage.setItem("vet_username", usuario);
    localStorage.setItem("vet_id", String(data.id_veterinaria));
    localStorage.setItem("vet_token", data.token_sesion);
    window.location.href = "veterinaria-dashboard.html";
  } catch (error) {
    console.error("Error al iniciar sesión como veterinaria:", error);
    mostrarMensaje(message, error.message, true);
  } finally {
    if (submitButton) submitButton.disabled = false;
  }
}

async function cargarPerfilVeterinaria() {
  const token = localStorage.getItem("vet_token");
  if (!token) {
    window.location.href = "index.html?acceso=unificado";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/auth/veterinaria/perfil`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const perfil = await leerRespuesta(response);
    document.getElementById("vetName").textContent = perfil.nombre;
    document.getElementById("vetAddress").textContent = perfil.direccion;
    document.getElementById("vetPhone").textContent = perfil.telefono_guardia;
    document.getElementById("vetAvailability").textContent =
      perfil.estado_disponibilidad === "DISPONIBLE"
        ? "Disponible"
        : "No disponible";
    document.getElementById("vetAvailability").classList.toggle(
      "urgency-low",
      perfil.estado_disponibilidad === "DISPONIBLE",
    );
    document.getElementById("vetHours").textContent = perfil.es_24hs
      ? "Atención de guardia las 24 horas"
      : "Atención con horario habitual";
    document.getElementById("vetWelcome").textContent = `Hola, ${perfil.nombre}`;
  } catch (error) {
    console.error("Error al cargar el perfil veterinario:", error);
    localStorage.removeItem("vet_token");
    localStorage.removeItem("vet_id");
    localStorage.removeItem("vet_username");
    window.location.href = "index.html?acceso=unificado";
  }
}

async function solicitarApiVeterinaria(path, options = {}) {
  const token = localStorage.getItem("vet_token");
  if (!token) throw new Error("La sesión veterinaria venció. Iniciá sesión nuevamente.");
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
      ...(options.body ? { "Content-Type": "application/json" } : {}),
    },
  });
  return leerRespuesta(response);
}

async function cargarAlertasVeterinarias(silencioso = false) {
  const alertas = document.getElementById("vetAlertsList");
  const mensajeAlertas = document.getElementById("vetAlertsMessage");
  const historial = document.getElementById("vetAlertHistoryList");
  const mensajeHistorial = document.getElementById("vetAlertHistoryMessage");
  if (
    !alertas ||
    !mensajeAlertas ||
    !historial ||
    !mensajeHistorial ||
    cargandoAlertasVeterinarias
  ) return;

  cargandoAlertasVeterinarias = true;
  for (const [contenedor, mensaje] of [
    [alertas, mensajeAlertas],
    [historial, mensajeHistorial],
  ]) {
    mensaje.classList.remove("text-danger");
    if (!silencioso) mensaje.textContent = "Cargando...";
    contenedor.setAttribute("aria-busy", "true");
  }

  try {
    const [activas, resueltas] = await Promise.all([
      solicitarApiVeterinaria("/veterinaria/alertas"),
      solicitarApiVeterinaria("/veterinaria/alertas/historial"),
    ]);
    renderizarListaAlertasVeterinarias(
      activas,
      alertas,
      mensajeAlertas,
      "Todavía no hay alertas recibidas.",
    );
    renderizarListaAlertasVeterinarias(
      resueltas,
      historial,
      mensajeHistorial,
      "Las alertas marcadas como resueltas aparecerán aquí.",
    );
    for (const alerta of activas) {
      if (
        alerta.estado === "RECIBIDA" &&
        !alertasVeterinariasMostradas.has(alerta.id_alerta) &&
        !colaAlertasVeterinarias.includes(alerta.id_alerta)
      ) {
        colaAlertasVeterinarias.push(alerta.id_alerta);
      }
    }
    await mostrarSiguienteAlertaVeterinaria();
  } catch (error) {
    const detalle = error.message || "No se pudieron cargar las alertas.";
    for (const mensaje of [mensajeAlertas, mensajeHistorial]) {
      mensaje.textContent = detalle;
      mensaje.classList.add("text-danger");
    }
  } finally {
    alertas.setAttribute("aria-busy", "false");
    historial.setAttribute("aria-busy", "false");
    cargandoAlertasVeterinarias = false;
  }
}

async function mostrarSiguienteAlertaVeterinaria() {
  const modal = document.getElementById("modalDetalleAlertaVet");
  if (!modal || modal.classList.contains("show")) return;

  const idAlerta = colaAlertasVeterinarias.shift();
  if (!idAlerta) return;
  await abrirDetalleAlertaVeterinaria(idAlerta);
}

function renderizarListaAlertasVeterinarias(
  alertas,
  contenedor,
  mensaje,
  mensajeVacio,
) {
  contenedor.replaceChildren();
  if (!alertas.length) {
    mensaje.textContent = mensajeVacio;
    return;
  }

  mensaje.textContent = `${alertas.length} ${
    alertas.length === 1 ? "alerta" : "alertas"
  }.`;
  for (const alerta of alertas) {
    const card = document.createElement("article");
    card.className = "vet-alert-card";
    const details = document.createElement("div");
    const title = document.createElement("h3");
    title.textContent = `${alerta.mascota.nombre} · ${alerta.nivel_urgencia}`;
    if (alerta.es_demostracion) {
      const demo = document.createElement("span");
      demo.className = "vet-alert-demo-badge";
      demo.textContent = "DEMO";
      title.append(" ", demo);
    }
    const symptoms = document.createElement("p");
    symptoms.textContent = alerta.sintomas;
    const meta = document.createElement("div");
    meta.className = "vet-alert-card-meta";
    const tutor = document.createElement("span");
    tutor.textContent = `Tutor/a: ${alerta.tutor.nombre}`;
    const arrival = document.createElement("span");
    arrival.textContent = `Arribo estimado: ${alerta.tiempo_estimado_arribo_min} min`;
    const state = document.createElement("span");
    state.textContent = `Estado: ${alerta.estado.replace(/_/g, " ")}`;
    meta.append(tutor, arrival, state);
    details.append(title, symptoms, meta);

    const open = document.createElement("button");
    open.type = "button";
    open.className = "btn btn-outline-teal btn-sm";
    open.textContent = "Ver alerta";
    open.addEventListener("click", () =>
      abrirDetalleAlertaVeterinaria(alerta.id_alerta),
    );
    card.append(details, open);
    contenedor.appendChild(card);
  }
}

async function simularAlertaVeterinaria(button) {
  const mensaje = document.getElementById("vetAlertsMessage");
  button.disabled = true;
  button.textContent = "Creando alerta...";
  try {
    await solicitarApiVeterinaria(
      "/veterinaria/alertas/simular",
      { method: "POST" },
    );
    await cargarAlertasVeterinarias();
    mensaje.textContent =
      "Alerta de demostración creada. No se envió ninguna notificación externa.";
  } catch (error) {
    mensaje.textContent = error.message || "No se pudo crear la alerta de demostración.";
    mensaje.classList.add("text-danger");
  } finally {
    button.disabled = false;
    button.textContent = "Simular alerta";
  }
}

async function abrirDetalleAlertaVeterinaria(idAlerta) {
  alertasVeterinariasMostradas.add(idAlerta);
  const indiceEnCola = colaAlertasVeterinarias.indexOf(idAlerta);
  if (indiceEnCola !== -1) colaAlertasVeterinarias.splice(indiceEnCola, 1);
  const mensaje = document.getElementById("vetAlertActionMessage");
  mensaje.textContent = "Cargando detalle...";
  try {
    const alerta = await solicitarApiVeterinaria(
      `/veterinaria/alertas/${encodeURIComponent(idAlerta)}`,
    );
    alertaVeterinariaSeleccionada = alerta;
    const animal = alerta.mascota;
    const tutor = alerta.tutor;
    document.getElementById("vetAlertDetailKicker").textContent =
      alerta.es_demostracion ? "ALERTA DE DEMOSTRACIÓN" : "ALERTA DE GUARDIA";
    document.getElementById("vetAlertDetailTitle").textContent =
      `${alerta.es_demostracion ? "Demostración · " : ""}Alerta #${alerta.id_alerta}`;
    document.getElementById("vetAlertAnimal").textContent =
      `${animal.nombre} · ${animal.especie} · ${animal.raza} · ${animal.edad} · ${animal.sexo} · ${animal.peso_kg} kg`;
    document.getElementById("vetAlertTutor").textContent =
      `${tutor.nombre} (@${tutor.username}) · ${tutor.email} · ${tutor.telefono}`;
    document.getElementById("vetAlertSymptoms").textContent = alerta.sintomas;
    document.getElementById("vetAlertUrgency").textContent =
      `${alerta.nivel_urgencia} · arribo estimado en ${alerta.tiempo_estimado_arribo_min} min`;
    document.getElementById("vetAlertClinic").textContent =
      `${alerta.veterinaria.nombre} · ${alerta.veterinaria.direccion} · ${alerta.fecha_hora}`;
    const botonAceptar = document.getElementById("vetAcceptAlert");
    botonAceptar.disabled = alerta.estado !== "RECIBIDA";
    botonAceptar.textContent =
      alerta.estado === "RECIBIDA"
        ? "Aceptar"
        : alerta.estado === "EN_ATENCION"
          ? "Aceptada"
          : "Alerta resuelta";
    const alertaResuelta = alerta.estado === "RESUELTA";
    document.getElementById("vetAlertResolved").disabled = alertaResuelta;
    document.getElementById("vetHistorySection").hidden = true;
    document.getElementById("vetHistoryList").replaceChildren();
    mensaje.textContent = `Estado actual: ${alerta.estado.replace(/_/g, " ")}.`;
    bootstrap.Modal.getOrCreateInstance(
      document.getElementById("modalDetalleAlertaVet"),
    ).show();
  } catch (error) {
    mensaje.textContent = error.message || "No se pudo abrir la alerta.";
    mensaje.classList.add("text-danger");
  }
}

async function actualizarEstadoAlertaVeterinaria(estado) {
  if (!alertaVeterinariaSeleccionada) return;
  const mensaje = document.getElementById("vetAlertActionMessage");
  mensaje.textContent = "Actualizando estado...";
  try {
    const alerta = await solicitarApiVeterinaria(
      `/veterinaria/alertas/${encodeURIComponent(alertaVeterinariaSeleccionada.id_alerta)}/estado`,
      { method: "PATCH", body: JSON.stringify({ estado }) },
    );
    alertaVeterinariaSeleccionada = alerta;
    const botonAceptar = document.getElementById("vetAcceptAlert");
    botonAceptar.disabled = alerta.estado !== "RECIBIDA";
    botonAceptar.textContent =
      alerta.estado === "RECIBIDA"
        ? "Aceptar"
        : alerta.estado === "EN_ATENCION"
          ? "Aceptada"
          : "Alerta resuelta";
    document.getElementById("vetAlertResolved").disabled =
      alerta.estado === "RESUELTA";
    mensaje.textContent = `Alerta marcada como ${alerta.estado.replace(/_/g, " ").toLowerCase()}.`;
    await cargarAlertasVeterinarias();
  } catch (error) {
    mensaje.textContent = error.message || "No se pudo actualizar el estado.";
    mensaje.classList.add("text-danger");
  }
}

async function cargarHistoriaAlertaVeterinaria() {
  if (!alertaVeterinariaSeleccionada) return;
  const section = document.getElementById("vetHistorySection");
  const list = document.getElementById("vetHistoryList");
  const message = document.getElementById("vetHistoryMessage");
  section.hidden = false;
  list.setAttribute("aria-busy", "true");
  list.replaceChildren();
  message.textContent = "";
  try {
    const data = await solicitarApiVeterinaria(
      `/veterinaria/alertas/${encodeURIComponent(alertaVeterinariaSeleccionada.id_alerta)}/historia`,
    );
    if (!data.historial.length) {
      const empty = document.createElement("p");
      empty.className = "text-secondary mb-0";
      empty.textContent = "Todavía no hay evoluciones registradas para esta mascota.";
      list.appendChild(empty);
      return;
    }
    for (const registro of data.historial) {
      const item = document.createElement("article");
      item.className = "list-group-item mb-2 rounded";
      const heading = document.createElement("h4");
      heading.className = "h6";
      heading.textContent = `${registro.fecha} · ${registro.motivo}`;
      const diagnosis = document.createElement("p");
      diagnosis.textContent = `Evaluación: ${registro.diagnostico}`;
      const treatment = document.createElement("p");
      treatment.textContent = `Tratamiento: ${registro.tratamiento}`;
      const observations = document.createElement("p");
      observations.className = "small text-secondary mb-1";
      observations.textContent = registro.observaciones
        ? `Observaciones: ${registro.observaciones}`
        : "";
      const vet = document.createElement("p");
      vet.className = "small text-secondary mb-0";
      vet.textContent = `Registrado por: ${registro.veterinario}`;
      item.append(heading, diagnosis, treatment, observations, vet);
      list.appendChild(item);
    }
  } catch (error) {
    const failure = document.createElement("p");
    failure.className = "text-danger mb-0";
    failure.textContent = error.message || "No se pudo cargar la historia clínica.";
    list.appendChild(failure);
  } finally {
    list.setAttribute("aria-busy", "false");
  }
}

async function guardarEvolucionVeterinaria(event) {
  event.preventDefault();
  if (!alertaVeterinariaSeleccionada) return;
  const form = event.currentTarget;
  const button = document.getElementById("vetSaveEvolution");
  const message = document.getElementById("vetHistoryMessage");
  button.disabled = true;
  message.textContent = "Guardando evolución...";
  const payload = {
    motivo: document.getElementById("vetEvolutionReason").value.trim(),
    diagnostico: document.getElementById("vetEvolutionDiagnosis").value.trim(),
    tratamiento: document.getElementById("vetEvolutionTreatment").value.trim(),
    observaciones:
      document.getElementById("vetEvolutionObservations").value.trim() || null,
  };
  try {
    await solicitarApiVeterinaria(
      `/veterinaria/alertas/${encodeURIComponent(alertaVeterinariaSeleccionada.id_alerta)}/historia`,
      { method: "POST", body: JSON.stringify(payload) },
    );
    form.reset();
    await cargarHistoriaAlertaVeterinaria();
    message.textContent = "La evolución se agregó a la historia clínica.";
  } catch (error) {
    message.textContent = error.message || "No se pudo guardar la evolución.";
    message.classList.add("text-danger");
  } finally {
    button.disabled = false;
  }
}

async function evaluarTriaje(
  nombreMascota,
  sintomas,
  lat,
  lng,
  datosClinicos,
  despacharAlerta = false,
) {
  const idCliente = Number(localStorage.getItem("id_cliente"));
  const payload = {
    nombre_mascota: nombreMascota,
    sintomas,
    ...datosClinicos,
    latitud_cliente: Number.isFinite(lat) ? lat : -34.6037,
    longitud_cliente: Number.isFinite(lng) ? lng : -58.3816,
  };
  if (Number.isInteger(idCliente) && idCliente > 0) {
    payload.id_cliente = idCliente;
  }

  const response = await fetch(
    `${API_URL}/triaje/evaluar?despachar_alerta=${despacharAlerta ? "true" : "false"}`,
    {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    },
  );
  return leerRespuesta(response);
}

function obtenerUbicacion() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve({ lat: -34.6037, lng: -58.3816 });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ lat: coords.latitude, lng: coords.longitude }),
      () => resolve({ lat: -34.6037, lng: -58.3816 }),
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 },
    );
  });
}

function crearElementoClinica(clinic) {
  const item = document.createElement("li");
  item.className = "clinic-item";

  const details = document.createElement("div");
  details.className = "clinic-details";

  const name = document.createElement("strong");
  name.textContent = clinic.nombre;
  const address = document.createElement("span");
  address.textContent = clinic.direccion;
  details.append(name, address);

  const phone = document.createElement("span");
  phone.className = "clinic-whatsapp";
  const phoneDigits = (clinic.telefono || "").replace(/\D/g, "");
  if (phoneDigits) {
    const whatsapp = document.createElement("a");
    whatsapp.href = `https://wa.me/${phoneDigits}`;
    whatsapp.target = "_blank";
    whatsapp.rel = "noopener noreferrer";
    whatsapp.textContent = "WhatsApp";
    phone.appendChild(whatsapp);
  } else {
    phone.textContent = "WhatsApp no disponible";
  }

  const validation = document.createElement("span");
  validation.className = "clinic-validation";
  validation.setAttribute("aria-label", "Dato a validar");
  const dot = document.createElement("span");
  dot.className = "clinic-validation-dot";
  dot.setAttribute("aria-hidden", "true");
  const validationText = document.createElement("span");
  validationText.textContent = "Dato a validar";
  validation.append(dot, validationText);

  item.append(details, phone, validation);
  return item;
}

function actualizarListadosClinicas(clinics) {
  const summaryList = document.getElementById("clinicsList");
  const fullList = document.getElementById("clinicsModalList");
  const moreButton = document.getElementById("clinicsMoreButton");
  if (!summaryList || !fullList || !moreButton) return;

  summaryList.replaceChildren(...clinics.slice(0, 3).map(crearElementoClinica));
  fullList.replaceChildren(...clinics.map(crearElementoClinica));
  moreButton.hidden = clinics.length <= 3;
}

async function cargarClinicasCercanas() {
  const mapElement = document.getElementById("landingMap");
  const clinicsList = document.getElementById("clinicsList");
  const message = document.getElementById("clinicsMessage");
  if (!mapElement || !clinicsList || !message) return;

  const location = { lat: -34.6037, lng: -58.3816 };
  const candidatasLocales = [
    {
      nombre: "Centro Médico Veterinario Belgrano",
      direccion: "Amenábar 2214, Belgrano, CABA",
      telefono: null,
      latitud: -34.562069,
      longitud: -58.4596054,
    },
    {
      nombre: "Panda",
      direccion: "Av. Ruiz Huidobro 4771, Saavedra, CABA",
      telefono: null,
      latitud: -34.5549092,
      longitud: -58.4945994,
    },
  ];
  const nombresMarcadoresLocales = new Set();
  if (typeof L !== "undefined") {
    if (mapaInstancia) mapaInstancia.remove();
    mapaInstancia = L.map("landingMap").setView(
      [location.lat, location.lng],
      12,
    );
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(mapaInstancia);
    L.marker([location.lat, location.lng])
      .addTo(mapaInstancia)
      .bindPopup("Ubicación de referencia · CABA");
    for (const clinic of candidatasLocales) {
      const popup = document.createElement("div");
      const name = document.createElement("strong");
      name.textContent = clinic.nombre;
      const address = document.createElement("p");
      address.textContent = clinic.direccion;
      popup.append(name, address);
      L.marker([clinic.latitud, clinic.longitud])
        .addTo(mapaInstancia)
        .bindPopup(popup);
      nombresMarcadoresLocales.add(clinic.nombre);
    }
    mapaInstancia.fitBounds(
      [
        [location.lat, location.lng],
        ...candidatasLocales.map((clinic) => [
          clinic.latitud,
          clinic.longitud,
        ]),
      ],
      { padding: [24, 24] },
    );
  } else {
    mapElement.textContent = "No se pudo cargar el mapa. Revisá tu conexión.";
  }

  try {
    const params = new URLSearchParams({
      latitud: String(location.lat),
      longitud: String(location.lng),
      radio_km: "25",
    });
    const response = await fetch(
      `${API_URL}/veterinarias/cercanas?${params.toString()}`,
    );
    const data = await leerRespuesta(response);

    for (const clinic of data.veterinarias) {
      if (typeof L !== "undefined") {
        if (!nombresMarcadoresLocales.has(clinic.nombre)) {
          const popup = document.createElement("div");
          const popupName = document.createElement("strong");
          popupName.textContent = clinic.nombre;
          const popupAddress = document.createElement("p");
          popupAddress.className = "mb-0";
          popupAddress.textContent = clinic.direccion;
          popup.append(popupName, popupAddress);
          L.marker([clinic.latitud, clinic.longitud])
            .addTo(mapaInstancia)
            .bindPopup(popup);
        }
      }
    }
    actualizarListadosClinicas(data.veterinarias);

    message.textContent = data.cantidad
      ? `${data.cantidad} centros cercanos`
      : "No encontramos clínicas en el radio seleccionado.";
    if (typeof L !== "undefined" && data.veterinarias.length) {
      const locations = [
        [location.lat, location.lng],
        ...data.veterinarias.map((clinic) => [
          clinic.latitud,
          clinic.longitud,
        ]),
      ];
      mapaInstancia.fitBounds(locations, { padding: [24, 24] });
    }
  } catch (error) {
    console.error("Error al cargar clínicas cercanas:", error);
    actualizarListadosClinicas(candidatasLocales);
    message.textContent =
      `Mostrando ${candidatasLocales.length} centros; ` +
      "no pudimos actualizar desde el servidor.";
  }
}

function renderizarMapaGPS(
  latCliente,
  lngCliente,
  vetNombre,
  vetLat,
  vetLng,
) {
  const mapaSection = document.getElementById("mapaSection");
  const coordenadas = [
    latCliente,
    lngCliente,
    vetLat,
    vetLng,
  ];
  if (!mapaSection || coordenadas.some((valor) => !Number.isFinite(valor))) {
    if (mapaSection) mapaSection.hidden = true;
    return;
  }
  if (typeof L === "undefined") {
    mostrarMensaje(
      document.getElementById("triageMessage"),
      "El mapa no está disponible. Verificá tu conexión para cargar Leaflet.",
      true,
    );
    return;
  }

  mapaSection.hidden = false;
  if (mapaInstancia) mapaInstancia.remove();

  const cliente = [latCliente, lngCliente];
  const veterinaria = [vetLat, vetLng];
  mapaInstancia = L.map("mapaGPS").setView(cliente, 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(mapaInstancia);

  L.marker(cliente)
    .addTo(mapaInstancia)
    .bindPopup("<b>Tu ubicación</b><br>Ubicación del paciente.");
  const popup = document.createElement("strong");
  popup.textContent = vetNombre || "Veterinaria de guardia";
  L.marker(veterinaria).addTo(mapaInstancia).bindPopup(popup);
  mapaInstancia.fitBounds([cliente, veterinaria], { padding: [32, 32] });
  window.setTimeout(() => mapaInstancia?.invalidateSize(), 0);
}

function renderizarResultadoTriaje(data) {
  ultimoResultadoTriaje = data;
  const resultado = document.getElementById("resultadoCard");
  const urgencia = document.getElementById("resultadoUrgencia");
  const nivel = String(data.nivel_urgencia || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase();
  const etiquetas = {
    ALTA: { texto: "Atención urgente", clase: "urgency-high" },
    MODERADA: { texto: "Consulta recomendada", clase: "urgency-medium" },
    BAJA: { texto: "Urgencia baja", clase: "urgency-low" },
    "NO CONCLUYENTE": {
      texto: "No se pudo determinar",
      clase: "urgency-unknown",
    },
    "EMERGENCIA CRITICA": {
      texto: "Atención veterinaria inmediata",
      clase: "urgency-high",
    },
  };
  const etiqueta = etiquetas[nivel] || {
    texto: "Nivel por confirmar",
    clase: "urgency-unknown",
  };

  resultado.hidden = false;
  document.getElementById("triageChat").hidden =
    data.nivel_urgencia !== "No concluyente";
  urgencia.textContent = etiqueta.texto;
  urgencia.className = `urgency-badge ${etiqueta.clase}`;
  document.getElementById("resultadoPaciente").textContent =
    data.paciente || "Tu mascota";
  document.getElementById("resultadoSintomas").textContent =
    data.sintomas_ingresados || "";
  document.getElementById("resultadoEspecialidad").textContent =
    data.especialidad_sugerida || "No disponible";
  document.getElementById("resultadoPrimerosAuxilios").textContent =
    data.primeros_auxilios || "Contactá a una veterinaria para recibir indicaciones.";
  document.getElementById("resultadoVeterinaria").textContent =
    data.veterinaria_cercana || "No encontramos una guardia disponible.";
  document.getElementById("resultadoDistancia").textContent =
    Number.isFinite(data.distancia_km)
      ? `A ${data.distancia_km.toFixed(1)} km de tu ubicación`
      : "No se pudo calcular la distancia.";
  document.getElementById("resultadoDireccion").textContent =
    data.direccion_veterinaria || "";

  const telefono = document.getElementById("resultadoTelefono");
  const telefonoSeguro = String(data.telefono_veterinaria || "").replace(/[^\d+]/g, "");
  telefono.hidden = !telefonoSeguro;
  if (telefonoSeguro) {
    telefono.href = `tel:${telefonoSeguro}`;
  } else {
    telefono.removeAttribute("href");
  }

  const alerta = document.getElementById("alertaGuardia");
  alerta.hidden = !data.alerta_despachada;
  alerta.textContent = data.alerta_despachada
    ? data.mensaje_alerta || "Se notificó a la guardia veterinaria asignada."
    : "";

  const puedeAlertar =
    ["Alta", "Emergencia Crítica"].includes(data.nivel_urgencia) &&
    !data.alerta_despachada &&
    data.veterinaria_cercana &&
    data.veterinaria_cercana !== "No disponible";
  const botonUrgencia = document.getElementById("abrirAccionesUrgencia");
  if (botonUrgencia) botonUrgencia.hidden = !puedeAlertar;

  if (puedeAlertar) {
    abrirModalUrgencia(data);
  }
  document.getElementById("triageMessage").textContent = "";
}

function agregarMensajeChatTriaje(rol, mensaje) {
  const messages = document.getElementById("triageChatMessages");
  if (!messages || !mensaje) return;

  const bubble = document.createElement("p");
  bubble.className = `triage-chat-message triage-chat-message-${rol}`;
  bubble.textContent = mensaje;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function abrirModalUrgencia(data) {
  const modalElement = document.getElementById("modalAccionesUrgencia");
  if (!modalElement) return;

  document.getElementById("urgenciaModalNivel").textContent =
    data.nivel_urgencia || "Urgencia";
  document.getElementById("urgenciaModalMascota").textContent =
    data.paciente || "Tu mascota";
  document.getElementById("urgenciaModalVeterinaria").textContent =
    data.veterinaria_cercana || "Veterinaria asignada";
  document.getElementById("urgenciaModalDireccion").textContent =
    data.direccion_veterinaria || "";
  document.getElementById("urgenciaModalPasos").textContent =
    data.primeros_auxilios || "Trasladá a la mascota a una guardia veterinaria.";

  if (typeof bootstrap !== "undefined") {
    bootstrap.Modal.getOrCreateInstance(modalElement).show();
  }
}

function agregarRespuestasRapidasChat() {
  const messages = document.getElementById("triageChatMessages");
  if (!messages) return;

  const botones = [
    ["Está alerta", "Está alerta y responde normalmente"],
    ["Está decaído", "Está decaído y responde poco"],
    ["No responde", "No responde o cuesta despertarlo"],
    ["Tiene sangrado abundante", "Tiene sangrado abundante y no se detiene"],
    ["No tiene sangrado", "No tiene sangrado abundante"],
  ];

  const contenedor = document.createElement("div");
  contenedor.className = "triage-chat-quick-replies";
  for (const [etiqueta, respuesta] of botones) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn btn-outline-teal btn-sm";
    button.textContent = etiqueta;
    button.addEventListener("click", () => {
      const replyInput = document.getElementById("triageChatReply");
      if (replyInput) {
        replyInput.value = respuesta;
        document.getElementById("triageChatForm")?.requestSubmit();
      }
    });
    contenedor.appendChild(button);
  }
  messages.appendChild(contenedor);
  messages.scrollTop = messages.scrollHeight;
}

function agregarMensajeConsultaGuiada(rol, mensaje) {
  const messages = document.getElementById("consultaTriageMensajes");
  if (!messages || !mensaje) return;
  const bubble = document.createElement("p");
  bubble.className = `triage-chat-message triage-chat-message-${rol}`;
  bubble.textContent = mensaje;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function mostrarOpcionesConsultaGuiada(opciones) {
  const contenedor = document.getElementById("consultaTriageOpciones");
  if (!contenedor) return;
  contenedor.replaceChildren();
  for (const opcion of opciones) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn btn-outline-teal btn-sm";
    button.textContent = opcion.label;
    button.addEventListener("click", () => procesarRespuestaConsultaGuiada(
      opcion.answer,
      opcion.value,
    ));
    contenedor.appendChild(button);
  }
}

function iniciarConsultaGuiada() {
  consultaGuiada = {
    paso: "mascota",
    mascota: null,
    sintomas: "",
    horas: null,
    conciencia: "Alerta",
    hemorragia: 0,
    ubicacion: null,
  };
  document.getElementById("consultaTriageMensajes").replaceChildren();
  document.getElementById("consultaTriageResultado").hidden = true;
  const estado = document.getElementById("consultaTriageEstado");
  estado.textContent = "";
  estado.classList.remove("text-danger");
  document.getElementById("consultaTriageAlertaEstado").hidden = true;
  document.getElementById("consultaTriageForm").hidden = true;
  agregarMensajeConsultaGuiada(
    "asistente",
    "Hola. Te voy a hacer unas preguntas breves para orientarte. ¿Por cuál mascota consultás?",
  );
  const mascotas = Array.from(mascotasPorId.values());
  if (!mascotas.length) {
    agregarMensajeConsultaGuiada(
      "asistente",
      "Todavía no hay mascotas registradas. Cerrá esta ventana y cargá una mascota en “Mis mascotas” para iniciar la consulta.",
    );
    mostrarOpcionesConsultaGuiada([]);
    return;
  }
  mostrarOpcionesConsultaGuiada(
    mascotas.map((mascota) => ({
      label: `${mascota.nombre} (${mascota.especie || "mascota"})`,
      answer: mascota.nombre,
      value: mascota,
    })),
  );
}

function avanzarConsultaGuiada(mensaje, opciones) {
  if (mensaje) agregarMensajeConsultaGuiada("asistente", mensaje);
  mostrarOpcionesConsultaGuiada(opciones);
  const form = document.getElementById("consultaTriageForm");
  const input = document.getElementById("consultaTriageRespuesta");
  form.hidden = opciones.length > 0;
  input.value = "";
  input.placeholder = "Escribí tu respuesta...";
  input.focus();
}

async function procesarRespuestaConsultaGuiada(respuesta, valor) {
  if (!consultaGuiada) return;
  agregarMensajeConsultaGuiada("tutor", respuesta);

  if (consultaGuiada.paso === "mascota") {
    consultaGuiada.mascota = valor;
    consultaGuiada.paso = "sintomas";
    document.getElementById("consultaTriageEtiqueta").textContent =
      "¿Qué cambio o síntoma notaste?";
    avanzarConsultaGuiada(
      `¿Qué le está pasando a ${valor.nombre}? Contalo con tus palabras, por ejemplo: “vomitó dos veces y está decaído”.`,
      [],
    );
    return;
  }

  if (consultaGuiada.paso === "sintomas") {
    consultaGuiada.sintomas = respuesta;
    consultaGuiada.paso = "horas";
    document.getElementById("consultaTriageForm").hidden = true;
    avanzarConsultaGuiada("¿Hace cuánto empezó?", [
      { label: "Hace menos de 1 hora", answer: "Hace menos de 1 hora", value: 0.5 },
      { label: "Hace unas 2 horas", answer: "Hace unas 2 horas", value: 2 },
      { label: "Hace unas 6 horas", answer: "Hace unas 6 horas", value: 6 },
      { label: "Desde ayer o más", answer: "Desde ayer o más", value: 24 },
    ]);
    return;
  }

  if (consultaGuiada.paso === "horas") {
    consultaGuiada.horas = valor;
    consultaGuiada.paso = "conciencia";
    avanzarConsultaGuiada("¿Cómo está de ánimo y respuesta?", [
      { label: "Alerta y responde", answer: "Está alerta y responde normalmente", value: "Alerta" },
      { label: "Decaído o responde poco", answer: "Está decaído y responde poco", value: "Deprimido" },
      { label: "No responde / cuesta despertarlo", answer: "No responde o cuesta despertarlo", value: "Estuporoso/Comatoso" },
    ]);
    return;
  }

  if (consultaGuiada.paso === "conciencia") {
    consultaGuiada.conciencia = valor;
    consultaGuiada.paso = "sangrado";
    avanzarConsultaGuiada("¿Tiene un sangrado abundante que no se detiene?", [
      { label: "Sí", answer: "Sí, tiene sangrado abundante", value: 1 },
      { label: "No", answer: "No tiene sangrado abundante", value: 0 },
    ]);
    return;
  }

  if (consultaGuiada.paso === "sangrado") {
    consultaGuiada.hemorragia = valor;
    await enviarConsultaGuiada();
    return;
  }

  if (consultaGuiada.paso === "aclaracion") {
    consultaGuiada.sintomas += `\nAclaración del tutor: ${respuesta}`;
    await enviarConsultaGuiada();
  }
}

async function enviarConsultaGuiada() {
  if (!consultaGuiada) return;
  document.getElementById("consultaTriageOpciones").replaceChildren();
  document.getElementById("consultaTriageForm").hidden = true;
  const estado = document.getElementById("consultaTriageEstado");
  estado.textContent = "Revisando la información...";
  try {
    consultaGuiada.ubicacion =
      consultaGuiada.ubicacion || await obtenerUbicacion();
    const mascota = consultaGuiada.mascota;
    const datosClinicos = {
      especie: mascota.especie || "Canino",
      tiempo_evolucion_hs: consultaGuiada.horas,
      estado_conciencia: consultaGuiada.conciencia,
      presencia_hemorragia: consultaGuiada.hemorragia,
    };
    const data = await evaluarTriaje(
      mascota.nombre,
      consultaGuiada.sintomas,
      consultaGuiada.ubicacion.lat,
      consultaGuiada.ubicacion.lng,
      datosClinicos,
    );
    ultimoNombreMascotaTriaje = mascota.nombre;
    ultimoDatosTriaje = {
      sintomas: consultaGuiada.sintomas,
      lat: consultaGuiada.ubicacion.lat,
      lng: consultaGuiada.ubicacion.lng,
      datosClinicos,
    };
    mostrarResultadoConsultaGuiada(data);
    estado.textContent = "";

    if (data.nivel_urgencia === "No concluyente") {
      consultaGuiada.paso = "aclaracion";
      agregarMensajeConsultaGuiada(
        "asistente",
        data.pregunta_aclaratoria ||
          "No pude identificar con claridad el síntoma. ¿Podés describirlo de otra manera?",
      );
      document.getElementById("consultaTriageEtiqueta").textContent =
        "Aclaración";
      avanzarConsultaGuiada("", []);
    }
  } catch (error) {
    estado.textContent = error.message || "No se pudo completar la consulta.";
    estado.classList.add("text-danger");
    document.getElementById("consultaTriageForm").hidden = false;
  }
}

function mostrarResultadoConsultaGuiada(data) {
  const resultado = document.getElementById("consultaTriageResultado");
  resultado.hidden = false;
  document.getElementById("consultaTriagePaciente").textContent =
    data.paciente || "Tu mascota";
  document.getElementById("consultaTriageUrgencia").textContent =
    data.nivel_urgencia || "Por confirmar";
  const nivel = String(data.nivel_urgencia || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase();
  const clasesUrgencia = {
    ALTA: "urgency-high",
    "EMERGENCIA CRITICA": "urgency-high",
    MODERADA: "urgency-medium",
    BAJA: "urgency-low",
    "NO CONCLUYENTE": "urgency-unknown",
  };
  document.getElementById("consultaTriageUrgencia").className =
    `urgency-badge ${clasesUrgencia[nivel] || "urgency-unknown"}`;
  document.getElementById("consultaTriageSintomas").textContent =
    data.sintomas_ingresados || "";
  document.getElementById("consultaTriagePasos").textContent =
    data.primeros_auxilios || "Contactá a un/a veterinario/a si el cuadro te preocupa.";

  const hayVeterinaria =
    data.veterinaria_cercana && data.veterinaria_cercana !== "No disponible";
  document.getElementById("consultaTriageVeterinaria").hidden = !hayVeterinaria;
  document.getElementById("consultaTriageClinica").textContent =
    data.veterinaria_cercana || "";
  document.getElementById("consultaTriageDireccion").textContent =
    data.direccion_veterinaria || "";
  const telefono = document.getElementById("consultaTriageTelefono");
  const telefonoSeguro = String(data.telefono_veterinaria || "").replace(/[^\d+]/g, "");
  telefono.hidden = !telefonoSeguro;
  if (telefonoSeguro) telefono.href = `tel:${telefonoSeguro}`;
  else telefono.removeAttribute("href");

  const mapaSection = document.getElementById("consultaTriageMapaSection");
  const coordenadas = [
    data.latitud_cliente,
    data.longitud_cliente,
    data.latitud_veterinaria,
    data.longitud_veterinaria,
  ];
  mapaSection.hidden = coordenadas.some((valor) => !Number.isFinite(valor));
  if (!mapaSection.hidden) {
    const [lat, lng, vetLat, vetLng] = coordenadas;
    const margen = 0.012;
    const bounds = [
      Math.min(lng, vetLng) - margen,
      Math.min(lat, vetLat) - margen,
      Math.max(lng, vetLng) + margen,
      Math.max(lat, vetLat) + margen,
    ];
    const map = document.getElementById("consultaTriageMapa");
    map.src = `https://www.openstreetmap.org/export/embed.html?bbox=${bounds.join("%2C")}&layer=mapnik&marker=${vetLat}%2C${vetLng}`;
    document.getElementById("consultaTriageMapaExterno").href =
      `https://www.openstreetmap.org/directions?from=${lat}%2C${lng}&to=${vetLat}%2C${vetLng}`;
  }

  const esUrgente = ["ALTA", "EMERGENCIA CRITICA"].includes(nivel);
  const alertaEstado = document.getElementById("consultaTriageAlertaEstado");
  alertaEstado.hidden = !data.alerta_despachada;
  alertaEstado.textContent = data.alerta_despachada
    ? data.mensaje_alerta || "Alerta de demostración registrada."
    : "";
  if (esUrgente && hayVeterinaria && !data.alerta_despachada) {
    abrirModalAlertaUrgencia(data);
  }
}

function abrirModalAlertaUrgencia(data) {
  const parentModal = document.getElementById("consultaTriage");
  const urgentModal = document.getElementById("modalAlertaUrgencia");
  if (!parentModal || !urgentModal || typeof bootstrap === "undefined") return;

  document.getElementById("modalUrgenciaMascota").textContent =
    data.paciente || "Tu mascota";
  document.getElementById("modalUrgenciaNivel").textContent =
    data.nivel_urgencia || "Urgencia";
  document.getElementById("modalUrgenciaPasos").textContent =
    data.primeros_auxilios || "Trasladá a la mascota a una guardia veterinaria.";
  document.getElementById("modalUrgenciaClinica").textContent =
    data.veterinaria_cercana || "Veterinaria asignada";
  document.getElementById("modalUrgenciaDireccion").textContent =
    data.direccion_veterinaria || "";
  document.getElementById("modalUrgenciaError").textContent = "";
  const alertButton = document.getElementById("modalUrgenciaAlertar");
  alertButton.disabled = false;
  alertButton.textContent = "Alertar a la veterinaria asignada";

  const telefono = document.getElementById("modalUrgenciaTelefono");
  const telefonoSeguro = String(data.telefono_veterinaria || "").replace(/[^\d+]/g, "");
  telefono.hidden = !telefonoSeguro;
  if (telefonoSeguro) telefono.href = `tel:${telefonoSeguro}`;
  else telefono.removeAttribute("href");

  const comoLlegar = document.getElementById("modalUrgenciaComoLlegar");
  const mapaSection = document.getElementById("modalUrgenciaMapaSection");
  const coordenadas = [
    data.latitud_cliente,
    data.longitud_cliente,
    data.latitud_veterinaria,
    data.longitud_veterinaria,
  ];
  mapaSection.hidden = coordenadas.some((valor) => !Number.isFinite(valor));
  comoLlegar.hidden = mapaSection.hidden;
  if (!mapaSection.hidden) {
    const [lat, lng, vetLat, vetLng] = coordenadas;
    comoLlegar.href =
      `https://www.openstreetmap.org/directions?from=${lat}%2C${lng}&to=${vetLat}%2C${vetLng}`;
    const margen = 0.012;
    const bounds = [
      Math.min(lng, vetLng) - margen,
      Math.min(lat, vetLat) - margen,
      Math.max(lng, vetLng) + margen,
      Math.max(lat, vetLat) + margen,
    ];
    document.getElementById("modalUrgenciaMapa").src =
      `https://www.openstreetmap.org/export/embed.html?bbox=${bounds.join("%2C")}&layer=mapnik&marker=${vetLat}%2C${vetLng}`;
  }

  const urgentInstance = bootstrap.Modal.getOrCreateInstance(urgentModal);
  const mostrarUrgencia = () => {
    parentModal.removeEventListener("hidden.bs.modal", mostrarUrgencia);
    urgentInstance.show();
  };
  if (parentModal.classList.contains("show")) {
    suspenderReinicioConsulta = true;
    parentModal.addEventListener("hidden.bs.modal", mostrarUrgencia, { once: true });
    bootstrap.Modal.getOrCreateInstance(parentModal).hide();
  } else {
    mostrarUrgencia();
  }
}

async function confirmarAlertaConsultaGuiada(button) {
  if (!ultimoNombreMascotaTriaje || !ultimoDatosTriaje) return;
  button.disabled = true;
  button.textContent = "Enviando alerta...";
  try {
    const data = await evaluarTriaje(
      ultimoNombreMascotaTriaje,
      ultimoDatosTriaje.sintomas,
      ultimoDatosTriaje.lat,
      ultimoDatosTriaje.lng,
      ultimoDatosTriaje.datosClinicos,
      true,
    );
    mostrarResultadoConsultaGuiada(data);
    bootstrap.Modal.getInstance(
      document.getElementById("modalAlertaUrgencia"),
    )?.hide();
  } catch (error) {
    document.getElementById("modalUrgenciaError").textContent =
      error.message || "No se pudo registrar la alerta.";
  } finally {
    button.disabled = false;
  }
}

async function cargarMascotasEnSelect() {
  const username = localStorage.getItem("username");
  const select = document.getElementById("mascotaSelect");
  const submitButton = document.querySelector(
    "#triageForm button[type='submit']",
  );
  const grid = document.getElementById("mascotasGrid");
  const message = document.getElementById("mascotasMessage");
  if ((!select && !grid) || !username) return;

  if (select) {
    select.replaceChildren(new Option("Cargando tus mascotas...", ""));
    select.disabled = true;
  }
  if (submitButton) submitButton.disabled = true;
  if (message) message.textContent = "Cargando tus mascotas...";

  try {
    const response = await fetch(
      `${API_URL}/mascotas/cliente/${encodeURIComponent(username)}`,
    );
    const mascotas = await leerRespuesta(response);
    mascotasPorId.clear();
    for (const mascota of mascotas) {
      mascotasPorId.set(String(mascota.id_mascota), mascota);
    }

    if (select) {
      select.replaceChildren();
      if (mascotas.length === 0) {
        select.add(new Option("Primero cargá una mascota", ""));
      } else {
        for (const mascota of mascotas) {
          select.add(
            new Option(
              `🐾 ${mascota.nombre} (${mascota.especie} - ${mascota.raza})`,
              String(mascota.id_mascota),
            ),
          );
        }
        const mascotaInicial = new URLSearchParams(window.location.search).get("mascota");
        select.value = mascotasPorId.has(mascotaInicial)
          ? mascotaInicial
          : String(mascotas[0].id_mascota);
      }
      select.disabled = mascotas.length === 0;
    }
    if (submitButton) submitButton.disabled = mascotas.length === 0;
    if (grid) renderizarResumenMascotas(mascotas, grid);
    if (message) {
      message.textContent = mascotas.length
        ? ""
        : "Todavía no cargaste mascotas. Usá “Cargar mascota” para agregar la primera.";
    }
    actualizarAccionesMascota();
  } catch (error) {
    console.error("Error al cargar mascotas:", error);
    mascotasPorId.clear();
    if (select) {
      select.replaceChildren(new Option("No se pudieron cargar tus mascotas", ""));
      select.disabled = true;
    }
    if (submitButton) submitButton.disabled = true;
    if (grid) grid.replaceChildren();
    mostrarMensaje(message || document.getElementById("triageMessage"), error.message, true);
  }
}

function renderizarResumenMascotas(mascotas, contenedor) {
  contenedor.replaceChildren();
  const count = document.getElementById("mascotasCount");
  if (count) {
    count.textContent = `${mascotas.length} ${mascotas.length === 1 ? "mascota" : "mascotas"}`;
  }

  for (const mascota of mascotas) {
    const column = document.createElement("div");
    column.className = "col-sm-6 col-lg-4";
    const card = document.createElement("article");
    card.className = "pet-summary-card";

    const photo = document.createElement("div");
    photo.className = "pet-summary-photo";
    if (mascota.foto_url) {
      const image = document.createElement("img");
      image.src = mascota.foto_url;
      image.alt = `Foto de ${mascota.nombre}`;
      image.loading = "lazy";
      image.addEventListener("error", () => {
        const placeholder = document.createElement("span");
        placeholder.textContent = "🐾";
        placeholder.setAttribute("aria-hidden", "true");
        photo.replaceChildren(placeholder);
      }, { once: true });
      photo.appendChild(image);
    } else {
      const placeholder = document.createElement("span");
      placeholder.textContent = "🐾";
      placeholder.setAttribute("aria-hidden", "true");
      photo.appendChild(placeholder);
    }

    const details = document.createElement("div");
    details.className = "pet-summary-details";
    const name = document.createElement("h3");
    name.textContent = mascota.nombre;
    const species = document.createElement("p");
    species.textContent = mascota.especie || "Animal";
    details.append(name, species);

    const actions = document.createElement("div");
    actions.className = "pet-summary-actions";
    const edit = document.createElement("button");
    edit.className = "btn btn-outline-teal btn-sm";
    edit.type = "button";
    edit.dataset.action = "edit";
    edit.dataset.petId = String(mascota.id_mascota);
    edit.textContent = "Modificar";
    const remove = document.createElement("button");
    remove.className = "btn btn-outline-danger btn-sm";
    remove.type = "button";
    remove.dataset.action = "delete";
    remove.dataset.petId = String(mascota.id_mascota);
    remove.textContent = "Eliminar";
    const history = document.createElement("button");
    history.className = "btn btn-outline-teal btn-sm";
    history.type = "button";
    history.dataset.action = "history";
    history.dataset.petId = String(mascota.id_mascota);
    history.textContent = "Historial";
    actions.append(edit, remove, history);
    card.append(photo, details, actions);
    column.appendChild(card);
    contenedor.appendChild(column);
  }
}

function actualizarAccionesMascota() {
  const select = document.getElementById("mascotaSelect");
  const habilitar = Boolean(select?.value && mascotasPorId.has(select.value));
  const editButton = document.getElementById("editarMascotaButton");
  const deleteButton = document.getElementById("eliminarMascotaButton");
  const historyButton = document.getElementById("historialMascotaButton");
  if (editButton) editButton.disabled = !habilitar;
  if (deleteButton) deleteButton.disabled = !habilitar;
  if (historyButton) historyButton.disabled = !habilitar;
}

async function abrirHistorialMedico(idMascota) {
  idMascota ||= document.getElementById("mascotaSelect")?.value;
  const username = localStorage.getItem("username");
  const contenedor = document.getElementById("contenedorHistorial");
  if (!idMascota || !username) return;

  contenedor.replaceChildren();
  contenedor.setAttribute("aria-busy", "true");
  const loading = document.createElement("p");
  loading.textContent = "Cargando historial clínico...";
  contenedor.appendChild(loading);
  bootstrap.Modal.getOrCreateInstance(
    document.getElementById("modalHistorial"),
  ).show();

  try {
    const response = await fetch(
      `${API_URL}/mascotas/${encodeURIComponent(idMascota)}/historial?username_cliente=${encodeURIComponent(username)}`,
    );
    const data = await leerRespuesta(response);
    contenedor.replaceChildren();

    if (data.historial.length === 0) {
      const empty = document.createElement("p");
      empty.className = "text-secondary mb-0";
      empty.textContent = "No hay registros médicos previos para esta mascota.";
      contenedor.appendChild(empty);
      return;
    }

    for (const registro of data.historial) {
      const item = document.createElement("article");
      item.className =
        "list-group-item mb-2 rounded border-start border-4 border-info shadow-sm";

      const header = document.createElement("div");
      header.className = "d-flex justify-content-between gap-3";
      const motive = document.createElement("h3");
      motive.className = "h6";
      motive.textContent = `🩺 ${registro.motivo}`;
      const date = document.createElement("time");
      date.className = "small text-secondary";
      date.dateTime = registro.fecha;
      date.textContent = `📅 ${registro.fecha}`;
      header.append(motive, date);

      const diagnosis = document.createElement("p");
      diagnosis.className = "mb-2";
      const label = document.createElement("strong");
      label.textContent = "Diagnóstico / Tratamiento: ";
      diagnosis.append(label, document.createTextNode(registro.diagnostico));

      const veterinarian = document.createElement("p");
      veterinarian.className = "small text-secondary mb-0";
      veterinarian.textContent = `👨‍⚕️ Atendido por: ${registro.veterinario}`;
      item.append(header, diagnosis, veterinarian);
      contenedor.appendChild(item);
    }
  } catch (error) {
    console.error("Error al cargar historial:", error);
    contenedor.replaceChildren();
    const message = document.createElement("p");
    message.className = "text-danger mb-0";
    message.textContent = error.message;
    contenedor.appendChild(message);
  } finally {
    contenedor.setAttribute("aria-busy", "false");
  }
}

function prepararEdicionMascota(idMascota) {
  mascotaEnEdicionId = idMascota || document.getElementById("mascotaSelect")?.value;
  const mascota = mascotasPorId.get(mascotaEnEdicionId);
  if (!mascota) return;

  document.getElementById("editNombre").value = mascota.nombre;
  document.getElementById("editEspecie").value = mascota.especie;
  document.getElementById("editRaza").value = mascota.raza;
  document.getElementById("editSexo").value = mascota.sexo;
  document.getElementById("editPeso").value = mascota.peso_kg;
  document.getElementById("editFechaNacimiento").value =
    mascota.fecha_nacimiento || "";
  document.getElementById("editFotoUrl").value = mascota.foto_url || "";
  mostrarMensaje(document.getElementById("edicionMascotaMessage"), "");
}

async function guardarEdicionMascota(event) {
  event.preventDefault();
  const select = document.getElementById("mascotaSelect");
  const idMascota = mascotaEnEdicionId || select?.value;
  const username = localStorage.getItem("username");
  const form = event.currentTarget;
  const formData = new FormData(form);
  const datos = {
    username_cliente: username,
    nombre: formData.get("nombre"),
    especie: formData.get("especie"),
    raza: formData.get("raza"),
    sexo: formData.get("sexo"),
    peso_kg: Number.parseFloat(formData.get("peso_kg")),
    fecha_nacimiento: formData.get("fecha_nacimiento") || null,
    foto_url: formData.get("foto_url") || null,
  };
  const button = document.getElementById("guardarEdicionButton");
  const message = document.getElementById("edicionMascotaMessage");
  button.disabled = true;
  mostrarMensaje(message, "Guardando cambios...");

  try {
    const response = await fetch(
      `${API_URL}/mascotas/${encodeURIComponent(idMascota)}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
      },
    );
    const mascota = await leerRespuesta(response);
    await cargarMascotasEnSelect();
    if (select) select.value = String(mascota.id_mascota);
    mascotaEnEdicionId = null;
    bootstrap.Modal.getOrCreateInstance(
      document.getElementById("modalEditarMascota"),
    ).hide();
    mostrarMensaje(
      document.getElementById("petManagementMessage") || document.getElementById("triageMessage"),
      `${mascota.nombre} se actualizó correctamente.`,
    );
  } catch (error) {
    console.error("Error al editar mascota:", error);
    mostrarMensaje(message, error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function confirmarEliminarMascota(idMascota) {
  const selectedId = idMascota || document.getElementById("mascotaSelect")?.value;
  const mascota = mascotasPorId.get(selectedId);
  const username = localStorage.getItem("username");
  if (!mascota || !username) return;
  if (!window.confirm(`¿Querés eliminar a ${mascota.nombre}?`)) return;

  try {
    const response = await fetch(
      `${API_URL}/mascotas/${encodeURIComponent(mascota.id_mascota)}?username_cliente=${encodeURIComponent(username)}`,
      { method: "DELETE" },
    );
    const data = await leerRespuesta(response);
    await cargarMascotasEnSelect();
    mostrarMensaje(
      document.getElementById("petManagementMessage") || document.getElementById("triageMessage"),
      data.mensaje,
    );
  } catch (error) {
    console.error("Error al eliminar mascota:", error);
    mostrarMensaje(
      document.getElementById("petManagementMessage") || document.getElementById("triageMessage"),
      error.message,
      true,
    );
  }
}

async function registrarNuevaMascota(event) {
  event.preventDefault();
  const username = localStorage.getItem("username");
  const form = event.currentTarget;
  const formData = new FormData(form);
  const datos = {
    username_cliente: username,
    nombre: formData.get("nombre"),
    especie: formData.get("especie"),
    raza: formData.get("raza"),
    sexo: formData.get("sexo"),
    peso_kg: Number.parseFloat(formData.get("peso_kg")),
  };
  const fechaNacimiento = formData.get("fecha_nacimiento");
  const fotoUrl = formData.get("foto_url");
  if (fechaNacimiento) datos.fecha_nacimiento = fechaNacimiento;
  if (fotoUrl) datos.foto_url = fotoUrl;

  const message = document.getElementById("registroMascotaMessage");
  const saveButton = document.getElementById("guardarMascotaButton");
  saveButton.disabled = true;
  mostrarMensaje(message, "Guardando mascota...");

  try {
    const response = await fetch(`${API_URL}/mascotas/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    });
    const mascota = await leerRespuesta(response);
    await cargarMascotasEnSelect();
    const select = document.getElementById("mascotaSelect");
    if (select) select.value = String(mascota.id_mascota);
    bootstrap.Modal.getOrCreateInstance(
      document.getElementById("modalNuevaMascota"),
    ).hide();
    form.reset();
    message.textContent = "";
    mostrarMensaje(
      document.getElementById("petManagementMessage") || document.getElementById("triageMessage"),
      `${mascota.nombre} se registró correctamente.`,
    );
  } catch (error) {
    console.error("Error al registrar mascota:", error);
    mostrarMensaje(message, error.message, true);
  } finally {
    saveButton.disabled = false;
  }
}

function cerrarSesion() {
  localStorage.removeItem("username");
  localStorage.removeItem("id_cliente");
  localStorage.removeItem("token");
  localStorage.removeItem("vet_username");
  localStorage.removeItem("vet_id");
  localStorage.removeItem("vet_token");
  window.location.href = "index.html";
}

function inicializarAplicacion() {
  cargarClinicasCercanas();
  const loginForm = document.getElementById("loginForm");
  loginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(loginForm);
    await iniciarSesion(form.get("usuario_o_email"), form.get("password"));
  });

  const veterinaryLoginForm = document.getElementById("veterinaryLoginForm");
  veterinaryLoginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(veterinaryLoginForm);
    await iniciarSesionVeterinaria(form.get("usuario"), form.get("password"));
  });

  if (loginForm || veterinaryLoginForm) {
    const acceso = new URLSearchParams(window.location.search).get("acceso");
    if (acceso === "unificado") {
      bootstrap.Modal.getOrCreateInstance(
        document.getElementById("loginModal"),
      ).show();
    } else if (acceso === "veterinaria" && veterinaryLoginForm) {
      bootstrap.Modal.getOrCreateInstance(
        document.getElementById("veterinaryLoginModal"),
      ).show();
    }
  }

  if (document.getElementById("veterinaryDashboard")) {
    document.getElementById("vetLogoutButton")
      ?.addEventListener("click", cerrarSesion);
    document.getElementById("vetRefreshAlerts")
      ?.addEventListener("click", () => cargarAlertasVeterinarias());
    document.getElementById("vetSimulateAlert")
      ?.addEventListener("click", (event) =>
        simularAlertaVeterinaria(event.currentTarget),
      );
    document.getElementById("vetAcceptAlert")
      ?.addEventListener("click", () =>
        actualizarEstadoAlertaVeterinaria("EN_ATENCION"),
      );
    document.getElementById("vetAlertResolved")
      ?.addEventListener("click", () =>
        actualizarEstadoAlertaVeterinaria("RESUELTA"),
      );
    document.getElementById("vetOpenHistory")
      ?.addEventListener("click", cargarHistoriaAlertaVeterinaria);
    document.getElementById("vetEvolutionForm")
      ?.addEventListener("submit", guardarEvolucionVeterinaria);
    document.getElementById("modalDetalleAlertaVet")
      ?.addEventListener("hidden.bs.modal", mostrarSiguienteAlertaVeterinaria);
    cargarPerfilVeterinaria();
    cargarAlertasVeterinarias();
    window.setInterval(() => cargarAlertasVeterinarias(true), 5000);
  }

  const triageForm = document.getElementById("triageForm");
  const triageChatForm = document.getElementById("triageChatForm");
  const mascotasGrid = document.getElementById("mascotasGrid");
  let textoSintomasConversacion = "";
  let datosClinicosConversacion = null;
  let ubicacionConversacion = null;
  if (triageForm || mascotasGrid) {
    const consultaModal = document.getElementById("consultaTriage");
    const modalUrgencia = document.getElementById("modalAlertaUrgencia");
    consultaModal?.addEventListener("shown.bs.modal", () => {
      if (!consultaGuiada) iniciarConsultaGuiada();
    });
    consultaModal?.addEventListener("hidden.bs.modal", () => {
      if (suspenderReinicioConsulta) {
        suspenderReinicioConsulta = false;
        return;
      }
      consultaGuiada = null;
    });
    modalUrgencia?.addEventListener("hidden.bs.modal", () => {
      if (consultaGuiada && !consultaModal.classList.contains("show")) {
        bootstrap.Modal.getOrCreateInstance(consultaModal).show();
      }
    });
    document.getElementById("consultaTriageReiniciar")
      ?.addEventListener("click", iniciarConsultaGuiada);

    document.getElementById("consultaTriageForm")
      ?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const input = document.getElementById("consultaTriageRespuesta");
        const respuesta = input.value.trim();
        if (!respuesta || !consultaGuiada) return;
        input.value = "";
        await procesarRespuestaConsultaGuiada(respuesta);
      });

    document.getElementById("modalUrgenciaAlertar")
      ?.addEventListener("click", (event) =>
        confirmarAlertaConsultaGuiada(event.currentTarget),
      );

    document
      .getElementById("abrirAccionesUrgencia")
      ?.addEventListener("click", () => {
        if (ultimoResultadoTriaje) abrirModalUrgencia(ultimoResultadoTriaje);
      });

    document
      .getElementById("confirmarAlertaVeterinaria")
      ?.addEventListener("click", async (event) => {
        const button = event.currentTarget;
        if (!ultimoNombreMascotaTriaje || !ultimoDatosTriaje) return;
        button.disabled = true;
        button.textContent = "Enviando alerta...";
        try {
          const data = await evaluarTriaje(
            ultimoNombreMascotaTriaje,
            ultimoDatosTriaje.sintomas,
            ultimoDatosTriaje.lat,
            ultimoDatosTriaje.lng,
            ultimoDatosTriaje.datosClinicos,
            true,
          );
          renderizarResultadoTriaje(data);
          renderizarMapaGPS(
            data.latitud_cliente,
            data.longitud_cliente,
            data.veterinaria_cercana,
            data.latitud_veterinaria,
            data.longitud_veterinaria,
          );
          bootstrap.Modal.getInstance(
            document.getElementById("modalAccionesUrgencia"),
          )?.hide();
        } catch (error) {
          document.getElementById("triageMessage").textContent =
            error.message || "No se pudo enviar la alerta.";
        } finally {
          button.disabled = false;
          button.textContent = "Alertar a la veterinaria asignada";
        }
      });

    const username = localStorage.getItem("username");
    if (!username) {
      window.location.href = "index.html";
      return;
    }

    const welcome = document.getElementById("welcomeMessage");
    if (welcome) welcome.textContent = `Hola, ${username}`;
    const greeting = document.getElementById("dashboardGreeting");
    if (greeting) greeting.textContent = `¡Hola, ${username}! 🐾`;
    cargarMascotasEnSelect();
    triageForm?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(triageForm);
      const result = document.getElementById("triageMessage");
      const submitButton = triageForm.querySelector("button[type='submit']");
      submitButton.disabled = true;
      mostrarMensaje(result, "Evaluando síntomas...");

      try {
        const ubicacion = await obtenerUbicacion();
        textoSintomasConversacion = String(form.get("sintomas"));
        datosClinicosConversacion = {
          tiempo_evolucion_hs: Number(form.get("tiempo_evolucion_hs")),
          estado_conciencia: form.get("estado_conciencia"),
          presencia_hemorragia: Number(form.get("presencia_hemorragia")),
        };
        ubicacionConversacion = ubicacion;
        const messages = document.getElementById("triageChatMessages");
        messages.replaceChildren();
        agregarMensajeChatTriaje("tutor", textoSintomasConversacion);
        const data = await evaluarTriaje(
          mascotasPorId.get(form.get("nombre_mascota"))?.nombre,
          textoSintomasConversacion,
          ubicacion.lat,
          ubicacion.lng,
          datosClinicosConversacion,
        );
        ultimoNombreMascotaTriaje =
          mascotasPorId.get(form.get("nombre_mascota"))?.nombre ||
          "Tu mascota";
        ultimoDatosTriaje = {
          sintomas: textoSintomasConversacion,
          lat: ubicacion.lat,
          lng: ubicacion.lng,
          datosClinicos: datosClinicosConversacion,
        };
        renderizarResultadoTriaje(data);
        if (data.nivel_urgencia === "No concluyente") {
          agregarMensajeChatTriaje(
            "asistente",
            data.pregunta_aclaratoria ||
              "No llego a identificar ese síntoma. ¿Podés describir qué cambio observás?",
          );
          agregarRespuestasRapidasChat();
          document.getElementById("triageChatReply").focus();
        }
        renderizarMapaGPS(
          data.latitud_cliente,
          data.longitud_cliente,
          data.veterinaria_cercana,
          data.latitud_veterinaria,
          data.longitud_veterinaria,
        );
      } catch (error) {
        console.error("Error en el triaje:", error);
        mostrarMensaje(result, error.message, true);
      } finally {
        submitButton.disabled = false;
      }
    });

    triageChatForm?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const replyInput = document.getElementById("triageChatReply");
      const reply = replyInput.value.trim();
      if (!reply || !datosClinicosConversacion || !ubicacionConversacion) return;

      const submitButton = triageChatForm.querySelector("button[type='submit']");
      const result = document.getElementById("triageMessage");
      submitButton.disabled = true;
      mostrarMensaje(result, "Revisando tu aclaración...");
      agregarMensajeChatTriaje("tutor", reply);
      textoSintomasConversacion += `\nAclaración del tutor: ${reply}`;
      if (/no responde|cuesta despertarlo/i.test(reply)) {
        datosClinicosConversacion.estado_conciencia = "Estuporoso/Comatoso";
      } else if (/decaído|responde poco/i.test(reply)) {
        datosClinicosConversacion.estado_conciencia = "Deprimido";
      } else if (/alerta|responde normalmente/i.test(reply)) {
        datosClinicosConversacion.estado_conciencia = "Alerta";
      }
      if (/sangrado abundante|no se detiene/i.test(reply)) {
        datosClinicosConversacion.presencia_hemorragia = 1;
      } else if (/no tiene sangrado|no hay sangrado/i.test(reply)) {
        datosClinicosConversacion.presencia_hemorragia = 0;
      }

      try {
        const form = new FormData(triageForm);
        const data = await evaluarTriaje(
          mascotasPorId.get(form.get("nombre_mascota"))?.nombre,
          textoSintomasConversacion,
          ubicacionConversacion.lat,
          ubicacionConversacion.lng,
          datosClinicosConversacion,
        );
        ultimoNombreMascotaTriaje =
          mascotasPorId.get(form.get("nombre_mascota"))?.nombre ||
          "Tu mascota";
        ultimoDatosTriaje = {
          sintomas: textoSintomasConversacion,
          lat: ubicacionConversacion.lat,
          lng: ubicacionConversacion.lng,
          datosClinicos: datosClinicosConversacion,
        };
        renderizarResultadoTriaje(data);
        if (data.nivel_urgencia === "No concluyente") {
          agregarMensajeChatTriaje(
            "asistente",
            data.pregunta_aclaratoria ||
              "Todavía no puedo confirmarlo. ¿Podés describir qué observás con otras palabras?",
          );
          agregarRespuestasRapidasChat();
          replyInput.value = "";
          replyInput.focus();
        }
        renderizarMapaGPS(
          data.latitud_cliente,
          data.longitud_cliente,
          data.veterinaria_cercana,
          data.latitud_veterinaria,
          data.longitud_veterinaria,
        );
        mostrarMensaje(result, "");
      } catch (error) {
        console.error("Error al aclarar el triaje:", error);
        mostrarMensaje(result, error.message, true);
      } finally {
        submitButton.disabled = false;
      }
    });

    document.getElementById("logoutButton")
      ?.addEventListener("click", cerrarSesion);
    document.getElementById("mascotaSelect")
      ?.addEventListener("change", actualizarAccionesMascota);
    document.getElementById("editarMascotaButton")
      ?.addEventListener("click", () => prepararEdicionMascota());
    document.getElementById("eliminarMascotaButton")
      ?.addEventListener("click", () => confirmarEliminarMascota());
    document.getElementById("historialMascotaButton")
      ?.addEventListener("click", () => abrirHistorialMedico());
    mascotasGrid?.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      const { action, petId } = button.dataset;
      if (action === "edit") {
        prepararEdicionMascota(petId);
        bootstrap.Modal.getOrCreateInstance(
          document.getElementById("modalEditarMascota"),
        ).show();
      } else if (action === "delete") {
        confirmarEliminarMascota(petId);
      } else if (action === "history") {
        abrirHistorialMedico(petId);
      }
    });
  }

  document
    .getElementById("formNuevaMascota")
    ?.addEventListener("submit", registrarNuevaMascota);
  document
    .getElementById("formEditarMascota")
    ?.addEventListener("submit", guardarEdicionMascota);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", inicializarAplicacion, {
    once: true,
  });
} else {
  inicializarAplicacion();
}

window.iniciarSesion = iniciarSesion;
window.evaluarTriaje = evaluarTriaje;
window.cargarMascotasEnSelect = cargarMascotasEnSelect;
window.registrarNuevaMascota = registrarNuevaMascota;
window.guardarEdicionMascota = guardarEdicionMascota;
window.confirmarEliminarMascota = confirmarEliminarMascota;
window.abrirHistorialMedico = abrirHistorialMedico;
window.cerrarSesion = cerrarSesion;
window.renderizarMapaGPS = renderizarMapaGPS;
window.cargarClinicasCercanas = cargarClinicasCercanas;