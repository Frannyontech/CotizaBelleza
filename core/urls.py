"""
URLs para la arquitectura MVT - Rutas limpias que usan las vistas optimizadas
"""
from django.urls import path
from .views import (
    home,
    DashboardAPIView,
    ProductoListAPIView,
    CategoriaListAPIView,
    TiendaListAPIView,
    PreciosPorProductoAPIView,
    ProductoDetalleAPIView,
    TiendaProductosAPIView,
    TiendaProductoDetalleAPIView,
    UsuarioCreateAPIView,
    AlertaPrecioCreateAPIView,
    ProductoResenasAPIView,
    ETLControlAPIView,
    ETLStatusAPIView,
    UnifiedProductsAPIView,
    UnifiedDashboardAPIView,
)

urlpatterns = [
    # Vista principal
    path('', home, name='home'),
    
    # API Core - Dashboard y estadísticas
    path('api/dashboard/', DashboardAPIView.as_view(), name='dashboard-api'),
    path('api/dashboard/unified/', UnifiedDashboardAPIView.as_view(), name='unified-dashboard-api'),
    
    # API Core - Productos
    path('api/productos/', ProductoListAPIView.as_view(), name='productos-list-api'),
    path('api/productos/<int:producto_id>/', ProductoDetalleAPIView.as_view(), name='producto-detalle-api'),
    path('api/productos/<int:producto_id>/precios/', PreciosPorProductoAPIView.as_view(), name='producto-precios-api'),
    
    # API Core - Categorías y Tiendas
    path('api/categorias/', CategoriaListAPIView.as_view(), name='categorias-list-api'),
    path('api/tiendas/', TiendaListAPIView.as_view(), name='tiendas-list-api'),
    
    # API por Tienda - Productos específicos
    path('api/productos-<str:tienda_nombre>/', TiendaProductosAPIView.as_view(), name='tienda-productos-api'),
    path('api/productos-<str:tienda_nombre>/<int:producto_id>/', TiendaProductoDetalleAPIView.as_view(), name='tienda-producto-detalle-api'),
    
    # API - Usuarios y Alertas
    path('api/usuarios/', UsuarioCreateAPIView.as_view(), name='usuario-create-api'),
    path('api/alertas/', AlertaPrecioCreateAPIView.as_view(), name='alerta-create-api'),
    
    # API - Reseñas (Compatible con IDs unificados)
    path('api/productos-dbs/<str:producto_id>/resenas/', ProductoResenasAPIView.as_view(), name='producto-resenas-dbs-api'),
    path('api/productos-preunic/<str:producto_id>/resenas/', ProductoResenasAPIView.as_view(), name='producto-resenas-preunic-api'),
    path('api/productos-maicao/<str:producto_id>/resenas/', ProductoResenasAPIView.as_view(), name='producto-resenas-maicao-api'),
    path('api/productos/<str:producto_id>/resenas/', ProductoResenasAPIView.as_view(), name='producto-resenas-api'),
    
    # API - ETL Control
    path('api/etl/control/', ETLControlAPIView.as_view(), name='etl-control-api'),
    path('api/etl/status/', ETLStatusAPIView.as_view(), name='etl-status-api'),
    
    # API - Datos Unificados
    path('api/unified/', UnifiedProductsAPIView.as_view(), name='unified-products-api'),
]