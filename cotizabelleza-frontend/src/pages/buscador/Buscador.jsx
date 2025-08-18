import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Layout,
  Row,
  Col,
  Typography,
  Select,
  Skeleton,
  Empty,
  Button
} from 'antd';
import { LinkOutlined } from '@ant-design/icons';
import { unifiedProductsService } from '../../services/unifiedApi';
import { resolveImageUrl } from '../../utils/image';
import './Buscador.css';

const { Content } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;

const Buscador = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const searchQuery = searchParams.get('search') || '';
  
  const [data, setData] = useState({ items: [] });
  const [loading, setLoading] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState(undefined);
  const [storeFilter, setStoreFilter] = useState(undefined);
  const [filterOptions, setFilterOptions] = useState({ categorias: [], tiendas: [] });
  const [filtersLoading, setFiltersLoading] = useState(true);

  // Formatear precio en formato CLP sin decimales
  const formatPriceCLP = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      maximumFractionDigits: 0
    }).format(price);
  };

  // Cargar opciones de filtros desde la API del dashboard
  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        setFiltersLoading(true);
        console.log('🔄 Cargando opciones de filtros...');
        
        const response = await fetch('http://localhost:8000/api/dashboard/');
        const dashboardData = await response.json();
        
        console.log('📊 Dashboard data:', dashboardData);
        
        const categorias = dashboardData.categorias_disponibles?.map(cat => cat.nombre) || [];
        const tiendas = dashboardData.tiendas_disponibles?.map(tienda => tienda.nombre) || [];
        
        console.log('✅ Filtros cargados:', { categorias, tiendas });
        setFilterOptions({ categorias, tiendas });
      } catch (error) {
        console.error('❌ Error loading filter options:', error);
        // Fallback estático
        console.log('🔄 Usando fallback estático...');
        setFilterOptions({ 
          categorias: ['maquillaje', 'skincare'], 
          tiendas: ['DBS', 'PREUNIC', 'MAICAO'] 
        });
      } finally {
        setFiltersLoading(false);
      }
    };
    
    loadFilterOptions();
  }, []);

  // Cargar productos unificados
  useEffect(() => {
    const fetchData = async () => {
      if (!searchQuery.trim()) {
        setData({ items: [] });
        return;
      }

      try {
        setLoading(true);
        
        // Buscar en productos unificados
        const results = await unifiedProductsService.searchUnifiedProducts(searchQuery);
        
        // Convertir a formato de listing
        const listingProducts = unifiedProductsService.convertToListingFormat({ productos: results });
        
        setData({ items: listingProducts });
        
      } catch (error) {
        console.error('Error loading unified products:', error);
        setData({ items: [] });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [searchQuery]);

  // Filtrar productos por categoría y tienda
  const filteredProducts = useMemo(() => {
    let filtered = data.items || [];

    // Filtro por categoría
    if (categoryFilter && categoryFilter !== undefined) {
      filtered = filtered.filter(product => product.categoria === categoryFilter);
    }

    // Filtro por tienda
    if (storeFilter && storeFilter !== undefined) {
      filtered = filtered.filter(product => 
        product.tiendas_disponibles?.includes(storeFilter.toUpperCase())
      );
    }

    return filtered;
  }, [data.items, categoryFilter, storeFilter]);

  // Obtener categorías únicas (usar API + productos cargados)
  const categories = useMemo(() => {
    const fromProducts = new Set((data.items || []).map(p => p.categoria).filter(Boolean));
    const fromAPI = new Set(filterOptions.categorias);
    const result = Array.from(new Set([...fromAPI, ...fromProducts]));
    console.log('🏷️ Categories final:', result);
    return result;
  }, [data.items, filterOptions.categorias]);

  // Obtener tiendas únicas (usar API + productos cargados)
  const stores = useMemo(() => {
    const fromProducts = new Set();
    (data.items || []).forEach(product => {
      product.tiendas_disponibles?.forEach(store => fromProducts.add(store));
    });
    const fromAPI = new Set(filterOptions.tiendas);
    const result = Array.from(new Set([...fromAPI, ...fromProducts]));
    console.log('🏪 Stores final:', result);
    return result;
  }, [data.items, filterOptions.tiendas]);

  if (!searchQuery.trim()) {
    return (
      <Layout style={{ minHeight: '400px', background: '#f5f5f5' }}>
        <Content style={{ padding: '50px 24px' }}>
          <div style={{ textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
            <Title level={3}>🔍 Buscar productos</Title>
            <Text type="secondary" style={{ fontSize: '16px' }}>
              Usa la barra de búsqueda en la parte superior para encontrar productos de belleza en DBS, Preunic y Maicao.
            </Text>
          </div>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '400px', background: '#f5f5f5' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          
          {/* Filtros */}
          <div style={{ marginBottom: '24px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <Select
              placeholder="Categoría"
              style={{ width: 200 }}
              value={categoryFilter}
              onChange={setCategoryFilter}
              allowClear
              loading={filtersLoading}
              disabled={filtersLoading}
            >
              {categories.map(cat => (
                <Option key={cat} value={cat}>{cat}</Option>
              ))}
            </Select>
            
            <Select
              placeholder="Tienda"
              style={{ width: 200 }}
              value={storeFilter}
              onChange={setStoreFilter}
              allowClear
              loading={filtersLoading}
              disabled={filtersLoading}
            >
              {stores.map(store => (
                <Option key={store} value={store}>{store.toUpperCase()}</Option>
              ))}
            </Select>
          </div>

          {/* Resultados */}
          {loading ? (
            <div className="products-grid">
              {[...Array(6)].map((_, index) => (
                <Col key={index} xs={24} sm={12} md={8} lg={6}>
                  <Skeleton active />
                </Col>
              ))}
            </div>
          ) : filteredProducts.length > 0 ? (
            <>
              <div style={{ marginBottom: '16px' }}>
                <Text type="secondary">
                  {filteredProducts.length} producto{filteredProducts.length !== 1 ? 's' : ''} encontrado{filteredProducts.length !== 1 ? 's' : ''} para "{searchQuery}"
                </Text>
              </div>
              
              <div className="products-grid">
                {filteredProducts.map((product) => (
                  <div 
                    key={product.product_id}
                    className="product-card" 
                    onClick={() => navigate(`/detalle-producto/${encodeURIComponent(product.product_id)}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="product-image">
                      <img 
                        src={product.imagen_url || '/image-not-found.png'} 
                        alt={product.nombre}
                        onError={(e) => {
                          e.target.src = '/image-not-found.png';
                        }}
                      />
                    </div>
                    <div className="product-info">
                      <Text className="product-brand">{product.marca}</Text>
                      <Text className="product-name">{product.nombre}</Text>
                      <Text className="product-price">
                        {product.tiendasCount > 1 ? 'Desde ' : ''}{formatPriceCLP(product.precio_min || 0)}
                      </Text>
                      <Button 
                        type="primary" 
                        size="small" 
                        className="view-more-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/detalle-producto/${encodeURIComponent(product.product_id)}`);
                        }}
                      >
                        Ver más <LinkOutlined />
                      </Button>
                      <div className="product-stores">
                        <Text type="secondary">
                          {product.tiendasCount > 1 
                            ? `${product.tiendasCount} tiendas` 
                            : `Disponible en: ${product.tiendas_disponibles?.join(', ') || 'N/A'}`
                          }
                        </Text>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <Empty 
              description={`No se encontraron productos para "${searchQuery}"`}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
    </div>
      </Content>
    </Layout>
  );
};

export default Buscador; 
