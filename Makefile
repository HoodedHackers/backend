VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
BLACK = $(VENV_DIR)/bin/black
ISORT = $(VENV_DIR)/bin/isort
PYTEST = $(VENV_DIR)/bin/pytest
COVERAGE = $(VENV_DIR)/bin/coverage
DB_PATH = "sqlite:///./local.db"

all: help

venv: $(VENV_DIR)/bin/activate

$(VENV_DIR)/bin/activate: requirements.txt
	python3 -m venv $(VENV_DIR)
	$(PIP) install -r requirements.txt

install: venv
	$(PIP) install -r requirements.txt

cleardb:
	rm -rf *.db

createdb: venv
	PYTHONPATH=. $(PYTHON) ./scripts/createIntegrationDB.py --dbpath $(DB_PATH)

start: venv
	DB_URI=$(DB_PATH) $(PYTHON) -m uvicorn main:app --reload

format: venv
	$(BLACK) .
	$(ISORT) --skip $(VENV_DIR) .

test: venv
	$(PYTEST)

coverage: venv
	$(COVERAGE) run -m pytest
	$(COVERAGE) html
	$(COVERAGE) report -m

clean:
	rm -rf $(VENV_DIR)
	rm -rf *.db

help:
	@echo "Comandos disponibles:"
	@echo "  make install   - Instala las dependencias en el entorno virtual"
	@echo "  make start     - Inicia la aplicación usando FastAPI"
	@echo "  make format    - Formatea el código usando Black"
	@echo "  make clean     - Borra el entorno virtual y la base de datos"
	@echo "  make test      - Ejecuta las pruebas usando Pytest"
	@echo "  make coverage  - Ejecuta las pruebas y reporta estadisticas de covertura"
	@echo "  make help      - Muestra esta ayuda"
	@echo "  make cleardb   - Elimina la base de datos"
	@echo "  make createdb  - Crea la base de datos de integración"
	@echo "  make venv      - Crea el entorno virtual"
