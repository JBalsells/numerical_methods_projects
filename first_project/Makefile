# Ecuación de onda 2D — arquitectura multicapa · venv autocontenido
PY := .venv/bin/python
PIP := .venv/bin/pip
SENTINEL := .venv/.installed

.PHONY: run test list clean

$(SENTINEL): requirements.txt
	python3 -m venv .venv
	$(PIP) install -q -r requirements.txt
	touch $(SENTINEL)

run: $(SENTINEL)          ## corre la simulación (display.mode en config.yaml)
	$(PY) main.py

test: $(SENTINEL)         ## corre los tests (dominio + solvers + aplicación)
	$(PY) -m pytest -q

list: $(SENTINEL)         ## lista los métodos numéricos registrados
	$(PY) -c "from onda2d.solvers import available; print('métodos:', available())"

clean:
	rm -rf .venv .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
