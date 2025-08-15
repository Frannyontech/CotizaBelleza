import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Layout,
  Button,
  Card,
  Row,
  Col,
  Typography,
  Space,
  Tag,
  Rate,
  Breadcrumb,
  message,
  Spin
} from 'antd';
import {
  ShareAltOutlined,
  BellOutlined,
  StarFilled,
  ArrowDownOutlined
} from '@ant-design/icons';
import axios from 'axios';
import PriceAlertModal from '../../components/PriceAlertModal';
import StoreComparison from '../../components/StoreComparison';
import './DetalleProducto.css';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const DetalleProducto = () => {
  const { id } = useParams();
  const [producto, setProducto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);

  useEffect(() => {
    const fetchProducto = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`/api/productos-dbs/${id}/`);
        setProducto(response.data);
      } catch (error) {
        console.error('Error fetching producto:', error);
        message.error('Error al cargar el producto');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchProducto();
    }
  }, [id]);

  const getImageUrl = (imagenUrl) => {
    if (!imagenUrl || imagenUrl === '') {
      return '/image-not-found.png';
    }
    if (imagenUrl.startsWith('http') && imagenUrl.includes('dbs.cl')) {
      return imagenUrl;
    }
    if (imagenUrl.startsWith('/')) {
      return `https://dbs.cl${imagenUrl}`;
    }
    return '/image-not-found.png';
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP'
    }).format(price);
  };

  const calculateDiscount = (originalPrice, currentPrice) => {
    if (!originalPrice || !currentPrice) return null;
    const discount = ((originalPrice - currentPrice) / originalPrice) * 100;
    return Math.round(discount);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <Text>Cargando producto...</Text>
      </div>
    );
  }

  if (!producto) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Text>Producto no encontrado</Text>
      </div>
    );
  }

  const breadcrumbItems = [
    { title: 'Inicio', href: '/' },
    { title: producto.categoria || 'Productos', href: '/productos' },
    { title: producto.marca, href: `/productos?marca=${producto.marca}` },
    { title: producto.nombre }
  ];

  return (
    <Layout className="detalle-producto-layout">
      <Content className="detalle-producto-content">
        {/* Breadcrumbs */}
        <div className="breadcrumb-container">
          <Breadcrumb items={breadcrumbItems} />
        </div>

        {/* Product Information Section */}
        <div className="product-info-section">
          <Row gutter={[32, 32]}>
            {/* Product Image */}
            <Col xs={24} md={12}>
              <div className="product-image-container">
                <img 
                  src={getImageUrl(producto.imagen_url)} 
                  alt={producto.nombre}
                  className="product-image"
                  onError={(e) => {
                    e.target.src = '/image-not-found.png';
                  }}
                />
              </div>
            </Col>

            {/* Product Details */}
            <Col xs={24} md={12}>
              <div className="product-details">
                <div className="brand-name">{producto.marca}</div>
                <Title level={2} className="product-name">{producto.nombre}</Title>
                
                {/* Rating */}
                <div className="rating-section">
                  <Rate 
                    disabled 
                    defaultValue={4.7} 
                    allowHalf 
                    className="product-rating"
                  />
                  <Text className="rating-text">4.7 (324 reseñas)</Text>
                </div>

                {/* Price Information */}
                <div className="price-section">
                  <div className="price-info">
                    <Text className="price-label">Mejor precio</Text>
                    <Text className="best-price">{formatPrice(producto.precio_min || producto.precio)}</Text>
                  </div>
                  {producto.precio_max && producto.precio_max !== producto.precio_min && (
                    <div className="price-info">
                      <Text className="price-label">Precio más alto</Text>
                      <Text className="highest-price" delete>{formatPrice(producto.precio_max)}</Text>
                    </div>
                  )}
                </div>

                {/* Product Description */}
                <div className="description-section">
                  <Paragraph className="product-description">
                    {producto.descripcion || `${producto.nombre} de ${producto.marca}. Producto de calidad disponible en las mejores tiendas.`}
                  </Paragraph>
                  <Button 
                    type="link" 
                    className="expand-description"
                    onClick={() => setExpanded(!expanded)}
                  >
                    Ver más <ArrowDownOutlined style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }} />
                  </Button>
                </div>

                {/* Action Buttons */}
                <div className="action-buttons">
                  <Button 
                    type="primary" 
                    size="large" 
                    icon={<BellOutlined />}
                    className="alert-button"
                    onClick={() => setModalVisible(true)}
                  >
                    Activar alerta de precio
                  </Button>
                  <Space className="action-icons">
                    <Button 
                      type="text" 
                      icon={<ShareAltOutlined />} 
                      className="share-button"
                    />
                  </Space>
                </div>
              </div>
            </Col>
          </Row>
        </div>

        {/* Price Comparison Section */}
        <StoreComparison
          offers={producto.tiendas_detalladas || []}
          productName={producto.nombre}
          loading={loading}
          formatPrice={formatPrice}
          calculateDiscount={calculateDiscount}
        />
      </Content>
      
      {/* Price Alert Modal */}
      <PriceAlertModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        producto={producto}
      />
    </Layout>
  );
};

export default DetalleProducto; 