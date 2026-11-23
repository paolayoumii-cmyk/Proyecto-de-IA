"""
PlateMatch - Servidor web
Ejecuta:  python app.py   y abre http://127.0.0.1:5000
"""

import sys
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from recomendador import PlateMatch

CARPETA = Path(__file__).parent
app = Flask(__name__, static_folder=None)
motor = PlateMatch()


def _lista_porciones(items):
    limpios = []
    for item in items or []:
        if isinstance(item, str):
            item = {"ingrediente": item}
        ing = item.get("ingrediente")
        if ing not in motor.indice:
            continue
        try:
            max_g = float(item["max_g"]) if item.get("max_g") not in (None, "") else None
        except (TypeError, ValueError):
            max_g = None
        limpios.append({"ingrediente": ing, "max_g": max_g if max_g and max_g > 0 else None})
    return limpios


def _validar_perfil(datos, numero):
    perfil = {
        "nombre": str(datos.get("nombre") or f"Comensal {numero}")[:40],
        "favoritos": _lista_porciones(datos.get("favoritos")),
        "evitar": _lista_porciones(datos.get("evitar")),
        "prohibidos": [i for i in datos.get("prohibidos") or [] if i in motor.indice],
        "grupos": [g for g in datos.get("grupos") or [] if isinstance(g, str)],
        "objetivos": [o for o in datos.get("objetivos") or [] if isinstance(o, str)],
        "porcion": datos.get("porcion"),
    }
    if not perfil["favoritos"]:
        raise ValueError(f"{perfil['nombre']}: elige al menos 1 ingrediente favorito.")
    return perfil


@app.get("/")
def inicio():
    return send_from_directory(CARPETA, "eleccion.html")


@app.get("/<path:archivo>")
def estaticos(archivo):
    if Path(archivo).suffix not in {".html", ".css", ".js", ".svg", ".png"}:
        return "No encontrado", 404
    return send_from_directory(CARPETA, archivo)


@app.get("/api/catalogo")
def catalogo():
    return jsonify(motor.catalogo())


@app.get("/api/menu")
def menu():
    return jsonify(motor.platillos())


@app.post("/api/recomendar")
def recomendar():
    datos = request.get_json(silent=True) or {}
    try:
        try:
            tamano = int(datos.get("tamano_mesa") or 1)
        except (TypeError, ValueError):
            raise ValueError("El tamaño de la mesa debe ser un número.")
        if not 1 <= tamano <= 200:
            raise ValueError("El tamaño de la mesa debe estar entre 1 y 200 personas.")
        comensales = datos.get("comensales") or []
        if not comensales:
            raise ValueError("Agrega al menos un comensal.")
        if tamano <= motor.catalogo()["limite_mesa_individual"] and len(comensales) > tamano:
            raise ValueError(f"La mesa es de {tamano} personas pero hay {len(comensales)} perfiles.")
        perfiles = [_validar_perfil(c, i + 1) for i, c in enumerate(comensales)]
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    resultado = motor.recomendar_mesa(tamano, perfiles)
    resultado["tamano_mesa"] = tamano
    resultado["total_platillos"] = len(motor.menu)
    return jsonify(resultado)


if __name__ == "__main__":
    url = "http://127.0.0.1:5000"
    print(f"\n  PlateMatch listo en {url}  (Ctrl+C para detener)\n")
    if "--sin-navegador" not in sys.argv:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(debug=False)
