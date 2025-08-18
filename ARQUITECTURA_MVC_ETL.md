# 🏗️ Arquitectura MVC + ETL - CotizaBelleza

## 📋 Resumen Ejecutivo

**CotizaBelleza** ahora implementa una **arquitectura MVC (Model-View-Controller)** completa con **integración ETL (Extract-Transform-Load)**, manteniendo el pipeline de datos existente mientras mejora significativamente la organización del código y la separación de responsabilidades.

## 🎯 Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA MVC + ETL                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   EXTRACT   │───▶│  TRANSFORM  │───▶│    LOAD     │     │
│  │  (Scrapers) │    │(Processor)  │    │ (Django DB) │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│           │                                     │           │
│           ▼                                     ▼           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    BACKEND MVC                          ││
│  │                                                         ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │   MODELS    │  │ CONTROLLERS │  │    VIEWS    │    ││
│  │  │             │  │             │  │             │    ││
│  │  │ • Producto  │  │ • Dashboard │  │ • API       │    ││
│  │  │ • Precio    │  │ • Producto  │  │ • REST      │    ││
│  │  │ • Categoria │  │ • ETL       │  │ • JSON      │    ││
│  │  │ • Managers  │  │ • Usuario   │  │ • Clean     │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  │                                                         ││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │                  SERVICES                           │││
│  │  │ • ETLService     • DataIntegrationService           │││
│  │  │ • ProductoService • ETLSchedulerService             │││
│  │  └─────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────┘│
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   FRONTEND MVC                          ││
│  │                                                         ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │    VIEWS    │  │ CONTROLLERS │  │   SERVICES  │    ││
│  │  │             │  │             │  │             │    ││
│  │  │ • Dashboard │  │ • Dashboard │  │ • mvcApi    │    ││
│  │  │ • Products  │  │ • Producto  │  │ • etlApi    │    ││
│  │  │ • Search    │  │ • ETL       │  │ • unified   │    ││
│  │  │ • React     │  │ • State     │  │ • HTTP      │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Componentes Principales

### 1. **Backend MVC + ETL**

#### **Models (Modelos)**
```python
# core/models.py + core/managers.py
├── Modelos optimizados con managers personalizados
├── Métodos de negocio en modelos
└── Consultas optimizadas con prefetch/select_related
```

#### **Controllers (Controladores)**
```python
# core/controllers.py
├── DashboardController    # Lógica de dashboard
├── ProductoController     # Lógica de productos  
├── ETLController         # Control del pipeline ETL
├── UsuarioController     # Gestión de usuarios
└── ResenaController      # Gestión de reseñas
```

#### **Views (Vistas)**
```python
# core/views_mvc.py
├── Vistas limpias (20-50 líneas cada una)
├── Solo lógica de presentación
├── Delegación total a controladores
└── Manejo de errores HTTP
```

#### **Services (Servicios)**
```python
# core/services.py
├── ETLService            # Pipeline completo Extract-Transform-Load
├── DataIntegrationService # Integración datos ETL ↔ Django
├── ProductoService       # Lógica de dominio productos
└── ETLSchedulerService   # Automatización del ETL
```

### 2. **Frontend MVC React**

#### **Controllers**
```javascript
// src/controllers/
├── DashboardController.js  # Estado y lógica dashboard
├── ProductoController.js   # Estado y lógica productos
└── ETLController.js       # Control ETL desde frontend
```

#### **Services**
```javascript
// src/services/
├── mvcApi.js              # Servicios API MVC limpios
└── api.js                 # API original (compatibilidad)
```

#### **Views**
```javascript
// src/components/ + src/pages/
├── Componentes React limpios
├── Hooks para controladores
└── UI sin lógica de negocio
```

## 🔄 Pipeline ETL Integrado

### **Extract (Extracción)**
```
scraper/
├── scrapers/
│   ├── dbs_selenium_scraper.py
│   ├── maicao_selenium_scraper.py
│   └── preunic_selenium_scraper.py
└── data/raw/
    ├── dbs_productos.json
    ├── maicao_productos.json
    └── preunic_productos.json
```

### **Transform (Transformación)**
```
processor/
├── normalize.py              # Normalización y deduplicación
└── data/processed/
    └── unified_products.json # Datos unificados
```

### **Load (Carga)**
```
core/management/commands/
└── load_scraper_data.py     # Carga a Django DB
```

## 🚀 Beneficios de la Nueva Arquitectura

### **Código Mejorado**
- ✅ **Vistas reducidas**: De 850+ líneas a 20-50 líneas por vista
- ✅ **Separación clara**: Cada capa tiene una responsabilidad específica
- ✅ **Reutilización**: Controladores reutilizables entre vistas
- ✅ **Mantenimiento**: Cambios centralizados en controladores/servicios

### **ETL Perfectamente Integrado**
- ✅ **Control desde API**: Ejecutar ETL via REST endpoints
- ✅ **Monitoreo**: Estado en tiempo real del pipeline
- ✅ **Datos híbridos**: Combina BD Django + archivo unificado
- ✅ **Automatización**: Base para scheduling con Celery

### **Escalabilidad**
- ✅ **Nuevas tiendas**: Solo agregar scraper + configuración
- ✅ **Nuevas funcionalidades**: Agregar controlador + vista
- ✅ **Testing**: Cada capa testeable independientemente
- ✅ **Deploy**: Componentes deployables por separado

## 📁 Estructura de Archivos

