import pandas as pd
from datasets import load_dataset

print("1. Conectando con el dataset en Hugging Face...")
dataset = load_dataset("Humanbased-AI/MM-Food-100K", split="train", streaming=True)

print("2. Filtrando platillos")
platillos_filtrados = []

contador = 0
for item in dataset:
    tipo_comida = item.get("type", "Restaurant food")
    ingredientes = item.get("ingredients", [])
    if contador < 50:
        platillos_filtrados.append({
            "id": contador + 1,
            "nombre": item.get("title", f"Platillo {contador + 1}"),
            "ingredientes": ingredientes,
            "calorias": item.get("calories", 400),
            "porcion": "Mediana"
        })
        contador += 1
    else:
        break

df_menu_50 = pd.DataFrame(platillos_filtrados)

print(f"¡Listo! Ya tenemos nuestro menú oficial de {len(df_menu_50)} platillos listos para el algoritmo.")
print(df_menu_50.head(5))