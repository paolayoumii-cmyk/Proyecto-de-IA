// PlateMatch · pantalla de preferencias
const CLAVE_ESTADO = "platematch_estado";
const CLAVE_RESULTADO = "platematch_resultado";
const $ = (sel) => document.querySelector(sel);
const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

let catalogo = null;
const busquedas = { favoritos: "", evitar: "", prohibidos: "" };

const nuevoPerfil = (nombre) => ({
  nombre, favoritos: [], evitar: [], prohibidos: [], grupos: [], objetivos: [], porcion: "",
});

let estado = JSON.parse(sessionStorage.getItem(CLAVE_ESTADO) || "null") || {
  modo: "individual",
  tamano: 4,
  actual: 0,
  comensales: [nuevoPerfil("Comensal 1")],
  mesa: nuevoPerfil("Perfil de la mesa"),
};

const limite = () => (catalogo ? catalogo.limite_mesa_individual : 10);
const esMesaGrande = () => estado.modo === "grupal" && estado.tamano > limite();
const porComensal = () => estado.modo === "grupal" && !esMesaGrande();
const guardar = () => sessionStorage.setItem(CLAVE_ESTADO, JSON.stringify(estado));

function perfilActivo() {
  if (estado.modo === "individual") return estado.comensales[0];
  if (esMesaGrande()) return estado.mesa;
  return estado.comensales[estado.actual];
}

// ------------------------------------------------------------ ingredientes
const nombresEn = (perfil, lista) =>
  lista === "prohibidos" ? perfil.prohibidos : perfil[lista].map((x) => x.ingrediente);

function listaDe(perfil, ing) {
  for (const l of ["favoritos", "evitar", "prohibidos"]) if (nombresEn(perfil, l).includes(ing)) return l;
  return null;
}

function quitar(perfil, ing) {
  perfil.favoritos = perfil.favoritos.filter((x) => x.ingrediente !== ing);
  perfil.evitar = perfil.evitar.filter((x) => x.ingrediente !== ing);
  perfil.prohibidos = perfil.prohibidos.filter((x) => x !== ing);
}

// Un ingrediente solo puede estar en una lista: al elegirlo en otra, se mueve.
function alternar(lista, ing) {
  const perfil = perfilActivo();
  const actual = listaDe(perfil, ing);
  quitar(perfil, ing);
  if (actual !== lista) {
    if (lista === "prohibidos") perfil.prohibidos.push(ing);
    else perfil[lista].push({ ingrediente: ing, max_g: null });
  }
  guardar();
  render();
}

const CLASE_SEL = { favoritos: "sel-fav", evitar: "sel-evitar", prohibidos: "sel-prohibido" };

function renderChips(lista) {
  const perfil = perfilActivo();
  const texto = busquedas[lista].trim().toLowerCase();
  const cont = document.querySelector(`[data-lista="${lista}"]`);
  const items = catalogo.ingredientes.filter((i) => !texto || i.toLowerCase().includes(texto));
  cont.innerHTML = items.length
    ? items.map((ing) => {
        const en = listaDe(perfil, ing);
        const clase = en === lista ? CLASE_SEL[lista] : en ? "en-uso" : "";
        return `<button type="button" class="chip ${clase}" data-ing="${esc(ing)}">${esc(ing)}</button>`;
      }).join("")
    : `<span class="texto-ayuda">Sin coincidencias.</span>`;
  cont.querySelectorAll("button").forEach((b) => (b.onclick = () => alternar(lista, b.dataset.ing)));
}

function renderSeleccion(lista) {
  const perfil = perfilActivo();
  const cont = document.querySelector(`[data-seleccion="${lista}"]`);
  const clase = lista === "favoritos" ? "fav" : "evitar";
  const rotulo = lista === "favoritos" ? "Porción máx. deseada" : "Porción máx. tolerada";
  cont.innerHTML = perfil[lista].map((x, i) => `
    <div class="seleccionado ${clase}">
      <span>${esc(x.ingrediente)}</span>
      <span class="acciones">
        <label for="g-${lista}-${i}">${rotulo}</label>
        <input id="g-${lista}-${i}" type="number" min="1" step="10" placeholder="g" value="${x.max_g ?? ""}" data-i="${i}">
        <button type="button" class="btn-texto" data-quitar="${esc(x.ingrediente)}">Quitar</button>
      </span>
    </div>`).join("");
  cont.querySelectorAll("input").forEach((inp) => (inp.oninput = () => {
    const v = parseFloat(inp.value);
    perfil[lista][inp.dataset.i].max_g = v > 0 ? v : null;
    guardar();
  }));
  cont.querySelectorAll("[data-quitar]").forEach((b) => (b.onclick = () => alternar(lista, b.dataset.quitar)));
}

