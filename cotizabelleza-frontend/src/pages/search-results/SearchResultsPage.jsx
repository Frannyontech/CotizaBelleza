import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { 
  Layout, 
  Row, 
  Col, 
  Card, 
  Typography, 
  Select, 
  Slider, 
  Checkbox, 
  Switch,
  Image,
  Skeleton,
  Empty,
  Pagination,
  Collapse
} from 'antd';

const SearchResultsPage = () => {
  console.log('SearchResultsPage component mounted - SIMPLIFIED VERSION');
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(12);
  const [favorites, setFavorites] = useState([]);
  const [sortBy, setSortBy] = useState('price_asc');
  
  // Estados de filtros
  const [priceRange, setPriceRange] = useState([0, 100000]);
  const [selectedStores, setSelectedStores] = useState([]);
  const [selectedAvailability, setSelectedAvailability] = useState([]);
  
  // Destructuring de componentes Ant Design
  const { Content } = Layout;
  const { Title, Text, Paragraph } = Typography;
  const { Option } = Select;
  
  console.log('Search params:', searchParams.toString());

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const searchTerm = searchParams.get('search') || '';
        console.log('Searching for:', searchTerm);
        
        // Buscar en ambas tiendas en paralelo
        const [dbsResponse, preunicResponse] = await Promise.all([
          fetch(`/api/productos-dbs/?search=${encodeURIComponent(searchTerm)}`),
          fetch(`/api/productos-preunic/?search=${encodeURIComponent(searchTerm)}`)
        ]);
        
        const dbsData = await dbsResponse.json();
        const preunicData = await preunicResponse.json();
        
        console.log('DBS API Response:', dbsData);
        console.log('Preunic API Response:', preunicData);
        
        // Combinar productos de ambas tiendas
        const dbsProducts = (dbsData.productos || dbsData || []).map(product => ({
          ...product,
          tienda: 'DBS'
        }));
        
        const preunicProducts = (preunicData.productos || preunicData || []).map(product => ({
          ...product,
          tienda: 'PREUNIC'
        }));
        
        const allProducts = [...dbsProducts, ...preunicProducts];
        console.log('Combined products data:', allProducts);
        setProducts(allProducts);
        
      } catch (error) {
        console.error('Error loading data:', error);
        setError(error.message || 'Error al cargar los datos');
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [searchParams]);

  // Formatear precio
  const formatPrice = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP'
    }).format(price);
  };

  // Obtener imagen del producto
  const getImageUrl = (product) => {
    if (!product.imagen_url || product.imagen_url === '') {
      return '/image-not-found.png';
    }
    
    if (product.imagen_url.startsWith('http')) {
      return product.imagen_url;
    }
    
    if (product.imagen_url.startsWith('/')) {
      return `https://dbs.cl${product.imagen_url}`;
    }
    
    return '/image-not-found.png';
  };

  // Filtros como opciones para checkboxes
  const storeOptions = [
    { label: '🛍️ DBS', value: 'DBS' },
    { label: '🛒 Preunic', value: 'PREUNIC' }
  ];

  // Filtrar y ordenar productos
  const filteredProducts = products.filter(product => {
    const price = product.precio || product.precio_min || 0;
    
    // Filtrar por precio
    if (price < priceRange[0] || price > priceRange[1]) {
      return false;
    }
    
    // Filtrar por tienda
    if (selectedStores.length > 0 && !selectedStores.includes(product.tienda)) {
      return false;
    }
    
    // Filtrar por disponibilidad
    if (selectedAvailability.includes('disponible') && !product.stock) {
      return false;
    }
    
    return true;
  });

  const sortedProducts = [...filteredProducts].sort((a, b) => {
    const priceA = a.precio || a.precio_min || 0;
    const priceB = b.precio || b.precio_min || 0;
    
    switch (sortBy) {
      case 'price_asc':
        return priceA - priceB;
      case 'price_desc':
        return priceB - priceA;
      default:
        return 0;
    }
  });

  // Calcular productos para la página actual
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const currentProducts = sortedProducts.slice(startIndex, endIndex);
  const totalPages = Math.ceil(sortedProducts.length / pageSize);

  // Obtener query de búsqueda
  const searchQuery = searchParams.get('search') || '';

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h3 style={{ color: '#ff4d4f' }}>Error</h3>
        <p>{error}</p>
        <button 
          onClick={() => window.location.reload()}
          style={{
            padding: '12px 24px',
            background: '#ff69b4',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '1rem',
            fontWeight: '500',
            marginTop: '16px'
          }}
        >
          Recargar página
        </button>
      </div>
    );
  }
  
  return (
    <Content style={{ background: '#f0f2f5' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 16px' }}>
        <Row gutter={24}>
          {/* Sidebar de filtros */}
          <Col xs={24} lg={6}>
            <Card 
              title="Filtros" 
              size="small" 
              style={{ position: 'sticky', top: 88 }}
            >
              {/* Filtro de Precio */}
              <div style={{ marginBottom: 24 }}>
                <Text strong>Precio</Text>
                <div style={{ marginTop: 12 }}>
                  <Slider
                    range
                    min={0}
                    max={100000}
                    step={1000}
                    value={priceRange}
                    onChange={setPriceRange}
                    tooltip={{
                      formatter: (value) => `$${value?.toLocaleString()}`
                    }}
                  />
                  <Row justify="space-between" style={{ marginTop: 8 }}>
                    <Text type="secondary">${priceRange[0]?.toLocaleString()}</Text>
                    <Text type="secondary">${priceRange[1]?.toLocaleString()}</Text>
                  </Row>
                </div>
              </div>

              {/* Filtro de Tiendas */}
              <div style={{ marginBottom: 24 }}>
                <Text strong>Tiendas</Text>
                <div style={{ marginTop: 12 }}>
                  <Checkbox.Group
                    options={storeOptions}
                    value={selectedStores}
                    onChange={setSelectedStores}
                    style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
                  />
                </div>
              </div>

              {/* Filtro de Disponibilidad */}
              <div style={{ marginBottom: 24 }}>
                <Text strong>Disponibilidad</Text>
                <div style={{ marginTop: 12 }}>
                  <Checkbox
                    checked={selectedAvailability.includes('disponible')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedAvailability(['disponible']);
                      } else {
                        setSelectedAvailability([]);
                      }
                    }}
                  >
                    Solo productos disponibles
                  </Checkbox>
                </div>
              </div>
            </Card>
          </Col>

          {/* Contenido principal */}
          <Col xs={24} lg={18}>
            {/* Header de resultados */}
            <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
              <Col>
                <Title level={4} style={{ margin: 0 }}>
                  Resultados para "{searchQuery}"
                </Title>
                <Text type="secondary">
                  {sortedProducts.length} productos encontrados
                  {filteredProducts.length !== products.length && 
                    ` (${products.length} productos en total)`
                  }
                </Text>
              </Col>
              <Col>
                <Select
                  value={sortBy}
                  onChange={setSortBy}
                  style={{ width: 200 }}
                  placeholder="Ordenar por"
                >
                  <Option value="price_asc">Precio: menor a mayor</Option>
                  <Option value="price_desc">Precio: mayor a menor</Option>
                </Select>
              </Col>
            </Row>

            {/* Estados de carga y resultados */}
            {loading ? (
              <Row gutter={[16, 16]}>
                {Array.from({ length: 8 }, (_, i) => (
                  <Col xs={24} sm={12} md={8} lg={6} key={i}>
                    <Card 
                      hoverable
                      cover={<Skeleton.Image style={{ height: 200 }} />}
                    >
                      <Skeleton active paragraph={{ rows: 2 }} />
                    </Card>
                  </Col>
                ))}
              </Row>
            ) : currentProducts.length === 0 ? (
              <Empty 
                description="No se encontraron productos"
                style={{ padding: '60px 0' }}
              />
            ) : (
              <>
                {/* Grid de productos */}
                <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
                  {currentProducts.map(product => (
                    <Col xs={24} sm={12} md={8} lg={6} key={product.id}>
                      <Link 
                        to={`/detalle-producto/${product.id}`}
                        style={{ textDecoration: 'none' }}
                      >
                        <Card
                          hoverable
                          cover={
                            <Image
                              alt={product.nombre}
                              src={getImageUrl(product)}
                              style={{ 
                                objectFit: 'contain', 
                                height: 200,
                                backgroundColor: '#f5f5f5'
                              }}
                              fallback="/image-not-found.png"
                              preview={false}
                            />
                          }
                          style={{ height: '100%' }}
                          bodyStyle={{ padding: 16 }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                            <Text 
                              type="secondary" 
                              style={{ fontSize: 12 }}
                            >
                              {product.marca || 'Sin marca'}
                            </Text>
                            <Text 
                              style={{ 
                                fontSize: 11, 
                                padding: '2px 6px', 
                                borderRadius: '4px',
                                backgroundColor: product.tienda === 'DBS' ? '#e6f7ff' : '#f6ffed',
                                color: product.tienda === 'DBS' ? '#1890ff' : '#52c41a',
                                fontWeight: 'bold'
                              }}
                            >
                              {product.tienda === 'DBS' ? '🛍️ DBS' : '🛒 Preunic'}
                            </Text>
                          </div>
                          <Paragraph 
                            ellipsis={{ rows: 2 }} 
                            style={{ 
                              fontSize: 14, 
                              fontWeight: 500, 
                              marginBottom: 8,
                              minHeight: 40
                            }}
                          >
                            {product.nombre}
                          </Paragraph>
                          <Text 
                            strong 
                            style={{ 
                              color: '#ff4d4f', 
                              fontSize: 16 
                            }}
                          >
                            {formatPrice(product.precio || product.precio_min || 0)}
                          </Text>
                        </Card>
                      </Link>
                    </Col>
                  ))}
                </Row>

                {/* Paginación */}
                {totalPages > 1 && (
                  <Row justify="center">
                    <Pagination
                      current={currentPage}
                      total={sortedProducts.length}
                      pageSize={pageSize}
                      onChange={setCurrentPage}
                      showSizeChanger={false}
                      showQuickJumper={false}
                      showTotal={(total, range) => 
                        `${range[0]}-${range[1]} de ${total} productos`
                      }
                    />
                  </Row>
                )}
              </>
            )}
          </Col>
        </Row>
      </div>
    </Content>
  );
};

export default SearchResultsPage;
