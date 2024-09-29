VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
BLACK = $(VENV_DIR)/bin/black
PYTEST = $(VENV_DIR)/bin/pytest
DB_PATH = "sqlite:///./local.db"

all: help

venv: $(VENV_DIR)/bin/activate

$(VENV_DIR)/bin/activate: requirements.txt
	python3 -m venv $(VENV_DIR)
	$(PIP) install -r requirements.txt

install: venv
	$(PIP) install -r requirements.txt

start: venv
	DB_URI=$(DB_PATH) $(PYTHON) -m uvicorn main:app --reload

format: venv
	$(BLACK) .

test: venv
	$(PYTEST)

clean:
	rm -rf $(VENV_DIR)
	rm -rf *.db

help:
	@echo "Comandos disponibles:"
	@echo "  make install  - Instala las dependencias en el entorno virtual"
	@echo "  make start    - Inicia la aplicación usando FastAPI"
	@echo "  make format   - Formatea el código usando Black"
	@echo "  make clean    - Borra el entorno virtual"
	@echo "  make test     - Ejecuta las pruebas usando Pytest"
	@echo "  make help     - Muestra esta ayuda"
