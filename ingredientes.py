"""
Diccionarios de apoyo: traducción de ingredientes y platillos al español
y grupos de restricciones (alergias / dietas).

Los ingredientes del dataset vienen en inglés y con variantes
("tomato" / "tomatoes"). La traducción los une en un solo nombre
canónico, lo que también limpia el espacio vectorial del modelo.
"""

import re

TRADUCCION = {
    "almonds": "almendras", "basil": "albahaca", "beef": "res",
    "beef patty": "carne de hamburguesa", "beef sauce": "salsa de res",
    "blueberries": "arándanos", "bok choy": "bok choy", "bread": "pan",
    "breading": "empanizado", "broccoli": "brócoli", "broth": "caldo",
    "bun": "pan de hamburguesa", "butter sauce": "salsa de mantequilla",
    "cabbage": "col", "carrots": "zanahoria", "cheese": "queso",
    "chicken": "pollo", "chicken wings": "alitas de pollo", "chili": "chile",
    "chili oil": "aceite de chile", "chocolate sauce": "salsa de chocolate",
    "cilantro": "cilantro", "corn": "elote", "crab": "cangrejo",
    "crawfish": "cangrejo de río", "cream": "crema", "cucumber": "pepino",
    "cucumbers": "pepino", "dipping sauce": "salsa para mojar", "dough": "masa",
    "dressing": "aderezo", "duck": "pato", "dumpling dough": "masa de dumpling",
    "dumplings": "dumplings", "egg": "huevo", "fish": "pescado",
    "fried chicken": "pollo frito", "fried dough sticks": "palitos de masa frita",
    "fried onions": "cebolla frita", "fried ribs": "costillas fritas",
    "garlic": "ajo", "ginger": "jengibre", "green onion": "cebollín",
    "green onions": "cebollín", "green peppers": "pimiento verde",
    "greens": "hojas verdes", "ham": "jamón", "herbs": "hierbas finas",
    "ice cream": "helado", "lemon": "limón amarillo", "lettuce": "lechuga",
    "lime": "limón", "meat": "carne", "mushrooms": "champiñones",
    "noodles": "fideos", "oil": "aceite", "omelette": "omelette",
    "onions": "cebolla", "parsley": "perejil", "pasta": "pasta",
    "peanuts": "cacahuate", "peppers": "pimientos", "pineapple": "piña",
    "pizza dough": "masa de pizza", "pork": "cerdo", "pork belly": "panceta de cerdo",
    "pumpkin": "calabaza", "rice": "arroz", "roast duck": "pato asado",
    "roast pork": "cerdo asado", "salad": "ensalada", "salad greens": "hojas de ensalada",
    "salmon": "salmón", "samosas": "samosas", "sauce": "salsa", "soup": "sopa",
    "soup base": "base de sopa", "soup broth": "caldo", "soy sauce": "salsa de soya",
    "spices": "especias", "spicy sauce": "salsa picante", "steak": "bistec",
    "sushi": "sushi", "tea": "té", "tofu": "tofu", "tomato": "jitomate",
    "tomato sauce": "salsa de tomate", "tomatoes": "jitomate",
    "vegetables": "verduras", "yogurt": "yogur",
}

