"""Cuantificación de incertidumbre (UQ) por MONTE CARLO (capa de APLICACIÓN).

Corre N simulaciones con parámetros INCIERTOS (c, γ) muestreados de
distribuciones, y agrega estadísticas de una cantidad de interés (QoI) medida en
un sensor: la amplitud pico y el tiempo de llegada de la onda.

Reutiliza todo lo posible: `build_simulation` (una sim por muestra), la fachada
`Simulation`, y el mismo patrón de muestreo con semilla que la lluvia
(`np.random.default_rng`). Como cada corrida es independiente, se paraleliza con
`ProcessPoolExecutor` (multiprocessing real). No toca dominio ni solvers.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace

import numpy as np

from onda2d.application.builder import build_simulation

_ARRIVAL_THRESHOLD = 0.02   # |u| en el sensor que cuenta como "llegó la onda"


def _run_sample(task):
    """Una corrida Monte Carlo (top-level para que sea picklable por el pool)."""
    base_cfg, c, damping, sx, sy, steps, substeps = task
    cfg = replace(base_cfg, c=float(c), damping=float(max(damping, 0.0)))
    sim = build_simulation(cfg)
    peak = 0.0
    arrival = np.nan
    for _ in range(steps):
        sim.step(substeps)
        val = abs(float(sim.field()[sy, sx]))
        if val > peak:
            peak = val
        if np.isnan(arrival) and val > _ARRIVAL_THRESHOLD:
            arrival = sim.t
    return peak, arrival


@dataclass
class UQResult:
    c: np.ndarray            # velocidades muestreadas
    damping: np.ndarray      # amortiguamientos muestreados
    peak: np.ndarray         # QoI: amplitud pico en el sensor
    arrival: np.ndarray      # QoI: tiempo de llegada (nan si no llegó)

    def summary(self) -> dict:
        arrived = self.arrival[~np.isnan(self.arrival)]
        return {
            'samples': int(self.peak.size),
            'peak_mean': float(np.mean(self.peak)),
            'peak_std': float(np.std(self.peak)),
            'peak_p05': float(np.percentile(self.peak, 5)),
            'peak_p50': float(np.percentile(self.peak, 50)),
            'peak_p95': float(np.percentile(self.peak, 95)),
            'arrival_mean': float(np.mean(arrived)) if arrived.size else float('nan'),
            'arrival_std': float(np.std(arrived)) if arrived.size else float('nan'),
            'arrived_frac': float(arrived.size / self.peak.size),
        }


class MonteCarloUQ:
    """Estudio de incertidumbre: muestrea (c, γ) y agrega la QoI en un sensor."""

    def __init__(self, cfg, *, samples, nx, ny, steps, substeps,
                 c_std, damping_std, sensor, pulse, seed, workers):
        self.cfg = cfg
        self.samples = int(samples)
        self.nx, self.ny = int(nx), int(ny)
        self.steps, self.substeps = int(steps), int(substeps)
        self.c_std, self.damping_std = float(c_std), float(damping_std)
        self.sensor, self.pulse = tuple(sensor), tuple(pulse)
        self.seed = seed
        self.workers = int(workers)

    @classmethod
    def from_config(cls, cfg) -> 'MonteCarloUQ':
        u = cfg.uq
        return cls(cfg, samples=u['samples'], nx=u['nx'], ny=u['ny'],
                   steps=u['steps'], substeps=cfg.substeps,
                   c_std=u['c_std'], damping_std=u['damping_std'],
                   sensor=u['sensor'], pulse=u['pulse'],
                   seed=u['seed'], workers=u['workers'])

    def run(self, progress=None) -> UQResult:
        # muestreo reproducible (mismo patrón de semilla que la lluvia)
        rng = np.random.default_rng(self.seed)
        cs = self.cfg.c * (1.0 + self.c_std * rng.standard_normal(self.samples))
        cs = np.clip(cs, 1e-3, None)
        ds = np.clip(self.cfg.damping + self.damping_std * rng.standard_normal(self.samples),
                     0.0, None)

        # config base: malla propia de UQ + gota inicial fija + (lluvia irrelevante)
        px = int(self.pulse[0] * (self.nx - 1)); py = int(self.pulse[1] * (self.ny - 1))
        sx = int(self.sensor[0] * (self.nx - 1)); sy = int(self.sensor[1] * (self.ny - 1))
        base = replace(self.cfg, nx=self.nx, ny=self.ny,
                       initial_pulses=[{'x': px, 'y': py, 'amp': 1.0, 'width': 4.0}])
        tasks = [(base, cs[i], ds[i], sx, sy, self.steps, self.substeps)
                 for i in range(self.samples)]

        workers = min(max(self.workers, 1), os.cpu_count() or 1)
        results = []
        if workers > 1:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                for i, r in enumerate(ex.map(_run_sample, tasks), 1):
                    results.append(r)
                    if progress:
                        progress(i, self.samples)
        else:
            for i, t in enumerate(tasks, 1):
                results.append(_run_sample(t))
                if progress:
                    progress(i, self.samples)

        peaks = np.array([r[0] for r in results])
        arrivals = np.array([r[1] for r in results])
        return UQResult(cs, ds, peaks, arrivals)
