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
import { productService } from '../../services/api';
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
        
        // Intentar buscar en productos unificados primero
        let foundProduct = await unifiedProductsService.getProductById(decodedId);
        
        if (foundProduct) {
          // Convertir a formato esperado
          const convertedProduct = unifiedProductsService.convertToListingFormat([foundProduct])[0];
          setProduct(convertedProduct);
        } else {
          // Fallback: buscar en APIs individuales para IDs legacy (dbs_559, etc.)
          await handleLegacyId(decodedId);
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

  const handleLegacyId = async (legacyId) => {
    try {
      // Para IDs prefijados como dbs_559, maicao_123, etc.
      if (/^(dbs|maicao|preunic)_/.test(legacyId)) {
        const [storeName] = legacyId.split('_');
        const storeProducts = await unifiedProductsService.getProductsByStore(storeName);
        
        // Buscar el producto específico
        const foundStoreProduct = storeProducts.find(p => 
          p.id === legacyId || p.unified_product_id === legacyId
        );
        
        if (foundStoreProduct) {
          // Convertir producto individual a formato detalle
          setProduct({
            product_id: foundStoreProduct.unified_product_id || legacyId,
            nombre: foundStoreProduct.nombre,
            marca: foundStoreProduct.marca,
            categoria: foundStoreProduct.categoria,
            imagen: foundStoreProduct.imagen,
            precioMin: foundStoreProduct.precio,
            tiendasCount: 1,
            tiendas: [storeName],
            ofertas: [{
              fuente: foundStoreProduct.fuente,
              precio: foundStoreProduct.precio,
              stock: foundStoreProduct.stock,
              url: foundStoreProduct.url,
              imagen: foundStoreProduct.imagen,
              marca_origen: foundStoreProduct.marca
            }]
          });
        }
      }
      // Para IDs numéricos legacy
      else if (/^\d+$/.test(legacyId)) {
        // Buscar en todas las tiendas
        const [dbsProducts, preunicProducts, maicaoProducts] = await Promise.all([
          unifiedProductsService.getProductsByStore('dbs'),
          unifiedProductsService.getProductsByStore('preunic'),
          unifiedProductsService.getProductsByStore('maicao')
        ]);
        
        const allStoreProducts = [...dbsProducts, ...preunicProducts, ...maicaoProducts];
        const foundProduct = allStoreProducts.find(p => p.id.includes(legacyId));
        
        if (foundProduct) {
          setProduct({
            product_id: foundProduct.unified_product_id || legacyId,
            nombre: foundProduct.nombre,
            marca: foundProduct.marca,
            categoria: foundProduct.categoria,
            imagen: foundProduct.imagen,
            precioMin: foundProduct.precio,
            tiendasCount: 1,
            tiendas: [foundProduct.fuente],
            ofertas: [{
              fuente: foundProduct.fuente,
              precio: foundProduct.precio,
              stock: foundProduct.stock,
              url: foundProduct.url,
              imagen: foundProduct.imagen,
              marca_origen: foundProduct.marca
            }]
          });
        }
      }
    } catch (error) {
      console.error('Error handling legacy ID:', error);
    }
  };

  // Cargar reseñas cuando se encuentra el producto
  useEffect(() => {
    const loadReviews = async () => {
      if (product) {
        try {
          // Intentar cargar reseñas usando diferentes IDs
          const reviewId = product.ofertas?.[0]?.productId || product.product_id || id;
          if (reviewId) {
            const reviews = await productService.getProductReviews(reviewId);
        setReviewsData(reviews);
          }
      } catch (error) {
          console.error('Error loading reviews:', error);
        }
      }
    };

    loadReviews();
  }, [product, id]);

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
              { title: product.categoria || 'Productos', href: '/productos' },
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
                    src={getImageUrl(product.imagen)} 
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
                          <Text className="best-price">{formatPrice(product.precioMin)}</Text>
                  </div>
                    <div className="price-info">
                          <Text className="price-label">Disponible en</Text>
                          <Text style={{ color: '#52c41a', fontWeight: 'bold' }}>
                            {product.tiendasCount} {product.tiendasCount === 1 ? 'tienda' : 'tiendas'}
                          </Text>
                    </div>
                      </>
                    ) : (
                      <Text className="best-price">{formatPrice(product.precioMin)}</Text>
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
                  Comparación de tiendas ({product.ofertas?.length || 0})
                </Title>
                <div className="comparacion" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {(product.ofertas || []).map((oferta, index) => (
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
              <>
                <Title level={3}>Información de la tienda</Title>
                <Card className="store-info-card">
                  <div className="store-row">
                    <span className="store-name">
                      {getStoreDisplayName(product.ofertas?.[0]?.fuente || product.tiendas?.[0])}
                    </span>
                    <span className="store-stock" style={{ color: getStockColor(product.ofertas?.[0]?.stock) }}>
                      {product.ofertas?.[0]?.stock || 'Desconocido'}
                    </span>
                    <strong className="store-price">
                      ${(product.precioMin || 0).toLocaleString("es-CL")}
                    </strong>
                    <a 
                      href={product.ofertas?.[0]?.url} 
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
          <ProductReviews productId={product.product_id || id} />

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
