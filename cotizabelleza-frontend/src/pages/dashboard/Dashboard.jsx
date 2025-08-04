import React, { useState, useEffect } from 'react';
import {
  Layout,
  Button,
  Card,
  Row,
  Col,
  Typography,
  Space,
  Tag,
  Carousel,
  Spin,
  message
} from 'antd';
import {
  HeartOutlined,
  LinkOutlined,
  DollarOutlined,
  ClockCircleOutlined,
  BellOutlined
} from '@ant-design/icons';
import { dashboardService, categoryService, storeService } from '../../services/api';
import './Dashboard.css';

const { Content } = Layout;
const { Title, Text } = Typography;

const Dashboard = () => {
  const [selectedCategory, setSelectedCategory] = useState('Todos');
  const [selectedStore, setSelectedStore] = useState('Todas');
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [categories, setCategories] = useState([]);
  const [stores, setStores] = useState([]);

  // Cargar datos del dashboard
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        
        // Cargar datos del dashboard
        const dashboardResponse = await dashboardService.getDashboardData();
        setDashboardData(dashboardResponse);

        // Cargar categorías
        const categoriesResponse = await categoryService.getCategories();
        setCategories(categoriesResponse);

        // Cargar tiendas
        const storesResponse = await storeService.getStores();
        setStores(storesResponse);

      } catch (error) {
        console.error('Error loading dashboard data:', error);
        message.error('Error al cargar los datos del dashboard');
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  // Función para obtener la URL de imagen correcta
  const getImageUrl = (product) => {
    // Si no hay imagen_url o está vacía, usar la imagen por defecto
    if (!product.imagen_url || product.imagen_url === '') {
      return '/image-not-found.png';
    }
    
    // Si es una URL válida de DBS, usarla directamente
    if (product.imagen_url.startsWith('http') && product.imagen_url.includes('dbs.cl')) {
      return product.imagen_url;
    }
    
    // Si es una URL relativa, agregar el dominio de DBS
    if (product.imagen_url.startsWith('/')) {
      return `https://dbs.cl${product.imagen_url}`;
    }
    
    // Si no es una URL válida, usar la imagen por defecto
    return '/image-not-found.png';
  };

  // Obtener datos procesados
  const popularProducts = dashboardData?.productos_populares || [];
  const categoriesList = categories.length > 0 ? ['Todos', ...categories.map(cat => cat.nombre || cat)] : ['Todos'];
  const storesList = stores.length > 0 ? ['Todas', ...stores.map(store => store.nombre || store)] : ['Todas'];

  // Datos de beneficios
  const benefits = [
    {
      icon: <DollarOutlined />,
      title: 'Ahorra dinero',
      description: 'Compara precios entre diferentes tiendas y encuentra las mejores ofertas.'
    },
    {
      icon: <ClockCircleOutlined />,
      title: 'Ahorra tiempo',
      description: 'Encuentra rápidamente los productos que buscas sin visitar múltiples sitios.'
    },
    {
      icon: <BellOutlined />,
      title: 'Alertas de precio',
      description: 'Recibe notificaciones cuando tus productos favoritos bajen de precio.'
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <Text>Cargando dashboard...</Text>
      </div>
    );
  }

  return (
    <Layout className="dashboard-layout">
      {/* Hero Carousel Section */}
      <div className="hero-carousel-section">
        <Carousel autoplay>
          <div>
            <div className="carousel-slide">
              <img 
                src="/src/assets/hero-slider-1.jpg" 
                alt="Productos de belleza"
                className="carousel-image"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
              <div className="carousel-content">
                <h2>Revisa los productos disponibles</h2>
                <p>Ya disponibles en Chile</p>
                <Button type="primary" size="large">
                  Ver oferta
                </Button>
              </div>
            </div>
          </div>
          <div>
            <div className="carousel-slide">
              <img 
                src="/src/assets/hero-slider-2.jpg" 
                alt="Ofertas especiales"
                className="carousel-image"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
              <div className="carousel-content">
                <h2>Ofertas especiales</h2>
                <p>Hasta 50% de descuento</p>
                <Button type="primary" size="large">
                  Ver ofertas
                </Button>
              </div>
            </div>
          </div>
          <div>
            <div className="carousel-slide">
              <img 
                src="/src/assets/hero-slider-3.jpg" 
                alt="Productos destacados"
                className="carousel-image"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
              <div className="carousel-content">
                <h2>Productos destacados</h2>
                <p>Las mejores marcas de belleza</p>
                <Button type="primary" size="large">
                  Explorar
                </Button>
              </div>
            </div>
          </div>
        </Carousel>
      </div>

      {/* Filter Section */}
      <div className="filter-container">
        <div className="filter-row">
          <Text strong>Categoría:</Text>
          <Space wrap>
            {categoriesList.map(category => (
              <Tag
                key={category}
                className={`filter-tag ${selectedCategory === category ? 'active' : ''}`}
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </Tag>
            ))}
          </Space>
        </div>

        <div className="filter-row">
          <Text strong>Tienda:</Text>
          <Space wrap>
            {storesList.map(store => (
              <Tag
                key={store}
                className={`filter-tag ${selectedStore === store ? 'active' : ''}`}
                onClick={() => setSelectedStore(store)}
              >
                {store}
              </Tag>
            ))}
          </Space>
          <Button type="link" className="clear-filters">
            Limpiar filtros
          </Button>
        </div>
      </div>

      {/* Popular Products Section */}
      <div className="products-section">
        <div className="section-header">
          <Title level={3}>Productos más populares ({popularProducts.length})</Title>
          <Button type="link" className="view-all">
            Ver todos <LinkOutlined />
          </Button>
        </div>

        <div className="products-grid">
          <Row gutter={[16, 16]}>
            {popularProducts.length > 0 ? (
              popularProducts.map(product => (
                <Col xs={24} sm={12} md={8} lg={6} key={product.id}>
                  <Card className="product-card" hoverable>
                    <div className="product-header">
                      <HeartOutlined className="favorite-icon" />
                    </div>
                    <div className="product-image">
                      <img 
                        src={getImageUrl(product)} 
                        alt={product.nombre}
                        onError={(e) => {
                          e.target.src = '/src/assets/image-not-found.png';
                        }}
                      />
                    </div>
                    <div className="product-info">
                      <Text className="product-brand">{product.marca}</Text>
                      <Text className="product-name">{product.nombre}</Text>
                      <Text className="product-price">
                        Desde ${product.precio_min?.toLocaleString() || product.precio_min}
                      </Text>
                      <Button type="primary" size="small" className="view-more-btn">
                        Ver más <LinkOutlined />
                      </Button>
                      <div className="product-stores">
                        <Text type="secondary">Disponible en:</Text>
                        <Text className="store-list">
                          {product.tiendas_disponibles?.join(', ') || 'DBS'}
                        </Text>
                      </div>
                    </div>
                  </Card>
                </Col>
              ))
            ) : (
              <Col span={24}>
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <Text type="secondary">No hay productos disponibles</Text>
                </div>
              </Col>
            )}
          </Row>
        </div>
      </div>

      {/* Benefits Section */}
      <div className="benefits-section">
        <div className="benefits-container">
          <Title level={2} className="benefits-title">¿Por qué elegir CotizaBelleza?</Title>
          <Row gutter={[24, 24]}>
            {benefits.map((benefit, index) => (
              <Col xs={24} sm={12} md={8} key={index}>
                <Card className="benefit-card" hoverable>
                  <div className="benefit-icon">
                    {benefit.icon}
                  </div>
                  <Title level={4} className="benefit-title">{benefit.title}</Title>
                  <Text className="benefit-description">{benefit.description}</Text>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard; 