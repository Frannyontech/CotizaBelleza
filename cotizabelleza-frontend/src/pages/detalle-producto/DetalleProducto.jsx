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
import { productService } from '../../services/api';
import PriceAlertModal from '../../components/PriceAlertModal';
import StoreComparison from '../../components/StoreComparison';
import ProductReviews from '../../components/ProductReviews';
import './DetalleProducto.css';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const DetalleProducto = () => {
  const { id } = useParams();
  const [producto, setProducto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [reviewsData, setReviewsData] = useState(null);
  const [reviewsLoading, setReviewsLoading] = useState(false);

  useEffect(() => {
    const fetchProducto = async () => {
      try {
        setLoading(true);
        
        // Detectar el tipo de producto basándose en el ID
        const isPreunicProduct = id && id.startsWith('preunic_');
        const isMaicaoProduct = id && id.startsWith('maicao_');
        const isDBSProduct = id && id.startsWith('dbs_');
        
        let response;
        if (isPreunicProduct) {
          // Para Preunic, necesitamos buscar el producto por ID
          const productId = id.replace('preunic_', '');
          const searchResponse = await axios.get(`/api/productos-preunic/`);
          const productos = searchResponse.data.productos || [];
          const producto = productos.find(p => p.id.toString() === productId);
          
          if (!producto) {
            throw new Error('Producto no encontrado');
          }
          
          // Adaptar el formato para que sea compatible con el resto del componente
          response = {
            data: {
              id: producto.id,
              nombre: producto.nombre,
              marca: producto.marca || '',
              categoria: producto.categoria,
              precio: producto.precio,
              stock: producto.stock,
              url_producto: producto.url_producto,
              imagen_url: producto.imagen_url,
              descripcion: producto.descripcion || producto.nombre,
              tienda: 'PREUNIC',
              tiendas_disponibles: ['PREUNIC'],
              tiendas_detalladas: [{
                tienda: 'PREUNIC',
                precio: producto.precio,
                stock: producto.stock,
                url_producto: producto.url_producto
              }],
              num_precios: 1
            }
          };
        } else if (isMaicaoProduct) {
          // Para Maicao, necesitamos buscar el producto por ID
          const productId = id.replace('maicao_', '');
          const searchResponse = await axios.get(`/api/productos-maicao/`);
          const productos = searchResponse.data.productos || [];
          const producto = productos.find(p => p.id.toString() === productId);
          
          if (!producto) {
            throw new Error('Producto no encontrado');
          }
          
          // Adaptar el formato para que sea compatible con el resto del componente
          response = {
            data: {
              id: producto.id,
              nombre: producto.nombre,
              marca: producto.marca || '',
              categoria: producto.categoria,
              precio: producto.precio,
              stock: producto.stock,
              url_producto: producto.url_producto,
              imagen_url: producto.imagen_url,
              descripcion: producto.descripcion || producto.nombre,
              tienda: 'MAICAO',
              tiendas_disponibles: ['MAICAO'],
              tiendas_detalladas: [{
                tienda: 'MAICAO',
                precio: producto.precio,
                stock: producto.stock,
                url_producto: producto.url_producto
              }],
              num_precios: 1
            }
          };
        } else if (isDBSProduct) {
          // Para DBS, necesitamos buscar el producto por ID
          const productId = id.replace('dbs_', '');
          const searchResponse = await axios.get(`/api/productos-dbs/`);
          const productos = searchResponse.data.productos || [];
          const producto = productos.find(p => p.id.toString() === productId);
          
          if (!producto) {
            throw new Error('Producto no encontrado');
          }
          
          // Adaptar el formato para que sea compatible con el resto del componente
          response = {
            data: {
              id: producto.id,
              nombre: producto.nombre,
              marca: producto.marca || '',
              categoria: producto.categoria,
              precio: producto.precio,
              stock: producto.stock,
              url_producto: producto.url_producto,
              imagen_url: producto.imagen_url,
              descripcion: producto.descripcion || producto.nombre,
              tienda: 'DBS',
              tiendas_disponibles: ['DBS'],
              tiendas_detalladas: [{
                tienda: 'DBS',
                precio: producto.precio,
                stock: producto.stock,
                url_producto: producto.url_producto
              }],
              num_precios: 1
            }
          };
        } else {
          // Fallback para IDs antiguos sin prefijo
          response = await axios.get(`/api/productos-dbs/${id}/`);
        }
        
        setProducto(response.data);
        
        // Obtener reseñas solo para productos DBS
        if (isDBSProduct) {
          const productId = id.replace('dbs_', '');
          await fetchReviews(productId);
        } else if (!isPreunicProduct && !isMaicaoProduct) {
          // Fallback para IDs antiguos sin prefijo
          await fetchReviews(id);
        }
      } catch (error) {
        console.error('Error fetching producto:', error);
        message.error('Error al cargar el producto');
      } finally {
        setLoading(false);
      }
    };
    
    const fetchReviews = async (productId) => {
      try {
        setReviewsLoading(true);
        const reviews = await productService.getProductReviews(productId);
        setReviewsData(reviews);
      } catch (error) {
        console.error('Error fetching reviews:', error);
        // No mostrar error al usuario ya que las reseñas son opcionales
      } finally {
        setReviewsLoading(false);
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
    
    // Si la URL ya es completa (incluyendo Preunic), usarla directamente
    if (imagenUrl.startsWith('http')) {
      return imagenUrl;
    }
    
    // Si es una ruta relativa, agregar el dominio de DBS
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
                <div className="brand-name">
                  {producto.marca}
                  {producto.tienda && (
                    <span style={{ 
                      marginLeft: '10px', 
                      fontSize: '12px', 
                      backgroundColor: producto.tienda === 'PREUNIC' ? '#f6ffed' : '#e6f7ff',
                      color: producto.tienda === 'PREUNIC' ? '#52c41a' : '#1890ff',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontWeight: 'bold'
                    }}>
                      {producto.tienda === 'PREUNIC' ? '🛒 Preunic' : '🛍️ DBS'}
                    </span>
                  )}
                </div>
                <Title level={2} className="product-name">{producto.nombre}</Title>
                
                {/* Rating - Solo mostrar si hay reseñas reales */}
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
                  {/* Solo mostrar alerta de precio para productos DBS */}
                  {!id.startsWith('preunic_') && !id.startsWith('maicao_') && (
                    <Button 
                      type="primary" 
                      size="large" 
                      icon={<BellOutlined />}
                      className="alert-button"
                      onClick={() => setModalVisible(true)}
                    >
                      Activar alerta de precio
                    </Button>
                  )}
                  
                  {/* Para productos de Preunic, mostrar botón de ir a tienda */}
                  {id.startsWith('preunic_') && producto.url_producto && (
                    <Button 
                      type="primary" 
                      size="large" 
                      className="store-button"
                      onClick={() => window.open(producto.url_producto, '_blank')}
                    >
                      🛒 Ver en Preunic
                    </Button>
                  )}
                  
                  {/* Para productos de Maicao, mostrar botón de ir a tienda */}
                  {id.startsWith('maicao_') && producto.url_producto && (
                    <Button 
                      type="primary" 
                      size="large" 
                      className="store-button"
                      onClick={() => window.open(producto.url_producto, '_blank')}
                    >
                      💄 Ver en Maicao
                    </Button>
                  )}
                  
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

        {/* Product Reviews Section - Solo para productos DBS */}
        {!id.startsWith('preunic_') && !id.startsWith('maicao_') && <ProductReviews productId={id} />}
      </Content>
      
      {/* Price Alert Modal - Solo para productos DBS */}
      {!id.startsWith('preunic_') && !id.startsWith('maicao_') && (
        <PriceAlertModal
          visible={modalVisible}
          onClose={() => setModalVisible(false)}
          producto={producto}
        />
      )}
    </Layout>
  );
};

export default DetalleProducto; 