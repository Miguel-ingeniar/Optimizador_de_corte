# -*- coding: utf-8 -*-
"""
Optimizador de cortes de tablero (nesting por estantes)

Problema: dada una lista de piezas de mobiliario (laterales, puertas,
repisas...) y el tamaño de un tablero, acomodar las piezas para usar la
menor cantidad de tableros posible y dibujar el plano de corte.

Estrategia ("estantes" o shelf packing):
  1. Se ordenan las piezas de la más alta a la más baja.
  2. Cada tablero se divide en franjas horizontales (estantes).
  3. Cada pieza se coloca en el primer estante donde quepa; si no cabe en
     ninguno, se abre un estante nuevo; si el tablero está lleno, se abre
     un tablero nuevo.
  Se descuentan 5 mm de refilado en cada borde del tablero y 5 mm de
  desgaste de sierra entre piezas contiguas.
"""

import matplotlib
matplotlib.use("Agg")          # permite guardar la imagen sin abrir ventana
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ---------------------------------------------------------------- constantes
ANCHO_TABLERO = 244.0   # cm (2,44 m)
ALTO_TABLERO = 122.0    # cm (1,22 m)
GROSOR_SIERRA = 0.5     # cm (5 mm) que desgasta la sierra en cada línea de corte
REFILADO = 0.5          # cm (5 mm) que se recortan en cada borde del tablero

# Zona realmente utilizable una vez refilados los cuatro bordes
ANCHO_UTIL = ANCHO_TABLERO - 2 * REFILADO
ALTO_UTIL = ALTO_TABLERO - 2 * REFILADO


# ------------------------------------------------------------------- entrada
def leer_numero(mensaje, minimo, maximo):
    """Pide un número y repite la pregunta (while) hasta que sea válido."""
    while True:
        texto = input(mensaje).strip().replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            print("  -> Escriba un número, por ejemplo 45.5")
            continue
        if valor < minimo or valor > maximo:
            print(f"  -> El valor debe estar entre {minimo} y {maximo}")
        else:
            return valor


def pedir_piezas():
    """Pide las piezas al usuario hasta que escriba 'fin' como nombre."""
    piezas = []
    print("\nIngrese las piezas (medidas en cm). Escriba 'fin' para terminar.")
    while True:
        nombre = input("Nombre de la pieza: ").strip()
        if nombre.lower() == "fin":
            if len(piezas) == 0:
                print("  -> Debe ingresar al menos una pieza.")
                continue
            break
        if nombre == "":
            print("  -> El nombre no puede estar vacío.")
            continue
        ancho = leer_numero("  Ancho (cm): ", 1, max(ANCHO_UTIL, ALTO_UTIL))
        alto = leer_numero("  Alto  (cm): ", 1, max(ANCHO_UTIL, ALTO_UTIL))
        cantidad = int(leer_numero("  Cantidad  : ", 1, 100))
        piezas.append((nombre, ancho, alto, cantidad))
    return piezas


def piezas_ejemplo():
    """Lista de un mueble de cocina para probar rápido el programa."""
    return [
        ("Lateral",        60.0, 100.0, 4),
        ("Puerta",         45.0,  70.0, 4),
        ("Repisa",         80.0,  35.0, 6),
        ("Fondo",         120.0,  60.0, 2),
        ("Frente cajon",   80.0,  20.0, 3),
    ]


# ------------------------------------------------------------------ lógica
def expandir_piezas(lista):
    """Convierte (nombre, ancho, alto, cantidad) en una pieza por unidad."""
    unidades = []
    for nombre, ancho, alto, cantidad in lista:
        for n in range(1, cantidad + 1):          # ciclo for por cantidad
            unidades.append({"nombre": f"{nombre} {n}", "w": ancho, "h": alto})
    return unidades


def orientar(pieza):
    """Deja la pieza 'acostada' (ancho >= alto) para formar filas largas."""
    if pieza["w"] < pieza["h"]:
        pieza["w"], pieza["h"] = pieza["h"], pieza["w"]
        pieza["rotada"] = True
    else:
        pieza["rotada"] = False


def nuevo_tablero():
    return {"estantes": [], "y_usado": 0.0, "piezas": []}


def intentar_colocar(tablero, pieza):
    """
    Intenta ubicar la pieza en el tablero. Devuelve True si la colocó.
    Prueba primero la orientación actual y luego la pieza girada 90 grados.
    """
    for girada in (False, True):
        w = pieza["h"] if girada else pieza["w"]
        h = pieza["w"] if girada else pieza["h"]

        # 1) ¿cabe en algún estante existente?
        for est in tablero["estantes"]:
            hay_ancho = est["x_usado"] + w <= ANCHO_UTIL
            cabe_alto = h <= est["alto"]
            if hay_ancho and cabe_alto:
                x, y = est["x_usado"], est["y"]
                est["x_usado"] += w + GROSOR_SIERRA
                # se suma REFILADO para medir desde el borde real del tablero
                tablero["piezas"].append(
                    {"nombre": pieza["nombre"], "x": REFILADO + x,
                     "y": REFILADO + y, "w": w, "h": h})
                return True

        # 2) ¿se puede abrir un estante nuevo?
        if tablero["y_usado"] + h <= ALTO_UTIL and w <= ANCHO_UTIL:
            y = tablero["y_usado"]
            tablero["estantes"].append(
                {"y": y, "alto": h, "x_usado": w + GROSOR_SIERRA})
            tablero["y_usado"] += h + GROSOR_SIERRA
            tablero["piezas"].append(
                {"nombre": pieza["nombre"], "x": REFILADO,
                 "y": REFILADO + y, "w": w, "h": h})
            return True

    return False       # no cupo ni girada: hay que usar otro tablero


