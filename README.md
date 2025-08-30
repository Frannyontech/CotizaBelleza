# CotizaBelleza

Sistema completo de cotizaciones de belleza con ETL automatizado, API REST y frontend React.

## ✅ Estado del Proyecto

**FLUJO COMPLETO FUNCIONANDO** - Sistema operativo con:
- **ETL automatizado** con preservación de datos de usuarios
- **API REST** funcionando correctamente  
- **Frontend React** operativo
- **Sistema de IDs persistentes** preservando reseñas y alertas
- **Patrón Observer** para notificaciones automáticas de precio
- **360 productos unificados** de 3 tiendas (PREUNIC, DBS, MAICAO)

## 🚀 Características Principales

### Sistema de Protección de Datos de Usuarios
- ✅ **Productos con reseñas NUNCA se eliminan** del sistema
- ✅ **Alertas de precio preservadas** automáticamente
- ✅ **URLs existentes siguen funcionando** sin cambios
- ✅ **Compatibilidad total** con frontend y APIs existentes

### Sistema de Notificaciones con Patrón Observer
- ✅ **Notificaciones automáticas** cuando cambian los precios
- ✅ **Desacoplamiento total** entre productos y alertas
- ✅ **Escalabilidad** para múltiples tipos de observadores
- ✅ **Integración con Celery** para emails asíncronos

### ETL Pipeline Avanzado
- **Scrapers optimizados**: Preunic (Algolia API), DBS, Maicao
- **Deduplicación inteligente**: Algoritmo de similitud (umbral 0.75)
- **Normalización automática**: Tamaños (ml, gr) y nombres de productos
- **Persistencia de datos**: Sistema de IDs persistentes

### API REST Completa
- `/api/dashboard/` - Estadísticas y productos populares
- `/api/unified/` - Todos los productos unificados
- `/api/productos/{id}/resenas/` - Sistema de reseñas
- `/api/tienda/{nombre}/` - Productos por tienda

## 📋 Requisitos

- Python 3.13+
- Django 5.2.4
- React 19 con Vite
- PostgreSQL (opcional, SQLite por defecto)
- Redis (para Celery, opcional)

## 🛠️ Instalación

1. **Clona el repositorio:**
```bash
git clone <url-del-repositorio>
cd CotizaBelleza
```

2. **Configura las variables de entorno:**
```bash
# Copia el archivo de ejemplo
cp env.example .env

# Edita .env con tus configuraciones
# IMPORTANTE: Genera la clave secreta para emails
python manage.py generate_email_secret_key
```

3. **Instala las dependencias Python:**
```bash
py -m pip install -r requirements.txt
```

4. **Instala las dependencias del frontend:**
```bash
cd cotizabelleza-frontend
npm install
cd ..
```

5. **Ejecuta las migraciones:**
```bash
py manage.py migrate
```

6. **Crea un superusuario (opcional):**
```bash
py manage.py createsuperuser
```



## 🚀 Uso

### Iniciar Servicios

**Backend Django:**
```bash
py manage.py runserver
```

**Frontend React:**
```bash
cd cotizabelleza-frontend && npm run dev
```

**Celery (opcional):**
```bash
py celery_etl.py services
```

### Ejecutar ETL Completo
```bash
py -m etl.etl_v2 full --headless --max-pages 2
```

## 📁 Estructura del Proyecto

```
CotizaBelleza/
├── 📁 core/                    # Backend Django (APIs, modelos)
├── 📁 cotizabelleza/           # Configuración Django
├── 📁 cotizabelleza-frontend/  # Frontend React
├── 📁 data/                    # Datos del ETL (raw/processed)
├── 📁 etl/                     # Pipeline ETL completo
├── 📁 processor/               # Procesadores de datos
├── 📁 scraper/                 # Scrapers web (DBS, Preunic, Maicao)
├── 📁 logs/                    # Logs del sistema
├── 📁 stats/                   # Estadísticas de ETL
├── 📄 celery_etl.py           # Gestión de Celery
├── 📄 manage.py               # Django management
└── 📄 requirements.txt        # Dependencias Python
```

## 🌐 URLs de Acceso

- **Frontend**: http://localhost:5173/
- **API**: http://localhost:8000/api/
- **Dashboard**: http://localhost:5173/
- **Productos**: http://localhost:5173/productos

## 🔧 Comandos Útiles

### Verificar Estado del Sistema
```bash
# Verificar que el flujo completo funciona
py -c "import requests; r=requests.get('http://localhost:8000/api/unified/'); print(f'API: {r.status_code}, Productos: {len(r.json().get(\"productos\", []))}')"
```

### Sistema de Observadores
```bash
# Configurar sistema de observadores
py manage.py setup_observer setup

# Ver estadísticas de observadores
py manage.py setup_observer stats

# Probar notificación
py manage.py setup_observer test --product-id cb_0444195a --test-price 8000

# Limpiar observadores inactivos
py manage.py setup_observer cleanup
```



### Limpiar Cachés
```bash
# Limpiar cachés de Python
py -c "import os, shutil; [shutil.rmtree(os.path.join(root, '__pycache__')) for root, dirs, files in os.walk('.') if '__pycache__' in dirs]"
```

## 📊 Datos Actuales

