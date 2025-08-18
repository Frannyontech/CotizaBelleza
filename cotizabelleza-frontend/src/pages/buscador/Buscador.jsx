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
  const [categoryFilter, setCategoryFilter] = useState('');
  const [storeFilter, setStoreFilter] = useState('');

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
        const listingProducts = unifiedProductsService.convertToListingFormat(results);
        
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
    if (categoryFilter) {
      filtered = filtered.filter(product => product.categoria === categoryFilter);
    }

    // Filtro por tienda
    if (storeFilter) {
      filtered = filtered.filter(product => 
        product.tiendas?.includes(storeFilter.toLowerCase())
      );
    }

    return filtered;
  }, [data.items, categoryFilter, storeFilter]);

  // Obtener categorías únicas
  const categories = useMemo(() => {
    const cats = new Set((data.items || []).map(p => p.categoria).filter(Boolean));
    return Array.from(cats);
  }, [data.items]);

  // Obtener tiendas únicas
  const stores = useMemo(() => {
    const storeSet = new Set();
    (data.items || []).forEach(product => {
      product.tiendas?.forEach(store => storeSet.add(store));
    });
    return Array.from(storeSet);
  }, [data.items]);

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
              placeholder="Filtrar por categoría"
              style={{ width: 200 }}
              value={categoryFilter}
              onChange={setCategoryFilter}
              allowClear
            >
              {categories.map(cat => (
                <Option key={cat} value={cat}>{cat}</Option>
              ))}
            </Select>
            
            <Select
              placeholder="Filtrar por tienda"
              style={{ width: 200 }}
              value={storeFilter}
              onChange={setStoreFilter}
              allowClear
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
                <Row gutter={[16, 16]}>
                  {filteredProducts.map((card) => (
                    <Col key={card.product_id} xs={24} sm={12} md={8} lg={6}>
                      <div 
                        className="product-card" 
                        onClick={() => navigate(`/detalle-producto/${encodeURIComponent(card.product_id)}`)}
                        style={{ cursor: 'pointer' }}
                      >
                        <div className="product-image">
                          <img
                            src={resolveImageUrl({ imagen_url: card.imagen })}
                            alt={card.nombre}
                            onError={(e) => {
                              e.target.src = '/image-not-found.png';
                            }}
                          />
                        </div>
                        
                        <div className="product-info">
                          <div className="product-brand">{card.marca}</div>
                          <div className="product-name">{card.nombre}</div>
                          <div className="product-price">
                            {card.tiendasCount > 1 ? 'Desde ' : ''}${card.precioMin?.toLocaleString('es-CL')}
                          </div>
                          
                          <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Button 
                              type="primary" 
                              size="small" 
                              className="view-more-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/detalle-producto/${encodeURIComponent(card.product_id)}`);
                              }}
                            >
                              Ver más
                            </Button>
                            
                            <div className="product-stores">
                              {card.tiendasCount > 1 ? (
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                  {card.tiendasCount} tiendas
                                </Text>
                              ) : (
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                  {card.tiendas?.join(', ').toUpperCase()}
                                </Text>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </Col>
                  ))}
                </Row>
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
