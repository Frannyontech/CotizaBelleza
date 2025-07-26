from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('productos/', views.ProductoListAPIView.as_view(), name='productos-list'),
    path('precios/', views.PreciosPorProductoAPIView.as_view(), name='precios-producto'),
    path('usuarios/', views.UsuarioCreateAPIView.as_view(), name='usuario-create'),
] 