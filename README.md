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