const API_URL = "http://127.0.0.1:8000";

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

    localStorage.setItem("username", data.username);
    localStorage.setItem("id_cliente", String(data.id_cliente));
    localStorage.setItem("token", data.token_sesion);
    window.location.href = "dashboard.html";
  } catch (error) {
    console.error("Error al iniciar sesión:", error);
    mostrarMensaje(document.getElementById("loginMessage"), error.message, true);
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

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  loginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(loginForm);
    await iniciarSesion(form.get("usuario_o_email"), form.get("password"));
  });

  const triageForm = document.getElementById("triageForm");
  if (triageForm) {
    const username = localStorage.getItem("username");
    if (!username) {
      window.location.href = "index.html";
      return;
    }

    document.getElementById("welcomeMessage").textContent = `Hola, ${username}`;
    triageForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(triageForm);
      const result = document.getElementById("triageResult");
      const submitButton = triageForm.querySelector("button[type='submit']");
      submitButton.disabled = true;
      mostrarMensaje(result, "Evaluando síntomas...");

      try {
        const data = await evaluarTriaje(
          form.get("nombre_mascota"),
          form.get("sintomas"),
        );
        result.textContent = JSON.stringify(data, null, 2);
        result.classList.remove("text-danger");
        result.classList.add("text-success");
      } catch (error) {
        console.error("Error en el triaje:", error);
        mostrarMensaje(result, error.message, true);
      } finally {
        submitButton.disabled = false;
      }
    });

    document.getElementById("logoutButton").addEventListener("click", () => {
      localStorage.removeItem("username");
      localStorage.removeItem("id_cliente");
      localStorage.removeItem("token");
      window.location.href = "index.html";
    });
  }
});

window.iniciarSesion = iniciarSesion;
window.evaluarTriaje = evaluarTriaje;