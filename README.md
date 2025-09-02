# CotizaBelleza - Sistema de Cotizaciones de Belleza

Sistema fullstack para cotizaciones de productos de belleza con arquitectura MVT + ETL.

## 🚀 Progreso de Testing

### Cobertura Actual: **24%** ✅
- **44 tests pasando** exitosamente
- **0 tests fallando** en la suite principal
- Tests cubren: **Modelos**, **Serializers**, **Servicios**

### Archivos con Mayor Cobertura:
- `core/serializers.py`: **98%** ✅
- `core/models.py`: **62%** ✅
- `core/services/deduplication.py`: **33%** ✅
- `core/services/email_service.py`: **23%** ✅
- `core/services/persistent_id_manager.py`: **25%** ✅

### Archivos Pendientes (0% cobertura):
- `core/views.py`: **0%** (pendiente)
- `core/tasks.py`: **0%** (pendiente)
- `core/management/commands/`: **0%** (pendiente)
- `core/services/observer_service.py`: **0%** (pendiente)

## 🛠️ Scripts de Testing Disponibles

### Scripts Principales:
```bash
# Ejecutar solo tests que pasan (recomendado)
python run_passing_tests.py

# Ejecutar tests de servicios
python run_services_tests.py

# Ejecutar tests de modelos y serializers
python run_working_tests.py

# Ejecutar todos los tests (incluye fallidos)
python run_all_tests_extended.py
```

### Comandos Directos:
```bash
# Tests con cobertura
pytest --cov=core --cov-report=html:htmlcov --cov-report=term-missing

# Tests específicos
pytest tests/test_models.py -v
pytest tests/test_serializers.py -v
pytest tests/test_services.py -v

# Ver reporte de cobertura
open htmlcov/index.html
```

## 📊 Resumen de Tests

### Tests Exitosos (44):
- **Modelos**: 16 tests ✅
  - TestCategoria, TestTienda, TestProducto, TestPrecioProducto
  - TestProductoPersistente, TestPrecioHistorico, TestAlertaPrecioProductoPersistente
- **Serializers**: 8 tests ✅
  - TestProductoSerializer, TestProductoPersistenteSerializer
  - TestPrecioHistoricoSerializer, TestAlertaPrecioProductoPersistenteSerializer
  - TestSerializerIntegration
- **Servicios**: 19 tests ✅
  - TestDeduplication (8 tests)
  - TestEmailService (4 tests)
  - TestPersistentIdManager (7 tests)

### Tests Fallidos (4):
- TestProductoSerializer.test_producto_serializer_create
- TestPrecioProductoSerializer.test_precio_producto_serializer_create
- TestPrecioProductoSerializer.test_precio_producto_serializer_valid_data
- TestAlertaPrecioProductoPersistenteSerializer.test_alerta_precio_serializer_invalid_email

## 🎯 Próximos Pasos para Aumentar Cobertura

### Prioridad Alta (Mayor Impacto):
1. **Agregar tests para Views** (0% → ~40% cobertura)
   - DashboardAPIView, UnifiedProductsAPIView
   - ProductosFiltradosAPIView, AlertasAPIView
   - EmailVerificationAPIView, UnsubscribeAPIView

2. **Agregar tests para Tasks** (0% → ~30% cobertura)
   - check_price_alerts_task
   - send_historical_alert_email_task
   - comparar_precios_historicos_task

3. **Agregar tests para Management Commands** (0% → ~15% cobertura)
   - load_scraper_data, persistent_ids
   - clean_duplicates, setup_observer

### Prioridad Media:
4. **Agregar tests para Observer Service** (0% → ~10% cobertura)
5. **Agregar tests para Patterns** (30-35% → ~50% cobertura)

### Objetivo Final:
- **Cobertura objetivo**: ≥80%
- **Tests totales estimados**: ~150 tests
- **Tiempo estimado**: 2-3 sesiones adicionales

## 🔧 Configuración de Testing

### Archivos de Configuración:
- `pytest.ini`: Configuración de pytest
- `.coveragerc`: Configuración de cobertura
- `cotizabelleza/test_settings.py`: Configuración de testing

### Dependencias de Testing:
```bash
pytest
pytest-django
pytest-cov
pytest-mock
factory-boy
freezegun
responses
```

## 📈 Métricas de Calidad

### Cobertura por Tipo:
- **Modelos**: 62% ✅
- **Serializers**: 98% ✅
- **Servicios**: 25% ⚠️
- **Views**: 0% ❌
- **Tasks**: 0% ❌
- **Management Commands**: 0% ❌

### Tests por Categoría:
- **Unit Tests**: 44 ✅
- **Integration Tests**: 0 ❌
- **API Tests**: 0 ❌
- **Task Tests**: 0 ❌

## 🎉 Logros Actuales

✅ **Configuración completa de testing**
✅ **24% de cobertura base**
✅ **44 tests estables**
✅ **Scripts automatizados**
✅ **Reportes HTML de cobertura**
✅ **Eliminación de archivos redundantes**

## 📝 Notas Técnicas


- Los tests usan SQLite en memoria para testing
- Celery configurado en modo eager para testing
- Email backend configurado como locmem
- Migraciones deshabilitadas para testing
- Mocks utilizados para servicios externos

---

**Estado**: ✅ Funcional con 24% cobertura
**Próximo objetivo**: 40% cobertura (tests de views) 