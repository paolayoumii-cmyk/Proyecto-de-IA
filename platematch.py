"""
PlateMatch - Construcción del menú
==================================
Toma el dataset MM-Food-100K de Hugging Face y arma el menú oficial del
restaurante con 50 platillos, siguiendo las reglas del planteamiento:

  * Solo platillos de tipo "Restaurant food".
  * Listado de ingredientes con 2 o más elementos.
  * Columnas usadas: ingredientes, porciones y valores nutricionales.

El menú se guarda en data/menu.json para no descargarlo cada vez.
Ejecuta `python platematch.py --actualizar` para volver a generarlo.
"""

import json
import re
import sys
from pathlib import Path

DATASET = "Humanbased-AI/MM-Food-100K"
NUM_PLATILLOS = 50
RUTA_MENU = Path(__file__).parent / "data" / "menu.json"


def _leer_json(valor, defecto):
    """Los campos del dataset vienen como texto JSON; los convierte a objetos."""
    if isinstance(valor, (list, dict)):
        return valor
    try:
        return json.loads(valor)
    except (TypeError, ValueError):
        return defecto


def normalizar(texto):
    return re.sub(r"\s+", " ", str(texto).strip().lower())


def _leer_porciones(lista):
    """["chicken:300g", "rice:1 cup"] -> {"chicken": 300.0} (solo gramos/ml)."""
    porciones = {}
    for entrada in _leer_json(lista, []):
        if ":" not in str(entrada):
            continue
        nombre, cantidad = str(entrada).rsplit(":", 1)
        m = re.match(r"\s*([\d.]+)\s*(g|gr|grams?|ml)\b", cantidad.lower())
        if m:
            try:
                porciones[normalizar(nombre)] = float(m.group(1))
            except ValueError:
                pass
    return porciones


def construir_menu(num_platillos=NUM_PLATILLOS):
    from datasets import load_dataset

    print("1. Conectando con el dataset en Hugging Face...")
    dataset = load_dataset(DATASET, split="train", streaming=True)

    print("2. Filtrando platillos (Restaurant food, 2+ ingredientes)...")
    menu, vistos = [], set()
    for item in dataset:
        if str(item.get("food_type", "")).strip() != "Restaurant food":
            continue

        ingredientes = []
        for ing in _leer_json(item.get("ingredients"), []):
            ing = normalizar(ing)
            if ing and ing not in ingredientes:
                ingredientes.append(ing)
        if len(ingredientes) < 2:
            continue

        nombre = str(item.get("dish_name") or "").strip()
        if not nombre or nombre.lower() in vistos:
            continue  # un menú no repite el mismo platillo

        nutricion = _leer_json(item.get("nutritional_profile"), {})
        if "calories_kcal" not in nutricion:
            continue

        porciones = _leer_porciones(item.get("portion_size"))
        vistos.add(nombre.lower())
        menu.append({
            "id": len(menu) + 1,
            "nombre": nombre,
            "ingredientes": ingredientes,
            "porciones_g": porciones,
            "porcion_total_g": round(sum(porciones.values()), 1) or None,
            "calorias": float(nutricion.get("calories_kcal") or 0),
            "proteina_g": float(nutricion.get("protein_g") or 0),
            "grasa_g": float(nutricion.get("fat_g") or 0),
            "carbohidratos_g": float(nutricion.get("carbohydrate_g") or 0),
            "metodo": str(item.get("cooking_method") or "").strip(),
            "imagen": item.get("image_url"),
        })
        if len(menu) == num_platillos:
            break
    return menu


def cargar_menu(actualizar=False):
    """Devuelve el menú desde data/menu.json; lo genera si no existe."""
    if RUTA_MENU.exists() and not actualizar:
        return json.loads(RUTA_MENU.read_text(encoding="utf-8"))
    menu = construir_menu()
    RUTA_MENU.parent.mkdir(exist_ok=True)
    RUTA_MENU.write_text(json.dumps(menu, ensure_ascii=False, indent=2), encoding="utf-8")
    return menu


if __name__ == "__main__":
    import pandas as pd

    menu = cargar_menu(actualizar="--actualizar" in sys.argv)
    df = pd.DataFrame(menu)
    print(f"\n¡Listo! Menú oficial de {len(df)} platillos (guardado en {RUTA_MENU}).\n")
    pd.set_option("display.width", 160)
    pd.set_option("display.max_colwidth", 50)
    print(df[["id", "nombre", "ingredientes", "porcion_total_g", "calorias", "proteina_g"]].to_string(index=False))
