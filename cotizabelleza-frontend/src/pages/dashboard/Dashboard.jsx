import React, { useState } from 'react';
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
  Divider
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
import './Dashboard.css';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { Search } = Input;

const Dashboard = () => {
  const [selectedCategory, setSelectedCategory] = useState('Todos');
  const [selectedStore, setSelectedStore] = useState('Todas');

  // Mock data for categories
  const categories = ['Todos', 'Maquillaje', 'Skincare', 'Cabello', 'Fragancias', 'Uñas', 'Accesorios'];
  
  // Mock data for stores
  const stores = ['Todas', 'Falabella', 'Paris', 'Ripley', 'Sephora', 'Jumbo', 'Líder', 'MAC', 'Sally Beauty'];

  // Mock data for popular products
  const popularProducts = [
    {
      id: 1,
      name: 'Base de maquillaje Fit Me',
      brand: 'Maybelline',
      price: 8990,
      image: '/src/assets/image-not-found.png',
      stores: ['Falabella', 'Paris', 'Ripley']
    },
    {
      id: 2,
      name: 'Máscara de pestañas Lash Sensational',
      brand: 'Maybelline',
      price: 7990,
      image: '/src/assets/image-not-found.png',
      stores: ['Sephora', 'Falabella']
    },
    {
      id: 3,
      name: 'Paleta de sombras Naked',
      brand: 'Urban Decay',
      price: 32990,
      image: '/src/assets/image-not-found.png',
      stores: ['Falabella', 'Jumbo', 'Líder']
    },
    {
      id: 4,
      name: 'Labial Matte Revolution',
      brand: 'Charlotte Tilbury',
      price: 24990,
      image: '/src/assets/image-not-found.png',
      stores: ['Sephora', 'MAC']
    },
    {
      id: 5,
      name: 'Agua Micelar',
      brand: 'Garnier',
      price: 5990,
      image: '/src/assets/image-not-found.png',
      stores: ['Falabella', 'Paris', 'Ripley', 'Jumbo']
    },
    {
      id: 6,
      name: 'Crema Hidratante Nivea',
      brand: 'Nivea',
      price: 4990,
      image: '/src/assets/image-not-found.png',
      stores: ['Falabella', 'Jumbo', 'Líder']
    },
    {
      id: 7,
      name: 'Sérum Facial Vitamin C',
      brand: 'The Ordinary',
      price: 12990,
      image: '/src/assets/image-not-found.png',
      stores: ['Sephora', 'Falabella']
    },
    {
      id: 8,
      name: 'Aretes de Plata',
      brand: 'Accesorios Belleza',
      price: 15990,
      image: '/src/assets/image-not-found.png',
      stores: ['Falabella', 'Paris']
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
              {categories.map(category => (
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
              {stores.map(store => (
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
                    <img src={product.image} alt={product.name} />
                  </div>
                  <div className="product-info">
                    <Text className="product-brand">{product.brand}</Text>
                    <Text className="product-name">{product.name}</Text>
                    <Text className="product-price">
                      Desde ${product.price.toLocaleString()}
                    </Text>
                    <Button type="primary" size="small" className="view-more-btn">
                      Ver más <LinkOutlined />
                    </Button>
                    <div className="product-stores">
                      <Text type="secondary">Disponible en:</Text>
                      <Text className="store-list">{product.stores.join(' ')}</Text>
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