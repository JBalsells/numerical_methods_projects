"""Lluvia sobre el agua por MONTE CARLO (capa de APLICACIÓN).

Modela las gotas como un **proceso de Poisson**: en un intervalo de tiempo
simulado Δt caen N ~ Poisson(rate·Δt) gotas, cada una con posición uniforme
sobre la malla y amplitud/ancho uniformes en sus rangos. Es la parte estocástica
(Monte Carlo genera los eventos); el solver FDTD propaga las ondas resultantes.

No es un método numérico de la PDE (la ecuación de onda es hiperbólica y no
admite un solver Monte Carlo directo): es una FUENTE aleatoria que conduce la
simulación. Por eso vive en la capa de aplicación y actúa a través de la fachada
`Simulation.add_pulse`, sin tocar dominio ni solvers.
"""

from __future__ import annotations

import numpy as np

from onda2d.domain.grid import Grid2D


class RainMonteCarlo:
    """Generador Monte Carlo de gotas de lluvia (proceso de Poisson)."""

    def __init__(self, grid: Grid2D, *, rate: float = 3.0,
                 amp=(0.3, 1.0), width=(2.0, 4.0), margin: int = 8,
                 seed=None):
        self.grid = grid
        self.rate = float(rate)                 # gotas / unidad de tiempo (esperado)
        self.amp = (float(amp[0]), float(amp[1]))
        self.width = (float(width[0]), float(width[1]))
        self.margin = int(margin)
        self.rng = np.random.default_rng(seed)  # reproducible si seed fijo
        self.total_drops = 0

    @classmethod
    def from_config(cls, grid: Grid2D, rain_cfg: dict) -> 'RainMonteCarlo | None':
        """Crea la lluvia desde la sección `rain` del config, o None si off."""
        cfg = rain_cfg or {}
        if not cfg.get('enabled', False):
            return None
        return cls(grid,
                   rate=cfg.get('rate', 3.0),
                   amp=cfg.get('amp', (0.3, 1.0)),
                   width=cfg.get('width', (2.0, 4.0)),
                   margin=cfg.get('margin', 8),
                   seed=cfg.get('seed', None))

    def _num_drops(self, elapsed_time: float) -> int:
        """N ~ Poisson(rate · Δt)."""
        if self.rate <= 0.0 or elapsed_time <= 0.0:
            return 0
        return int(self.rng.poisson(self.rate * elapsed_time))

    def sample_drop(self) -> tuple[int, int, float, float]:
        """Una gota: (cx, cy, amp, width) muestreada al azar dentro del margen."""
        m = self.margin
        cx = int(self.rng.integers(m, self.grid.nx - m))
        cy = int(self.rng.integers(m, self.grid.ny - m))
        amp = float(self.rng.uniform(*self.amp))
        width = float(self.rng.uniform(*self.width))
        return cx, cy, amp, width

    def rain_on(self, sim, elapsed_time: float) -> int:
        """Inyecta en `sim` las gotas que caen en el intervalo. Devuelve cuántas."""
        n = self._num_drops(elapsed_time)
        for _ in range(n):
            cx, cy, amp, width = self.sample_drop()
            sim.add_pulse(cx, cy, amp=amp, width=width)
        self.total_drops += n
        return n
