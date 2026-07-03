"""Configuración TRANSVERSAL (cross-cutting): tema visual "agua".

No pertenece a ninguna capa: la usan la presentación y las herramientas de
render. Fondo océano profundo; valle azul marino, reposo ≈ fondo, cresta espuma.
"""

from matplotlib.colors import LinearSegmentedColormap

WATER_BG = '#04121d'          # azul océano profundo (fondo)

WATER_COLORS = {
    'bg':      WATER_BG,
    'primary': '#7fe0ff',     # cian claro (títulos/acento)
    'text':    '#a9cfe0',     # azul-gris claro (texto)
    'accent':  '#6ff0c8',     # verde-agua = estable
    'danger':  '#ff6b6b',     # coral = inestable
    'grid':    '#123449',     # líneas sutiles
}

# Divergente tipo agua para amplitud CON signo:
# valle azul marino → reposo (≈fondo) → cresta cian → blanco espuma.
WATER_CMAP = LinearSegmentedColormap.from_list('water', [
    (0.00, '#012a4a'),   # valle profundo
    (0.50, '#06263a'),   # reposo (0) ≈ fondo
    (0.68, '#1f8fb5'),   # ladera
    (0.85, '#7fdff0'),   # cerca de cresta
    (1.00, '#eafcff'),   # cresta = espuma
])

MPL_STYLE = {
    'figure.facecolor':  WATER_BG,
    'axes.facecolor':    WATER_BG,
    'axes.edgecolor':    WATER_COLORS['grid'],
    'text.color':        WATER_COLORS['text'],
    'font.family':       'monospace',
    'axes.spines.top':   False,
    'axes.spines.right': False,
}


def apply_mpl_style() -> None:
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_STYLE)
    plt.rcParams['font.size'] = 11
