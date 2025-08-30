# Guía de Testing - CotizaBelleza

Este documento contiene las instrucciones para ejecutar las pruebas unitarias del proyecto CotizaBelleza, tanto para el backend (Django) como para el frontend (React).

## Estructura de Pruebas

### Backend (Django)
```
tests/
├── conftest.py              # Configuración global de pytest
├── test_models.py           # Pruebas de modelos
├── test_views.py            # Pruebas de vistas DRF
├── test_tasks.py            # Pruebas de tareas Celery
├── test_serializers.py      # Pruebas de serializers
└── test_business_logic.py   # Pruebas de lógica de negocio
```

### Frontend (React)
```
cotizabelleza-frontend/src/__tests__/
├── mocks/
│   ├── handlers.js          # Handlers de MSW para APIs
│   ├── server.js            # Servidor MSW para tests
│   └── browser.js           # Configuración MSW para navegador
├── components/
│   ├── ProductCard.test.jsx
│   └── SearchBar.test.jsx
├── pages/
│   └── Home.test.jsx
└── services/
    └── apiService.test.js
```

## Configuración

### Backend

1. **Instalar dependencias de testing:**
```bash
pip install -r requirements.txt
```

2. **Configuración de pytest:**
- `pytest.ini`: Configuración principal de pytest
- `.coveragerc`: Configuración de cobertura de código

3. **Variables de entorno para testing:**
```bash
export DJANGO_SETTINGS_MODULE=cotizabelleza.settings
export CELERY_TASK_ALWAYS_EAGER=True
export CELERY_TASK_EAGER_PROPAGATES=True
export EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend
```

### Frontend

1. **Instalar dependencias de testing:**
```bash
cd cotizabelleza-frontend
npm install
```

2. **Configuración de Jest:**
- `jest.config.js`: Configuración principal de Jest
- `src/setupTests.js`: Configuración global de tests

## Ejecutar Pruebas

### Backend

1. **Ejecutar todas las pruebas:**
```bash
pytest
```

2. **Ejecutar con cobertura:**
```bash
pytest --cov=. --cov-report=html:htmlcov --cov-report=term-missing
```

3. **Ejecutar pruebas específicas:**
```bash
# Pruebas de modelos
pytest tests/test_models.py

# Pruebas de vistas
pytest tests/test_views.py

# Pruebas de tareas
pytest tests/test_tasks.py

# Pruebas de serializers
pytest tests/test_serializers.py
```

4. **Ejecutar con marcadores:**
```bash
# Solo pruebas unitarias
pytest -m unit

# Solo pruebas de integración
pytest -m integration

# Excluir pruebas lentas
pytest -m "not slow"
```

5. **Ejecutar en paralelo:**
```bash
pytest -n auto
```

### Frontend

1. **Ejecutar todas las pruebas:**
```bash
cd cotizabelleza-frontend
npm test
```

2. **Ejecutar con cobertura:**
```bash
npm run test:coverage
```

3. **Ejecutar en modo watch:**
```bash
npm run test:watch
```

4. **Ejecutar pruebas específicas:**
```bash
# Pruebas de componentes
npm test -- --testPathPattern=components

# Pruebas de páginas
npm test -- --testPathPattern=pages

# Pruebas de servicios
npm test -- --testPathPattern=services
```

## Reportes de Cobertura

### Backend
- **Consola:** Se muestra al ejecutar `pytest --cov=.`
- **HTML:** Se genera en `htmlcov/index.html`
- **Objetivo:** ≥ 80% de cobertura total

### Frontend
- **Consola:** Se muestra al ejecutar `npm run test:coverage`
- **HTML:** Se genera en `coverage/lcov-report/index.html`
- **Objetivo:** ≥ 80% de cobertura total

## Tipos de Pruebas

### Backend

1. **Pruebas de Modelos (`test_models.py`)**
   - Métodos `__str__`
   - Managers personalizados
   - Validaciones de campos
   - Constraints de base de datos

