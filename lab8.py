
import itertools
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from logic import And, Or, Not, Symbol, model_check


# 1. DEFINICIÓN DEL DOMINIO

COLORS      = ['azul', 'rojo', 'blanco', 'negro', 'verde', 'purpura']
NUM_COLORS  = len(COLORS)           # 6
NUM_SLOTS   = 4                     # fichas por combinación
ALL_COMBOS  = list(itertools.product(range(NUM_COLORS), repeat=NUM_SLOTS))
# |ALL_COMBOS| = 6^4 = 1296


# 2. FUNCIÓN DE EVALUACIÓN (ORACLE)

def score(secret: tuple, guess: tuple) -> tuple[int, int]:
    """
    Devuelve (fichas_posicion_correcta, fichas_color_correcto_posicion_incorrecta).
    Equivalente al feedback del juego Mastermind.
    """
    correct_pos   = sum(s == g for s, g in zip(secret, guess))
    correct_color = sum(min(secret.count(c), guess.count(c)) for c in range(NUM_COLORS))
    return correct_pos, correct_color - correct_pos



# 3. BASE DE CONOCIMIENTO Y FILTRADO

def filter_candidates(candidates: list, guess: tuple, feedback: tuple) -> list:
    """
    Actualiza el espacio de búsqueda conservando solo las combinaciones
    consistentes con el feedback observado.

    En términos de lógica proposicional, cada candidato descartado
    corresponde a agregar una cláusula NOT a la KB:
        ¬(pos0=c0 ∧ pos1=c1 ∧ pos2=c2 ∧ pos3=c3)
    para toda combinación inconsistente con el feedback.
    """
    return [c for c in candidates if score(c, guess) == feedback]



# 4. REPRESENTACIÓN EN LÓGICA PROPOSICIONAL

def build_symbols():
    """
    Crea símbolos proposicionales P_{pos}_{color}:
    P_i_c = "en la posición i hay el color c"
    """
    return {
        (pos, color): Symbol(f"P_{pos}_{COLORS[color]}")
        for pos in range(NUM_SLOTS)
        for color in range(NUM_COLORS)
    }

def build_initial_kb(symbols: dict) -> And:
    """
    Conocimiento base antes de cualquier propuesta:
    1. En cada posición DEBE haber exactamente un color.
       (al menos uno) OR(P_i_0, P_i_1, ..., P_i_5)  para cada i
    2. En cada posición NO pueden coexistir dos colores distintos.
       ¬(P_i_c ∧ P_i_c') = ¬P_i_c ∨ ¬P_i_c'       para c ≠ c'
    """
    clauses = []
    for pos in range(NUM_SLOTS):
        # Al menos un color por posición
        clauses.append(Or(*[symbols[(pos, c)] for c in range(NUM_COLORS)]))
        # A lo sumo un color por posición (exclusividad)
        for c1, c2 in itertools.combinations(range(NUM_COLORS), 2):
            clauses.append(Or(Not(symbols[(pos, c1)]), Not(symbols[(pos, c2)])))
    return And(*clauses)

def guess_to_model(guess: tuple, symbols: dict) -> dict:
    """Convierte una tupla de colores en un modelo proposicional."""
    model = {}
    for pos in range(NUM_SLOTS):
        for color in range(NUM_COLORS):
            model[f"P_{pos}_{COLORS[color]}"] = (guess[pos] == color)
    return model

def add_feedback_clause(kb: And, guess: tuple, feedback: tuple, symbols: dict):
    """
    Traduce el feedback a una cláusula proposicional y la agrega a la KB.

    Para cada candidato c* que es INCONSISTENTE con el feedback:
        ¬(P_0_guess[0] ∧ P_1_guess[1] ∧ ... ∧ P_3_guess[3])
    En la práctica, esto se implementa de forma eficiente con filter_candidates;
    la función aquí sirve para ilustrar la representación lógica formal.
    """
   



# 5. AGENTE SOLUCIONADOR

FIRST_GUESS = (0, 0, 1, 1)   # Propuesta inicial fija (óptima conocida)

def solve(secret: tuple) -> tuple[int, list[int]]:
    """
    Resuelve el juego para una combinación secreta dada.
    Retorna: (número_de_intentos, evolución_del_espacio_de_búsqueda)
    """
    candidates  = list(ALL_COMBOS)
    space_sizes = [len(candidates)]   # tamaño inicial: 1296
    guess       = FIRST_GUESS
    attempts    = 0

    while True:
        attempts += 1
        feedback   = score(secret, guess)

        # Actualizar espacio de búsqueda con el nuevo conocimiento
        candidates = filter_candidates(candidates, guess, feedback)
        space_sizes.append(len(candidates))

        # Si las 4 fichas están en posición correcta → solución encontrada
        if feedback[0] == NUM_SLOTS:
            break

        # Siguiente propuesta: primer candidato consistente
        guess = candidates[0]

    return attempts, space_sizes



# 6. SIMULACIÓN DE 1000 JUEGOS