```
CotizaBelleza/
├── core/                           # Backend MVC
│   ├── models.py                   # Models con managers
│   ├── managers.py                 # Managers personalizados
│   ├── controllers.py              # Controllers (lógica negocio)
│   ├── views_mvc.py               # Views limpias MVC
│   ├── services.py                # Services (lógica dominio)
│   ├── urls_mvc.py                # URLs MVC
│   ├── views.py                   # Views originales (deprecated)
│   └── migration_mvc.py           # Guía de migración
│
├── processor/                      # ETL Transform
│   ├── normalize.py               # Procesador principal
│   └── README.md                  # Documentación ETL
│
├── scraper/                       # ETL Extract
│   ├── scrapers/                  # Scrapers por tienda
│   └── data/                      # Datos raw
│
├── cotizabelleza-frontend/        # Frontend MVC React
│   ├── src/
│   │   ├── controllers/           # Controllers React
│   │   │   ├── DashboardController.js
│   │   │   ├── ProductoController.js
│   │   │   └── ETLController.js
│   │   ├── services/              # Services API
│   │   │   ├── mvcApi.js         # API MVC nueva
│   │   │   └── api.js            # API original
│   │   └── components/            # Views React
│
└── ARQUITECTURA_MVC_ETL.md        # Esta documentación
```

## 🔄 Migración y Compatibilidad

### **Configuración Híbrida**
```python
# cotizabelleza/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),         # URLs originales
    path('mvc/', include('core.urls_mvc')), # URLs MVC nuevas
]
```

### **APIs Disponibles**
```
# API Original
GET /api/productos/                 # Lista productos
GET /api/dashboard/                 # Dashboard original

# API MVC Nueva  
GET /mvc/api/productos/             # Lista productos MVC
GET /mvc/api/dashboard/             # Dashboard híbrido
POST /mvc/api/etl/control/          # Control ETL
GET /mvc/api/etl/status/            # Estado ETL
```

### **Frontend Híbrido**
```javascript
// Usar API MVC
import mvcApi from './services/mvcApi.js';
const productos = await mvcApi.productos.getProductos();

// Fallback API original
import { productService } from './services/api.js';
const productos = await productService.getProductos();
```

## 🎮 Control del ETL

### **Desde Backend (Django Commands)**
```bash
# Pipeline completo
python manage.py load_scraper_data --file scraper/data/dbs_productos.json --tienda DBS

# Procesador
python -m processor.normalize --min-strong 95 --min-prob 85
```

### **Desde API REST**
```bash
# Pipeline completo
curl -X POST http://localhost:8000/mvc/api/etl/control/ \
  -H "Content-Type: application/json" \
  -d '{"action": "full_pipeline", "tiendas": ["dbs", "maicao"]}'

# Solo scraper
curl -X POST http://localhost:8000/mvc/api/etl/control/ \
  -H "Content-Type: application/json" \
  -d '{"action": "scraper", "tienda": "dbs", "categoria": "maquillaje"}'

# Estado
curl http://localhost:8000/mvc/api/etl/status/
```

### **Desde Frontend**
```javascript
import etlController from './controllers/ETLController.js';

// Pipeline completo
await etlController.runFullPipeline({
  tiendas: ['dbs', 'maicao', 'preunic'],
  categorias: ['maquillaje', 'skincare']
});

// Estado en tiempo real
etlController.subscribe((data) => {
  console.log('ETL Status:', data.status);
});
```

## 📊 Monitoreo y Estado

### **Dashboard ETL**
- ✅ **Estado de archivos**: Raw data + processed data
- ✅ **Base de datos**: Estadísticas de registros
- ✅ **Operaciones**: Estado de scraping/processing/sync
- ✅ **Logs**: Historial de operaciones ETL

### **Datos Híbridos**
- ✅ **BD Django**: Datos normalizados con relaciones
- ✅ **Archivo unificado**: Datos procesados listos para frontend
- ✅ **Combinación inteligente**: Mejor de ambos mundos

## 🚦 Estados del Sistema

### **ETL Pipeline**
- 🟢 **Idle**: Sin operaciones en curso
- 🟡 **Running**: Ejecutando scraping/processing
- 🔴 **Error**: Error en alguna etapa
- 🔵 **Syncing**: Sincronizando datos

### **Fuentes de Datos**
- 🗄️ **Database**: Datos Django normalizados
- 📄 **Unified File**: Archivo procesado ETL
- 🔄 **Hybrid**: Combinación de ambas fuentes

## 🔧 Configuración de Desarrollo

### **Activar MVC Completo**
```python
# Reemplazar core.urls con core.urls_mvc en cotizabelleza/urls.py
path('', include('core.urls_mvc')),
```

### **Testing**
```bash
# Backend
python manage.py test core.tests

# Frontend  
cd cotizabelleza-frontend
npm test
```

## 🎯 Próximos Pasos

1. **Migración Gradual**: Mover frontend a usar APIs MVC
2. **Monitoring**: Implementar dashboards de monitoreo ETL
3. **Scheduling**: Automatizar ETL con Celery/Cron
4. **Performance**: Optimizar consultas y caching
5. **Testing**: Tests unitarios para cada capa MVC

---

## 🏆 Conclusión

La nueva **arquitectura MVC + ETL** mantiene todo el poder del pipeline de datos existente mientras proporciona:

- **Código más limpio y mantenible**
- **Separación clara de responsabilidades**
- **ETL completamente integrado y controlable**
- **Escalabilidad para nuevas tiendas y funcionalidades**
- **Base sólida para futuras mejoras**

El sistema ahora es **verdaderamente MVC** manteniendo la **potencia del ETL** que hace único a CotizaBelleza. 🚀
