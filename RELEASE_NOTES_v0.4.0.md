# CotizaBelleza v0.4.0 — 2025-08-15

## 🎉 Highlights

• **Scraping Multi-Tienda Completo**: Integración completa de scrapers para DBS y Preunic con extracción automática de productos, precios y stock
• **Interfaz de Búsqueda Avanzada**: Página de resultados con filtros por precio, tienda y disponibilidad, con paginación y ordenamiento dinámico  
• **Sistema de Alertas de Precio**: Funcionalidad RF-04 implementada con notificaciones por email para cambios de precio y disponibilidad
• **Módulo de Reseñas**: Sistema RF-06 de reseñas de productos con calificaciones de 1-5 estrellas y comentarios de usuarios
• **Comparación entre Tiendas**: Componente RF-02 para comparar precios entre diferentes tiendas con visualización de descuentos
• **Testing Automatizado**: Suite de pruebas unitarias con Jest para componentes críticos del frontend
• **Arquitectura Escalable**: Modelo de datos optimizado con relaciones normalizadas y API RESTful para productos y precios
• **UX/UI Moderna**: Interfaz responsive con Ant Design, manejo de estados de carga y experiencia de usuario fluida

## 📊 Estado por Sprint

| Sprint | Alcance | Estado |
|--------|---------|---------|
| 1-3 | Scrapers DBS/Preunic + unificación base | ✅ Listo |
| 4 | Interfaz productos/buscador | 🚧 En progreso |
| 5 | Alertas/Reseñas (frontend) | 🚧 En progreso |
| 6 | Integración/QA | ⏳ Pendiente |

## 📝 Changelog Detallado

### ➕ Added
- **RF-01 Búsqueda**: Página de resultados de búsqueda con filtros avanzados ([afdf5c9](https://github.com/CotizaBelleza/commit/afdf5c9))
- **RF-02 Comparación**: Componente StoreComparison para comparar precios entre tiendas ([2832cf6](https://github.com/CotizaBelleza/commit/2832cf6))
- **RF-04 Alertas**: Sistema completo de alertas de precio por email ([6520333](https://github.com/CotizaBelleza/commit/6520333))
- **RF-06 Reseñas**: Modal y componente para crear y visualizar reseñas de productos ([c316110](https://github.com/CotizaBelleza/commit/c316110))
- Scraper de Preunic con Selenium para extracción automática de productos ([afdf5c9](https://github.com/CotizaBelleza/commit/afdf5c9))
- Modelo de datos para AlertaPrecio con validaciones y relaciones ([6520333](https://github.com/CotizaBelleza/commit/6520333))
- Funcionalidad de paginación y ordenamiento en resultados de búsqueda
- Filtros por precio, tienda y disponibilidad en interfaz de búsqueda

### 🔄 Changed  
- Refactorización completa del scraper DBS con mejor manejo de errores ([3772913](https://github.com/CotizaBelleza/commit/3772913))
- Mejoras en la interfaz del dashboard con mejor organización de componentes ([2832cf6](https://github.com/CotizaBelleza/commit/2832cf6))
- Optimización de la página de resultados de búsqueda con mejor UX ([2832cf6](https://github.com/CotizaBelleza/commit/2832cf6))
- Actualización del modelo Resena con campo nombre_autor opcional

### 🐛 Fixed
- Corrección de bug de categorías duplicadas en el sistema ([334ea32](https://github.com/CotizaBelleza/commit/334ea32))
- Mejoras en la conexión entre frontend y backend para mostrar productos ([3772913](https://github.com/CotizaBelleza/commit/3772913))
- Validación mejorada de emails en sistema de alertas
- Manejo de errores en carga de imágenes de productos

### 🧪 Testing
- Implementación de suite de testing con Jest ([334ea32](https://github.com/CotizaBelleza/commit/334ea32))
- Pruebas unitarias para PriceAlertModal ([16537c5](https://github.com/CotizaBelleza/commit/16537c5))
- Testing de helpers de normalización de datos

### 🏗️ Build/CI
- Configuración de Jest para testing automatizado
- Estructura de proyecto optimizada para desarrollo y producción
- Scripts de npm para testing, desarrollo y build

## ⚠️ Known Issues

- Los scrapers pueden verse afectados por cambios en la estructura de las páginas web objetivo
- El sistema de alertas por email requiere configuración SMTP para funcionar en producción
- Algunos productos pueden no tener imágenes disponibles (se muestra imagen placeholder)

## 🔧 Breaking Changes

Ningún breaking change en esta versión. La API mantiene compatibilidad hacia atrás.

## 📋 Upgrade Notes

1. **Instalación de dependencias**:
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend  
   cd cotizabelleza-frontend
   npm install
   ```

2. **Migraciones de base de datos**:
   ```bash
   python manage.py migrate
   ```

3. **Configuración de testing**:
   ```bash
   cd cotizabelleza-frontend
   npm test
   ```

## 🚀 Next Milestones (v0.5.0)

- **Integración completa**: Finalización de la conexión backend-frontend para todas las funcionalidades
- **Sistema de notificaciones**: Implementación de envío de emails para alertas de precio
- **Análisis de tendencias**: Gráficos de evolución de precios históricos
- **Optimización de performance**: Caching de resultados de scrapers y mejoras de velocidad
- **API avanzada**: Endpoints para estadísticas y análisis de productos
- **Mobile app**: Aplicación móvil para iOS y Android

---

**Desarrollado por**: Francisca Galaz (@Frannyontech)  
**Fecha de lanzamiento**: 15 de agosto, 2025  
**Total de commits**: 26 desde el inicio del proyecto
