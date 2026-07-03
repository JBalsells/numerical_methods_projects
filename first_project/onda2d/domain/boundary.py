"""Condiciones de frontera (concepto de DOMINIO).

Aquí solo se declara *qué* frontera se quiere. El *cómo* aplicarla numérica-
mente vive en cada solver, porque el tratamiento depende del método (p.ej. la
absorbente de Mur usa c y dt, que son propios del esquema FDTD).
"""

from enum import Enum


class Boundary(str, Enum):
    DIRICHLET = 'dirichlet'   # borde fijo en 0 (pared rígida: refleja invirtiendo fase)
    NEUMANN = 'neumann'       # derivada normal 0 (extremo libre: refleja sin invertir)
    MUR = 'mur'               # absorbente 1er orden de Mur (la onda sale sin rebotar)

    def __str__(self) -> str:
        return self.value