// ------------------------------------------------------------ render general
function renderMesa() {
  document.querySelectorAll("#modo button").forEach((b) => b.classList.toggle("activo", b.dataset.modo === estado.modo));
  $("#config-grupal").hidden = estado.modo !== "grupal";
  $("#tamano-mesa").value = estado.tamano;

  const aviso = $("#aviso-mesa");
  if (esMesaGrande()) {
    aviso.className = "aviso aviso-ambar";
    aviso.innerHTML = `<b>Mesa grande (más de ${limite()} personas).</b> Las restricciones se generalizan para toda
      la mesa: un platillo solo sobrevive si no tiene ningún ingrediente prohibido. Mínimo 10 platillos.`;
  } else {
    aviso.className = "aviso aviso-azul";
    aviso.innerHTML = `Mesa de ${limite()} personas o menos: cada comensal registra sus propias restricciones
      y recibe mínimo 5 platillos.`;
  }

  $("#bloque-comensales").hidden = !porComensal();
  if (porComensal()) {
    const cont = $("#comensales");
    cont.innerHTML = estado.comensales.map((c, i) => `
      <button type="button" class="comensal ${i === estado.actual ? "activo" : ""}" data-i="${i}">
        <b>${esc(c.nombre)}</b>
        ${c.favoritos.length
          ? `<small class="ok">${c.favoritos.length} favorito${c.favoritos.length > 1 ? "s" : ""}</small>`
          : `<small class="falta">sin favoritos</small>`}
      </button>`).join("") +
      (estado.comensales.length < estado.tamano
        ? `<button type="button" class="btn-agregar" id="agregar">+ Agregar comensal (${estado.comensales.length} de ${estado.tamano})</button>`
        : "");
    cont.querySelectorAll("[data-i]").forEach((b) => (b.onclick = () => { estado.actual = +b.dataset.i; guardar(); render(); }));
    const ag = $("#agregar");
    if (ag) ag.onclick = () => {
      estado.comensales.push(nuevoPerfil(`Comensal ${estado.comensales.length + 1}`));
      estado.actual = estado.comensales.length - 1;
      guardar(); render();
    };
  }
}

function renderPerfil() {
  const perfil = perfilActivo();
  const nombre = $("#nombre-comensal");
  if (estado.modo === "individual") {
    $("#rotulo-perfil").textContent = "Comensal individual";
    nombre.value = "Tu perfil";
  } else if (esMesaGrande()) {
    $("#rotulo-perfil").textContent = `Restricciones generales · ${estado.tamano} personas`;
    nombre.value = "Perfil de la mesa";
  } else {
    $("#rotulo-perfil").textContent = `Comensal ${estado.actual + 1} de ${estado.tamano} · puedes editar el nombre`;
    nombre.value = perfil.nombre;
  }
  nombre.readOnly = !porComensal();
  $("#quitar-comensal").hidden = !(porComensal() && estado.comensales.length > 1);

  $("#r-fav").textContent = perfil.favoritos.length;
  $("#r-evi").textContent = perfil.evitar.length;
  $("#r-pro").textContent = perfil.prohibidos.length + perfil.grupos.length;

  document.querySelectorAll("#porcion button").forEach((b) => b.classList.toggle("activo", b.dataset.porcion === (perfil.porcion || "")));

  $("#objetivos").innerHTML = catalogo.objetivos.map((o) =>
    `<button type="button" class="chip objetivo ${perfil.objetivos.includes(o.id) ? "activo" : ""}" data-id="${o.id}">${esc(o.nombre)}</button>`).join("");
  $("#objetivos").querySelectorAll("button").forEach((b) => (b.onclick = () => {
    const id = b.dataset.id;
    perfil.objetivos = perfil.objetivos.includes(id) ? perfil.objetivos.filter((x) => x !== id) : [...perfil.objetivos, id];
    guardar(); render();
  }));

  $("#grupos").innerHTML = catalogo.grupos.map((g) =>
    `<button type="button" class="chip grupo ${perfil.grupos.includes(g.id) ? "sel-prohibido" : ""}" data-id="${g.id}">${esc(g.nombre)}</button>`).join("");
  $("#grupos").querySelectorAll("button").forEach((b) => (b.onclick = () => {
    const id = b.dataset.id;
    perfil.grupos = perfil.grupos.includes(id) ? perfil.grupos.filter((x) => x !== id) : [...perfil.grupos, id];
    guardar(); render();
  }));

  ["favoritos", "evitar", "prohibidos"].forEach(renderChips);
  ["favoritos", "evitar"].forEach(renderSeleccion);
}

