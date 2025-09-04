# Makefile para CotizaBelleza Testing
# Funciona en Windows (con make instalado), Linux y macOS

.PHONY: help test test-specific coverage clean install migrate superuser runserver

help:
	@echo "Comandos disponibles:"
	@echo "  make test          - Ejecutar todos los tests"
	@echo "  make test-specific - Ejecutar test específico (TEST=test_name)"
	@echo "  make coverage      - Ejecutar tests con cobertura"
	@echo "  make clean         - Limpiar archivos temporales"
	@echo "  make install       - Instalar dependencias"
	@echo "  make migrate       - Aplicar migraciones"
	@echo "  make superuser     - Crear superusuario"
	@echo "  make runserver     - Ejecutar servidor de desarrollo"

test:
	@echo "Ejecutando todos los tests..."
	pytest tests/ -v

test-specific:
	@echo "Ejecutando test específico..."
	pytest tests/ -k $(TEST) -v

coverage:
	@echo "Ejecutando tests con cobertura..."
	pytest --cov=core --cov-report=html:htmlcov --cov-report=term-missing tests/

clean:
	@echo "Limpiando archivos temporales..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf htmlcov/
	rm -rf .coverage

install:
	@echo "Instalando dependencias..."
	pip install -r requirements.txt

migrate:
	@echo "Aplicando migraciones..."
	python manage.py migrate

superuser:
	@echo "Creando superusuario..."
	python manage.py createsuperuser

runserver:
	@echo "Ejecutando servidor de desarrollo..."
	python manage.py runserver