NOMBRES_PLATILLOS = {
    "Fried Chicken": "Pollo frito",
    "Pho": "Pho vietnamita",
    "Pan-fried Dumplings": "Dumplings a la plancha",
    "Noodle Stir-Fry": "Fideos salteados",
    "Mixed Asian Dish": "Platillo asiático mixto",
    "Noodle Soup": "Sopa de fideos",
    "Spicy Crab": "Cangrejo picante",
    "Sandwiches": "Sándwiches",
    "Fried Chicken with Salad and Soup": "Pollo frito con ensalada y sopa",
    "Meatball in sauce": "Albóndigas en salsa",
    "Mixed Fried Chicken Dishes": "Combinado de pollo frito",
    "Stir-fried Meat Dish": "Carne salteada",
    "French Toast with Ice Cream": "Pan francés con helado",
    "Spaghetti with Beef Sauce": "Espagueti a la boloñesa",
    "Mixed Rice with Meat and Vegetables": "Arroz mixto con carne y verduras",
    "Mixed Meat Platter": "Parrillada mixta",
    "Hot Pot": "Hot pot",
    "Sandwich": "Sándwich",
    "Mixed Asian Salad": "Ensalada asiática",
    "Steamed Dumplings": "Dumplings al vapor",
    "Spicy Noodles": "Fideos picantes",
    "Steak with Noodles and Vegetables": "Bistec con fideos y verduras",
    "Mapo Tofu": "Mapo tofu",
    "Grilled Salmon": "Salmón a la parrilla",
    "Roast Meat Rice": "Arroz con carnes asadas",
    "Mixed Asian Dishes": "Surtido asiático",
    "Crawfish": "Cangrejos de río",
    "Grilled Salmon with Vegetables": "Salmón a la parrilla con verduras",
    "Pizza": "Pizza",
    "Stir-fried Noodles": "Fideos salteados con pollo",
    "Braised Pork Belly": "Panceta de cerdo estofada",
    "Dumpling": "Dumpling",
    "Cheeseburger": "Hamburguesa con queso",
    "Braised Pork": "Cerdo estofado",
    "Mixed Platter": "Plato combinado",
    "Assorted Asian Dishes": "Surtido asiático de pescado",
    "Spicy Cold Noodles": "Fideos fríos picantes",
    "Omelette Rice": "Arroz con omelette",
    "Braised Meat": "Carne estofada",
    "Sushi and Salad": "Sushi con ensalada",
    "Skewered Meat and Hot Pot": "Brochetas con hot pot",
    "Spicy Crawfish": "Cangrejos de río picantes",
    "Noodle Stir Fry": "Fideos salteados con champiñones",
    "Grilled Meat Skewers": "Brochetas de carne a la parrilla",
    "Roasted Duck": "Pato asado",
    "Ramen": "Ramen",
    "Noodle Soup with Egg": "Sopa de fideos con huevo",
    "Hawaiian Pizza": "Pizza hawaiana",
    "Stir-fried meat with vegetables and rice": "Carne salteada con verduras y arroz",
    "Steamed Meat Slices": "Láminas de carne al vapor",
}

# Grupos de restricción: palabras clave (en inglés, como vienen en el dataset).
GRUPOS_RESTRICCION = {
    "lacteos": {"nombre": "Lácteos", "claves": ["cheese", "cream", "butter", "yogurt", "milk", "ice cream"]},
    "gluten": {"nombre": "Gluten", "claves": ["bread", "bun", "noodles", "pasta", "dough", "breading",
                                              "dumpling", "soy sauce", "samosa", "fried dough sticks"]},
    "mariscos": {"nombre": "Mariscos", "claves": ["crab", "crawfish", "shrimp", "lobster", "clam", "oyster",
                                                  "mussel", "squid", "octopus"]},
    "pescado": {"nombre": "Pescado", "claves": ["fish", "salmon", "tuna", "sushi"]},
    "huevo": {"nombre": "Huevo", "claves": ["egg", "omelette"]},
    "frutos_secos": {"nombre": "Cacahuate y nueces", "claves": ["peanut", "almond", "walnut", "cashew"]},
    "soya": {"nombre": "Soya", "claves": ["soy", "tofu"]},
    "cerdo": {"nombre": "Cerdo", "claves": ["pork", "ham", "bacon", "ribs"]},
    "vegetariano": {"nombre": "Carne o pescado", "claves": [
        "meat", "beef", "chicken", "pork", "ham", "duck", "steak", "ribs", "patty", "fish", "salmon",
        "crab", "crawfish", "shrimp", "sushi", "wings"]},
    "picante": {"nombre": "Picante", "claves": ["chili", "spicy"]},
}


def traducir(ingrediente):
    return TRADUCCION.get(ingrediente, ingrediente)


def nombre_platillo(nombre):
    return NOMBRES_PLATILLOS.get(nombre, nombre)


def pertenece_a_grupo(ingrediente_en, grupo):
    """True si el ingrediente (en inglés) contiene alguna palabra clave del grupo."""
    for clave in GRUPOS_RESTRICCION[grupo]["claves"]:
        if re.search(rf"\b{re.escape(clave)}s?\b", ingrediente_en):
            return True
    return False
