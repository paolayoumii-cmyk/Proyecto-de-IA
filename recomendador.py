"""
PlateMatch - Motor de recomendación basado en contenido
=======================================================
Modelo de espacio vectorial + similitud de coseno (según el planteamiento):

1. Cada uno de los 50 platillos se convierte en un vector numérico con tres
   bloques: ingredientes (presencia), porción (chica/mediana/grande) y
   valores nutricionales normalizados.
2. Se descartan de inmediato los platillos con algún ingrediente prohibido
   (de la persona o de la mesa); esos ni se evalúan.
3. Con los sobrevivientes se calcula la similitud de coseno entre el perfil
   del comensal (favoritos, porción deseada, objetivo nutricional) y cada
   platillo -> porcentaje de compatibilidad.
4. Se suman puntos por ingredientes favoritos y se restan por ingredientes
   a evitar (tomando en cuenta la porción máxima si se indicó).
5. Se ordena la lista: mínimo 5 platillos por comensal individual y
   mínimo 10 para mesas grandes (más de 10 personas).
"""

import numpy as np

from ingredientes import GRUPOS_RESTRICCION, nombre_platillo, pertenece_a_grupo, traducir
from platematch import cargar_menu

LIMITE_MESA_INDIVIDUAL = 10   # hasta 10 personas: restricciones por comensal
MINIMO_INDIVIDUAL = 5
MINIMO_GRUPO_GRANDE = 10

# Peso de cada bloque del vector
PESO_INGREDIENTES = 1.0
PESO_PORCION = 0.6
PESO_NUTRICION = 0.6

# Ajustes de puntaje posteriores al coseno
BONO_FAVORITO = 0.10
BONO_FAVORITO_EXCEDE = 0.04      # el favorito viene en más cantidad de la deseada
CASTIGO_EVITAR = 0.20
CASTIGO_EVITAR_TOLERADO = 0.05   # viene en menos cantidad que la porción tolerada
CASTIGO_EVITAR_EXCEDE = 0.25

PORCIONES = ["chica", "mediana", "grande"]
OBJETIVOS = {
    "ninguno": "Sin preferencia",
    "alta_proteina": "Alto en proteína",
    "bajo_calorias": "Bajo en calorías",
    "bajo_carbohidratos": "Bajo en carbohidratos",
    "bajo_grasa": "Bajo en grasa",
}
# índice dentro del bloque nutricional: [proteína, 1-calorías, 1-carbohidratos, 1-grasa]
INDICE_OBJETIVO = {"alta_proteina": 0, "bajo_calorias": 1, "bajo_carbohidratos": 2, "bajo_grasa": 3}


