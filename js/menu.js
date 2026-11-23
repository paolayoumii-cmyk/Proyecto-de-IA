// PlateMatch · menú completo del restaurante
const $ = (sel) => document.querySelector(sel);
const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const PORCION = { chica: "Porción chica", mediana: "Porción mediana", grande: "Porción grande" };
const gramos = (g) => (g ? `${Math.round(g)} g` : "—");

let platillos = [];
let grupos = {};
const excluidos = new Set();

function tarjeta(p) {
  const contiene = p.grupos.map((g) => grupos[g]).filter(Boolean);
  return `
  <article class="platillo">
    <div class="platillo-foto">
      ${p.imagen ? `<img src="${esc(p.imagen)}" alt="${esc(p.nombre)}" loading="lazy" onerror="this.remove()">` : ""}
      <span class="rango">${p.id}</span>
    </div>
    <div class="platillo-cuerpo">
      <div>
        <h3>${esc(p.nombre)}</h3>
        <div class="original">${esc(p.nombre_original)} · ${PORCION[p.porcion] || "Porción no indicada"} (${gramos(p.porcion_total_g)})</div>
      </div>
      <div class="ingredientes">${p.ingredientes.map((i) => `<span class="ing">${esc(i)}</span>`).join("")}</div>
      <div class="nutricion">
        <div><b>${Math.round(p.calorias)}</b><small>kcal</small></div>
        <div><b>${Math.round(p.proteina_g)} g</b><small>proteína</small></div>
        <div><b>${Math.round(p.carbohidratos_g)} g</b><small>carbos</small></div>
        <div><b>${Math.round(p.grasa_g)} g</b><small>grasa</small></div>
      </div>
      ${contiene.length ? `<div class="contiene">Contiene: ${contiene.map(esc).join(", ")}</div>` : ""}
    </div>
  </article>`;
}

function render() {
  const texto = $("#buscar").value.trim().toLowerCase();
  const porcion = $("#porcion").value;
  const [campo, dir] = $("#orden").value.split("-");

  let lista = platillos.filter((p) =>
    (!texto || p.nombre.toLowerCase().includes(texto) || p.nombre_original.toLowerCase().includes(texto) ||
      p.ingredientes.some((i) => i.toLowerCase().includes(texto))) &&
    (!porcion || p.porcion === porcion) &&
    !p.grupos.some((g) => excluidos.has(g)));

  lista = lista.slice().sort((a, b) => {
    if (campo === "nombre") return a.nombre.localeCompare(b.nombre, "es");
    return dir === "desc" ? b[campo] - a[campo] : a[campo] - b[campo];
  });

  $("#conteo").textContent = `Mostrando ${lista.length} de ${platillos.length} platillos`;
  $("#rejilla").innerHTML = lista.length
    ? lista.map(tarjeta).join("")
    : `<div class="vacio" style="grid-column:1/-1">Ningún platillo coincide con los filtros.</div>`;
}

function renderExcluir() {
  $("#excluir").innerHTML = Object.entries(grupos).map(([id, nombre]) =>
    `<button type="button" class="chip grupo ${excluidos.has(id) ? "sel-prohibido" : ""}" data-id="${id}">${esc(nombre)}</button>`).join("");
  $("#excluir").querySelectorAll("button").forEach((b) => (b.onclick = () => {
    excluidos.has(b.dataset.id) ? excluidos.delete(b.dataset.id) : excluidos.add(b.dataset.id);
    renderExcluir(); render();
  }));
}

(async function iniciar() {
  try {
    const [menu, catalogo] = await Promise.all([
      fetch("/api/menu").then((r) => r.json()),
      fetch("/api/catalogo").then((r) => r.json()),
    ]);
    platillos = menu;
    grupos = Object.fromEntries(catalogo.grupos.map((g) => [g.id, g.nombre]));
  } catch {
    $("#error-servidor").hidden = false;
    $("#conteo").textContent = "";
    return;
  }
  $("#buscar").oninput = render;
  $("#porcion").onchange = render;
  $("#orden").onchange = render;
  $("#limpiar").onclick = () => {
    $("#buscar").value = ""; $("#porcion").value = ""; $("#orden").value = "id";
    excluidos.clear(); renderExcluir(); render();
  };
  renderExcluir();
  render();
})();