def optimizar(unidades):
    """Recorre las piezas ordenadas y arma la lista de tableros."""
    for p in unidades:
        orientar(p)
    unidades.sort(key=lambda p: p["h"], reverse=True)

    tableros = [nuevo_tablero()]
    for pieza in unidades:
        colocada = False
        for tablero in tableros:                  # probar tableros abiertos
            if intentar_colocar(tablero, pieza):
                colocada = True
                break
        if not colocada:                          # abrir un tablero nuevo
            tablero = nuevo_tablero()
            if intentar_colocar(tablero, pieza):
                tableros.append(tablero)
            else:
                print(f"AVISO: '{pieza['nombre']}' no cabe en el tablero.")
    return tableros


# --------------------------------------------------------------- resultados
def mostrar_resumen(tableros):
    area_tablero = ANCHO_TABLERO * ALTO_TABLERO
    area_util_total = 0.0
    print("\n" + "=" * 52)
    print("RESULTADO DEL PLAN DE CORTE")
    print("=" * 52)
    for i, t in enumerate(tableros, start=1):
        area_util = sum(p["w"] * p["h"] for p in t["piezas"])
        area_util_total += area_util
        aprov = area_util / area_tablero * 100
        if aprov >= 85:
            nivel = "excelente"
        elif aprov >= 70:
            nivel = "bueno"
        elif aprov >= 50:
            nivel = "regular"
        else:
            nivel = "bajo (conviene usar un retazo)"
        print(f"Tablero {i}: {len(t['piezas'])} piezas | "
              f"aprovechamiento {aprov:5.1f}% -> {nivel}")
    total = area_tablero * len(tableros)
    print("-" * 52)
    print(f"Tableros necesarios : {len(tableros)}")
    print(f"Aprovechamiento     : {area_util_total / total * 100:.1f}%")
    print(f"Desperdicio         : {(total - area_util_total) / 10000:.2f} m2")


def dibujar_plano(tableros, archivo):
    """Dibuja cada tablero con sus piezas y guarda la imagen."""
    fig, ejes = plt.subplots(len(tableros), 1,
                             figsize=(10, 5.4 * len(tableros)), squeeze=False)
    for i, t in enumerate(tableros):
        ax = ejes[i][0]
        ax.add_patch(Rectangle((0, 0), ANCHO_TABLERO, ALTO_TABLERO,
                               fill=True, facecolor="#f2ead8",
                               edgecolor="black", linewidth=2))
        # línea punteada = borde después del refilado
        ax.add_patch(Rectangle((REFILADO, REFILADO), ANCHO_UTIL, ALTO_UTIL,
                               fill=False, edgecolor="red", linestyle="--",
                               linewidth=0.8))
        for p in t["piezas"]:
            ax.add_patch(Rectangle((p["x"], p["y"]), p["w"], p["h"],
                                   facecolor="#9fc5e8", edgecolor="#1c4587"))
            ax.text(p["x"] + p["w"] / 2, p["y"] + p["h"] / 2,
                    f"{p['nombre']}\n{p['w']:.0f} x {p['h']:.0f}",
                    ha="center", va="center", fontsize=7)
        ax.set_xlim(-5, ANCHO_TABLERO + 5)
        ax.set_ylim(-5, ALTO_TABLERO + 5)
        ax.set_aspect("equal")
        ax.set_title(f"Tablero {i + 1} ({ANCHO_TABLERO:.0f} x "
                     f"{ALTO_TABLERO:.0f} cm)")
        ax.set_xlabel("cm")
    fig.tight_layout()
    fig.savefig(archivo, dpi=130)
    plt.close(fig)
    print(f"Plano guardado en: {archivo}")


# ------------------------------------------------------------------ principal
def main():
    print("OPTIMIZADOR DE CORTES DE TABLERO")
    while True:                                    # menú principal
        print("\n1. Usar lista de ejemplo (mueble de cocina)")
        print("2. Ingresar mis propias piezas")
        print("3. Salir")
        opcion = input("Elija una opción: ").strip()

        if opcion == "1":
            lista = piezas_ejemplo()
        elif opcion == "2":
            lista = pedir_piezas()
        elif opcion == "3":
            print("Hasta pronto.")
            break
        else:
            print("  -> Opción no válida.")
            continue

        tableros = optimizar(expandir_piezas(lista))
        mostrar_resumen(tableros)
        dibujar_plano(tableros, "plano_de_corte.png")


if __name__ == "__main__":
    main()
