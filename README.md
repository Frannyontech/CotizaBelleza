# CotizaBelleza - Sistema de Cotizaciones de Belleza

Sistema fullstack para cotizaciones de productos de belleza con arquitectura MVC + ETL, que permite a los usuarios comparar precios de productos de belleza de diferentes tiendas y recibir alertas de cambios de precios.

## Características Principales

- Comparación de Precios: Análisis de precios de productos de belleza de múltiples tiendas
- Alertas de Precios: Notificaciones automáticas cuando los precios cambian
- Deduplicación Inteligente: Identificación automática de productos duplicados entre tiendas
- Dashboard Interactivo: Interfaz web para visualizar y analizar datos
- ETL Automatizado: Procesamiento automático de datos de scrapers
- API REST: Endpoints para integración con otros sistemas

## Arquitectura

### Backend (Django + DRF)
- Framework: Django 4.x con Django REST Framework
- Base de Datos: PostgreSQL
- Cola de Tareas: Celery con Redis
- Autenticación: Sistema de verificación por email

### Frontend (React + Vite)
- Framework: React 18 con Vite
- Routing: React Router DOM v6.4.0
- Testing: Jest
- Estilos: CSS moderno con diseño responsive

### ETL Pipeline
- Scrapers: Selenium para extracción de datos
- Procesamiento: Normalización y deduplicación automática
- Almacenamiento: JSON estructurado y base de datos

## Estructura del Proyecto

```
CotizaBelleza/
├── core/                    # App principal Django
│   ├── models.py           # Modelos de datos
│   ├── views.py            # Vistas API
│   ├── serializers.py      # Serializers DRF
│   ├── services/           # Lógica de negocio
│   └── tasks.py            # Tareas Celery
├── cotizabelleza/          # Configuración Django
├── cotizabelleza-frontend/ # Frontend React
├── etl/                    # Pipeline ETL
├── scraper/                # Scrapers de tiendas
├── data/                   # Datos procesados
└── deploy/                 # Configuración Docker
```

## Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis

### Backend
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

### Frontend
```bash
cd cotizabelleza-frontend

# Instalar dependencias
npm install

# Ejecutar en desarrollo
npm run dev

# Construir para producción
npm run build
```

### ETL Pipeline
```bash
# Configurar variables de entorno
cp .env.example .env

# Ejecutar pipeline completo
python etl/orchestrator.py

# O ejecutar por componentes
python etl/scrapers.py
python etl/processor.py
```

## Configuración

### Variables de Entorno
```bash
# Django
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=postgresql://user:pass@localhost/cotizabelleza

# Redis
REDIS_URL=redis://localhost:6379

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

### Base de Datos
```bash
# Crear base de datos PostgreSQL
createdb cotizabelleza

# Aplicar migraciones
python manage.py migrate

# Cargar datos iniciales
python manage.py loaddata initial_data.json
```

## Uso

### API Endpoints
- GET /api/dashboard/ - Dashboard principal
- GET /api/products/unified/ - Productos unificados
- GET /api/products/filtered/ - Productos filtrados
- GET /api/alerts/ - Alertas de precios
- POST /api/verify-email/ - Verificación de email
- POST /api/unsubscribe/ - Cancelar suscripción

### ETL Pipeline
```bash
# Ejecutar scrapers
python -m etl.scrapers

# Procesar datos
python -m etl.processor

# Ejecutar pipeline completo
python -m etl.orchestrator
```

### Tareas Celery
```bash
# Iniciar worker
celery -A cotizabelleza worker -l info

# Iniciar beat (tareas programadas)
celery -A cotizabelleza beat -l info

# Verificar estado
celery -A cotizabelleza inspect active
```

## Testing

### Ejecutar Tests
```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=core --cov-report=html

# Tests específicos
pytest tests/test_models.py
pytest tests/test_views.py
```

### Cobertura Actual
- Total: 24%
- Modelos: 62%
- Serializers: 98%
- Servicios: 25%

## Docker

### Desarrollo
```bash
docker-compose -f deploy/docker-compose.yml up -d
```

### Producción
```bash
docker-compose -f deploy/docker-compose.prod.yml up -d
```

## Monitoreo

### Logs
- ETL: logs/etl_pipeline.log
- Django: logs/django.log
- Celery: logs/celery.log

### Métricas
- Productos procesados: Dashboard API
- Alertas activas: Alertas API
- Estado ETL: Logs del pipeline

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (git checkout -b feature/AmazingFeature)
3. Commit tus cambios (git commit -m 'Add some AmazingFeature')
4. Push a la rama (git push origin feature/AmazingFeature)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.

## Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Contactar al equipo de desarrollo

---

Estado: Funcional y en desarrollo activo
Versión: 1.0.0
Última actualización: Septiembre 2025 