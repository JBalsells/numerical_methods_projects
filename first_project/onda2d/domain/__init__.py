"""Capa de DOMINIO: física pura (malla, problema, operadores, fronteras).

No depende de ninguna otra capa ni de matplotlib. Es el núcleo estable.
"""

from onda2d.domain.boundary import Boundary
from onda2d.domain.grid import Grid2D
from onda2d.domain.problem import WaveProblem

__all__ = ['Boundary', 'Grid2D', 'WaveProblem']
