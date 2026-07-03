"""Registro + fábrica de solvers (patrones REGISTRY y FACTORY METHOD).

Cada método numérico se registra con `@solver("nombre")`. La UI / la capa de
aplicación crean solvers por nombre sin conocer la clase concreta → agregar un
método es soltar un archivo en `solvers/` con la clase decorada. Mismo patrón
`@simulation` del framework de rope-rescue.
"""

from __future__ import annotations

from typing import Type

from onda2d.domain.grid import Grid2D
from onda2d.domain.problem import WaveProblem
from onda2d.solvers.base import Solver

_REGISTRY: dict[str, Type[Solver]] = {}


def solver(name: str):
    """Decorador de clase: registra un Solver bajo `name`."""
    def deco(cls: Type[Solver]) -> Type[Solver]:
        if name in _REGISTRY:
            raise ValueError(f'solver duplicado: {name!r}')
        cls.name = name
        _REGISTRY[name] = cls
        return cls
    return deco


def create_solver(name: str, problem: WaveProblem, grid: Grid2D,
                  **kwargs) -> Solver:
    """Instancia el solver registrado bajo `name`."""
    if name not in _REGISTRY:
        raise KeyError(f'solver desconocido: {name!r}. '
                       f'Disponibles: {available()}')
    return _REGISTRY[name](problem, grid, **kwargs)


def available() -> list[str]:
    """Nombres de solvers registrados (orden alfabético)."""
    return sorted(_REGISTRY)
