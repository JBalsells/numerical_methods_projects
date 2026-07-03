# Ecuación de onda 2D — métodos numéricos · arquitectura multicapa

Simulación interactiva de la ecuación de onda en **2 dimensiones espaciales**:

```
u_tt = c² (u_xx + u_yy) − 2γ u_t
```

Diseñada para **enchufar y comparar varios métodos numéricos**. El método #1 es
diferencias finitas explícitas, esquema *leapfrog* (**FDTD**): central en tiempo
(2º orden) + Laplaciano de 5 puntos, sobre malla uniforme `dx = dy = h`.

## Correr

```bash
cd ~/Desktop/ecuacion_de_onda_2d_espacial
make run       # crea venv si falta + corre la sim (según display.mode)
make test      # tests por capa (dominio + solvers + aplicación)
make list      # lista los métodos numéricos registrados
```

Documentación completa (teoría + arquitectura + patrones): abre `documentacion.html`.

## Arquitectura (multicapa · dependencias hacia adentro)

```
  presentation  ─►  application  ─►  domain  ◄─  solvers
    (UI mpl)         (facade)        (física     (métodos numéricos:
                                      pura)        Strategy + Registry)

  config.py   = transversal (tema visual), sin capa
  settings.py = carga config.yaml → AppConfig (infraestructura)
```

| Capa | Paquete | Responsabilidad | Depende de |
|------|---------|-----------------|-----------|
| **Dominio** | `onda2d/domain/` | Física pura: `Grid2D`, `WaveProblem`, `Boundary`, operadores (`laplacian_5point`). *Qué* se resuelve. | nada |
| **Solvers** | `onda2d/solvers/` | Métodos numéricos intercambiables. Interfaz `Solver` (Strategy) + `@solver` (Registry/Factory). *Cómo* se resuelve. `fdtd.py` = método #1. | dominio |
| **Aplicación** | `onda2d/application/` | Fachada `Simulation` + `diagnostics` + `rain` (lluvia Monte Carlo) + `builder` (compone la sim desde el config). | dominio, solvers |
| **Presentación** | `onda2d/presentation/` | UI matplotlib (`app.py`) + controles. Habla **solo** con la fachada/builder (no toca dominio). | aplicación |

**Reglas de dependencia:** el dominio no importa a nadie; los solvers dependen
solo del dominio; la aplicación orquesta; la presentación solo ve la fachada.

### Agregar un método numérico

1. Crear `onda2d/solvers/mi_metodo.py` con una clase `@solver("mi_metodo")` que
   implemente la interfaz `Solver` (`step`, `field`, `inject`, `reset`, `dt`).
2. Añadir su import en `onda2d/solvers/__init__.py`.

Aparece solo en `make list`, en el selector "Método" de la UI y disponible para
`Simulation(..., method="mi_metodo")`. Nada más se toca.

> Nota de diseño: cada método puede tener estado interno distinto (valores en
> malla, coeficientes de Fourier, nodales…). La interfaz común opera a nivel de
> "dame el campo muestreado en la malla de referencia" (`field()`), lo que
> permite intercambiarlos y compararlos aunque por dentro sean diferentes.

## Configuración (`config.yaml`)

La ventana gráfica **no tiene controles**: es visualización pura. Toda la
parametrización vive en `config.yaml` (en la raíz del proyecto). Editar y volver
a correr `make run`.

```yaml
grid:    { nx: 220, ny: 220, h: 1.0 }
problem: { c: 1.0, damping: 0.0, boundary: mur }   # mur | dirichlet | neumann
solver:  { method: fdtd, courant: 0.5 }            # courant estable ≤ 0.7071
simulation: { substeps: 3 }                        # pasos de tiempo por frame
display: { mode: graphic, vmax: 1.0, interval_ms: 25 }   # mode: graphic | matrix
initial_pulses:
  - {x: 110, y: 110, amp: 1.0, width: 4.0}
rain:                                              # lluvia Monte Carlo (Poisson)
  enabled: true
  rate: 0.8            # gotas por unidad de tiempo simulado (esperado)
  amp: [0.3, 0.9]      # rango de amplitud por gota
  width: [2.0, 4.0]    # rango de ancho (radio gaussiano)
  margin: 8
  seed: null           # semilla fija = lluvia reproducible; null = aleatoria
```

**Lluvia (Monte Carlo):** las gotas se generan como un proceso de Poisson
(N ~ Poisson(rate·Δt) por intervalo, posición/amplitud/ancho uniformes) y se
inyectan como pulsos en la simulación FDTD. Monte Carlo genera la *fuente*
aleatoria; el solver propaga las ondas. Con `damping > 0` las ondas se
desvanecen y la superficie llega a un régimen estable (agua real).

Si falta el archivo o alguna clave, se usan valores por defecto (ver
`onda2d/settings.py`). El cargador valida `boundary` contra los valores permitidos.

**`display.mode`** elige la salida:
- `graphic` — **ventana** matplotlib con el campo a colores (la simulación gráfica),
  y en la **consola** los valores en vivo (método, c, γ, dt, Courant, borde, lluvia,
  paso, t, amp, energía, estado). Funciona a cualquier tamaño de malla. Click = gota.
- `matrix` — imprime la **matriz completa de números** en la **terminal** (sin ventana),
  refrescándose en vivo (Ctrl+C para salir). Cabe cualquier tamaño, pero para que se lea
  conviene una malla chica (≤ ~40×40); con malla grande avisa y de todos modos imprime.

## Estabilidad — condición CFL

En 2D el FDTD explícito es estable solo si `C = c·dt/h ≤ 1/√2 ≈ 0.7071`. El paso
`dt` se **deriva** del Courant (`dt = C·h/c`), así el slider Courant controla la
estabilidad y sirve para *ver* qué pasa al violar CFL.
