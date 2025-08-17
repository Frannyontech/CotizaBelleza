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
  HeartOutlined
} from '@ant-design/icons';
import { productService } from '../../services/api';
import { resolveImageUrl, getDefaultThumbnail } from '../../utils/image';
import { toCanonical, hasProductMatches } from '../../utils/dedupe';
import { clientKey } from '../../utils/groupCanon';
import PriceAlertModal from '../../components/PriceAlertModal';
import ProductReviews from '../../components/ProductReviews';
import './DetalleProducto.css';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const DetalleProducto = () => {
  const { id } = useParams();
  const [allItems, setAllItems] = useState([]);
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewsData, setReviewsData] = useState(null);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [originalProduct, setOriginalProduct] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Cargar todos los items de todas las tiendas
        const [dbsResponse, preunicResponse, maicaoResponse] = await Promise.all([
          fetch('http://localhost:8000/api/productos-dbs/'),
          fetch('http://localhost:8000/api/productos-preunic/'),
          fetch('http://localhost:8000/api/productos-maicao/')
        ]);

        const [dbsData, preunicData, maicaoData] = await Promise.all([
          dbsResponse.json(),
          preunicResponse.json(),
          maicaoResponse.json()
        ]);

        const allProducts = [
          ...(dbsData.productos || []),
          ...(preunicData.productos || []),
          ...(maicaoData.productos || [])
        ];

        setAllItems(allProducts);
      } catch (error) {
        console.error('Error loading products:', error);
        message.error('Error al cargar los productos');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Recalcular productos canónicos y buscar el específico cuando cambian los datos o el ID
  useEffect(() => {
    if (allItems.length > 0 && id) {
      const canonical = toCanonical(allItems);
      
      // Buscar por ID canónico primero
      let foundProduct = canonical.find(p => p.product_id === id);
      
      // Si no se encuentra, verificar diferentes formatos de ID
      if (!foundProduct) {
        let rawProduct = null;
        
        // 1. ID numérico simple (formato anterior): "559"
        if (/^\d+$/.test(id)) {
          rawProduct = allItems.find(item => item.id && item.id.toString() === id);
        }
        
        // 2. ID prefijado por tienda: "dbs_559", "maicao_123", "preunic_456"
        else if (/^(dbs|maicao|preunic)_\d+$/.test(id)) {
          const numericId = id.split('_')[1];
          const tiendaPrefix = id.split('_')[0];
          rawProduct = allItems.find(item => 
            item.id && item.id.toString() === numericId &&
            (item.fuente?.toLowerCase() === tiendaPrefix || item.tienda?.toLowerCase() === tiendaPrefix)
          );
        }
        
        if (rawProduct) {
          // Crear un producto canónico temporal para este caso
          foundProduct = {
            product_id: `temp_${id}`,
            nombre: rawProduct.nombre || 'Producto',
            categoria: rawProduct.categoria || '',
            imagen: rawProduct.imagen_url || rawProduct.imagen || '',
            precioMin: rawProduct.precio || 0,
            tiendasCount: 1,
            ofertas: [{
              fuente: rawProduct.fuente || rawProduct.tienda?.toLowerCase() || 'desconocido',
              precio: rawProduct.precio || 0,
              stock: rawProduct.stock || 'Desconocido',
              url: rawProduct.url || rawProduct.url_producto || '',
              imagen: rawProduct.imagen_url || rawProduct.imagen || '',
              marca_origen: rawProduct.marca || ''
            }]
          };
          // Establecer como producto original para usar datos completos
          setOriginalProduct(rawProduct);
        }
      }
      
      setProduct(foundProduct || null);
      
      console.log('DetalleProducto - ID:', id);
      console.log('DetalleProducto - foundProduct:', foundProduct);
      
      // Determinar si mostrar comparación o legacy
      if (foundProduct) {
        const hasMultipleStores = foundProduct.tiendasCount > 1;
        setShowComparison(hasMultipleStores);
        
        console.log('DetalleProducto - showComparison:', hasMultipleStores);
        console.log('DetalleProducto - tiendasCount:', foundProduct.tiendasCount);
      }
    }
  }, [allItems, id]);

  // Cargar reseñas cuando se encuentra el producto
  useEffect(() => {
    const loadReviews = async () => {
      if (product || originalProduct) {
        try {
          setReviewsLoading(true);
          const productIdForReviews = originalProduct?.id || product?.id || product?.product_id;
          if (productIdForReviews) {
            const reviews = await productService.getProductReviews(productIdForReviews);
            setReviewsData(reviews);
          }
        } catch (error) {
          console.error('Error loading reviews:', error);
        } finally {
          setReviewsLoading(false);
        }
      }
    };

    loadReviews();
  }, [product, originalProduct]);

  const getImageUrl = (imagenUrl) => {
    // Usar el helper de imagen existente
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

  // Función helper para verificar stock de forma segura
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

  if (!product && !originalProduct && allItems.length > 0) {
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

  if (!product && !originalProduct) {
    return (
      <div style={{ textAlign: 'center', padding: '50px', minHeight: '400px' }}>
        <Text>Inicializando...</Text>
      </div>
    );
  }

  // Determinar qué datos usar para el renderizado unificado
  const displayProduct = originalProduct || product;
  const isLegacyProduct = originalProduct && !showComparison;
  const isMultiStore = showComparison && product;

  // Usar diseño unificado para ambos tipos
  if (displayProduct) {
    return (
      <Layout className="detalle-producto-layout">
        <Content style={{ padding: '0', background: '#f5f5f5' }}>
          <div className="detalle-producto-content">
          {/* Breadcrumbs Unificados */}
          <div className="breadcrumb-container">
            <Breadcrumb items={[
              { title: 'Inicio', href: '/' },
              { title: displayProduct.categoria || 'Productos', href: '/productos' },
              { title: displayProduct.nombre }
            ]} />
          </div>

          {/* Product Information Section - Diseño Unificado */}
          <div className="product-info-section">
            <Row gutter={[32, 32]}>
              {/* Product Image */}
              <Col xs={24} md={12}>
                <div className="product-image-container">
                  <img 
                    src={getImageUrl(displayProduct.imagen_url || displayProduct.imagen)} 
                    alt={displayProduct.nombre}
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
                  <Title level={2} className="product-name">{displayProduct.nombre}</Title>
                  
                  {/* Product Brand - Solo mostrar si existe */}
                  {displayProduct.marca && (
                    <Text className="product-brand">{displayProduct.marca}</Text>
                  )}
                  
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
                    {isMultiStore ? (
                      // Para productos agrupados - mostrar rango de precios
                      <div className="price-info">
                        <Text className="price-label">Mejor precio</Text>
                        <Text className="best-price">{formatPrice(displayProduct.precioMin)}</Text>
                      </div>
                    ) : (
                      // Para productos individuales - mostrar precio único
                      <Text className="best-price">{formatPrice(displayProduct.precio || displayProduct.precioMin)}</Text>
                    )}
                    
                    {isMultiStore && (
                      <div className="price-info">
                        <Text className="price-label">Disponible en</Text>
                        <Text style={{ color: '#52c41a', fontWeight: 'bold' }}>
                          {displayProduct.tiendasCount} {displayProduct.tiendasCount === 1 ? 'tienda' : 'tiendas'}
                        </Text>
                      </div>
                    )}
                  </div>

                  {/* Product Description */}
                  <div className="description-section">
                    <Paragraph className="product-description">
                      {displayProduct.descripcion || 
                       (isMultiStore 
                         ? `${displayProduct.nombre}. Producto de calidad disponible en ${displayProduct.tiendasCount} ${displayProduct.tiendasCount === 1 ? 'tienda' : 'tiendas'}.`
                         : `${displayProduct.nombre}. Producto de calidad de la marca ${displayProduct.marca || 'reconocida'}.`
                       )}
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
              // Para productos con múltiples tiendas - mostrar comparación
              <>
                <Title level={3}>
                  Comparación de tiendas ({displayProduct.ofertas?.length || 0})
                </Title>
                <div className="comparacion" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {(displayProduct.ofertas || []).sort((a,b) => a.precio - b.precio).map((oferta, index) => (
                    <Card key={index} className="store-info-card">
                      <div className="store-row">
                        <span className="store-name">
                          {getStoreDisplayName(oferta.fuente)}
                        </span>
                        <span className="store-stock" style={{ color: getStockColor(oferta.stock) }}>
                          {oferta.stock || 'Desconocido'}
                        </span>
                        <strong className="store-price">
                          ${oferta.precio.toLocaleString("es-CL")}
                        </strong>
                        <a 
                          href={oferta.url} 
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
              // Para productos individuales - mostrar información de tienda única
              <>
                <Title level={3}>Información de la tienda</Title>
                <Card className="store-info-card">
                  <div className="store-row">
                    <span className="store-name">
                      {getStoreDisplayName(displayProduct.fuente || displayProduct.tienda)}
                    </span>
                    <span className="store-stock" style={{ color: getStockColor(displayProduct.stock) }}>
                      {displayProduct.stock || 'Desconocido'}
                    </span>
                    <strong className="store-price">
                      ${(displayProduct.precio || displayProduct.precioMin || 0).toLocaleString("es-CL")}
                    </strong>
                    <a 
                      href={displayProduct.url || displayProduct.url_producto} 
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
          <ProductReviews productId={displayProduct.product_id || displayProduct.id} />

          {/* Price Alert Modal */}
          <PriceAlertModal
            visible={modalVisible}
            onClose={() => setModalVisible(false)}
            producto={displayProduct}
          />

          </div>
        </Content>
      </Layout>
    );
  }

  // Fallback si no hay producto
  return (
    <div style={{ textAlign: 'center', padding: '50px', minHeight: '400px' }}>
      <Text>Producto no disponible</Text>
      <br />
      <Button onClick={() => window.location.href = '/'}>
        Volver al inicio
      </Button>
    </div>
  );
};

export default DetalleProducto;
