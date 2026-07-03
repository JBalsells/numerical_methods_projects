"""Tests de la lluvia Monte Carlo (proceso de Poisson de gotas)."""

from onda2d.domain import Grid2D, WaveProblem
from onda2d.application import Simulation, RainMonteCarlo


def _grid():
    return Grid2D(100, 80, h=1.0)


def test_rate_cero_no_llueve():
    r = RainMonteCarlo(_grid(), rate=0.0, seed=1)
    sim = Simulation(_grid(), WaveProblem(), method='fdtd')
    assert r.rain_on(sim, 10.0) == 0
    assert r.total_drops == 0


def test_semilla_es_reproducible():
    g = _grid()
    r1 = RainMonteCarlo(g, rate=5.0, seed=42)
    r2 = RainMonteCarlo(g, rate=5.0, seed=42)
    seq1 = [r1.sample_drop() for _ in range(20)]
    seq2 = [r2.sample_drop() for _ in range(20)]
    assert seq1 == seq2


def test_semillas_distintas_difieren():
    g = _grid()
    a = [RainMonteCarlo(g, rate=5.0, seed=1).sample_drop() for _ in range(20)]
    b = [RainMonteCarlo(g, rate=5.0, seed=2).sample_drop() for _ in range(20)]
    assert a != b


def test_gotas_dentro_de_margen():
    g = _grid()
    r = RainMonteCarlo(g, rate=5.0, margin=8, seed=7)
    for _ in range(200):
        cx, cy, amp, width = r.sample_drop()
        assert 8 <= cx < g.nx - 8
        assert 8 <= cy < g.ny - 8
        assert 0.3 <= amp <= 1.0
        assert 2.0 <= width <= 4.0


def test_rain_on_inyecta_y_cuenta():
    g = _grid()
    r = RainMonteCarlo(g, rate=50.0, seed=3)
    sim = Simulation(g, WaveProblem(), method='fdtd')
    n = r.rain_on(sim, 1.0)
    assert n > 0
    assert r.total_drops == n
    assert sim.amplitude() > 0     # las gotas dejaron huella en el campo


def test_from_config_off_devuelve_none():
    assert RainMonteCarlo.from_config(_grid(), {'enabled': False}) is None
    assert RainMonteCarlo.from_config(_grid(), {}) is None


def test_from_config_on_construye():
    r = RainMonteCarlo.from_config(_grid(), {'enabled': True, 'rate': 2.0, 'seed': 0})
    assert isinstance(r, RainMonteCarlo)
    assert r.rate == 2.0
