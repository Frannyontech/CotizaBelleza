import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Typography, Select, Empty, Button } from 'antd';
import { LinkOutlined } from '@ant-design/icons';
import { unifiedProductsService } from '../services/unifiedApi';
import './DBSProductos.css';

const { Content } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;

const DBSProductos = () => {
  const navigate = useNavigate();
  const [data, setData] = useState({ items: [] });
  const [loading, setLoading] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [searchFilter, setSearchFilter] = useState('');

  // Formatear precio en formato CLP sin decimales
  const formatPriceCLP = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      maximumFractionDigits: 0
    }).format(price);
  };

  // Cargar productos al montar el componente
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Obtener productos de DBS únicamente
        const dbsProducts = await unifiedProductsService.getProductsByStore('dbs');
        
        // Convertir a formato de listing
        const listingProducts = unifiedProductsService.convertToListingFormat({ productos: dbsProducts });
        
        setData({ items: listingProducts });
        
      } catch (error) {
        console.error('Error loading DBS products:', error);
        setData({ items: [] });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Filtrar productos por categoría y búsqueda
  const filteredProducts = useMemo(() => {
    let filtered = data.items || [];

    // Filtro por categoría
    if (categoryFilter) {
      filtered = filtered.filter(product => product.categoria === categoryFilter);
    }

    // Filtro por búsqueda en nombre o marca
    if (searchFilter.trim()) {
      const searchLower = searchFilter.toLowerCase();
      filtered = filtered.filter(product => 
        product.nombre?.toLowerCase().includes(searchLower) ||
        product.marca?.toLowerCase().includes(searchLower)
      );
    }

    return filtered;
  }, [data.items, categoryFilter, searchFilter]);

  // Obtener categorías únicas
  const categories = useMemo(() => {
    const cats = new Set((data.items || []).map(p => p.categoria).filter(Boolean));
    return Array.from(cats);
  }, [data.items]);

  return (
    <Layout style={{ minHeight: '400px', background: '#f5f5f5' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          
          {/* Header */}
          <div style={{ marginBottom: '24px', textAlign: 'center' }}>
            <Title level={2}>🛍️ Productos DBS</Title>
            <Text type="secondary" style={{ fontSize: '16px' }}>
              Encuentra los mejores productos de belleza en DBS
            </Text>
          </div>

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
              placeholder="Buscar productos..."
              style={{ minWidth: 250, flex: 1 }}
              value={searchFilter}
              onChange={setSearchFilter}
              allowClear
              showSearch
              filterOption={false}
              notFoundContent={null}
            >
              {(data.items || []).map(product => (
                <Option key={product.product_id} value={product.nombre}>
                  {product.nombre}
                </Option>
              ))}
            </Select>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Text>Cargando productos de DBS...</Text>
            </div>
          ) : filteredProducts.length > 0 ? (
            <>
              <div style={{ marginBottom: '16px' }}>
                <Text type="secondary">
                  {filteredProducts.length} producto{filteredProducts.length !== 1 ? 's' : ''} de DBS
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
                        {formatPriceCLP(product.precio_min || 0)}
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
                          🛍️ Disponible en DBS
                        </Text>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <Empty 
              description="No se encontraron productos de DBS"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </div>
      </Content>
    </Layout>
  );
};

export default DBSProductos;
