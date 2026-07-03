"""Tests de la capa de SOLVERS (registry + método FDTD)."""

import numpy as np
import pytest

from onda2d.domain import Grid2D, WaveProblem
from onda2d.solvers import available, create_solver
from onda2d.solvers.fdtd import CFL_LIMIT_2D


def _amp(s):
    """Amplitud máxima del campo de un solver (para las aserciones)."""
    return float(np.max(np.abs(s.field())))


def _fdtd(courant=0.5, boundary='dirichlet', c=1.0, damping=0.0, n=81):
    grid = Grid2D(n, n, h=1.0)
    prob = WaveProblem(c=c, damping=damping, boundary=boundary)
    return create_solver('fdtd', prob, grid, courant=courant), grid


def test_registry_expone_metodos():
    for m in ('fdtd', 'rk4', 'euler'):
        assert m in available()


def test_create_solver_desconocido_falla():
    grid = Grid2D(10, 10)
    prob = WaveProblem()
    with pytest.raises(KeyError):
        create_solver('no_existe', prob, grid)


def test_courant_y_dt():
    s, _ = _fdtd(courant=0.5, c=2.0)
    assert s.dt == pytest.approx(0.5 * 1.0 / 2.0)
    assert s.courant == pytest.approx(0.5)
    assert s.is_stable


def test_reposo_se_mantiene():
    s, _ = _fdtd()
    s.step(50)
    assert _amp(s) == 0.0


def test_pulso_se_propaga():
    s, g = _fdtd()
    s.inject(g.gaussian(40, 40, 1.0, 3.0))
    s.step(30)
    assert np.abs(s.field()[40, 60]) > 1e-4


def test_estable_no_diverge():
    s, g = _fdtd(courant=0.5)
    s.inject(g.gaussian(40, 40, 1.0, 3.0))
    s.step(400)
    assert np.isfinite(_amp(s))
    assert _amp(s) < 5.0


def test_inestable_diverge():
    s, g = _fdtd(courant=0.95)
    assert not s.is_stable
    assert s.courant > CFL_LIMIT_2D
    s.inject(g.gaussian(40, 40, 1.0, 3.0))
    s.step(300)
    assert (not np.isfinite(_amp(s))) or _amp(s) > 1e3


def test_simetria_radial():
    s, g = _fdtd()
    s.inject(g.gaussian(40, 40, 1.0, 3.0))
    s.step(20)
    u = s.field()
    assert u[40, 30] == pytest.approx(u[40, 50], abs=1e-9)
    assert u[30, 40] == pytest.approx(u[50, 40], abs=1e-9)
    assert u[40, 30] == pytest.approx(u[30, 40], abs=1e-9)


def test_reset_limpia_estado():
    s, g = _fdtd()
    s.inject(g.gaussian(40, 40, 1.0, 3.0))
    s.step(10)
    s.reset()
    assert _amp(s) == 0.0
    assert s.n == 0 and s.t == 0.0


# ── métodos de líneas: rk4 y euler ───────────────────────────────────
def _mol(method, courant=0.5, boundary='dirichlet', c=1.0, damping=0.0, n=81):
    grid = Grid2D(n, n, h=1.0)
    prob = WaveProblem(c=c, damping=damping, boundary=boundary)
    return create_solver(method, prob, grid, courant=courant), grid


def test_rk4_propaga_y_es_estable():
    s, g = _mol('rk4', courant=0.5)
    assert s.is_stable
    s.inject(g.gaussian(40, 40, 1.0, 3.0))
    s.step(400)
    assert np.isfinite(_amp(s))
    assert _amp(s) < 5.0                 # acotado, no explota
    assert np.abs(s.field()[40, 60]) > 1e-4    # el frente viajó


def test_rk4_velocidad_inicial_casi_cero():
    s, g = _mol('rk4')
    s.inject(g.gaussian(40, 40, 1.0, 3.0))
    assert np.max(np.abs(s.velocity_field())) == 0.0   # gota desde el reposo


def test_euler_es_inestable_para_ondas():
    s, g = _mol('euler', courant=0.5)
    assert not s.is_stable                      # CFL_LIMIT = 0
    s.inject(g.gaussian(40, 40, 1.0, 3.0))
    s.step(300)
    assert (not np.isfinite(_amp(s))) or _amp(s) > 5.0   # crece/explota


def test_metodos_de_lineas_rechazan_mur():
    grid = Grid2D(40, 40)
    prob = WaveProblem(boundary='mur')
    with pytest.raises(ValueError):
        create_solver('rk4', prob, grid)
    with pytest.raises(ValueError):
        create_solver('euler', prob, grid)


def test_rk4_reset():
    s, g = _mol('rk4')
    s.inject(g.gaussian(40, 40, 1.0, 3.0))
    s.step(5)
    s.reset()
    assert _amp(s) == 0.0
    assert s.n == 0 and s.t == 0.0
