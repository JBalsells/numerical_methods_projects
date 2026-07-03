"""FACADE de la simulación (capa de APLICACIÓN).

Cablea Grid + Problem + Solver y expone una API simple y de solo lectura para la
presentación (o scripts/tests). La UI habla SOLO con esta fachada: no conoce qué
método numérico hay detrás ni cómo guarda su estado. Los parámetros se fijan al
construir (desde config.yaml, vía el builder); no se mutan en caliente.
"""

from __future__ import annotations

from onda2d.application import diagnostics
from onda2d.solvers import create_solver


class Simulation:
    """Un problema físico resuelto por un método numérico elegido."""

    def __init__(self, grid, problem, method='fdtd', **solver_kwargs):
        self.grid = grid
        self.problem = problem
        self.solver = create_solver(method, problem, grid, **solver_kwargs)

    # ── lectura de parámetros (delegan a problem/solver) ─────────────
    @property
    def method(self):
        return self.solver.name

    @property
    def c(self):
        return self.problem.c

    @property
    def damping(self):
        return self.problem.damping

    @property
    def boundary(self):
        return self.problem.boundary

    @property
    def dt(self):
        return self.solver.dt

    @property
    def courant(self):
        return self.solver.courant

    @property
    def cfl_limit(self):
        return getattr(self.solver, 'CFL_LIMIT', None)

    @property
    def is_stable(self):
        return self.solver.is_stable

    @property
    def t(self):
        return self.solver.t

    @property
    def n(self):
        return self.solver.n

    # ── evolución / interacción ──────────────────────────────────────
    def step(self, substeps=1):
        self.solver.step(substeps)

    def add_pulse(self, cx, cy, amp=1.0, width=4.0):
        """Tira una gota gaussiana en (cx, cy) [índices de malla]."""
        self.solver.inject(self.grid.gaussian(cx, cy, amp, width))

    def reset(self):
        self.solver.reset()

    # ── lectura del estado ───────────────────────────────────────────
    def field(self):
        return self.solver.field()

    def amplitude(self):
        return diagnostics.amplitude(self.field())

    def energy(self):
        return diagnostics.energy(self.field(), self.solver.velocity_field(),
                                  self.grid.h, self.problem.c)
