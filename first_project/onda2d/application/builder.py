"""Composición de la simulación (capa de APLICACIÓN).

Punto único donde se ensamblan objetos de dominio + método + fuentes a partir
de una configuración. Aísla a la presentación de los constructores del dominio:
la UI solo pide `build_simulation(cfg)` / `build_rain(cfg, grid)` y recibe la
fachada lista.

`cfg` se usa por *duck typing* (se leen sus atributos), de modo que la capa de
aplicación NO se acopla al formato concreto del config (settings/AppConfig).
"""

from __future__ import annotations

from onda2d.domain import Grid2D, WaveProblem
from onda2d.application.rain import RainMonteCarlo
from onda2d.application.simulation import Simulation


def build_simulation(cfg) -> Simulation:
    """Arma la simulación (malla + problema + método + gotas iniciales)."""
    grid = Grid2D(cfg.nx, cfg.ny, h=cfg.h)
    problem = WaveProblem(c=cfg.c, damping=cfg.damping, boundary=cfg.boundary)
    sim = Simulation(grid, problem, method=cfg.method, courant=cfg.courant)
    for p in cfg.initial_pulses:
        sim.add_pulse(int(p['x']), int(p['y']),
                      amp=float(p.get('amp', 1.0)),
                      width=float(p.get('width', 4.0)))
    return sim


def build_rain(cfg, grid) -> 'RainMonteCarlo | None':
    """Arma la lluvia Monte Carlo desde el config, o None si está apagada."""
    return RainMonteCarlo.from_config(grid, cfg.rain)
