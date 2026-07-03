"""Diagnósticos escalares del campo (capa de APLICACIÓN, funciones puras)."""

from __future__ import annotations

import numpy as np


def amplitude(field: np.ndarray) -> float:
    """Máxima magnitud del campo."""
    return float(np.max(np.abs(field)))


def energy(field: np.ndarray, velocity: np.ndarray, h: float, c: float) -> float:
    """Energía total ≈ cinética + potencial (unidades arbitrarias).

    Cinética: ½·v²   ·   Potencial: ½·c²·|∇u|²   (integradas en el área h²).
    Útil para verificar conservación aproximada sin pérdidas ni absorbentes.
    """
    gx = np.gradient(field, h, axis=1)
    gy = np.gradient(field, h, axis=0)
    kinetic = 0.5 * np.sum(velocity ** 2)
    potential = 0.5 * c ** 2 * np.sum(gx ** 2 + gy ** 2)
    return float((kinetic + potential) * h ** 2)
