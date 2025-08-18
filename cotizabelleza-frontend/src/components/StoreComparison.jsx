import React from 'react';
import {
  Card,
  List,
  Avatar,
  Typography,
  Tag,
  Button,
  Space,
  Row,
  Col,
  Skeleton,
  Empty
} from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import { getDefaultThumbnail } from '../utils/image';
import './StoreComparison.css';

const { Text, Title } = Typography;

/**
 * Componente para mostrar la comparación de precios entre tiendas
 * @param {Object} props - Propiedades del componente
 * @param {Array} props.offers - Array de ofertas/tiendas con precios
 * @param {string} props.productName - Nombre del producto para accesibilidad
 * @param {boolean} props.loading - Estado de carga
 * @param {Function} props.formatPrice - Función para formatear precios
 * @param {Function} props.calculateDiscount - Función para calcular descuentos
 */
const StoreComparison = ({ 
  offers = [], 
  productName = '', 
  loading = false,
  formatPrice,
  calculateDiscount 
}) => {
  // Ordenar ofertas por precio final ascendente
  const sortedOffers = [...offers].sort((a, b) => {
    const priceA = a.precio || a.finalPrice || 0;
    const priceB = b.precio || b.finalPrice || 0;
    return priceA - priceB;
  });

  // Función para obtener las iniciales del nombre de la tienda
  const getStoreInitials = (storeName) => {
    if (!storeName) return '?';
    return storeName
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // Función para obtener el logo de la tienda (fallback a iniciales)
  const getStoreLogo = (store) => {
    return store.logo || store.storeLogo || null;
  };

  // Función para obtener el nombre de la tienda
  const getStoreName = (store) => {
    return store.nombre || store.storeName || 'Tienda';
  };

  // Función para obtener el precio final
  const getFinalPrice = (store) => {
    return store.precio || store.finalPrice || 0;
  };

  // Función para obtener el precio original
  const getOriginalPrice = (store, productOriginalPrice) => {
    return store.precio_original || store.originalPrice || productOriginalPrice || 0;
  };

  // Función para obtener información de precios de Preunic
  const getPreunicPriceInfo = (store) => {
    if (store.fuente === 'preunic') {
      return {
        hasOffer: store.precio_oferta !== null && store.precio_oferta !== undefined,
        normalPrice: store.precio_normal,
        offerPrice: store.precio_oferta,
        finalPrice: store.precio_oferta || store.precio_normal || store.precio
      };
    }
    return null;
  };

  // Función para verificar si está en stock
  const isInStock = (store) => {
    return store.stock || store.inStock || false;
  };

  // Función para obtener la URL de la tienda
  const getStoreUrl = (store) => {
    return store.url_producto || store.url || '';
  };

  // Función para calcular el descuento
  const getDiscountPercent = (store, productOriginalPrice) => {
    const originalPrice = getOriginalPrice(store, productOriginalPrice);
    const finalPrice = getFinalPrice(store);
    
    if (originalPrice > finalPrice && originalPrice > 0) {
      return calculateDiscount ? calculateDiscount(originalPrice, finalPrice) : 
        Math.round(((originalPrice - finalPrice) / originalPrice) * 100);
    }
    return null;
  };

  // Función para formatear precios en CLP sin decimales
  const formatPriceCLP = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      maximumFractionDigits: 0
    }).format(price);
  };

  // Renderizar skeleton mientras carga
  if (loading) {
    return (
      <Card title="Comparación de precios" className="store-comparison-card">
        <Skeleton active paragraph={{ rows: 3 }} />
      </Card>
    );
  }

  // Renderizar empty state si no hay ofertas
  if (!sortedOffers || sortedOffers.length === 0) {
    return (
      <Card title="Comparación de precios" className="store-comparison-card">
        <Empty 
          description="No hay precios disponibles" 
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  return (
    <Card 
      title="Comparación de precios" 
      className="store-comparison-card"
      role="region"
      aria-label="Comparación de precios entre tiendas"
    >
      <List
        dataSource={sortedOffers}
        renderItem={(store, index) => {
          const storeName = getStoreName(store);
          const finalPrice = getFinalPrice(store);
          const originalPrice = getOriginalPrice(store);
          const inStock = isInStock(store);
          const storeUrl = getStoreUrl(store);
          const discountPercent = getDiscountPercent(store, originalPrice);
          const storeLogo = getStoreLogo(store);
          const storeInitials = getStoreInitials(storeName);

          return (
            <List.Item 
              key={index}
              className="store-comparison-item"
              role="listitem"
            >
              <Row gutter={[16, 16]} style={{ width: '100%' }}>
                {/* Logo de la tienda */}
                <Col xs={24} sm={24} md={4} lg={3}>
                  <div style={{ textAlign: 'center' }}>
                                         <Avatar
                       shape="square"
                       size={40}
                       src={storeLogo || getDefaultThumbnail()}
                       style={{ 
                         backgroundColor: storeLogo ? 'transparent' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                         fontSize: '16px',
                         fontWeight: 'bold',
                         color: 'white'
                       }}
                     >
                       {!storeLogo && storeInitials}
                     </Avatar>
                  </div>
                </Col>

                {/* Información de la tienda y precios */}
                <Col xs={24} sm={24} md={14} lg={15}>
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    {/* Header con nombre y stock */}
                    <Row justify="space-between" align="middle">
                      <Col>
                                                 <Text strong style={{ fontSize: '18px', color: '#2c3e50' }}>
                           {storeName}
                         </Text>
                      </Col>
                      <Col>
                        <Tag 
                          color={inStock ? 'green' : 'red'}
                          style={{ 
                            fontWeight: 'bold',
                            borderRadius: '6px'
                          }}
                        >
                          {inStock ? 'En stock' : 'Sin stock'}
                        </Tag>
                      </Col>
                    </Row>

                    {/* Precios */}
                    <Row align="middle" gutter={[8, 8]}>
                      <Col>
                        {(() => {
                          const preunicInfo = getPreunicPriceInfo(store);
                          
                          if (preunicInfo && preunicInfo.hasOffer) {
                            // Mostrar precio de oferta para Preunic
                            return (
                              <Space direction="vertical" size={2}>
                                <Title 
                                  level={4} 
                                  style={{ 
                                    margin: 0, 
                                    color: '#e74c3c',
                                    fontWeight: 'bold',
                                    fontSize: '20px'
                                  }}
                                >
                                  {formatPrice ? formatPrice(preunicInfo.offerPrice) : formatPriceCLP(preunicInfo.offerPrice)}
                                  <Tag color="red" size="small" style={{ marginLeft: 8 }}>OFERTA</Tag>
                                </Title>
                                <Text 
                                  type="secondary" 
                                  delete 
                                  style={{ fontSize: '14px', color: '#8c9bab' }}
                                >
                                  Normal: {formatPrice ? formatPrice(preunicInfo.normalPrice) : formatPriceCLP(preunicInfo.normalPrice)}
                                </Text>
                              </Space>
                            );
                          } else {
                            // Precio normal para otras tiendas o Preunic sin oferta
                            return (
                              <Title 
                                level={4} 
                                style={{ 
                                  margin: 0, 
                                  color: '#667eea',
                                  fontWeight: 'bold',
                                  fontSize: '20px'
                                }}
                              >
                                {formatPrice ? formatPrice(finalPrice) : formatPriceCLP(finalPrice)}
                              </Title>
                            );
                          }
                        })()}
                      </Col>
                      
                      {/* Precio original tachado si hay descuento (para tiendas que no son Preunic) */}
                        <Col>
                          <Text 
                            type="secondary" 
                            delete 
                            style={{ fontSize: '15px', color: '#8c9bab' }}
                          >
                            {formatPrice ? formatPrice(originalPrice) : formatPriceCLP(originalPrice)}
                          </Text>
                        </Col>
                      )}
                      
                      {/* Tag de descuento para tiendas que no son Preunic */}
                        <Col>
                          <Tag 
                            color="red" 
                            style={{ 
                             fontWeight: 'bold',
                             borderRadius: '8px',
                             background: 'linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%)',
                             color: 'white',
                             border: 'none',
                             boxShadow: '0 2px 4px rgba(255, 77, 79, 0.3)'
                           }}
                         >
                           -{discountPercent}%
                         </Tag>
                        </Col>
                      )}
                    </Row>
                  </Space>
                </Col>

                {/* Botón de acción */}
                <Col xs={24} sm={24} md={6} lg={6}>
                  <div style={{ textAlign: 'center' }}>
                                         <Button
                       type="primary"
                       icon={<ExportOutlined />}
                       href={storeUrl}
                       target="_blank"
                       disabled={!inStock || !storeUrl}
                       style={{
                         width: '100%',
                         height: '44px',
                         borderRadius: '12px',
                         fontWeight: 'bold',
                         background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                         border: 'none',
                         boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
                         fontSize: '14px'
                       }}
                       aria-label={`Ir a tienda ${storeName} para ${productName}`}
                       role="button"
                     >
                       Ir a tienda
                     </Button>
                  </div>
                </Col>
              </Row>
            </List.Item>
          );
        }}
        locale={{
          emptyText: 'No hay precios disponibles'
        }}
      />
    </Card>
  );
};

export default StoreComparison;
