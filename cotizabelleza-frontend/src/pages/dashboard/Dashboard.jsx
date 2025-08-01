import React, { useState, useEffect } from 'react';
import {
  Layout,
  Input,
  Button,
  Card,
  Row,
  Col,
  Typography,
  Space,
  Badge,
  Tag,
  Carousel,
  Avatar,
  Divider,
  Spin,
  message
} from 'antd';
import {
  SearchOutlined,
  AppstoreOutlined,
  HeartOutlined,
  BellOutlined,
  UserOutlined,
  DollarOutlined,
  ClockCircleOutlined,
  LeftOutlined,
  RightOutlined,
  LinkOutlined
} from '@ant-design/icons';
import { dashboardService, categoryService, storeService } from '../../services/api';
import './Dashboard.css';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { Search } = Input;

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
        const [dashboardResponse, categoriesResponse, storesResponse] = await Promise.all([
          dashboardService.getDashboardData(),
          categoryService.getCategories(),
          storeService.getStores()
        ]);

        setDashboardData(dashboardResponse);
        setCategories(categoriesResponse);
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

  // Mock data para categorías (fallback)
  const mockCategories = ['Todos', 'Maquillaje', 'Skincare', 'Cabello', 'Fragancias', 'Uñas', 'Accesorios'];
  
  // Mock data para tiendas (fallback)
  const mockStores = ['Todas', 'Falabella', 'Paris', 'Ripley', 'Sephora', 'Jumbo', 'Líder', 'MAC', 'Sally Beauty'];

  // Mock data para productos populares (fallback)
  const mockPopularProducts = [
    {
      id: 1,
      nombre: 'Base de maquillaje Fit Me',
      marca: 'Maybelline',
      precio_min: 8990,
      imagen_url: '/src/assets/image-not-found.png',
      tiendas_disponibles: ['Falabella', 'Paris', 'Ripley']
    },
    {
      id: 2,
      nombre: 'Máscara de pestañas Lash Sensational',
      marca: 'Maybelline',
      precio_min: 7990,
      imagen_url: '/src/assets/image-not-found.png',
      tiendas_disponibles: ['Sephora', 'Falabella']
    },
    {
      id: 3,
      nombre: 'Paleta de sombras Naked',
      marca: 'Urban Decay',
      precio_min: 32990,
      imagen_url: '/src/assets/image-not-found.png',
      tiendas_disponibles: ['Falabella', 'Jumbo', 'Líder']
    },
    {
      id: 4,
      nombre: 'Labial Matte Revolution',
      marca: 'Charlotte Tilbury',
      precio_min: 24990,
      imagen_url: '/src/assets/image-not-found.png',
      tiendas_disponibles: ['Sephora', 'MAC']
    },
    {
      id: 5,
      nombre: 'Agua Micelar',
      marca: 'Garnier',
      precio_min: 5990,
      imagen_url: '/src/assets/image-not-found.png',
      tiendas_disponibles: ['Falabella', 'Paris', 'Ripley', 'Jumbo']
    },
    {
      id: 6,
      nombre: 'Crema Hidratante Nivea',
      marca: 'Nivea',
      precio_min: 4990,
      imagen_url: '/src/assets/image-not-found.png',
      tiendas_disponibles: ['Falabella', 'Jumbo', 'Líder']
    },
    {
      id: 7,
      nombre: 'Sérum Facial Vitamin C',
      marca: 'The Ordinary',
      precio_min: 12990,
      imagen_url: '/src/assets/image-not-found.png',
      tiendas_disponibles: ['Sephora', 'Falabella']
    },
    {
      id: 8,
      nombre: 'Aretes de Plata',
      marca: 'Accesorios Belleza',
      precio_min: 15990,
      imagen_url: '/src/assets/image-not-found.png',
      tiendas_disponibles: ['Falabella', 'Paris']
    }
  ];

  // Mock data for benefits
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

  // Función para obtener la URL de imagen correcta
  const getImageUrl = (product) => {
    // Si no hay imagen_url o está vacía, usar la imagen por defecto
    if (!product.imagen_url || product.imagen_url === '') {
      return '/src/assets/image-not-found.png';
    }
    
    // Si la URL es muy larga o parece ser base64, usar imagen por defecto
    if (product.imagen_url.length > 200 || product.imagen_url.startsWith('data:')) {
      return '/src/assets/image-not-found.png';
    }
    
    return product.imagen_url;
  };

  // Usar datos reales o fallback
  const popularProducts = dashboardData?.productos_populares || mockPopularProducts;
  const categoriesList = categories.length > 0 ? ['Todos', ...categories.map(c => c.nombre)] : mockCategories;
  const storesList = stores.length > 0 ? ['Todas', ...stores.map(s => s.nombre)] : mockStores;

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <Spin size="large" />
        <Text>Cargando datos del dashboard...</Text>
      </div>
    );
  }

  return (
    <Layout className="dashboard-layout">
      {/* Hero Banner Section */}
      <div className="hero-banner">
        <div className="hero-content">
          <div className="hero-text">
            <Title level={1} className="hero-title">
              Nuevos productos Fenty Beauty
            </Title>
            <Text className="hero-subtitle">
              Ya disponibles en Chile
            </Text>
            <Button type="primary" size="large" className="hero-button">
              Ver oferta
            </Button>
          </div>
          <div className="hero-products">
            {/* Product images would go here */}
            <div className="product-placeholder">Fenty Beauty Products</div>
          </div>
        </div>
        <div className="carousel-controls">
          <Button icon={<LeftOutlined />} className="carousel-btn" />
          <div className="carousel-dots">
            <span className="dot active"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
          <Button icon={<RightOutlined />} className="carousel-btn" />
        </div>
      </div>

      {/* Filter Section */}
      <div className="filter-section">
        <div className="filter-container">
          <Title level={4} className="filter-title"># Filtrar productos</Title>
          
          <div className="filter-row">
            <Text strong>Categorías:</Text>
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
      </div>

      {/* Popular Products Section */}
      <div className="products-section">
        <div className="section-header">
          <Title level={3}>Productos más populares</Title>
          <Button type="link" className="view-all">
            Ver todos <LinkOutlined />
          </Button>
        </div>

        <div className="products-grid">
          <Row gutter={[16, 16]}>
            {popularProducts.map(product => (
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
                        {product.tiendas_disponibles?.join(' ') || 'DBS'}
                      </Text>
                    </div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </div>

      {/* Benefits Section */}
      <div className="benefits-section">
        <Title level={2} className="benefits-title">
          ¿Por qué usar CotizaBelleza?
        </Title>
        <Row gutter={[24, 24]} className="benefits-grid">
          {benefits.map((benefit, index) => (
            <Col xs={24} md={8} key={index}>
              <Card className="benefit-card">
                <div className="benefit-icon">
                  {benefit.icon}
                </div>
                <Title level={4} className="benefit-title">
                  {benefit.title}
                </Title>
                <Text className="benefit-description">
                  {benefit.description}
                </Text>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </Layout>
  );
};

export default Dashboard; 