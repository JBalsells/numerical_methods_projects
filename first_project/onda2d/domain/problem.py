"""Definición del PROBLEMA físico (DOMINIO puro).

Describe *qué* se resuelve: la ecuación de onda 2D y sus parámetros físicos.
NO sabe *cómo* se resuelve (eso es responsabilidad de un Solver).

    u_tt = c² (u_xx + u_yy) − 2·γ·u_t
"""

from __future__ import annotations

from dataclasses import dataclass

from onda2d.domain.boundary import Boundary


@dataclass
class WaveProblem:
    """Parámetros físicos de la ecuación de onda 2D. Mutable (los edita la UI)."""
    c: float = 1.0                       # velocidad de la onda
    damping: float = 0.0                 # γ, amortiguamiento lineal (0 = sin pérdidas)
    boundary: Boundary = Boundary.MUR    # condición de frontera deseada

    def __post_init__(self) -> None:
        # normaliza si llega como string ('mur') desde la UI
        self.boundary = Boundary(self.boundary)