class PlateMatch:
    def __init__(self, menu=None):
        self.menu = menu if menu is not None else cargar_menu()
        for p in self.menu:
            p["ingredientes_es"] = sorted({traducir(i) for i in p["ingredientes"]})
            p["nombre_es"] = nombre_platillo(p["nombre"])

        # Vocabulario canónico (en español; une plurales y sinónimos)
        self.vocabulario = sorted({i for p in self.menu for i in p["ingredientes_es"]})
        self.indice = {ing: k for k, ing in enumerate(self.vocabulario)}

        # Rangos de porción por terciles del propio menú
        totales = np.array([p["porcion_total_g"] or 0 for p in self.menu], dtype=float)
        validos = totales[totales > 0]
        self.umbral_chica, self.umbral_mediana = np.percentile(validos, [33.3, 66.6])
        for p in self.menu:
            p["porcion"] = self._categoria_porcion(p["porcion_total_g"])

        # Normalización min-max de los valores nutricionales
        nutr = np.array([[p["proteina_g"], p["calorias"], p["carbohidratos_g"], p["grasa_g"]]
                         for p in self.menu], dtype=float)
        minimo, maximo = nutr.min(axis=0), nutr.max(axis=0)
        self._nutr_norm = (nutr - minimo) / np.where(maximo > minimo, maximo - minimo, 1)

        self.matriz = np.vstack([self._vector_platillo(k) for k in range(len(self.menu))])

    # ------------------------------------------------------------ vectores
    def _categoria_porcion(self, gramos):
        if not gramos:
            return None
        if gramos <= self.umbral_chica:
            return "chica"
        return "mediana" if gramos <= self.umbral_mediana else "grande"

    def _vector_platillo(self, k):
        p = self.menu[k]
        v_ing = np.zeros(len(self.vocabulario))
        for ing in p["ingredientes_es"]:
            v_ing[self.indice[ing]] = 1.0

        # Porción "suave": la categoría vecina cuenta a medias
        v_por = np.zeros(3)
        if p["porcion"]:
            c = PORCIONES.index(p["porcion"])
            v_por[c] = 1.0
            for vecino in (c - 1, c + 1):
                if 0 <= vecino < 3:
                    v_por[vecino] = 0.4

        prot, cal, carb, grasa = self._nutr_norm[k]
        v_nut = np.array([prot, 1 - cal, 1 - carb, 1 - grasa])

        return np.concatenate([v_ing * PESO_INGREDIENTES, v_por * PESO_PORCION, v_nut * PESO_NUTRICION])

    def _vector_perfil(self, perfil):
        v_ing = np.zeros(len(self.vocabulario))
        for fav in perfil["favoritos"]:
            if fav["ingrediente"] in self.indice:
                v_ing[self.indice[fav["ingrediente"]]] = 1.0

        v_por = np.zeros(3)
        if perfil.get("porcion") in PORCIONES:
            v_por[PORCIONES.index(perfil["porcion"])] = 1.0

        v_nut = np.zeros(4)
        for objetivo in perfil.get("objetivos", []):
            if objetivo in INDICE_OBJETIVO:
                v_nut[INDICE_OBJETIVO[objetivo]] = 1.0

        return np.concatenate([v_ing * PESO_INGREDIENTES, v_por * PESO_PORCION, v_nut * PESO_NUTRICION])

    @staticmethod
    def similitud_coseno(a, b):
        norma = np.linalg.norm(a) * np.linalg.norm(b)
        return float(a @ b / norma) if norma else 0.0

    # ------------------------------------------------------------ reglas
    def _gramos_de(self, platillo, ingrediente_es):
        """Gramos del ingrediente en el platillo, si el dataset los indica."""
        for nombre_en, gramos in platillo["porciones_g"].items():
            if traducir(nombre_en) == ingrediente_es:
                return gramos
        return None

    def _motivo_descarte(self, platillo, perfil):
        prohibidos = set(perfil.get("prohibidos", []))
        for ing_en in platillo["ingredientes"]:
            if traducir(ing_en) in prohibidos:
                return f"Contiene {traducir(ing_en)} (prohibido)"
            for grupo in perfil.get("grupos", []):
                if grupo in GRUPOS_RESTRICCION and pertenece_a_grupo(ing_en, grupo):
                    return f"Contiene {traducir(ing_en)} ({GRUPOS_RESTRICCION[grupo]['nombre']})"
        return None

    def ficha(self, p):
        """Datos de un platillo listos para mostrarse en la interfaz."""
        return {
            "id": p["id"],
            "nombre": p["nombre_es"],
            "nombre_original": p["nombre"],
            "ingredientes": p["ingredientes_es"],
            "porcion": p["porcion"],
            "porcion_total_g": p["porcion_total_g"],
            "calorias": p["calorias"],
            "proteina_g": p["proteina_g"],
            "carbohidratos_g": p["carbohidratos_g"],
            "grasa_g": p["grasa_g"],
            "metodo": p.get("metodo", ""),
            "imagen": p["imagen"],
            "grupos": [g for g in GRUPOS_RESTRICCION
                       if any(pertenece_a_grupo(i, g) for i in p["ingredientes"])],
        }

    def platillos(self):
        return [self.ficha(p) for p in self.menu]

    # ------------------------------------------------------------ recomendación
    def recomendar(self, perfil, minimo=MINIMO_INDIVIDUAL):
        v_perfil = self._vector_perfil(perfil)
        recomendados, descartados = [], []

        for k, p in enumerate(self.menu):
            motivo = self._motivo_descarte(p, perfil)
            if motivo:
                descartados.append({"id": p["id"], "nombre": p["nombre_es"], "motivo": motivo})
                continue

            coseno = self.similitud_coseno(v_perfil, self.matriz[k])
            ajuste, favoritos, evitados = 0.0, [], []

            for fav in perfil["favoritos"]:
                if fav["ingrediente"] not in p["ingredientes_es"]:
                    continue
                gramos = self._gramos_de(p, fav["ingrediente"])
                excede = bool(fav.get("max_g") and gramos and gramos > fav["max_g"])
                ajuste += BONO_FAVORITO_EXCEDE if excede else BONO_FAVORITO
                favoritos.append({"ingrediente": fav["ingrediente"], "gramos": gramos, "excede": excede})

            for evi in perfil.get("evitar", []):
                if evi["ingrediente"] not in p["ingredientes_es"]:
                    continue
                gramos = self._gramos_de(p, evi["ingrediente"])
                tolerado = None
                if evi.get("max_g") and gramos is not None:
                    tolerado = gramos <= evi["max_g"]
                    ajuste -= CASTIGO_EVITAR_TOLERADO if tolerado else CASTIGO_EVITAR_EXCEDE
                else:
                    ajuste -= CASTIGO_EVITAR
                evitados.append({"ingrediente": evi["ingrediente"], "gramos": gramos, "tolerado": tolerado})

            puntaje = coseno + ajuste
            recomendados.append({
                **self.ficha(p),
                "coseno": round(coseno, 4),
                "ajuste": round(ajuste, 4),
                "puntaje": round(puntaje, 4),
                "compatibilidad": int(round(max(0.0, min(1.0, puntaje)) * 100)),
                "favoritos": favoritos,
                "evitados": evitados,
            })

        recomendados.sort(key=lambda r: r["puntaje"], reverse=True)
        return {
            "minimo": minimo,
            "evaluados": len(recomendados),
            "descartados": descartados,
            "recomendados": recomendados,
            "suficientes": len(recomendados) >= minimo,
        }

    def recomendar_mesa(self, tamano_mesa, comensales):
        """
        Mesa de 10 personas o menos: cada comensal recibe su propia lista (mín. 5).
        Mesa más grande: las restricciones se generalizan para toda la mesa (mín. 10)
        y un platillo solo sobrevive si nadie tiene prohibido alguno de sus ingredientes.
        """
        if tamano_mesa <= LIMITE_MESA_INDIVIDUAL:
            return {
                "generalizado": False,
                "resultados": [{"comensal": c.get("nombre") or f"Comensal {i + 1}",
                                **self.recomendar(c, MINIMO_INDIVIDUAL)}
                               for i, c in enumerate(comensales)],
            }
        perfil_mesa = combinar_perfiles(comensales)
        return {
            "generalizado": True,
            "resultados": [{"comensal": f"Mesa completa ({tamano_mesa} personas)",
                            **self.recomendar(perfil_mesa, MINIMO_GRUPO_GRANDE)}],
        }

    def catalogo(self):
        return {
            "platillos": len(self.menu),
            "ingredientes": self.vocabulario,
            "grupos": [{"id": k, "nombre": g["nombre"]} for k, g in GRUPOS_RESTRICCION.items()],
            "objetivos": [{"id": k, "nombre": v} for k, v in OBJETIVOS.items() if k != "ninguno"],
            "porciones": {
                "chica": f"hasta {self.umbral_chica:.0f} g",
                "mediana": f"{self.umbral_chica:.0f}–{self.umbral_mediana:.0f} g",
                "grande": f"más de {self.umbral_mediana:.0f} g",
            },
            "limite_mesa_individual": LIMITE_MESA_INDIVIDUAL,
        }


