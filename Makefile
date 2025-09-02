# Makefile para CotizaBelleza Testing
# Funciona en Windows (con make instalado), Linux y macOS

.PHONY: test test-single verify coverage clean help

# Variables
PYTHON = python
DJANGO_SETTINGS = cotizabelleza.test_settings

# Comando principal para ejecutar todos los tests
test:
	@echo "🚀 Ejecutando todos los tests..."
	DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS) $(PYTHON) run_tests.py

# Ejecutar un test específico
test-single:
	@echo "🧪 Ejecutando test específico..."
	DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS) $(PYTHON) run_single_test.py

# Verificar configuración
verify:
	@echo "🔍 Verificando configuración..."
	$(PYTHON) verify_config.py

# Ejecutar tests con cobertura
coverage:
	@echo "📊 Ejecutando tests con cobertura..."
	DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS) $(PYTHON) -m pytest --nomigrations --cov=. --cov-report=html:htmlcov --cov-report=term-missing -v

# Limpiar archivos generados
clean:
	@echo "🧹 Limpiando archivos generados..."
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Mostrar ayuda
help:
	@echo "📋 Comandos disponibles:"
	@echo "  make test        - Ejecutar todos los tests"
	@echo "  make test-single - Ejecutar un test específico"
	@echo "  make verify      - Verificar configuración"
	@echo "  make coverage    - Ejecutar tests con cobertura"
	@echo "  make clean       - Limpiar archivos generados"
	@echo "  make help        - Mostrar esta ayuda"
