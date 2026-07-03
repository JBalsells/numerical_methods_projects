"""App de presentación. `display.mode` en config.yaml elige la salida:

  · 'graphic' → VENTANA matplotlib con el campo a colores (la simulación) y los
                valores en vivo en la consola.
  · 'matrix'  → imprime la MATRIZ de números completa en la TERMINAL (sin ventana).
  · 'uq'      → estudio Monte Carlo de incertidumbre: histogramas de la QoI.

Sin sliders ni botones: todo se parametriza en config.yaml. Esta capa solo habla
con la fachada de aplicación / builder.
"""

import sys
import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Tema "agua" (no usa la paleta fósforo).
from onda2d.config import (WATER_COLORS as COLORS, WATER_CMAP as WAVE_CMAP,
                           WATER_BG, apply_mpl_style)
from onda2d.application import build_simulation, build_rain
from onda2d.settings import load_config


def _advance(sim, rain, cfg):
    if rain is not None:
        rain.rain_on(sim, cfg.substeps * sim.dt)   # gotas del intervalo (Poisson)
    sim.step(cfg.substeps)


# códigos ANSI para colorear el estado en la terminal
_GREEN, _RED, _RESET = '\033[92m', '\033[91m', '\033[0m'


def _print_stats(cfg, sim, rain):
    """Imprime en la terminal los mismos valores del antiguo panel lateral,
    refrescándose en su lugar (limpia pantalla con ANSI)."""
    amp = sim.amplitude()
    diverged = (not np.isfinite(amp)) or amp > 1e3
    if diverged:
        status, col = 'DIVERGIÓ ✗', _RED
    elif sim.is_stable:
        status, col = 'ESTABLE ✓', _GREEN
    else:
        status, col = 'INESTABLE ✗', _RED

    courant, cfl = sim.courant, sim.cfl_limit
    cline = (f'Courant   {courant:.3f}\n' if courant is not None else '')
    limline = (f'límite    {cfl:.4f}\n' if cfl is not None else '')
    rainline = (f'lluvia    {rain.rate:.1f}/t · {rain.total_drops} gotas\n'
                if rain is not None else 'lluvia    off\n')

    txt = (
        f'MÉTODO    {sim.method}\n'
        f'malla     {cfg.nx}×{cfg.ny}   h = {cfg.h:.2f}\n'
        f'c         {sim.c:.2f}\n'
        f'γ         {sim.damping:.3f}\n'
        f'dt        {sim.dt:.4f}\n'
        f'{cline}{limline}'
        f'borde     {sim.boundary}\n'
        f'substeps  {cfg.substeps}\n'
        f'{rainline}'
        f'paso n    {sim.n}\n'
        f't         {sim.t:.2f}\n'
        f'amp máx   {amp:.3f}\n'
        f'energía   {sim.energy():.2e}\n'
        f'estado    {col}{status}{_RESET}\n'
    )
    sys.stdout.write('\033[H\033[J' + txt)
    sys.stdout.flush()


# ─────────────────────────────────────────────────────────────────────
# Modo GRÁFICO: ventana con el campo a colores
# ─────────────────────────────────────────────────────────────────────
def run_graphic(cfg, sim, rain):
    apply_mpl_style()
    fig = plt.figure(figsize=(9.0, 9.0))
    fig.set_facecolor(WATER_BG)
    fig.canvas.manager.set_window_title('Ecuación de onda 2D — simulación')

    ax = fig.add_axes([0.05, 0.05, 0.90, 0.88])
    ax.set_facecolor(WATER_BG)
    ax.set_title('Ecuación de onda 2D  ·  u_tt = c² ∇²u',
                 color=COLORS['primary'], fontsize=13, fontweight='bold', pad=10)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(COLORS['grid'])
    img = ax.imshow(sim.field(), cmap=WAVE_CMAP, vmin=-cfg.vmax, vmax=cfg.vmax,
                    origin='lower', interpolation='bilinear', animated=True)

    # click en el campo = gota
    def on_click(event):
        if event.inaxes is ax and event.xdata is not None:
            cx, cy = int(round(event.xdata)), int(round(event.ydata))
            if sim.grid.in_bounds(cx, cy):
                sim.add_pulse(cx, cy, amp=1.0, width=4.0)
    fig.canvas.mpl_connect('button_press_event', on_click)

    def update(_frame):
        _advance(sim, rain, cfg)
        img.set_data(sim.field())
        _print_stats(cfg, sim, rain)   # valores en la consola, a la par de la ventana
        return (img,)

    anim = FuncAnimation(fig, update, interval=cfg.interval_ms, blit=False,
                         cache_frame_data=False)
    fig._anim = anim
    print('Modo gráfico. Ventana = simulación · consola = valores. Click en el campo = gota.')
    plt.show()


