"""Interfaz común de los métodos numéricos (patrón STRATEGY).

Un `Solver` es un método que avanza en el tiempo la solución de un `WaveProblem`
sobre una `Grid2D`. Cada método concreto (FDTD explícito, implícito, espectral,
FEM…) implementa esta interfaz y se registra como plugin.

Contrato mínimo pensado para que métodos con estado interno distinto (valores en
malla, coeficientes de Fourier, coeficientes nodales) sean intercambiables y
comparables: siempre exponen su campo muestreado sobre la malla de referencia.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from onda2d.domain.grid import Grid2D
from onda2d.domain.problem import WaveProblem


class Solver(ABC):
    """Estrategia numérica intercambiable. Mantiene su propio estado temporal."""

    name: str = 'base'          # lo fija el decorador @solver

    def __init__(self, problem: WaveProblem, grid: Grid2D):
        self.problem = problem
        self.grid = grid
        self.t = 0.0            # tiempo simulado acumulado
        self.n = 0              # número de pasos dados

    # ── parámetros del esquema ───────────────────────────────────────
    @property
    @abstractmethod
    def dt(self) -> float:
        """Paso temporal efectivo del método."""

    @property
    def courant(self):
        """Número de Courant C = c·dt/h, o None si no aplica al método."""
        return None

    @property
    def is_stable(self) -> bool:
        """¿El método es estable con los parámetros actuales?"""
        return True

    # ── evolución ────────────────────────────────────────────────────
    @abstractmethod
    def step(self, substeps: int = 1) -> None:
        """Avanza `substeps` pasos de tiempo."""

    @abstractmethod
    def field(self):
        """Campo u actual muestreado en la malla de referencia (np.ndarray)."""

    def velocity_field(self):
        """∂u/∂t aproximado (para diagnósticos). Por defecto 0 si el método
        no lo provee."""
        return self.grid.zeros()

    # ── fuentes / condiciones iniciales ──────────────────────────────
    @abstractmethod
    def inject(self, bump) -> None:
        """Suma un campo (p.ej. una gota gaussiana) al estado actual."""

    @abstractmethod
    def reset(self) -> None:
        """Vuelve al reposo (campo en cero, t=0, n=0)."""
