"""Método numérico #1: diferencias finitas explícitas, esquema leapfrog (FDTD).

Central en tiempo (2º orden) + Laplaciano de 5 puntos (2º orden) sobre malla
uniforme. Recurrencia explícita con amortiguamiento tratado semi-implícito:

    u^{n+1} = [ 2u^n − (1 − γ dt) u^{n-1} + (c dt)² ∇²u^n ] / (1 + γ dt)

Estabilidad — condición CFL en 2D:  C = c·dt/h ≤ 1/√2 ≈ 0.7071.
El paso dt se DERIVA del número de Courant elegido (dt = C·h/c), de modo que el
Courant es el control directo de estabilidad (didáctico: cruzarlo = ver divergir).
"""

from __future__ import annotations

import math

from onda2d.domain.boundary import Boundary
from onda2d.domain.grid import Grid2D
from onda2d.domain.operators import laplacian_5point
from onda2d.domain.problem import WaveProblem
from onda2d.solvers.base import Solver
from onda2d.solvers.registry import solver

CFL_LIMIT_2D = 1.0 / math.sqrt(2.0)   # ≈ 0.7071


@solver('fdtd')
class FDTDSolver(Solver):
    """FDTD explícito leapfrog. Estado = 3 planos temporales en la malla."""

    CFL_LIMIT = CFL_LIMIT_2D

    def __init__(self, problem: WaveProblem, grid: Grid2D, *, courant: float = 0.5):
        super().__init__(problem, grid)
        self._courant = float(courant)
        self.u_prev = grid.zeros()
        self.u = grid.zeros()
        self.u_next = grid.zeros()

    # ── parámetros del esquema ───────────────────────────────────────
    @property
    def courant(self) -> float:
        return self._courant

    @courant.setter
    def courant(self, value: float) -> None:
        self._courant = float(value)

    @property
    def dt(self) -> float:
        return self._courant * self.grid.h / self.problem.c

    @property
    def is_stable(self) -> bool:
        return self._courant <= self.CFL_LIMIT

    # ── evolución ────────────────────────────────────────────────────
    def step(self, substeps: int = 1) -> None:
        for _ in range(substeps):
            self._one_step()

    def _one_step(self) -> None:
        c, dt, g, h = self.problem.c, self.dt, self.problem.damping, self.grid.h
        u, up = self.u, self.u_prev
        lap = laplacian_5point(u, h)

        un = self.u_next
        un[1:-1, 1:-1] = (
            2.0 * u[1:-1, 1:-1]
            - (1.0 - g * dt) * up[1:-1, 1:-1]
            + (c * dt) ** 2 * lap[1:-1, 1:-1]
        ) / (1.0 + g * dt)

        self._apply_boundary(un, u)

        # rotar buffers sin realocar: prev <- u <- next
        self.u_prev, self.u, self.u_next = self.u, self.u_next, self.u_prev
        self.n += 1
        self.t += dt

    def _apply_boundary(self, un, u) -> None:
        b = self.problem.boundary
        if b == Boundary.DIRICHLET:
            un[0, :] = un[-1, :] = 0.0
            un[:, 0] = un[:, -1] = 0.0
        elif b == Boundary.NEUMANN:
            un[0, :] = un[1, :]
            un[-1, :] = un[-2, :]
            un[:, 0] = un[:, 1]
            un[:, -1] = un[:, -2]
        elif b == Boundary.MUR:
            # Mur 1er orden por borde:
            #   u_new[edge] = u_old[in] + k (u_new[in] − u_old[edge])
            #   k = (c·dt − h)/(c·dt + h)
            cdt = self.problem.c * self.dt
            k = (cdt - self.grid.h) / (cdt + self.grid.h)
            un[0, :]  = u[1, :]  + k * (un[1, :]  - u[0, :])
            un[-1, :] = u[-2, :] + k * (un[-2, :] - u[-1, :])
            un[:, 0]  = u[:, 1]  + k * (un[:, 1]  - u[:, 0])
            un[:, -1] = u[:, -2] + k * (un[:, -2] - u[:, -1])

    # ── campo / diagnóstico ──────────────────────────────────────────
    def field(self):
        return self.u

    def velocity_field(self):
        return (self.u - self.u_prev) / self.dt

    # ── fuentes / reset ──────────────────────────────────────────────
    def inject(self, bump) -> None:
        # se agrega a u y a u_prev → velocidad inicial ≈ 0 (gota soltada
        # desde el reposo), evita un transitorio brusco.
        self.u += bump
        self.u_prev += bump

    def reset(self) -> None:
        self.u_prev.fill(0.0)
        self.u.fill(0.0)
        self.u_next.fill(0.0)
        self.t = 0.0
        self.n = 0
