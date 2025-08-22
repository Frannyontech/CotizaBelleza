import React from 'react';
import { 
  Layout,
  Typography,
  Row,
  Col,
  Button,
  Space,
  Breadcrumb
} from 'antd';
import { ShareAltOutlined } from '@ant-design/icons';
import { resolveImageUrl, getDefaultThumbnail } from '../utils/image';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const ProductDetailLegacy = ({ product }) => {
  if (!product) {
    return (
      <div style={{ textAlign: 'center', padding: '50px', minHeight: '400px' }}>
        <Text>Producto no encontrado</Text>
      </div>
    );
  }

  const getImageUrl = (imagenUrl) => {
    const fakeProduct = { imagen_url: imagenUrl };
    return resolveImageUrl(fakeProduct);
  };

  const getStoreDisplayName = (tienda) => {
    switch (tienda?.toUpperCase()) {
      case 'DBS':
        return '🛍️ DBS';
      case 'PREUNIC':
        return '🛒 Preunic';
      case 'MAICAO':
        return '💄 Maicao';
      default:
        return tienda || 'Tienda';
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP'
    }).format(price);
  };

  const getStockColor = (stock) => {
    if (!stock || typeof stock !== 'string') return '#fa8c16';
    return stock.toLowerCase().includes('stock') ? '#52c41a' : '#fa8c16';
  };

  const breadcrumbItems = [
    { title: 'Inicio', href: '/' },
    { title: product.categoria || 'Productos', href: '/productos' },
    { title: product.nombre }
  ];

  return (
    <Layout className="detalle-producto-layout">
      <Content className="detalle-producto-content">
        {/* Breadcrumbs */}
        <div className="breadcrumb-container" style={{ marginBottom: 24 }}>
          <Breadcrumb items={breadcrumbItems} />
        </div>

        {/* Product Information Section */}
        <div className="product-info-section">
          <Row gutter={[32, 32]}>
            {/* Product Image */}
            <Col xs={24} md={12}>
              <div className="product-image-container" style={{ textAlign: 'center' }}>
                <img 
                  src={getImageUrl(product.imagen_url || product.imagen)} 
                  alt={product.nombre}
                  style={{ 
                    maxWidth: '100%',
                    height: 'auto',
                    maxHeight: '400px',
                    objectFit: 'contain'
                  }}
                  onError={(e) => {
                    e.target.src = getDefaultThumbnail();
                  }}
                />
              </div>
            </Col>

            {/* Product Details */}
            <Col xs={24} md={12}>
              <div className="product-details">
                <Title level={2} className="product-name">{product.nombre}</Title>
                
                {/* Price Information */}
                <div className="price-section" style={{ margin: '24px 0' }}>
                  <div className="price-info" style={{ marginBottom: 16 }}>
                    <Text className="price-label" style={{ display: 'block', fontSize: 14, color: '#666' }}>Precio</Text>
                    <Text className="best-price" style={{ fontSize: 32, fontWeight: 'bold', color: '#ff4d4f' }}>
                      {formatPrice(product.precio || 0)}
                    </Text>
                  </div>
                  <div className="price-info" style={{ marginBottom: 16 }}>
                    <Text className="price-label" style={{ display: 'block', fontSize: 14, color: '#666' }}>Tienda</Text>
                    <Text style={{ color: '#1890ff', fontWeight: 'bold', fontSize: 16 }}>
                      {getStoreDisplayName(product.fuente || product.tienda)}
                    </Text>
                  </div>
                  <div className="price-info" style={{ marginBottom: 16 }}>
                    <Text className="price-label" style={{ display: 'block', fontSize: 14, color: '#666' }}>Stock</Text>
                    <Text style={{ color: getStockColor(product.stock), fontWeight: 'bold' }}>
                      {product.stock || 'Desconocido'}
                    </Text>
                  </div>
                </div>

                {/* Product Description */}
                <div className="description-section" style={{ margin: '24px 0' }}>
                  <Paragraph className="product-description">
                    {product.nombre}. Disponible en {getStoreDisplayName(product.fuente || product.tienda)}.
                  </Paragraph>
                </div>

                {/* Action Buttons */}
                <div className="action-buttons" style={{ margin: '24px 0' }}>
                  <Space>
                    <Button 
                      type="primary"
                      size="large"
                      href={product.url || product.url_producto}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ minWidth: 120 }}
                    >
                      Ir a tienda
                    </Button>
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
      </Content>
    </Layout>
  );
};

export default ProductDetailLegacy;
