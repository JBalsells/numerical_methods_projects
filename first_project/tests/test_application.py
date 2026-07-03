"""Tests de la capa de APLICACIÓN (fachada Simulation + diagnósticos)."""

import pytest

from onda2d.domain import Grid2D, WaveProblem
from onda2d.application import Simulation, build_simulation, build_rain
from onda2d.settings import AppConfig


def _sim(courant=0.5, boundary='neumann', damping=0.0):
    grid = Grid2D(80, 80, h=1.0)
    prob = WaveProblem(c=1.0, damping=damping, boundary=boundary)
    return Simulation(grid, prob, method='fdtd', courant=courant)


def test_facade_lee_parametros():
    grid = Grid2D(80, 80, h=1.0)
    prob = WaveProblem(c=2.0, damping=0.1, boundary='neumann')
    s = Simulation(grid, prob, method='fdtd', courant=0.6)
    assert s.c == 2.0                     # lee de problem
    assert s.damping == 0.1
    assert str(s.boundary) == 'neumann'
    assert s.courant == 0.6               # lee de solver
    assert s.method == 'fdtd'
    assert s.dt == pytest.approx(0.6 * 1.0 / 2.0)


def test_add_pulse_y_step():
    s = _sim()
    s.add_pulse(40, 40, amp=1.0, width=4.0)
    e0 = s.energy()
    assert e0 > 0
    s.step(20)
    assert s.n == 20


def test_energia_casi_conservada_sin_perdidas():
    s = _sim(boundary='neumann', damping=0.0)
    s.add_pulse(40, 40, amp=1.0, width=4.0)
    s.step(5)
    e0 = s.energy()
    s.step(200)
    assert s.energy() == pytest.approx(e0, rel=0.15)


def test_damping_reduce_energia():
    s = _sim(boundary='neumann', damping=0.1)
    s.add_pulse(40, 40, amp=1.0, width=4.0)
    s.step(5)
    e0 = s.energy()
    s.step(200)
    assert s.energy() < e0


def test_reset_limpia_estado():
    s = _sim()
    s.add_pulse(40, 40, 1.0, 4.0)
    s.step(10)
    s.reset()
    assert s.n == 0
    assert s.amplitude() == 0.0


def test_cfl_limit_expuesto():
    s = _sim()
    assert s.cfl_limit == pytest.approx(0.70710678, abs=1e-6)


# ── builder (composición en la capa de aplicación) ───────────────────
def test_build_simulation_desde_config():
    cfg = AppConfig.from_dict({
        'grid': {'nx': 60, 'ny': 50, 'h': 1.0},
        'problem': {'c': 1.5, 'boundary': 'neumann'},
        'solver': {'method': 'fdtd', 'courant': 0.4},
        'initial_pulses': [{'x': 30, 'y': 25, 'amp': 1.0, 'width': 3.0}],
    })
    sim = build_simulation(cfg)
    assert isinstance(sim, Simulation)
    assert sim.grid.nx == 60 and sim.grid.ny == 50
    assert sim.c == 1.5
    assert str(sim.boundary) == 'neumann'
    assert sim.courant == pytest.approx(0.4)
    assert sim.amplitude() > 0            # la gota inicial se inyectó


def test_build_rain_on_off():
    cfg_on = AppConfig.from_dict({'rain': {'enabled': True, 'rate': 2.0, 'seed': 0}})
    cfg_off = AppConfig.from_dict({'rain': {'enabled': False}})
    grid = Grid2D(40, 40)
    assert build_rain(cfg_on, grid) is not None
    assert build_rain(cfg_off, grid) is None
