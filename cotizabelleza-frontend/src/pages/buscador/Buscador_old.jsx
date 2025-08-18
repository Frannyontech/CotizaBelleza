import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
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
import { getDefaultThumbnail, resolveImageUrl } from '../../utils/image';
import { addCanonicalId, bucketize, toListingCards } from '../../utils/canon';
import './Buscador.css';

const { Content } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;


const Buscador = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState({ items: [] });
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('price_asc');

  const searchQuery = searchParams.get('search') || searchParams.get('q') || '';

  // Cargar productos cuando hay búsqueda
  useEffect(() => {
    if (!searchQuery) {
      setData({ items: [] });
      setLoading(false);
      return;
    }

    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const [dbsResponse, preunicResponse, maicaoResponse] = await Promise.all([
          fetch('http://localhost:8000/api/productos-dbs/'),
          fetch('http://localhost:8000/api/productos-preunic/'),
          fetch('http://localhost:8000/api/productos-maicao/')
        ]);

        const dbsData = await dbsResponse.json();
        const preunicData = await preunicResponse.json();
        const maicaoData = await maicaoResponse.json();

        const dbsProducts = (dbsData.productos || dbsData || []).map(product => ({
          ...product,
          fuente: 'dbs',
          tienda: 'DBS'
        }));
        
        const preunicProducts = (preunicData.productos || preunicData || []).map(product => ({
          ...product,
          fuente: 'preunic',
          tienda: 'PREUNIC'
        }));
        
        const maicaoProducts = (maicaoData.productos || maicaoData || []).map(product => ({
          ...product,
          fuente: 'maicao',
          tienda: 'MAICAO'
        }));
        
        const allProducts = [...dbsProducts, ...preunicProducts, ...maicaoProducts];

        // Filtrar por búsqueda
        const filteredProducts = allProducts.filter(product => 
          (product.nombre || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
          (product.marca || '').toLowerCase().includes(searchQuery.toLowerCase())
        );

        setData({ items: filteredProducts });
        
      } catch (error) {
        console.error('Error loading data:', error);
        setError(error.message || 'Error al cargar los datos');
        setData({ items: [] });
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [searchQuery]);

  // Procesar datos
  const cards = useMemo(() => {
    if (!data.items.length) return [];
    
    const withId = addCanonicalId(data.items || []);
    const buckets = bucketize(withId);
    const listing = toListingCards(buckets);
    
    return listing.sort((a, b) => {
      switch (sortBy) {
        case 'price_asc':
          return (a.precioMin || 0) - (b.precioMin || 0);
        case 'price_desc':
          return (b.precioMin || 0) - (a.precioMin || 0);
        case 'stores_desc':
          return (b.tiendasCount || 0) - (a.tiendasCount || 0);
        case 'stores_asc':
          return (a.tiendasCount || 0) - (b.tiendasCount || 0);
        default:
          return 0;
      }
    });
  }, [data.items, sortBy]);

  const formatPriceCLP = (precio) => {
    return `$${Number(precio || 0).toLocaleString('es-CL')}`;
  };

  const comparisionProducts = cards.filter(p => p.tiendasCount > 1);
  const singleProducts = cards.filter(p => p.tiendasCount === 1);



  return (
    <Content style={{ padding: '24px' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>


        {/* Resultados */}
        {searchQuery && (
          <Row gutter={[24, 24]}>
            <Col xs={24}>
              {/* Header de resultados */}
              <Row justify="space-between" align="middle" style={{ marginBottom: 24, marginTop: 16 }}>
                <Col>
                  <Title level={4} style={{ margin: 0 }}>
                    Resultados para "{searchQuery}"
                  </Title>
                  <Text type="secondary">
                    {loading ? 'Buscando...' : (
                      <>
                        {comparisionProducts.length > 0 && (
                          `${comparisionProducts.length} productos con comparación • `
                        )}
                        {singleProducts.length > 0 && (
                          `${singleProducts.length} productos individuales`
                        )}
                        {cards.length === 0 && !loading && 'No se encontraron productos'}
                      </>
                    )}
                  </Text>
                </Col>
                {cards.length > 0 && (
                  <Col>
                    <Select
                      value={sortBy}
                      onChange={setSortBy}
                      style={{ width: 220 }}
                      placeholder="Ordenar por"
                    >
                      <Option value="price_asc">Precio: menor a mayor</Option>
                      <Option value="price_desc">Precio: mayor a menor</Option>
                      <Option value="stores_desc">Más tiendas primero</Option>
                      <Option value="stores_asc">Menos tiendas primero</Option>
                    </Select>
                  </Col>
                )}
              </Row>

              {/* Estados de carga y error */}
              {loading && (
                <Row gutter={[16, 16]}>
                  {[1, 2, 3, 4].map(i => (
                    <Col xs={24} sm={12} md={8} lg={6} key={i}>
                      <Skeleton.Image style={{ width: '100%', height: 200 }} />
                      <Skeleton active paragraph={{ rows: 2 }} />
                    </Col>
                  ))}
                </Row>
              )}

              {error && (
                <Empty description={`Error: ${error}`} />
              )}

              {/* Productos con comparación */}
              {!loading && !error && comparisionProducts.length > 0 && (
                <div style={{ marginBottom: 32 }}>
                  <Title level={5} style={{ color: '#52c41a', marginBottom: 16 }}>
                    🆚 Comparación de Precios ({comparisionProducts.length})
                  </Title>
                  <div className="products-grid">
                    <Row gutter={[16, 16]}>
                    {comparisionProducts.map(card => (
                      <Col xs={24} sm={12} md={8} lg={6} key={card.product_id}>
                        <div 
                          className="product-card" 
                          onClick={() => navigate(`/detalle-producto/${encodeURIComponent(card.product_id)}`)}
                          style={{ cursor: 'pointer' }}
                        >
                          <div className="product-image">
                            <img 
                              src={card.imagen || getDefaultThumbnail()} 
                              alt={card.nombre}
                              onError={(e) => {
                                e.target.src = getDefaultThumbnail();
                              }}
                            />
                          </div>
                          <div className="product-info">
                            <Text className="product-brand">{card.marca || ''}</Text>
                            <Text className="product-name">{card.nombre}</Text>
                            <Text className="product-price">
                              Desde {formatPriceCLP(card.precioMin)}
                            </Text>
                            <Button 
                              type="primary" 
                              size="small" 
                              className="view-more-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/detalle-producto/${encodeURIComponent(card.product_id)}`);
                              }}
                            >
                              Ver más <LinkOutlined />
                            </Button>
                            <div className="product-stores">
                              <Text type="secondary">Disponible en:</Text>
                              <Text className="store-list">
                                {card.tiendas ? card.tiendas.join(', ') : `${card.tiendasCount} tiendas`}
                              </Text>
                            </div>
                          </div>
                        </div>
                      </Col>
                    ))}
                                      </Row>
                  </div>
                </div>
              )}

              {/* Productos individuales */}
              {!loading && !error && singleProducts.length > 0 && (
                <div>
                  <Title level={5} style={{ color: '#1890ff', marginBottom: 16 }}>
                    🛍️ Productos Individuales ({singleProducts.length})
                  </Title>
                  <div className="products-grid">
                    <Row gutter={[16, 16]}>
                      {singleProducts.map(card => (
                      <Col xs={24} sm={12} md={8} lg={6} key={card.product_id}>
                        <div 
                          className="product-card" 
                          onClick={() => navigate(`/detalle-producto/${encodeURIComponent(card.product_id)}`)}
                          style={{ cursor: 'pointer' }}
                        >
                          <div className="product-image">
                            <img 
                              src={card.imagen || getDefaultThumbnail()} 
                              alt={card.nombre}
                              onError={(e) => {
                                e.target.src = getDefaultThumbnail();
                              }}
                            />
                          </div>
                          <div className="product-info">
                            <Text className="product-brand">{card.marca || ''}</Text>
                            <Text className="product-name">{card.nombre}</Text>
                            <Text className="product-price">
                              {formatPriceCLP(card.precioMin)}
                            </Text>
                            <Button 
                              type="primary" 
                              size="small" 
                              className="view-more-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/detalle-producto/${encodeURIComponent(card.product_id)}`);
                              }}
                            >
                              Ver más <LinkOutlined />
                            </Button>
                            <div className="product-stores">
                              <Text type="secondary">Disponible en:</Text>
                              <Text className="store-list">
                                {card.tiendas ? card.tiendas.join(', ') : `${card.tiendasCount} tienda${card.tiendasCount > 1 ? 's' : ''}`}
                              </Text>
                            </div>
                          </div>
                        </div>
                      </Col>
                    )                    )}
                    </Row>
                  </div>
                </div>
              )}

              {/* Sin resultados */}
              {!loading && !error && searchQuery && cards.length === 0 && (
                <Empty 
                  description="No se encontraron productos que coincidan con tu búsqueda"
                  style={{ marginTop: 48 }}
                />
              )}
            </Col>
          </Row>
        )}

        {/* Estado inicial sin búsqueda */}
        {!searchQuery && (
          <div style={{ textAlign: 'center', marginTop: 80 }}>
            <Title level={2} style={{ color: '#8c8c8c', marginBottom: 16 }}>
              Buscar Productos de Belleza
            </Title>
            <Text type="secondary" style={{ fontSize: 16 }}>
              Usa la barra de búsqueda en la parte superior para encontrar productos
            </Text>
            <div style={{ marginTop: 32 }}>
              <Empty 
                description=""
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            </div>
          </div>
        )}
    </div>
    </Content>
  );
};

export default Buscador; 