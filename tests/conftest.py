import pytest
from django.conf import settings
from django.test import override_settings
from factory.django import DjangoModelFactory
from factory import SubFactory


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Configuración de base de datos para tests"""
    with django_db_blocker.unblock():
        pass


@pytest.fixture
def db_access_without_rollback_and_truncate(django_db_setup, django_db_blocker):
    """Permite acceso a DB sin rollback para tests de integración"""
    django_db_blocker.unblock()
    yield
    django_db_blocker.restore()


# Factory functions to avoid model resolution during import
def get_categoria_factory():
    from core.models import Categoria
    
    class CategoriaFactory(DjangoModelFactory):
        class Meta:
            model = Categoria
        
        nombre = "Maquillaje"
        descripcion = "Productos de maquillaje"
    
    return CategoriaFactory


def get_tienda_factory():
    from core.models import Tienda
    
    class TiendaFactory(DjangoModelFactory):
        class Meta:
            model = Tienda
        
        nombre = "Tienda Test"
        url_base = "https://test.com"
        activa = True
    
    return TiendaFactory


def get_producto_persistente_factory():
    from core.models import ProductoPersistente
    
    class ProductoPersistenteFactory(DjangoModelFactory):
        class Meta:
            model = ProductoPersistente
        
        nombre_original = "Producto Test"
        nombre_normalizado = "producto test"
        marca = "Marca Test"
        categoria = "Maquillaje"
        hash_unico = "test_hash_123"
        internal_id = "test-123"
    
    return ProductoPersistenteFactory


def get_precio_historico_factory():
    from core.models import PrecioHistorico
    
    class PrecioHistoricoFactory(DjangoModelFactory):
        class Meta:
            model = PrecioHistorico
        
        producto = SubFactory(get_producto_persistente_factory())
        tienda = "Tienda Test"
        precio = 100.00
        disponible = True
        url_producto = "https://test.com/producto"
    
    return PrecioHistoricoFactory


def get_alerta_precio_factory():
    from core.models import AlertaPrecioProductoPersistente
    
    class AlertaPrecioProductoPersistenteFactory(DjangoModelFactory):
        class Meta:
            model = AlertaPrecioProductoPersistente
        
        producto = SubFactory(get_producto_persistente_factory())
        email = "test@example.com"
        precio_inicial = 100.00
        activa = True
    
    return AlertaPrecioProductoPersistenteFactory


# Fixtures de datos
@pytest.fixture
def categoria():
    return get_categoria_factory()()


@pytest.fixture
def tienda():
    return get_tienda_factory()()


@pytest.fixture
def producto():
    return get_producto_persistente_factory()()


@pytest.fixture
def precio_historico(producto):
    factory = get_precio_historico_factory()
    return factory(producto=producto)


@pytest.fixture
def alerta_precio(producto):
    factory = get_alerta_precio_factory()
    return factory(producto=producto)


@pytest.fixture
def multiple_productos():
    """Crea múltiples productos para tests de listado"""
    factory = get_producto_persistente_factory()
    productos = []
    for i in range(5):
        producto = factory(
            nombre_original=f"Producto {i}",
            nombre_normalizado=f"producto {i}",
            marca=f"Marca {i}",
            categoria="Maquillaje",
            hash_unico=f"test_hash_{i}"
        )
        productos.append(producto)
    return productos


@pytest.fixture
def multiple_precios(producto):
    """Crea múltiples precios históricos para un producto"""
    factory = get_precio_historico_factory()
    precios = []
    for i in range(3):
        precio = factory(
            producto=producto,
            precio=100.00 + (i * 10),
            disponible=True
        )
        precios.append(precio)
    return precios


# Configuración de Celery para tests
@pytest.fixture(autouse=True)
def celery_settings():
    """Configura Celery para ejecutar tareas de forma síncrona en tests"""
    with override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    ):
        yield


@pytest.fixture
def mock_responses():
    """Fixture para mock de respuestas HTTP"""
    import responses
    with responses.RequestsMock() as rsps:
        yield rsps

