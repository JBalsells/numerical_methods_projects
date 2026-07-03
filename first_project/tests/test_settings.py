"""Tests del cargador de configuración (settings.py)."""

import pytest

from onda2d.domain import Boundary
from onda2d.settings import AppConfig, load_config, DEFAULT_CONFIG_PATH


def test_from_dict_vacio_usa_defaults():
    cfg = AppConfig.from_dict({})
    assert cfg.nx == 220 and cfg.ny == 220 and cfg.h == 1.0
    assert cfg.c == 1.0 and cfg.damping == 0.0
    assert cfg.boundary is Boundary.MUR
    assert cfg.method == 'fdtd' and cfg.courant == 0.5
    assert cfg.substeps == 3
    assert len(cfg.initial_pulses) >= 1


def test_from_dict_merge_parcial():
    cfg = AppConfig.from_dict({'problem': {'c': 2.5, 'boundary': 'dirichlet'}})
    assert cfg.c == 2.5                       # override
    assert cfg.boundary is Boundary.DIRICHLET
    assert cfg.damping == 0.0                 # default preservado
    assert cfg.courant == 0.5                 # otra sección intacta


def test_boundary_invalido_falla():
    with pytest.raises(ValueError):
        AppConfig.from_dict({'problem': {'boundary': 'no_existe'}})


def test_mode_default_y_valido():
    assert AppConfig.from_dict({}).mode == 'graphic'
    assert AppConfig.from_dict({'display': {'mode': 'matrix'}}).mode == 'matrix'


def test_mode_invalido_falla():
    with pytest.raises(ValueError):
        AppConfig.from_dict({'display': {'mode': 'no_existe'}})


def test_config_yaml_del_proyecto_carga():
    """El config.yaml versionado en el proyecto debe parsear bien."""
    assert DEFAULT_CONFIG_PATH.exists()
    cfg = load_config()
    assert isinstance(cfg, AppConfig)
    assert cfg.boundary in tuple(Boundary)
    assert cfg.substeps >= 1
