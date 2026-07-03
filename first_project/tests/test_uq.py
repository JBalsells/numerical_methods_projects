"""Tests de UQ Monte Carlo (application/uq.py)."""

import numpy as np

from onda2d.settings import AppConfig
from onda2d.application.uq import MonteCarloUQ, UQResult


def _study(**uq_over):
    uq = {'samples': 6, 'nx': 40, 'ny': 40, 'steps': 40,
          'c_std': 0.1, 'damping_std': 0.0, 'sensor': [0.75, 0.5],
          'pulse': [0.5, 0.5], 'seed': 0, 'workers': 1}
    uq.update(uq_over)
    cfg = AppConfig.from_dict({'problem': {'boundary': 'dirichlet'}, 'uq': uq})
    return MonteCarloUQ.from_config(cfg)


def test_run_devuelve_formas_correctas():
    res = _study().run()
    assert isinstance(res, UQResult)
    for arr in (res.c, res.damping, res.peak, res.arrival):
        assert arr.shape == (6,)
    assert np.all(res.peak >= 0)


def test_seed_reproducible():
    a = _study(seed=42).run()
    b = _study(seed=42).run()
    assert np.allclose(a.c, b.c)
    assert np.allclose(a.peak, b.peak)


def test_c_std_cero_no_varia_c():
    res = _study(c_std=0.0).run()
    assert np.allclose(res.c, res.c[0])     # todas iguales a la base


def test_summary_claves():
    s = _study().run().summary()
    for k in ('samples', 'peak_mean', 'peak_p50', 'arrived_frac'):
        assert k in s
    assert s['samples'] == 6
