"""Capa de SOLVERS: métodos numéricos intercambiables (Strategy + Registry).

Importar los módulos de método concretos AQUÍ los auto-registra en el registry.
Para agregar un método nuevo: crear `onda2d/solvers/mi_metodo.py` con una clase
`@solver("mi_metodo")` y añadir su import a esta lista.
"""

from onda2d.solvers.base import Solver
from onda2d.solvers.registry import available, create_solver, solver

# --- métodos registrados (cada import ejecuta su @solver) ---
from onda2d.solvers import fdtd             # noqa: F401  (leapfrog explícito)
from onda2d.solvers import method_of_lines  # noqa: F401  (euler, rk4)

__all__ = ['Solver', 'solver', 'create_solver', 'available']
