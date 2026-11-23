// PlateMatch · pestañas de navegación compartidas
(function () {
  const nav = document.querySelector(".navegacion");
  if (!nav) return;
  const actual = nav.dataset.actual;
  const hayResultados = !!sessionStorage.getItem("platematch_resultado");
  const pestanas = [
    { id: "preferencias", texto: "Preferencias", href: "eleccion.html" },
    { id: "menu", texto: "Menú", href: "menu.html" },
  ];
  if (hayResultados || actual === "recomendaciones") {
    pestanas.push({ id: "recomendaciones", texto: "Recomendaciones", href: "opciones.html" });
  }
  nav.innerHTML = pestanas
    .map((p) => `<a href="${p.href}" class="${p.id === actual ? "actual" : ""}">${p.texto}</a>`)
    .join("");
})();