def _unir_por_ingrediente(listas, elegir):
    """Une listas de {ingrediente, max_g}; con porciones distintas se queda con elegir()."""
    unidos = {}
    for lista in listas:
        for item in lista:
            ing, max_g = item["ingrediente"], item.get("max_g")
            if ing not in unidos:
                unidos[ing] = max_g
            elif max_g and unidos[ing]:
                unidos[ing] = elegir(unidos[ing], max_g)
            else:
                unidos[ing] = None
    return [{"ingrediente": i, "max_g": g} for i, g in unidos.items()]


def combinar_perfiles(perfiles):
    """Generaliza varios perfiles en uno solo para mesas grandes."""
    if len(perfiles) == 1:
        return perfiles[0]
    porciones = [p.get("porcion") for p in perfiles if p.get("porcion") in PORCIONES]
    return {
        "favoritos": _unir_por_ingrediente([p["favoritos"] for p in perfiles], max),
        "evitar": _unir_por_ingrediente([p.get("evitar", []) for p in perfiles], min),
        "prohibidos": sorted({i for p in perfiles for i in p.get("prohibidos", [])}),
        "grupos": sorted({g for p in perfiles for g in p.get("grupos", [])}),
        "objetivos": sorted({o for p in perfiles for o in p.get("objetivos", [])}),
        "porcion": max(set(porciones), key=porciones.count) if porciones else None,
    }


if __name__ == "__main__":
    # Prueba rápida desde la terminal
    motor = PlateMatch()
    perfil = {
        "favoritos": [{"ingrediente": "pollo"}, {"ingrediente": "fideos"}],
        "evitar": [{"ingrediente": "cebolla"}],
        "prohibidos": ["cacahuate"],
        "grupos": ["mariscos"],
        "porcion": "mediana",
        "objetivos": ["alta_proteina"],
    }
    res = motor.recomendar(perfil)
    print(f"Evaluados: {res['evaluados']}  Descartados: {len(res['descartados'])}\n")
    for i, r in enumerate(res["recomendados"][:res["minimo"]], 1):
        print(f"#{i} {r['nombre']:<40} coseno={r['coseno']:.3f} ajuste={r['ajuste']:+.2f} -> {r['compatibilidad']}%")