- **Total Productos**: 360 productos unificados
- **Tiendas**: PREUNIC, DBS, MAICAO
- **Categorías**: maquillaje, skincare
- **Productos Multi-tienda**: Preservados y balanceados en dashboard

## 🛡️ Sistema de Protección

El sistema garantiza que:
- ✅ **Productos con reseñas** nunca se eliminan
- ✅ **Alertas de precio** se mantienen activas
- ✅ **URLs existentes** siguen funcionando
- ✅ **Datos de usuarios** se preservan entre ejecuciones de ETL

## 📝 Caso de Éxito

Producto `cb_0444195a` ("Rubor Líquido Maybelline...") preservado con reseñas de usuarios:
- ✅ Presente en JSON procesado
- ✅ Disponible en API
- ✅ Visible en frontend
- ✅ Reseñas intactas

## 🔄 Tecnologías

- **Backend**: Django + Django REST Framework
- **Frontend**: React + Vite + Ant Design
- **Base de Datos**: PostgreSQL/SQLite
- **ETL**: Python + Selenium + BeautifulSoup
- **Cola de Tareas**: Celery + Redis
- **Deduplicación**: TF-IDF + Similitud de cadenas
- **Patrones de Diseño**: Observer Pattern para notificaciones

## 📞 Soporte

Para reportar problemas o solicitar features:
- Abre un issue en GitHub
- Incluye logs y pasos de reproducción
- Especifica la versión del sistema 

## Estado Actual de Testing

### ✅ **Problema de Configuración RESUELTO:**
- **Configuración de testing específica**: Creado `cotizabelleza/test_settings.py`
- **Scripts de ejecución**: Múltiples opciones para ejecutar tests
- **Base de datos en memoria**: SQLite optimizada para testing
- **Celery en modo eager**: Sin dependencias externas

### ✅ **Progreso Completado:**
- **Infraestructura de testing configurada**: pytest, pytest-django, pytest-cov, factory-boy
- **74 tests creados** organizados en 5 archivos principales:
  - `tests/test_models.py` - Tests para modelos Django
  - `tests/test_views.py` - Tests para vistas DRF
  - `tests/test_serializers.py` - Tests para serializers
  - `tests/test_tasks.py` - Tests para tareas Celery
  - `tests/test_business_logic.py` - Tests para lógica de negocio
- **Configuración de coverage**: HTML y terminal reports configurados
- **Factories y fixtures**: Configurados para crear datos de prueba
- **Correcciones de compatibilidad**: Campos requeridos, imports correctos, signaturas de métodos

### 🚀 **Cómo Ejecutar los Tests:**

#### **Opción 1: Script Principal (Recomendado)**
```bash
python run_tests.py
```

#### **Opción 2: Verificar Configuración**
```bash
python verify_config.py
```

#### **Opción 3: Test Específico**
```bash
python run_single_test.py
```

#### **Opción 4: Makefile (Si tienes make instalado)**
```bash
make test          # Ejecutar todos los tests
make test-single   # Ejecutar test específico
make verify        # Verificar configuración
make coverage      # Ejecutar con cobertura
make help          # Ver todos los comandos
```

### 🎯 **Próximos Pasos:**
1. ✅ **Resolver configuración de Django** - COMPLETADO
2. 🔄 **Ejecutar tests completos** para obtener cobertura real
3. 🔄 **Corregir tests fallando** basándose en errores específicos
4. 🔄 **Agregar tests faltantes** para alcanzar 80% de cobertura

### 📈 **Métricas Objetivo:**
- **Backend**: ≥ 80% cobertura (actual: pendiente de ejecución)
- **Frontend**: ≥ 80% cobertura (pendiente de implementar)
- **Tests ejecutándose**: 100% sin errores de configuración
- **Tiempo de ejecución**: < 2 minutos para suite completa

### 🛠️ **Herramientas Configuradas:**
- **Backend**: pytest, pytest-django, pytest-cov, factory-boy, freezegun
- **Frontend**: Jest, React Testing Library, MSW (Mock Service Worker)
- **CI/CD**: GitHub Actions workflow configurado
- **Reports**: HTML coverage reports en `htmlcov/`

### 📋 **Archivos de Testing Creados:**
```
tests/
├── __init__.py
├── conftest.py              # Fixtures globales
├── test_models.py           # 15 tests - Modelos Django
├── test_views.py            # 12 tests - Vistas DRF
├── test_serializers.py      # 12 tests - Serializers
├── test_tasks.py            # 20 tests - Tareas Celery
└── test_business_logic.py   # 15 tests - Lógica de negocio

Scripts Universales:
├── run_tests.py             # Script principal
├── run_single_test.py       # Test específico
├── verify_config.py         # Verificación
└── Makefile                 # Comandos simples
```

### 🚀 **Comandos para Ejecutar Tests:**
```bash
# Opción 1: Script principal (recomendado)
python run_tests.py

# Opción 2: Verificar configuración
python verify_config.py

# Opción 3: Makefile (si tienes make instalado)
make test

# Opción 4: Comando manual
export DJANGO_SETTINGS_MODULE=cotizabelleza.test_settings  # Linux/Mac
set DJANGO_SETTINGS_MODULE=cotizabelleza.test_settings     # Windows
python -m pytest --nomigrations --cov=. --cov-report=html:htmlcov

# Ver reporte de cobertura
open htmlcov/index.html  # Linux/Mac
start htmlcov/index.html # Windows
``` 