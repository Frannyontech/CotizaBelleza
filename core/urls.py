from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.DashboardAPIView.as_view(), name='dashboard'),
    path('productos/', views.ProductoListAPIView.as_view(), name='productos-list'),
    path('productos-dbs/', views.DBSProductosAPIView.as_view(), name='productos-dbs'),
    path('categorias/', views.CategoriaListAPIView.as_view(), name='categorias-list'),
    path('tiendas/', views.TiendaListAPIView.as_view(), name='tiendas-list'),
    path('precios/', views.PreciosPorProductoAPIView.as_view(), name='precios-producto'),
    path('usuarios/', views.UsuarioCreateAPIView.as_view(), name='usuario-create'),
] 