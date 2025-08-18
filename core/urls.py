from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.DashboardAPIView.as_view(), name='dashboard'),
    path('productos/', views.ProductoListAPIView.as_view(), name='productos-list'),
    path('productos-dbs/', views.DBSProductosAPIView.as_view(), name='productos-dbs'),
    path('productos-preunic/', views.PREUNICProductosAPIView.as_view(), name='productos-preunic'),
    path('productos-preunic/<str:producto_id>/', views.PREUNICProductoDetalleAPIView.as_view(), name='producto-preunic-detalle'),
    path('productos-maicao/', views.MAICAOProductosAPIView.as_view(), name='productos-maicao'),
    path('productos-maicao/<str:producto_id>/', views.MAICAOProductoDetalleAPIView.as_view(), name='producto-maicao-detalle'),
    path('productos-dbs/<int:producto_id>/', views.ProductoDetalleAPIView.as_view(), name='producto-detalle'),
    path('categorias/', views.CategoriaListAPIView.as_view(), name='categorias-list'),
    path('tiendas/', views.TiendaListAPIView.as_view(), name='tiendas-list'),
    path('precios/', views.PreciosPorProductoAPIView.as_view(), name='precios-producto'),
    path('usuarios/', views.UsuarioCreateAPIView.as_view(), name='usuario-create'),
    path('alertas-precio/', views.AlertaPrecioCreateAPIView.as_view(), name='alerta-precio-create'),
    path('productos-dbs/<str:producto_id>/resenas/', views.ProductoResenasAPIView.as_view(), name='producto-resenas'),
    path('unified/', views.UnifiedProductsAPIView.as_view(), name='unified-products'),
    path('unified/dashboard/', views.UnifiedDashboardAPIView.as_view(), name='unified-dashboard'),
] 