def run_simulation(n: int = 1000, seed: int = 42) -> dict:
    """Ejecuta n juegos aleatorios y recopila estadísticas."""
    random.seed(seed)
    secrets     = [tuple(random.randint(0, NUM_COLORS - 1) for _ in range(NUM_SLOTS))
                   for _ in range(n)]

    all_attempts  = []
    all_histories = []

    for secret in secrets:
        att, hist = solve(secret)
        all_attempts.append(att)
        all_histories.append(hist)

    # Espacio de búsqueda promedio por intento
    max_len   = max(len(h) for h in all_histories)
    avg_space = []
    for i in range(max_len):
        vals = [h[i] for h in all_histories if i < len(h)]
        avg_space.append(sum(vals) / len(vals))

    return {
        "attempts"   : all_attempts,
        "histories"  : all_histories,
        "avg_space"  : avg_space,
        "avg_attempts": sum(all_attempts) / len(all_attempts),
        "max_attempts": max(all_attempts),
        "distribution": {i: all_attempts.count(i)
                         for i in range(1, max(all_attempts) + 1)},
    }



# 7. GRÁFICAS

def plot_results(stats: dict, output_path: str = "mastermind_results.png"):
    """Genera las dos gráficas solicitadas en el laboratorio."""

    avg_space    = stats["avg_space"]
    distribution = stats["distribution"]
    avg_attempts = stats["avg_attempts"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("white")

    BLUE   = "blue"
    RED    = "red"
    YELLOW = "yellow"
    BLACK  = "black"
    GRID   = "#d9d9d9"

    for ax in axes:
        ax.set_facecolor("white")
        ax.tick_params(colors=BLACK, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(BLACK)
        ax.yaxis.label.set_color(BLACK)
        ax.xaxis.label.set_color(BLACK)
        ax.title.set_color(BLACK)
        ax.grid(True, color=GRID, linewidth=0.6, linestyle="--")

    # ── Gráfica 1: Espacio de búsqueda promedio por intento ──
    ax1 = axes[0]
    x_vals = list(range(len(avg_space)))

    ax1.plot(
        x_vals,
        avg_space,
        color=BLUE,
        linewidth=2.5,
        marker="o",
        markersize=7,
        markerfacecolor=RED,
        markeredgecolor=BLACK,
        zorder=5
    )
    ax1.fill_between(x_vals, avg_space, alpha=0.2, color=YELLOW)

    for i, val in enumerate(avg_space):
        ax1.annotate(
            f"{val:.0f}",
            (i, val),
            textcoords="offset points",
            xytext=(0, 9),
            ha="center",
            fontsize=8,
            color=BLACK,
            fontweight="bold"
        )

    ax1.set_title("Espacio de búsqueda promedio por intento\n(1 000 juegos)", pad=12)
    ax1.set_xlabel("Número de intento")
    ax1.set_ylabel("Candidatos restantes (promedio)")
    ax1.set_xticks(x_vals)
    ax1.set_xticklabels([f"Intento {i}" for i in x_vals], rotation=35, ha="right")
    ax1.set_ylim(0, max(avg_space) * 1.15)

    # ── Gráfica 2: Distribución de intentos ──
    ax2 = axes[1]
    attempts = sorted(distribution.keys())
    counts = [distribution[a] for a in attempts]

    bars = ax2.bar(
        attempts,
        counts,
        color=BLUE,
        edgecolor=RED,
        linewidth=1.2,
        width=0.6,
        zorder=3
    )

    for bar, cnt in zip(bars, counts):
        if cnt > 0:
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 5,
                str(cnt),
                ha="center",
                va="bottom",
                fontsize=8,
                color=BLACK,
                fontweight="bold"
            )

    ax2.axvline(
        avg_attempts,
        color=RED,
        linewidth=2,
        linestyle="--",
        label=f"Promedio: {avg_attempts:.2f} intentos"
    )

    ax2.legend(facecolor="white", edgecolor=BLACK, fontsize=9)
    ax2.set_title(f"Distribución de intentos (n=1 000)\nPromedio: {avg_attempts:.2f}", pad=12)
    ax2.set_xlabel("Intentos para resolver")
    ax2.set_ylabel("Número de juegos")
    ax2.set_xticks(attempts)

    fig.suptitle(
        "Mastermind — Agente de Inferencia Lógica",
        fontsize=14,
        color=BLACK,
        y=1.01,
        fontweight="bold"
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[✓] Gráfica guardada en: {output_path}")


# MAIN

if __name__ == "__main__":
    print("Ejecutando simulación de 1 000 juegos de Mastermind...")
    stats = run_simulation(n=1000, seed=42)

    print(f"\nPromedio de intentos : {stats['avg_attempts']:.2f}")
    print(f"Máximo de intentos   : {stats['max_attempts']}")
    print(f"Distribución         : {stats['distribution']}")
    print(f"\nEspacio de búsqueda promedio por intento:")
    for i, s in enumerate(stats["avg_space"]):
        print(f"  Intento {i}: {s:.1f}")

    plot_results(stats, output_path="mastermind_results.png")

    