// PlateMatch · pantalla de recomendaciones
const $ = (sel) => document.querySelector(sel);
const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const PORCION = { chica: "Porción chica", mediana: "Porción mediana", grande: "Porción grande" };

const datos = JSON.parse(sessionStorage.getItem("platematch_resultado") || "null");
let actual = 0;
const mostrados = {};

const nivel = (p) => (p >= 70 ? "nivel-alto" : p >= 40 ? "nivel-medio" : "nivel-bajo");
const gramos = (g) => (g ? `${Math.round(g)} g` : "—");

function tarjetaPlatillo(r, i) {
  const favs = new Set(r.favoritos.map((f) => f.ingrediente));
  const evis = new Set(r.evitados.map((e) => e.ingrediente));
  const chips = r.ingredientes
    .slice()
    .sort((a, b) => (favs.has(b) - favs.has(a)) || (evis.has(a) - evis.has(b)))
    .map((ing) => `<span class="ing ${favs.has(ing) ? "fav" : evis.has(ing) ? "evitar" : ""}">${esc(ing)}</span>`)
    .join("");

  const razones = [`Similitud de coseno con el perfil: <b>${(r.coseno * 100).toFixed(1)}%</b>`];
  r.favoritos.forEach((f) => razones.push(
    `<span class="pos">+${f.excede ? "4" : "10"} pts</span> contiene <b>${esc(f.ingrediente)}</b> (favorito)` +
    (f.gramos ? `, ${gramos(f.gramos)}` : "") + (f.excede ? ", supera la porción máxima deseada" : "")));
  r.evitados.forEach((e) => {
    const pts = e.tolerado === true ? 5 : e.tolerado === false ? 25 : 20;
    razones.push(`<span class="neg">−${pts} pts</span> contiene <b>${esc(e.ingrediente)}</b> (a evitar)` +
      (e.gramos ? `, ${gramos(e.gramos)}` : "") +
      (e.tolerado === true ? ", dentro de lo tolerado" : e.tolerado === false ? ", supera lo tolerado" : ""));
  });

  return `
  <article class="platillo ${i === 0 ? "top" : ""}" style="animation-delay:${Math.min(i, 10) * 40}ms">
    <div class="platillo-foto">
      ${r.imagen ? `<img src="${esc(r.imagen)}" alt="${esc(r.nombre)}" loading="lazy" onerror="this.remove()">` : ""}
      <span class="rango">#${i + 1}</span>
      <span class="match-flotante ${nivel(r.compatibilidad)}">${r.compatibilidad}%<small>match</small></span>
    </div>
    <div class="platillo-cuerpo">
      <div>
        <h3>${esc(r.nombre)}</h3>
        <div class="original">${esc(r.nombre_original)} · ${PORCION[r.porcion] || "Porción no indicada"} (${gramos(r.porcion_total_g)})</div>
      </div>
      <div class="barra"><span class="${nivel(r.compatibilidad)}" style="width:${r.compatibilidad}%"></span></div>
      <div class="ingredientes">${chips}</div>
      <div class="nutricion">
        <div><b>${Math.round(r.calorias)}</b><small>kcal</small></div>
        <div><b>${Math.round(r.proteina_g)} g</b><small>proteína</small></div>
        <div><b>${Math.round(r.carbohidratos_g)} g</b><small>carbos</small></div>
        <div><b>${Math.round(r.grasa_g)} g</b><small>grasa</small></div>
      </div>
      <details class="porque">
        <summary>¿Por qué se recomienda?</summary>
        <ul>${razones.map((x) => `<li>${x}</li>`).join("")}</ul>
      </details>
    </div>
  </article>`;
}

function renderLateral(res, sugeridos) {
  const bloque = $("#bloque-comensales");
  bloque.hidden = datos.resultados.length < 2;
  if (!bloque.hidden) {
    $("#comensales").innerHTML = datos.resultados.map((r, i) => `
      <button type="button" class="comensal ${i === actual ? "activo" : ""}" data-i="${i}">
        <b>${esc(r.comensal)}</b><small class="ok">${Math.min(r.minimo, r.evaluados)} platillos</small>
      </button>`).join("");
    $("#comensales").querySelectorAll("button").forEach((b) => (b.onclick = () => { actual = +b.dataset.i; render(); }));
  }

  $("#metricas").innerHTML = `
    <div class="metrica m-gris"><b>${datos.total_platillos}</b><small>En el menú</small></div>
    <div class="metrica m-rojo"><b>${res.descartados.length}</b><small>Descartados</small></div>
    <div class="metrica m-azul"><b>${res.evaluados}</b><small>Evaluados</small></div>
    <div class="metrica m-verde"><b>${sugeridos}</b><small>Mostrados</small></div>`;

  $("#bloque-descartados").hidden = !res.descartados.length;
  $("#descartados").innerHTML = res.descartados
    .map((d) => `<li><b>${esc(d.nombre)}</b><span>${esc(d.motivo)}</span></li>`).join("");
}

function render() {
  const res = datos.resultados[actual];
  const cuantos = mostrados[actual] ?? res.minimo;
  const lista = res.recomendados.slice(0, cuantos);
  renderLateral(res, lista.length);

  let html = `
    <div class="titulo-resultados">
      <div>
        <h2>${esc(res.comensal)}</h2>
        <p>Platillos ordenados por compatibilidad · mínimo ${res.minimo} recomendados</p>
      </div>
    </div>
    ${res.suficientes ? "" : `<div class="aviso aviso-ambar" style="margin:0 0 20px">
      Solo ${res.evaluados} platillos del menú cumplen con las restricciones, menos del mínimo de ${res.minimo}.
      Los platillos con ingredientes prohibidos nunca se recomiendan.</div>`}`;

  html += lista.length
    ? `<div class="rejilla">${lista.map(tarjetaPlatillo).join("")}</div>`
    : `<div class="vacio">Ningún platillo del menú es compatible con estas restricciones.</div>`;

  if (cuantos < res.recomendados.length) {
    const resto = res.recomendados.length - cuantos;
    html += `<div class="mas"><button type="button" class="btn-secundario" id="ver-mas">
      Ver ${Math.min(5, resto)} más (${resto} compatibles restantes)</button></div>`;
  }

  $("#contenido").innerHTML = html;
  const verMas = $("#ver-mas");
  if (verMas) verMas.onclick = () => { mostrados[actual] = cuantos + 5; render(); };
}

if (!datos) {
  $("#lateral").hidden = true;
  $("#contenido").innerHTML = `<div class="vacio">Aún no hay recomendaciones.<br><br>
    <a class="btn-secundario" href="eleccion.html">Configurar preferencias</a></div>`;
} else {
  $("#subtitulo").textContent = datos.modo === "individual"
    ? "Recomendaciones personalizadas · comensal individual"
    : datos.generalizado
      ? `Mesa grande de ${datos.tamano_mesa} personas · restricciones generalizadas`
      : `Mesa de ${datos.tamano_mesa} personas · ${datos.resultados.length} perfiles individuales`;
  render();
}