function render() {
  renderMesa();
  renderPerfil();
}

// ------------------------------------------------------------ eventos
function cambiarTamano(n) {
  n = Math.max(2, Math.min(200, parseInt(n) || 2));
  estado.tamano = n;
  if (n <= limite() && estado.comensales.length > n) {
    estado.comensales = estado.comensales.slice(0, n);
    estado.actual = Math.min(estado.actual, n - 1);
  }
  guardar(); render();
}

function conectarEventos() {
  document.querySelectorAll("#modo button").forEach((b) => (b.onclick = () => {
    estado.modo = b.dataset.modo;
    if (estado.modo === "individual") estado.actual = 0;
    guardar(); render();
  }));
  $("#menos").onclick = () => cambiarTamano(estado.tamano - 1);
  $("#mas").onclick = () => cambiarTamano(estado.tamano + 1);
  $("#tamano-mesa").onchange = (e) => cambiarTamano(e.target.value);

  $("#nombre-comensal").oninput = (e) => {
    if (!porComensal()) return;
    perfilActivo().nombre = e.target.value || `Comensal ${estado.actual + 1}`;
    guardar(); renderMesa();
  };
  $("#quitar-comensal").onclick = () => {
    estado.comensales.splice(estado.actual, 1);
    estado.actual = Math.max(0, estado.actual - 1);
    guardar(); render();
  };
  document.querySelectorAll("#porcion button").forEach((b) => (b.onclick = () => {
    perfilActivo().porcion = b.dataset.porcion; guardar(); render();
  }));
  document.querySelectorAll("[data-buscar]").forEach((inp) => (inp.oninput = () => {
    busquedas[inp.dataset.buscar] = inp.value; renderChips(inp.dataset.buscar);
  }));
  $("#analizar").onclick = analizar;
}

function mostrarError(msg) {
  const box = $("#error-form");
  box.hidden = !msg;
  box.textContent = msg || "";
}

async function analizar() {
  let comensales, tamano;
  if (estado.modo === "individual") { comensales = [estado.comensales[0]]; tamano = 1; }
  else if (esMesaGrande()) { comensales = [estado.mesa]; tamano = estado.tamano; }
  else { comensales = estado.comensales; tamano = estado.tamano; }

  const sinFav = comensales.findIndex((c) => !c.favoritos.length);
  if (sinFav >= 0) {
    if (porComensal()) { estado.actual = sinFav; render(); }
    const quien = estado.modo === "individual" ? "Elige" : esMesaGrande() ? "La mesa debe elegir" : `${comensales[sinFav].nombre} debe elegir`;
    mostrarError(`${quien} al menos 1 ingrediente favorito.`);
    return;
  }
  mostrarError("");

  const btn = $("#analizar");
  btn.disabled = true;
  btn.textContent = "Calculando similitud…";
  try {
    const r = await fetch("/api/recomendar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tamano_mesa: tamano, comensales }),
    });
    const datos = await r.json();
    if (!r.ok) throw new Error(datos.error || "Error al calcular recomendaciones.");
    datos.modo = estado.modo;
    sessionStorage.setItem(CLAVE_RESULTADO, JSON.stringify(datos));
    location.href = "opciones.html";
  } catch (e) {
    mostrarError(e.message);
    btn.disabled = false;
    btn.textContent = "Analizar menú";
  }
}

// ------------------------------------------------------------ inicio
(async function iniciar() {
  try {
    catalogo = await (await fetch("/api/catalogo")).json();
  } catch {
    $("#error-servidor").hidden = false;
    $("#editor").hidden = true;
    $("#analizar").disabled = true;
    return;
  }
  $("#num-platillos").textContent = catalogo.platillos;
  for (const [k, v] of Object.entries(catalogo.porciones)) $(`[data-rango="${k}"]`).textContent = v;
  conectarEventos();
  render();
})();
