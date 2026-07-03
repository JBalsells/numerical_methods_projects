"""Tests de la capa de DOMINIO (malla, operadores, problema)."""

import numpy as np
import pytest

from onda2d.domain import Boundary, Grid2D, WaveProblem
from onda2d.domain.operators import laplacian_5point


def test_grid_shape_y_zeros():
    g = Grid2D(30, 20, h=0.5)
    assert g.shape == (20, 30)          # (ny, nx)
    assert g.zeros().shape == (20, 30)
    assert np.all(g.zeros() == 0)


def test_grid_gaussian_pico_en_centro():
    g = Grid2D(41, 41)
    bump = g.gaussian(20, 20, amp=2.0, width=3.0)
    assert bump[20, 20] == pytest.approx(2.0)
    assert bump.max() == pytest.approx(2.0)
    assert bump[0, 0] < 1e-6


def test_laplaciano_de_constante_es_cero():
    u = np.ones((10, 10)) * 3.7
    assert np.allclose(laplacian_5point(u, 1.0)[1:-1, 1:-1], 0.0)


def test_laplaciano_de_parabola():
    """∇²(x²+y²) = 4 en el interior."""
    n = 20
    xs = np.arange(n, dtype=float)
    xx, yy = np.meshgrid(xs, xs)
    u = xx ** 2 + yy ** 2
    lap = laplacian_5point(u, 1.0)
    assert np.allclose(lap[1:-1, 1:-1], 4.0)


def test_problem_normaliza_boundary_string():
    p = WaveProblem(boundary='mur')
    assert p.boundary is Boundary.MUR
