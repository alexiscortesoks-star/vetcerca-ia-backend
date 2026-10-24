const API_URL = `${window.location.protocol}//${window.location.hostname}:8000`;
let mapaInstancia = null;
const mascotasPorId = new Map();
let mascotaEnEdicionId = null;

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
    document.getElementById("vetPhoneLink").href =
      `tel:${perfil.telefono_guardia.replace(/[^\d+]/g, "")}`;
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

async function evaluarTriaje(nombreMascota, sintomas, lat, lng) {
  const idCliente = Number(localStorage.getItem("id_cliente"));
  const payload = {
    nombre_mascota: nombreMascota,
    sintomas,
    latitud_cliente: Number.isFinite(lat) ? lat : -34.6037,
    longitud_cliente: Number.isFinite(lng) ? lng : -58.3816,
  };
  if (Number.isInteger(idCliente) && idCliente > 0) {
    payload.id_cliente = idCliente;
  }

  const response = await fetch(`${API_URL}/triaje/evaluar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
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
      latitud: -34.562069,
      longitud: -58.4596054,
      horario_informado:
        "24/7 según OpenStreetMap; pendiente de confirmación directa",
      fuente_url: "https://www.openstreetmap.org/node/2276920088",
    },
    {
      nombre: "Panda",
      direccion: "Av. Ruiz Huidobro 4771, Saavedra, CABA",
      latitud: -34.5549092,
      longitud: -58.4945994,
      horario_informado:
        "24/7 según OpenStreetMap; pendiente de confirmación directa",
      fuente_url: "https://www.openstreetmap.org/node/8067203564",
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
      const status = document.createElement("p");
      status.textContent = "Candidata · horario por confirmar";
      const source = document.createElement("a");
      source.href = clinic.fuente_url;
      source.target = "_blank";
      source.rel = "noopener noreferrer";
      source.textContent = "Fuente: OpenStreetMap";
      popup.append(name, address, status, source);
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

    clinicsList.replaceChildren();

    for (const clinic of data.veterinarias) {
      const verificacionPendiente =
        clinic.estado_verificacion !== "VERIFICADO";
      const guardia24hsVerificada =
        !verificacionPendiente && clinic.es_24hs;
      const estadoHorario = guardia24hsVerificada
        ? "Guardia 24 h verificada"
        : verificacionPendiente
          ? "Horario por confirmar"
          : "Guardia 24 h no verificada";
      if (typeof L !== "undefined") {
        if (!nombresMarcadoresLocales.has(clinic.nombre)) {
          const popup = document.createElement("div");
          const popupName = document.createElement("strong");
          popupName.textContent = clinic.nombre;
          const popupStatus = document.createElement("p");
          popupStatus.className = "mb-0";
          popupStatus.textContent = estadoHorario;
          popup.append(popupName, popupStatus);
          L.marker([clinic.latitud, clinic.longitud])
            .addTo(mapaInstancia)
            .bindPopup(popup);
        }
      }

      const item = document.createElement("li");
      const name = document.createElement("strong");
      name.textContent = clinic.nombre;
      const details = document.createElement("span");
      details.textContent =
        `${clinic.distancia_km.toFixed(1)} km · ${clinic.direccion}`;
      const status = document.createElement("span");
      status.className = guardia24hsVerificada
        ? "clinic-verification clinic-verification-confirmed"
        : "clinic-verification clinic-verification-pending";
      status.textContent = estadoHorario;
      item.append(name, details, status);

      if (clinic.horario_informado) {
        const hours = document.createElement("span");
        hours.textContent = clinic.horario_informado;
        item.appendChild(hours);
      }
      if (clinic.telefono) {
        const phone = document.createElement("span");
        phone.textContent = `Teléfono: ${clinic.telefono}`;
        item.appendChild(phone);
      } else {
        const phone = document.createElement("span");
        phone.textContent = "Teléfono no disponible";
        item.appendChild(phone);
      }
      if (clinic.fuente_url) {
        const source = document.createElement("a");
        source.href = clinic.fuente_url;
        source.target = "_blank";
        source.rel = "noopener noreferrer";
        source.textContent = `Fuente: ${clinic.fuente_datos || "consultar"}`;
        item.appendChild(source);
      }
      if (clinic.atribucion_fuente) {
        const attribution = document.createElement("small");
        attribution.textContent = clinic.atribucion_fuente;
        item.appendChild(attribution);
      }
      clinicsList.appendChild(item);
    }

    const pendientes = data.veterinarias.filter(
      (clinic) =>
        clinic.estado_verificacion !== "VERIFICADO" || !clinic.es_24hs,
    ).length;
    message.textContent = data.cantidad
      ? `${data.cantidad} clínicas candidatas dentro de 25 km${
          pendientes
            ? ` · ${pendientes} sin guardia 24 h verificada`
            : ""
        }`
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
    clinicsList.replaceChildren();
    for (const clinic of candidatasLocales) {
      const item = document.createElement("li");
      const name = document.createElement("strong");
      name.textContent = clinic.nombre;
      const address = document.createElement("span");
      address.textContent = clinic.direccion;
      const status = document.createElement("span");
      status.className = "clinic-verification clinic-verification-pending";
      status.textContent = "Horario por confirmar";
      const hours = document.createElement("span");
      hours.textContent = clinic.horario_informado;
      const source = document.createElement("a");
      source.href = clinic.fuente_url;
      source.target = "_blank";
      source.rel = "noopener noreferrer";
      source.textContent = "Fuente: OpenStreetMap";
      item.append(name, address, status, hours, source);
      clinicsList.appendChild(item);
    }
    message.textContent =
      `Mostrando ${candidatasLocales.length} candidatas guardadas; ` +
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
  const resultado = document.getElementById("resultadoCard");
  const urgencia = document.getElementById("resultadoUrgencia");
  const nivel = String(data.nivel_urgencia || "").toUpperCase();
  const etiquetas = {
    ALTA: { texto: "Atención urgente", clase: "urgency-high" },
    MEDIA: { texto: "Consulta recomendada", clase: "urgency-medium" },
    BAJA: { texto: "Urgencia baja", clase: "urgency-low" },
  };
  const etiqueta = etiquetas[nivel] || {
    texto: "Nivel por confirmar",
    clase: "urgency-unknown",
  };

  resultado.hidden = false;
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
  document.getElementById("triageMessage").textContent = "";
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

document.addEventListener("DOMContentLoaded", () => {
  cargarClinicasCercanas();
  const loginForm = document.getElementById("loginForm");
  loginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(loginForm);
    await iniciarSesion(form.get("usuario_o_email"), form.get("password"));
  });

  if (
    loginForm &&
    new URLSearchParams(window.location.search).get("acceso") === "unificado"
  ) {
    bootstrap.Modal.getOrCreateInstance(
      document.getElementById("loginModal"),
    ).show();
  }

  if (document.getElementById("veterinaryDashboard")) {
    document.getElementById("vetLogoutButton")
      ?.addEventListener("click", cerrarSesion);
    cargarPerfilVeterinaria();
  }

  const triageForm = document.getElementById("triageForm");
  const mascotasGrid = document.getElementById("mascotasGrid");
  if (triageForm || mascotasGrid) {
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
        const data = await evaluarTriaje(
          mascotasPorId.get(form.get("nombre_mascota"))?.nombre,
          form.get("sintomas"),
          ubicacion.lat,
          ubicacion.lng,
        );
        renderizarResultadoTriaje(data);
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
});

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