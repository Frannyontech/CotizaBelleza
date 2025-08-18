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
  Rate,
  Breadcrumb,
  message,
  Spin
} from 'antd';
import {
  ShareAltOutlined,
  BellOutlined,
  HeartOutlined
} from '@ant-design/icons';
import { unifiedProductsService } from '../../services/unifiedApi';
import { resolveImageUrl } from '../../utils/image';
import PriceAlertModal from '../../components/PriceAlertModal';
import ProductReviews from '../../components/ProductReviews';
import './DetalleProducto.css';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const DetalleProducto = () => {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewsData, setReviewsData] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        setLoading(true);
        // Decodificar el ID (puede venir URL-encoded)
        const decodedId = decodeURIComponent(id);
        
        // Buscar en productos unificados exclusivamente
        const foundProduct = await unifiedProductsService.getProductById(decodedId);
        
        if (foundProduct) {
          
          // Usar los datos directamente del JSON unificado
          setProduct({
            product_id: foundProduct.product_id,
            nombre: foundProduct.nombre,
            marca: foundProduct.marca,
            categoria: foundProduct.categoria,
            imagen_url: foundProduct.imagen || foundProduct.tiendas?.[0]?.imagen,
            precio_min: Math.min(...foundProduct.tiendas.map(t => parseFloat(t.precio))),
            tiendasCount: foundProduct.tiendas.length,
            tiendas_disponibles: foundProduct.tiendas.map(t => t.fuente.toUpperCase()),
            tiendas: foundProduct.tiendas // Datos completos de tiendas
          });
        } else {
          message.error('Producto no encontrado');
        }
        
      } catch (error) {
        console.error('Error loading product:', error);
        message.error('Error al cargar el producto');
      } finally {
        setLoading(false);
      }
    };
    
    if (id) {
      fetchProduct();
    }
  }, [id]);



  // Las reseñas se manejan directamente en el componente ProductReviews
  // No necesitamos cargar reseñas aquí ya que el componente las maneja

  const getImageUrl = (imagenUrl) => {
    return resolveImageUrl({ imagen_url: imagenUrl });
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

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px', minHeight: '400px' }}>
        <Spin size="large" />
        <br />
        <Text>Cargando producto...</Text>
      </div>
    );
  }

  if (!product) {
    return (
      <div style={{ textAlign: 'center', padding: '50px', minHeight: '400px' }}>
        <Text>Producto no encontrado</Text>
        <br />
        <Text type="secondary">ID buscado: {id}</Text>
        <br />
        <Button onClick={() => window.location.href = '/'}>
          Volver al inicio
        </Button>
      </div>
    );
  }

  const isMultiStore = product.tiendasCount > 1;

  return (
    <Layout className="detalle-producto-layout">
      <Content style={{ padding: '0', background: '#f5f5f5' }}>
        <div className="detalle-producto-content">
        {/* Breadcrumbs */}
        <div className="breadcrumb-container">
            <Breadcrumb items={[
              { title: 'Inicio', href: '/' },
              { 
                title: product.categoria || 'Productos', 
                href: product.categoria ? `/categorias/${product.categoria.toLowerCase()}` : '/productos' 
              },
              { title: product.nombre }
            ]} />
        </div>

        {/* Product Information Section */}
        <div className="product-info-section">
          <Row gutter={[32, 32]}>
            {/* Product Image */}
            <Col xs={24} md={12}>
              <div className="product-image-container">
                <img 
                    src={getImageUrl(product.imagen_url)} 
                    alt={product.nombre}
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
                  <Title level={2} className="product-name">{product.nombre}</Title>
                  
                  {/* Product Brand */}
                  {product.marca && (
                    <Text className="product-brand">{product.marca}</Text>
                  )}
                  
                  {/* Rating */}
                {reviewsData && reviewsData.total_resenas > 0 && (
                  <div className="rating-section">
                    <Rate 
                      disabled 
                      value={reviewsData.promedio_valoracion} 
                      allowHalf 
                      className="product-rating"
                    />
                    <Text className="rating-text">
                      {reviewsData.promedio_valoracion.toFixed(1)} ({reviewsData.total_resenas} {reviewsData.total_resenas === 1 ? 'reseña' : 'reseñas'})
                    </Text>
                  </div>
                )}

                {/* Price Information */}
                <div className="price-section">
                    {isMultiStore ? (
                      <>
                  <div className="price-info">
                    <Text className="price-label">Mejor precio</Text>
                          <Text className="best-price">{formatPrice(product.precio_min)}</Text>
                  </div>
                    <div className="price-info">
                          <Text className="price-label">Disponible en</Text>
                          <Text style={{ color: '#52c41a', fontWeight: 'bold' }}>
                            {product.tiendasCount} {product.tiendasCount === 1 ? 'tienda' : 'tiendas'}
                          </Text>
                    </div>
                      </>
                    ) : (
                      <Text className="best-price">{formatPrice(product.precio_min)}</Text>
                  )}
                </div>

                {/* Product Description */}
                <div className="description-section">
                  <Paragraph className="product-description">
                      {isMultiStore 
                        ? `${product.nombre}. Producto de calidad disponible en ${product.tiendasCount} ${product.tiendasCount === 1 ? 'tienda' : 'tiendas'}.`
                        : `${product.nombre}. Producto de calidad de la marca ${product.marca || 'reconocida'}.`
                      }
                  </Paragraph>
                </div>

                {/* Action Buttons */}
                <div className="action-buttons">
                    <Space className="action-icons">
                    <Button 
                      icon={<BellOutlined />}
                        onClick={() => setModalVisible(true)}
                      className="alert-button"
                      >
                        Alerta de precio
                    </Button>
                    <Button 
                      type="text" 
                      icon={<ShareAltOutlined />} 
                      className="share-button"
                    />
                      <Button 
                        type="text" 
                        icon={<HeartOutlined />} 
                        className="wishlist-button"
                      />
                  </Space>
                </div>
              </div>
            </Col>
          </Row>
        </div>

          {/* Store Information Section */}
          <section className="store-info-section">
            {isMultiStore ? (
              <>
                <Title level={3}>
                  Comparación de tiendas ({product.tiendas?.length || 0})
                </Title>
                <div className="comparacion" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {(product.tiendas || []).map((tienda, index) => (
                    <Card key={index} className="store-info-card">
                      <div className="store-row">
                        <span className="store-name">
                          {getStoreDisplayName(tienda.fuente)}
                        </span>
                        <span className="store-stock" style={{ color: getStockColor(tienda.stock) }}>
                          {tienda.stock || 'Desconocido'}
                        </span>
                        <strong className="store-price">
                          ${parseFloat(tienda.precio).toLocaleString("es-CL")}
                        </strong>
                        <a 
                          href={tienda.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="store-button"
                        >
                          Ir a tienda
                        </a>
                      </div>
                    </Card>
                  ))}
                </div>
              </>
            ) : (
              <>
                <Title level={3}>Información de la tienda</Title>
                <Card className="store-info-card">
                  <div className="store-row">
                    <span className="store-name">
                      {getStoreDisplayName(product.tiendas?.[0]?.fuente)}
                    </span>
                    <span className="store-stock" style={{ color: getStockColor(product.tiendas?.[0]?.stock) }}>
                      {product.tiendas?.[0]?.stock || 'Desconocido'}
                    </span>
                    <strong className="store-price">
                      ${(product.precio_min || 0).toLocaleString("es-CL")}
                    </strong>
                    <a 
                      href={product.tiendas?.[0]?.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="store-button"
                    >
                      Ir a tienda
                    </a>
                  </div>
                </Card>
              </>
            )}
          </section>

          {/* Product Reviews Section */}
          {product && (
            <ProductReviews productId={id} />
          )}

          {/* Price Alert Modal */}
        <PriceAlertModal
          visible={modalVisible}
          onClose={() => setModalVisible(false)}
            producto={product}
        />

        </div>
      </Content>
    </Layout>
  );
};

export default DetalleProducto; 
