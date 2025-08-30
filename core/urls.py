"""
URLs para CotizaBelleza - Arquitectura MVT/MVC
"""
from django.urls import path
from .views import (
    home,
    DashboardAPIView,
    UnifiedProductsAPIView,
    TiendaProductosAPIView,
    ProductoResenasAPIView,
    ProductosFiltradosAPIView,
    AlertasAPIView,
    EmailVerificationAPIView,
    UnsubscribeAPIView,
)

urlpatterns = [
    # Vista principal
    path('', home, name='home'),
    
    # Dashboard API
    path('api/dashboard/', DashboardAPIView.as_view(), name='dashboard-api'),
    
    # Productos unificados
    path('api/unified/', UnifiedProductsAPIView.as_view(), name='unified-products-api'),
    
    # Productos filtrados
    path('api/productos-filtrados/', ProductosFiltradosAPIView.as_view(), name='productos-filtrados-api'),
    
    # Productos por tienda
    path('api/productos-<str:tienda_nombre>/', TiendaProductosAPIView.as_view(), name='tienda-productos-api'),
    
    # Reseñas de productos (compatible con todas las tiendas)
    path('api/productos-dbs/<str:producto_id>/resenas/', ProductoResenasAPIView.as_view(), {'tienda_nombre': 'dbs'}, name='resenas-dbs-api'),
    path('api/productos-preunic/<str:producto_id>/resenas/', ProductoResenasAPIView.as_view(), {'tienda_nombre': 'preunic'}, name='resenas-preunic-api'),
    path('api/productos-maicao/<str:producto_id>/resenas/', ProductoResenasAPIView.as_view(), {'tienda_nombre': 'maicao'}, name='resenas-maicao-api'),
    path('api/productos/<str:producto_id>/resenas/', ProductoResenasAPIView.as_view(), {'tienda_nombre': 'general'}, name='resenas-general-api'),
    
    # Alertas de precio
    path('api/alertas/', AlertasAPIView.as_view(), name='alertas-api'),
    path('api/alertas/<int:alerta_id>/', AlertasAPIView.as_view(), name='alerta-detail-api'),
    
    # Verificación de emails
    path('api/email/verify/', EmailVerificationAPIView.as_view(), name='email-verify-api'),
    path('api/email/verify/<str:token>/', EmailVerificationAPIView.as_view(), name='email-verify-token-api'),
    
    # Unsubscribe de emails
    path('api/email/unsubscribe/<str:token>/', UnsubscribeAPIView.as_view(), name='email-unsubscribe-api'),
    

]