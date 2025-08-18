"""
URLs para la arquitectura MVC - Rutas limpias que usan las nuevas vistas
"""
from django.urls import path
from .views_mvc import (
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
    path('api/productos/unified/', UnifiedProductsAPIView.as_view(), name='unified-products-api'),
    
    # API Core - Categorías y Tiendas
    path('api/categorias/', CategoriaListAPIView.as_view(), name='categorias-list-api'),
    path('api/tiendas/', TiendaListAPIView.as_view(), name='tiendas-list-api'),
    
    # API Core - Precios
    path('api/precios/', PreciosPorProductoAPIView.as_view(), name='precios-producto-api'),
    
    # API por Tienda - Rutas genéricas
    path('api/<str:tienda_nombre>/productos/', TiendaProductosAPIView.as_view(), name='tienda-productos-api'),
    path('api/<str:tienda_nombre>/productos/<int:producto_id>/', TiendaProductoDetalleAPIView.as_view(), name='tienda-producto-detalle-api'),
    
    # API - Usuarios y Autenticación
    path('api/usuarios/crear/', UsuarioCreateAPIView.as_view(), name='usuario-create-api'),
    
    # API - Alertas de Precio
    path('api/alertas/crear/', AlertaPrecioCreateAPIView.as_view(), name='alerta-precio-create-api'),
    
    # API - Reseñas
    path('api/productos/<str:producto_id>/resenas/', ProductoResenasAPIView.as_view(), name='producto-resenas-api'),
    
    # API ETL - Control y Monitoreo
    path('api/etl/control/', ETLControlAPIView.as_view(), name='etl-control-api'),
    path('api/etl/status/', ETLStatusAPIView.as_view(), name='etl-status-api'),
]

# URLs específicas de tiendas para compatibilidad con frontend actual
tienda_specific_patterns = [
    # DBS
    path('api/productos-dbs/', TiendaProductosAPIView.as_view(), {'tienda_nombre': 'DBS'}, name='dbs-productos-api'),
    
    # Preunic
    path('api/productos-preunic/', TiendaProductosAPIView.as_view(), {'tienda_nombre': 'PREUNIC'}, name='preunic-productos-api'),
    path('api/productos-preunic/<int:producto_id>/', TiendaProductoDetalleAPIView.as_view(), {'tienda_nombre': 'PREUNIC'}, name='preunic-producto-detalle-api'),
    
    # Maicao
    path('api/productos-maicao/', TiendaProductosAPIView.as_view(), {'tienda_nombre': 'MAICAO'}, name='maicao-productos-api'),
    path('api/productos-maicao/<int:producto_id>/', TiendaProductoDetalleAPIView.as_view(), {'tienda_nombre': 'MAICAO'}, name='maicao-producto-detalle-api'),
]

urlpatterns += tienda_specific_patterns
