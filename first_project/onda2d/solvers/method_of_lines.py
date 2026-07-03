"""Métodos de LÍNEAS (Method of Lines) para la ecuación de onda.

Idea: discretizar SOLO el espacio (Laplaciano de 5 puntos) y quedarse con un
sistema de ODEs de 1er orden en el tiempo, introduciendo la velocidad v = ∂u/∂t:

    du/dt = v
    dv/dt = c²·∇²u − 2γ·v

Ese sistema se integra con un integrador clásico (Euler, Runge–Kutta, …). Es la
vía natural para usar Runge–Kutta con la ecuación de onda (que es de 2º orden).

`MoLSolver` es la base (patrón TEMPLATE METHOD): define el estado (u, v), el lado
derecho `_rhs`, las fronteras y el bucle `step()`; cada método concreto solo
implementa `_advance()` (cómo dar UN paso). Comparten estado interno DISTINTO al
FDTD (que guarda 3 instantes), lo que valida que la interfaz `Solver` los hace
intercambiables aunque por dentro sean diferentes.
"""

from __future__ import annotations

from abc import abstractmethod

from onda2d.domain.boundary import Boundary
from onda2d.domain.operators import laplacian_5point
from onda2d.solvers.base import Solver
from onda2d.solvers.registry import solver


class MoLSolver(Solver):
    """Base de los métodos de líneas. Estado = (u desplazamiento, v velocidad)."""

    CFL_LIMIT = 1.0   # cada método concreto lo ajusta

    def __init__(self, problem, grid, *, courant: float = 0.5):
        super().__init__(problem, grid)
        if problem.boundary == Boundary.MUR:
            raise ValueError(
                "la frontera 'mur' (absorbente) solo la soporta el método 'fdtd'; "
                "con métodos de líneas (rk4/euler) usa 'dirichlet' o 'neumann'.")
        self._courant = float(courant)
        self.u = grid.zeros()
        self.v = grid.zeros()

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

    # ── sistema de ODEs y fronteras ──────────────────────────────────
    def _rhs(self, u, v):
        """(du/dt, dv/dt) = (v, c²∇²u − 2γv)."""
        c, g = self.problem.c, self.problem.damping
        return v, c * c * laplacian_5point(self._with_bc(u), self.grid.h) - 2.0 * g * v

    def _with_bc(self, u):
        """Copia de u con la frontera aplicada, para calcular bien el Laplaciano."""
        b = self.problem.boundary
        ub = u.copy()
        if b == Boundary.DIRICHLET:
            ub[0, :] = ub[-1, :] = 0.0
            ub[:, 0] = ub[:, -1] = 0.0
        elif b == Boundary.NEUMANN:
            ub[0, :] = ub[1, :]; ub[-1, :] = ub[-2, :]
            ub[:, 0] = ub[:, 1]; ub[:, -1] = ub[:, -2]
        return ub

    def _enforce_bc(self):
        """Fija la frontera del estado tras cada paso."""
        b = self.problem.boundary
        for a in (self.u, self.v):
            if b == Boundary.DIRICHLET:
                a[0, :] = a[-1, :] = 0.0
                a[:, 0] = a[:, -1] = 0.0
            elif b == Boundary.NEUMANN:
                a[0, :] = a[1, :]; a[-1, :] = a[-2, :]
                a[:, 0] = a[:, 1]; a[:, -1] = a[:, -2]

    @abstractmethod
    def _advance(self):
        """Avanza (u, v) UN paso de tiempo dt (lo define cada método)."""

    # ── interfaz Solver ──────────────────────────────────────────────
    def step(self, substeps: int = 1):
        for _ in range(substeps):
            self._advance()
            self._enforce_bc()
            self.n += 1
            self.t += self.dt

    def field(self):
        return self.u

    def velocity_field(self):
        return self.v

    def inject(self, bump):
        self.u = self.u + bump   # v sin cambio → gota soltada desde el reposo

    def reset(self):
        self.u.fill(0.0)
        self.v.fill(0.0)
        self.t = 0.0
        self.n = 0


@solver('euler')
class EulerSolver(MoLSolver):
    """Euler explícito (1er orden). Para ondas es INESTABLE (didáctico): su
    región de estabilidad no incluye el eje imaginario, así que la energía crece.
    Útil justamente para VER por qué no todo integrador sirve."""

    CFL_LIMIT = 0.0   # nunca estable para oscilaciones puras

    def _advance(self):
        dt = self.dt
        du, dv = self._rhs(self.u, self.v)
        self.u = self.u + dt * du
        self.v = self.v + dt * dv


@solver('rk4')
class RK4Solver(MoLSolver):
    """Runge–Kutta clásico de 4º orden. Preciso (4º orden en tiempo) y
    condicionalmente estable: admite Courant hasta ~1.0 en 2D."""

    CFL_LIMIT = 1.0

    def _advance(self):
        dt = self.dt
        u, v = self.u, self.v
        k1u, k1v = self._rhs(u, v)
        k2u, k2v = self._rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
        k3u, k3v = self._rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
        k4u, k4v = self._rhs(u + dt * k3u, v + dt * k3v)
        self.u = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
        self.v = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
