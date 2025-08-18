import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  LinkOutlined,
  DollarOutlined,
  ClockCircleOutlined,
  BellOutlined
} from '@ant-design/icons';
import { unifiedProductsService } from '../../services/unifiedApi';
import { resolveImageUrl, getDefaultThumbnail } from '../../utils/image';
import './Dashboard.css';

// Importar imágenes del carrusel
import heroSlider1 from '../../assets/hero-slider-1.jpg';
import heroSlider2 from '../../assets/hero-slider-2.jpg';
import heroSlider3 from '../../assets/hero-slider-3.jpg';

const { Content } = Layout;
const { Title, Text } = Typography;

const Dashboard = () => {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState('Todos');
  const [selectedStore, setSelectedStore] = useState('Todas');
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState([]);

  // Cargar productos unificados
  useEffect(() => {
    const loadProducts = async () => {
      try {
        setLoading(true);
        // Cargar productos unificados directamente desde el backend
        const response = await fetch('http://localhost:8000/api/unified/');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const unifiedData = await response.json();
        const productos = unifiedData.productos || [];
        
        // Función para seleccionar productos mixtos (priorizar multi-tienda)
        const selectMixedProducts = (productos, count) => {
          const multiStore = productos.filter(p => (p.tiendas || []).length > 1);
          const singleStore = productos.filter(p => (p.tiendas || []).length === 1);
          
          const selected = [];
          
          // Agregar productos multi-tienda primero
          selected.push(...multiStore.slice(0, Math.min(count, multiStore.length)));
          
          // Completar con productos de tienda única, balanceado
          const remaining = count - selected.length;
          if (remaining > 0) {
            const dbsProducts = singleStore.filter(p => p.tiendas?.[0]?.fuente === 'dbs');
            const maicaoProducts = singleStore.filter(p => p.tiendas?.[0]?.fuente === 'maicao');
            const preunicProducts = singleStore.filter(p => p.tiendas?.[0]?.fuente === 'preunic');
            
            const perStore = Math.ceil(remaining / 3);
            selected.push(...dbsProducts.slice(0, perStore));
            selected.push(...maicaoProducts.slice(0, perStore));
            selected.push(...preunicProducts.slice(0, perStore));
          }
          
          return selected.slice(0, count);
        };
        
        // Seleccionar 10 productos mixtos
        const selectedProducts = selectMixedProducts(productos, 10);
        
        // Convertir productos a formato simple para dashboard
        const dashboardProducts = selectedProducts.map(product => {
          const tiendas = product.tiendas || [];
          let precio_min = null;
          let imagen_url = '';
          let tiendas_disponibles = [];
          
          // Extraer precio mínimo e imagen
          tiendas.forEach(tienda => {
            // Imagen - usar cualquier imagen disponible
            if (tienda.imagen && !imagen_url) {
              imagen_url = tienda.imagen;
            }
            
            // Precio - convertir y validar
            const precio = parseFloat(tienda.precio);
            if (!isNaN(precio) && precio > 0 && (precio_min === null || precio < precio_min)) {
              precio_min = precio;
            }
            
            // Tienda - agregar fuente
            if (tienda.fuente) {
              tiendas_disponibles.push(tienda.fuente.toUpperCase());
            }
          });
          
          return {
            id: product.product_id,
            product_id: product.product_id,
            nombre: product.nombre || 'Sin nombre',
            marca: product.marca || '',
            categoria: product.categoria || '',
            precio_min: precio_min || 0, // Default a 0 en lugar de null
            imagen_url: imagen_url || '', // Default a string vacío
            tiendas_disponibles: [...new Set(tiendas_disponibles)],
            tiendasCount: tiendas.length
          };
        });
        
        setProducts(dashboardProducts);
        
      } catch (error) {
        console.error('❌ Error loading dashboard data:', error);
        message.error('Error al cargar los datos del dashboard');
      } finally {
        setLoading(false);
      }
    };

    loadProducts();
  }, []);

  // Formatear precio en formato CLP sin decimales
  const formatPriceCLP = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      maximumFractionDigits: 0
    }).format(price);
  };

  // Extraer categorías y tiendas disponibles
  const categorias_unicas = [...new Set(products.map(product => product.categoria))];
  const tiendas_unicas = [...new Set(products.flatMap(product => product.tiendas || []))];
  
  const categoriesList = ['Todos', ...categorias_unicas];
  const storesList = ['Todas', ...tiendas_unicas.map(store => store.toUpperCase())];

  // Aplicar filtros a los productos
  const filteredProducts = products.filter(product => {
    // Filtro por categoría
    if (selectedCategory !== 'Todos' && product.categoria !== selectedCategory) {
      return false;
    }
    
    // Filtro por tienda
    if (selectedStore !== 'Todas') {
      const storeMatch = product.tiendas_disponibles?.some(store => 
        store.toUpperCase() === selectedStore
      );
      if (!storeMatch) return false;
    }
    
    return true;
  });

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
            <div className="carousel-slide" style={{ backgroundImage: `url(${heroSlider1})` }}>
              <div className="carousel-content">
                <h2>Productos de belleza unificados</h2>
                <p>Comparación de precios en tiempo real</p>
              </div>
            </div>
          </div>
          <div>
            <div className="carousel-slide" style={{ backgroundImage: `url(${heroSlider2})` }}>
              <div className="carousel-content">
                <h2>Mejor precio garantizado</h2>
                <p>Compara entre DBS, Preunic y Maicao</p>
              </div>
            </div>
          </div>
          <div>
            <div className="carousel-slide" style={{ backgroundImage: `url(${heroSlider3})` }}>
              <div className="carousel-content">
                <h2>Productos destacados</h2>
                <p>Las mejores marcas de belleza</p>
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
          <Button 
            type="link" 
            className="clear-filters"
            onClick={() => {
              setSelectedCategory('Todos');
              setSelectedStore('Todas');
            }}
          >
            Limpiar filtros
          </Button>
        </div>
      </div>

      {/* Popular Products Section */}
      <div className="products-section">
        <div className="section-header">
          <Title level={3}>Productos más populares ({filteredProducts.length})</Title>
          <Button type="link" className="view-all">
            Ver todos <LinkOutlined />
          </Button>
        </div>

        <div className="products-grid">
          {filteredProducts.length > 0 ? (
            filteredProducts.map(product => (
              <div 
                key={product.product_id}
                className="product-card" 
                onClick={() => navigate(`/detalle-producto/${encodeURIComponent(product.product_id)}`)}
                style={{ cursor: 'pointer' }}
              >
                <div className="product-image">
                  <img 
                    src={product.imagen_url || getDefaultThumbnail()} 
                    alt={product.nombre}
                    onError={(e) => {
                      e.target.src = getDefaultThumbnail();
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
            ))
          ) : (
            <div className="no-products">
              <Text type="secondary">No hay productos disponibles</Text>
            </div>
          )}
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
