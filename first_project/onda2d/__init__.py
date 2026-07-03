"""Simulación de la ecuación de onda 2D por métodos numéricos.

Arquitectura MULTICAPA (dependencias apuntan hacia adentro):

    presentation  →  application  →  domain  ←  solvers
    (UI mpl)         (facade)        (física     (métodos numéricos,
                                      pura)        Strategy + Registry)

    config.py = transversal (tema visual), sin capa.

Reglas: el dominio no importa a nadie; los solvers dependen solo del dominio;
la aplicación orquesta dominio+solvers; la presentación solo habla con la
fachada de aplicación. Agregar un método = un archivo en `solvers/`.
"""

__version__ = '0.2.0'
