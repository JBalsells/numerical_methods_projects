"""Carga de configuración desde `config.yaml` (infraestructura / driver).

Traduce el archivo YAML a un `AppConfig` con valores validados. Es la única
puerta de entrada de configuración: la presentación construye la simulación a
partir de este objeto, sin leer el YAML directamente.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from onda2d.domain.boundary import Boundary

# raíz del proyecto = carpeta que contiene al paquete onda2d/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / 'config.yaml'

# valores por defecto (si el YAML falta o omite claves)
DEFAULTS = {
    'grid':       {'nx': 220, 'ny': 220, 'h': 1.0},
    'problem':    {'c': 1.0, 'damping': 0.0, 'boundary': 'mur'},
    'solver':     {'method': 'fdtd', 'courant': 0.5},
    'simulation': {'substeps': 3},
    'display':    {'mode': 'graphic', 'vmax': 1.0, 'interval_ms': 25},
    'initial_pulses': [{'x': 110, 'y': 110, 'amp': 1.0, 'width': 4.0}],
    # Lluvia Monte Carlo (proceso de Poisson de gotas sobre el agua)
    'rain': {
        'enabled': True,
        'rate': 3.0,           # gotas por unidad de tiempo simulado (esperado)
        'amp': [0.3, 1.0],     # rango de amplitud de cada gota
        'width': [2.0, 4.0],   # rango de ancho (radio gaussiano)
        'margin': 8,           # margen al borde (no cae pegada al muro)
        'seed': None,          # semilla (None = aleatoria cada corrida)
    },
    # Cuantificación de incertidumbre por Monte Carlo (mode: uq)
    'uq': {
        'samples': 120,        # nº de simulaciones
        'nx': 120, 'ny': 120,  # malla (propia de UQ, para que sea rápida)
        'steps': 300,          # pasos de tiempo por simulación
        'c_std': 0.1,          # incertidumbre relativa de c (Normal)
        'damping_std': 0.0,    # incertidumbre absoluta de γ (Normal)
        'sensor': [0.75, 0.5], # posición del sensor (fracción del dominio)
        'pulse': [0.5, 0.5],   # posición de la gota inicial (fracción)
        'seed': None,          # semilla (None = aleatoria)
        'workers': 4,          # procesos en paralelo (1 = serie)
    },
}


@dataclass
class AppConfig:
    # malla
    nx: int
    ny: int
    h: float
    # problema físico
    c: float
    damping: float
    boundary: Boundary
    # método numérico
    method: str
    courant: float
    # animación / display
    substeps: int
    mode: str            # 'graphic' (colores) | 'matrix' (números)
    vmax: float
    interval_ms: int
    # gotas iniciales
    initial_pulses: list = field(default_factory=list)
    # lluvia Monte Carlo
    rain: dict = field(default_factory=dict)
    # cuantificación de incertidumbre Monte Carlo
    uq: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> 'AppConfig':
        """Construye desde un dict (YAML ya parseado), completando defaults."""
        merged = _deep_merge(DEFAULTS, data or {})
        g, p, s, d = (merged['grid'], merged['problem'],
                      merged['solver'], merged['simulation'])
        disp = merged['display']
        return cls(
            nx=int(g['nx']), ny=int(g['ny']), h=float(g['h']),
            c=float(p['c']), damping=float(p['damping']),
            boundary=Boundary(p['boundary']),          # valida el string
            method=str(s['method']), courant=float(s['courant']),
            substeps=int(d['substeps']),
            mode=_valid_mode(disp['mode']),
            vmax=float(disp['vmax']), interval_ms=int(disp['interval_ms']),
            initial_pulses=list(merged.get('initial_pulses') or []),
            rain=dict(merged.get('rain') or {}),
            uq=dict(merged.get('uq') or {}),
        )


def load_config(path: str | Path | None = None) -> AppConfig:
    """Lee `config.yaml` (o `path`). Si no existe, usa solo defaults."""
    path = Path(path) if path else DEFAULT_CONFIG_PATH
    data = {}
    if path.exists():
        with open(path, 'r', encoding='utf-8') as fh:
            data = yaml.safe_load(fh) or {}
    else:
        print(f'[settings] {path} no encontrado — usando valores por defecto')
    return AppConfig.from_dict(data)


DISPLAY_MODES = ('graphic', 'matrix', 'uq')


def _valid_mode(mode) -> str:
    m = str(mode)
    if m not in DISPLAY_MODES:
        raise ValueError(f'display.mode debe ser uno de {DISPLAY_MODES}, no {m!r}')
    return m


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge recursivo: `override` pisa `base` clave por clave."""
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out
