"""Operadores diferenciales discretos (DOMINIO puro, reutilizables por solvers).

Separar el Laplaciano aquí evita que cada método lo reimplemente y permite,
más adelante, ofrecer variantes (5-pt vs 9-pt) sin tocar los solvers.
"""

from __future__ import annotations

import numpy as np


def laplacian_5point(u: np.ndarray, h: float) -> np.ndarray:
    """Laplaciano ∇²u por diferencias finitas centradas de 5 puntos.

    2º orden de precisión. El interior se calcula vectorizado; los bordes
    quedan en 0 (cada solver decide cómo tratarlos según su frontera).
    """
    lap = np.zeros_like(u)
    lap[1:-1, 1:-1] = (
        u[2:, 1:-1] + u[:-2, 1:-1] +
        u[1:-1, 2:] + u[1:-1, :-2] -
        4.0 * u[1:-1, 1:-1]
    ) / (h * h)
    return lap
