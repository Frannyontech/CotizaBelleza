# 🚀 Conexión Frontend-Backend CotizaBelleza

Este documento explica cómo conectar el frontend React con el backend Django utilizando los datos del scraper de DBS.

## 📋 Prerrequisitos

- Python 3.8+
- Node.js 16+
- PostgreSQL configurado
- Variables de entorno configuradas en `.env`

## 🔧 Configuración del Backend

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar base de datos
Asegúrate de que tu archivo `.env` tenga las variables correctas:
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=cotizabelleza
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

### 3. Ejecutar migraciones y cargar datos
```bash
# Opción 1: Usar el script automático
python setup_backend.py

# Opción 2: Ejecutar manualmente
python manage.py makemigrations
python manage.py migrate
python manage.py load_scraper_data
```

### 4. Verificar la carga de datos
```bash
python manage.py shell
```
```python
from core.models import Producto, Categoria, Tienda, PrecioProducto
print(f"Productos: {Producto.objects.count()}")
print(f"Categorías: {Categoria.objects.count()}")
print(f"Tiendas: {Tienda.objects.count()}")
print(f"Precios: {PrecioProducto.objects.count()}")
```

### 5. Iniciar el servidor Django
```bash
python manage.py runserver
```

El backend estará disponible en: `http://localhost:8000`

## 🌐 APIs Disponibles

### Dashboard
- `GET /api/dashboard/` - Datos del dashboard con estadísticas y productos populares

### Productos
- `GET /api/productos/` - Lista de productos con filtros
- `GET /api/precios/?producto={id}` - Precios de un producto específico

### Categorías
- `GET /api/categorias/` - Lista de categorías disponibles

### Tiendas
- `GET /api/tiendas/` - Lista de tiendas disponibles

### Usuarios
- `POST /api/usuarios/` - Crear nuevo usuario

## ⚛️ Configuración del Frontend

### 1. Instalar dependencias
```bash
cd cotizabelleza-frontend
npm install
```

### 2. Verificar configuración de API
El archivo `src/services/api.js` está configurado para conectarse a:
- URL Base: `http://localhost:8000/api/`
- CORS habilitado para `http://localhost:5173`

### 3. Iniciar el frontend
```bash
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

## 🔄 Flujo de Datos

### 1. Carga de Datos del Scraper
```
scraper/dbs_productos.json → Django Management Command → PostgreSQL
```

### 2. APIs del Backend
```
PostgreSQL → Django Views → JSON APIs → Frontend
```

### 3. Frontend
```
React Components → API Services → Backend APIs
```

## 📊 Estructura de Datos

### Producto (Modelo Django)
```python
{
    "id": 1,
    "nombre": "Base de maquillaje Fit Me",
    "marca": "Maybelline",
    "categoria": "Maquillaje",
    "imagen_url": "https://...",
    "descripcion": "..."
}
```

### PrecioProducto (Modelo Django)
```python
{
    "id": 1,
    "producto": 1,
    "tienda": "DBS",
    "precio": 8990.00,
    "stock": true,
    "url_producto": "https://dbs.cl/...",
    "fecha_extraccion": "2025-01-29T..."
}
```

### API Response (Dashboard)
```json
{
    "estadisticas": {
        "total_productos": 960,
        "productos_con_precios": 850,
        "total_categorias": 7,
        "total_tiendas": 1,
        "precio_promedio": 12500.50,
        "precio_min": 1000.00,
        "precio_max": 50000.00
    },
    "productos_populares": [
        {
            "id": 1,
            "nombre": "Base de maquillaje Fit Me",
            "marca": "Maybelline",
            "categoria": "Maquillaje",
            "precio_min": 8990,
            "tiendas_disponibles": ["DBS"],
            "imagen_url": "https://...",
            "num_precios": 1
        }
    ]
}
```

## 🛠️ Comandos Útiles

### Backend
```bash
# Cargar datos del scraper
python manage.py load_scraper_data

# Verificar datos
python manage.py shell
>>> from core.models import Producto, PrecioProducto
>>> print(f"Productos: {Producto.objects.count()}")
>>> print(f"Precios: {PrecioProducto.objects.count()}")

# Crear superusuario
python manage.py createsuperuser

# Ejecutar tests
python manage.py test
```

### Frontend
```bash
# Instalar dependencias
npm install

# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview build
npm run preview
```

## 🔍 Troubleshooting

### Error de CORS
Si ves errores de CORS, verifica que en `settings.py` tengas:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173"
]
```

### Error de conexión a la base de datos
Verifica tu archivo `.env` y asegúrate de que PostgreSQL esté corriendo.

### Error cargando datos del scraper
Verifica que el archivo `scraper/dbs_productos.json` existe y tiene el formato correcto.

### Error en las APIs
Revisa los logs de Django para ver errores específicos:
```bash
python manage.py runserver --verbosity=2
```

## 📈 Próximos Pasos

1. **Implementar autenticación** - JWT tokens
2. **Agregar más tiendas** - Integrar otros scrapers
3. **Sistema de alertas** - Notificaciones de precios
4. **Favoritos** - Lista de productos favoritos
5. **Comparación de precios** - Gráficos de precios
6. **Búsqueda avanzada** - Filtros más complejos

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📞 Soporte

Si tienes problemas con la conexión:
1. Verifica que ambos servidores estén corriendo
2. Revisa la consola del navegador para errores
3. Revisa los logs de Django
4. Verifica la configuración de CORS 