2. **Pruebas de Vistas (`test_views.py`)**
   - Endpoints DRF (GET, POST, DELETE)
   - Casos de éxito y error
   - Validación de permisos
   - Paginación y filtros

3. **Pruebas de Tareas (`test_tasks.py`)**
   - Tareas de Celery
   - Envío de emails
   - Cálculo de variaciones de precio
   - Manejo de errores

4. **Pruebas de Serializers (`test_serializers.py`)**
   - Serialización/deserialización
   - Validaciones de datos
   - Casos borde

5. **Pruebas de Lógica de Negocio (`test_business_logic.py`)**
   - Normalización de productos
   - Cálculo de similitud
   - Deduplicación
   - Validaciones

### Frontend

1. **Pruebas de Componentes**
   - Renderizado correcto
   - Interacciones de usuario
   - Props y estado
   - Casos de error

2. **Pruebas de Páginas**
   - Integración con APIs
   - Estados de carga y error
   - Navegación

3. **Pruebas de Servicios**
   - Llamadas a APIs
   - Manejo de errores
   - Transformación de datos

## Herramientas Utilizadas

### Backend
- **pytest**: Framework de testing
- **pytest-django**: Integración con Django
- **pytest-cov**: Cobertura de código
- **factory-boy**: Generación de datos de prueba
- **freezegun**: Mock de fechas
- **responses**: Mock de HTTP requests

### Frontend
- **Jest**: Framework de testing
- **@testing-library/react**: Testing de componentes React
- **@testing-library/user-event**: Simulación de interacciones
- **MSW**: Mock Service Worker para APIs
- **@testing-library/jest-dom**: Matchers adicionales

## Mejores Prácticas

### Backend
1. **Usar factories para datos de prueba**
2. **Mantener pruebas atómicas e independientes**
3. **Usar fixtures para configuración común**
4. **Mockear dependencias externas**
5. **Probar casos borde y errores**

### Frontend
1. **Usar MSW para mock de APIs**
2. **Probar comportamiento, no implementación**
3. **Usar data-testid para selección de elementos**
4. **Probar accesibilidad básica**
5. **Mantener pruebas rápidas y confiables**

## Troubleshooting

### Backend
1. **Error de base de datos:**
   - Verificar configuración de PostgreSQL
   - Ejecutar migraciones: `python manage.py migrate`

2. **Error de Celery:**
   - Verificar configuración de Celery
   - Usar `CELERY_TASK_ALWAYS_EAGER=True` en tests

3. **Error de cobertura:**
   - Verificar archivo `.coveragerc`
   - Excluir archivos irrelevantes

### Frontend
1. **Error de MSW:**
   - Verificar configuración en `setupTests.js`
   - Reiniciar servidor de desarrollo

2. **Error de Jest:**
   - Limpiar cache: `npm test -- --clearCache`
   - Verificar configuración en `jest.config.js`

3. **Error de cobertura:**
   - Verificar `coveragePathIgnorePatterns` en Jest
   - Excluir archivos irrelevantes

## CI/CD

### GitHub Actions
```yaml
# Ejemplo de workflow para CI
name: Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=. --cov-fail-under=80

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node.js
        uses: actions/setup-node@v2
        with:
          node-version: 16
      - name: Install dependencies
        run: cd cotizabelleza-frontend && npm install
      - name: Run tests
        run: cd cotizabelleza-frontend && npm run test:coverage
```

## Mantenimiento

1. **Actualizar dependencias regularmente**
2. **Revisar cobertura de código mensualmente**
3. **Refactorizar pruebas cuando sea necesario**
4. **Documentar nuevos casos de prueba**
5. **Mantener sincronizados los mocks con APIs reales**

## Contacto

Para preguntas sobre testing, contactar al equipo de desarrollo o crear un issue en el repositorio.