# ─────────────────────────────────────────────────────────────────────
# Modo MATRIZ: imprime todos los números del campo en la TERMINAL
# ─────────────────────────────────────────────────────────────────────
def run_matrix(cfg, sim, rain):
    refresh = max(cfg.interval_ms, 100) / 1000.0   # no más rápido que ~10 fps
    if cfg.nx * cfg.ny > 4000:
        print(f'[matriz] malla {cfg.nx}×{cfg.ny} es grande: la matriz no cabrá '
              f'legible en la terminal.\n'
              f'         Baja grid.nx/ny en config.yaml (recomendado ≤ ~40×40).\n')
    print(f'Modo matriz en terminal — malla {cfg.nx}×{cfg.ny}. Ctrl+C para salir.\n')
    time.sleep(1.0)

    try:
        while True:
            _advance(sim, rain, cfg)
            f = sim.field()
            body = np.array2string(
                f, precision=2, suppress_small=True, sign='+',
                floatmode='fixed', threshold=f.size, max_line_width=100000)
            header = (f'onda 2D · matriz {cfg.nx}×{cfg.ny} · '
                      f'paso n={sim.n} · t={sim.t:.2f}'
                      + (f' · gotas={rain.total_drops}' if rain is not None else ''))
            sys.stdout.write('\033[H\033[J')   # cursor arriba + limpiar pantalla
            sys.stdout.write(header + '\n' + body + '\n')
            sys.stdout.flush()
            time.sleep(refresh)
    except KeyboardInterrupt:
        print('\n(fin)')


# ─────────────────────────────────────────────────────────────────────
# Modo UQ: Monte Carlo de incertidumbre (histogramas de la QoI)
# ─────────────────────────────────────────────────────────────────────
def run_uq(cfg):
    from onda2d.application.uq import MonteCarloUQ
    study = MonteCarloUQ.from_config(cfg)
    print(f'UQ Monte Carlo: {study.samples} simulaciones '
          f'(malla {study.nx}×{study.ny}, {study.workers} procesos). Espera…')

    def progress(i, n):
        if i % max(1, n // 20) == 0 or i == n:
            sys.stdout.write(f'\r  {i}/{n}'); sys.stdout.flush()
    res = study.run(progress=progress)
    print()

    s = res.summary()
    print(f"c ~ Normal(media={cfg.c:.2f}, σ={study.c_std*100:.0f}%)  ·  "
          f"γ base={cfg.damping:.3f}\n"
          f"amplitud pico en el sensor: media={s['peak_mean']:.3f} "
          f"σ={s['peak_std']:.3f}  p05={s['peak_p05']:.3f} "
          f"p50={s['peak_p50']:.3f} p95={s['peak_p95']:.3f}\n"
          f"tiempo de llegada: media={s['arrival_mean']:.2f} "
          f"σ={s['arrival_std']:.2f}  (llegó en {s['arrived_frac']*100:.0f}% de las corridas)")

    apply_mpl_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.set_facecolor(WATER_BG)
    fig.canvas.manager.set_window_title('Ecuación de onda 2D — UQ Monte Carlo')
    fig.suptitle(f'Incertidumbre (Monte Carlo, {s["samples"]} corridas) · '
                 f'c incierta ±{study.c_std*100:.0f}%',
                 color=COLORS['primary'], fontweight='bold')
    for ax, data, title in ((ax1, res.peak, 'amplitud pico en el sensor'),
                            (ax2, res.arrival[~np.isnan(res.arrival)], 'tiempo de llegada')):
        ax.set_facecolor(WATER_BG)
        ax.hist(data, bins=24, color=COLORS['primary'], alpha=0.55,
                edgecolor=COLORS['accent'])
        ax.set_title(title, color=COLORS['text'])
        ax.tick_params(colors=COLORS['text'])
        for sp in ax.spines.values():
            sp.set_color(COLORS['grid'])
    plt.show()


def main():
    cfg = load_config()
    if cfg.mode == 'uq':
        run_uq(cfg)
        return
    sim = build_simulation(cfg)
    rain = build_rain(cfg, sim.grid)
    if cfg.mode == 'matrix':
        run_matrix(cfg, sim, rain)
    else:
        run_graphic(cfg, sim, rain)


if __name__ == '__main__':
    main()
