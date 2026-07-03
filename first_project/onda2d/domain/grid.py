"""Malla espacial uniforme 2D. Concepto de DOMINIO: puro, sin UI ni método."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Grid2D:
    """Malla cartesiana uniforme dx = dy = h. Inmutable.

    Es la "malla de referencia" común: todos los solvers exponen su campo
    muestreado sobre esta malla, sin importar su representación interna.
    """
    nx: int
    ny: int
    h: float = 1.0

    @property
    def shape(self) -> tuple[int, int]:
        return (self.ny, self.nx)          # (filas=y, columnas=x)

    def zeros(self) -> np.ndarray:
        return np.zeros(self.shape, dtype=np.float64)

    def gaussian(self, cx: int, cy: int, amp: float = 1.0,
                 width: float = 4.0) -> np.ndarray:
        """Campo gaussiano centrado en (cx, cy) [índices de malla].

        Sirve como condición inicial / fuente ("gota"). Vive en la malla
        porque es una construcción puramente espacial.
        """
        yy, xx = np.ogrid[0:self.ny, 0:self.nx]
        return amp * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2)
                            / (2.0 * width ** 2))

    def in_bounds(self, cx: int, cy: int) -> bool:
        return 0 <= cx < self.nx and 0 <= cy < self.ny
