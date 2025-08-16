# Changelog

Todos los cambios notables a este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-08-15

### ➕ Added
- **RF-01 Búsqueda**: Página de resultados de búsqueda con filtros avanzados por precio, tienda y disponibilidad
- **RF-02 Comparación**: Componente StoreComparison para comparar precios entre tiendas con visualización de descuentos
- **RF-04 Alertas**: Sistema completo de alertas de precio por email con modelo AlertaPrecio
- **RF-06 Reseñas**: Modal y componente para crear y visualizar reseñas de productos con calificaciones de 1-5 estrellas
- Scraper de Preunic con Selenium para extracción automática de productos, precios y stock
- Funcionalidad de paginación y ordenamiento dinámico en resultados de búsqueda
- Filtros interactivos por rango de precio con slider
- Sistema de testing automatizado con Jest
- Validación avanzada de emails en alertas de precio
- Componente ProductReviews para mostrar reseñas existentes
- Modelo de datos normalizado para productos, tiendas y precios

### 🔄 Changed  
- Refactorización completa del scraper DBS con mejor manejo de errores y extracción de dataLayer
- Mejoras significativas en la interfaz del dashboard con mejor organización y UX
- Optimización de la página de resultados de búsqueda con estados de carga y manejo de errores
- Actualización del modelo Resena con campo nombre_autor opcional para flexibilidad
- Mejora en la conexión frontend-backend para visualización de productos
- Reorganización de componentes de productos por tienda (DBSProductos, PreunicProductos)

### 🐛 Fixed
- Corrección crítica de bug de categorías duplicadas en el sistema
- Mejoras en la validación y manejo de datos de productos
- Corrección de errores en carga de imágenes con fallbacks apropiados
- Mejoras en el manejo de estados de error en componentes React
- Corrección de problemas de renderizado en comparación de tiendas

### 🧪 Testing
- Implementación de suite completa de testing con Jest y configuración personalizada
- Pruebas unitarias para PriceAlertModal con validación de comportamiento
- Testing de helpers de normalización de datos (normalizeHelpers.test.js)
- Configuración de mocks para archivos estáticos
- Scripts npm para testing en modo watch y coverage

### 🏗️ Build/CI
- Configuración de Jest con support para ES6 modules y React components
- Estructura de proyecto optimizada para desarrollo y producción
- Scripts de npm para testing, desarrollo y build
- Configuración de ESLint para mantener calidad de código
- Setup de Vite para desarrollo rápido y hot reload

### 📚 Documentation
- README actualizado con instrucciones detalladas de instalación
- Documentación completa del módulo de scraping con ejemplos de uso
- Comentarios en código mejorados para mejor mantenibilidad

## [Unreleased]

### Planned for v0.5.0
- Integración completa backend-frontend para todas las funcionalidades
- Sistema de notificaciones por email para alertas de precio
- Análisis de tendencias con gráficos de evolución de precios
- Optimización de performance con caching de scrapers
- API avanzada para estadísticas y análisis
- Aplicación móvil para iOS y Android

---

**Formato**: [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)  
**Versionado**: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
