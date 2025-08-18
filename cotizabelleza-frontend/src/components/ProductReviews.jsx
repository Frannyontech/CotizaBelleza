import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Rate, 
  List, 
  Skeleton, 
  Empty, 
  Alert, 
  Divider,
  Row,
  Col,
  Button,
  message
} from 'antd';
import { useNavigate } from 'react-router-dom';
import { productService } from '../services/api';
import CreateReviewModal from './CreateReviewModal';
import dayjs from 'dayjs';
import 'dayjs/locale/es';

// Configurar dayjs en español
dayjs.locale('es');

const { Title, Text, Paragraph, Link } = Typography;

const ProductReviews = ({ productId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviewsData, setReviewsData] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const navigate = useNavigate();

  const fetchReviews = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await productService.getProductReviews(productId);
      setReviewsData(data);
    } catch (err) {
      console.error('Error fetching reviews:', err);
      const errorMessage = err.response?.data?.error || 'Error al cargar las reseñas';
      
      // Si el error es por ID inválido o producto no encontrado, no mostrar error
      if (errorMessage.includes('inválido') || errorMessage.includes('no encontrado')) {
        setReviewsData({ resenas: [], total_resenas: 0, promedio_valoracion: 0 });
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId && productId !== 'null' && productId !== 'undefined') {
      fetchReviews();
    } else {
      // Si no hay productId válido, establecer estado vacío
      setReviewsData({ resenas: [], total_resenas: 0, promedio_valoracion: 0 });
      setLoading(false);
    }
  }, [productId]);

  const handleModalSuccess = () => {
    setModalOpen(false);
    fetchReviews(); // Refetch reviews after successful creation
    message.success('Reseña publicada exitosamente');
  };

  const handleViewAllReviews = () => {
    // Navegar a la vista completa de reseñas (ajustar ruta según el proyecto)
    navigate(`/producto/${productId}/resenas`);
  };

  const formatDate = (dateString) => {
    return dayjs(dateString).format('D MMMM YYYY');
  };

  if (loading) {
    return (
      <div style={{ marginTop: 32 }}>
        <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
          <Col>
            <Skeleton.Input active size="default" style={{ width: 200 }} />
          </Col>
          <Col>
            <Skeleton.Input active size="small" style={{ width: 120 }} />
          </Col>
        </Row>
        <List
          split={false}
          dataSource={[1, 2, 3]}
          renderItem={() => (
            <List.Item style={{ paddingLeft: 0, paddingRight: 0 }}>
              <div style={{ width: '100%' }}>
                <Skeleton active paragraph={{ rows: 2 }} />
                <Divider style={{ margin: '16px 0' }} />
              </div>
            </List.Item>
          )}
        />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ marginTop: 32 }}>
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={fetchReviews}>
              Reintentar
            </Button>
          }
        />
      </div>
    );
  }

  if (!reviewsData || reviewsData.total_resenas === 0) {
    return (
      <div style={{ marginTop: 32 }}>
        <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
          <Col>
            <Title level={4} style={{ margin: 0 }}>
              Reseñas de usuarias
            </Title>
          </Col>
          <Col>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Rate 
                allowHalf 
                disabled 
                value={0} 
                style={{ fontSize: 16 }}
              />
              <Text strong>0.0</Text>
              <Text type="secondary">(0)</Text>
            </div>
          </Col>
        </Row>
        <Empty 
          description="Aún no hay reseñas"
          style={{ padding: '40px 0' }}
        >
          <Button 
          type="primary" 
          onClick={() => setModalOpen(true)}
          disabled={!productId || productId === 'null' || productId === 'undefined'}
        >
            Escribir reseña
          </Button>
        </Empty>

        {/* Modal para crear reseña */}
        <CreateReviewModal
          open={modalOpen}
          onCancel={() => setModalOpen(false)}
          onSuccess={handleModalSuccess}
          productId={productId}
        />
      </div>
    );
  }

  const { total_resenas, promedio_valoracion, resenas_recientes } = reviewsData;

  return (
    <div style={{ marginTop: 32 }}>
      {/* Cabecera */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>
            Reseñas de usuarias
          </Title>
        </Col>
        <Col>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Rate 
              allowHalf 
              disabled 
              value={promedio_valoracion} 
              style={{ fontSize: 16 }}
            />
            <Text strong>{promedio_valoracion.toFixed(1)}</Text>
            <Text type="secondary">({total_resenas})</Text>
          </div>
        </Col>
      </Row>

      {/* Botón Escribir reseña */}
      <div style={{ marginBottom: 24 }}>
        <Button 
          type="primary" 
          onClick={() => setModalOpen(true)}
          disabled={!productId || productId === 'null' || productId === 'undefined'}
        >
          Escribir reseña
        </Button>
      </div>

      {/* Lista de reseñas */}
      <List
        split={false}
        dataSource={resenas_recientes}
        renderItem={(resena, index) => (
          <List.Item style={{ paddingLeft: 0, paddingRight: 0 }}>
            <div style={{ width: '100%' }}>
              <div style={{ marginBottom: 8 }}>
                <Text strong style={{ display: 'block', marginBottom: 4 }}>
                  {resena.nombre_autor || 'Usuario anónimo'}
                </Text>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <Rate 
                    disabled 
                    value={resena.valoracion} 
                    style={{ fontSize: 14 }}
                  />
                  <Text type="secondary" style={{ fontSize: 14 }}>
                    {formatDate(resena.fecha_creacion)}
                  </Text>
                </div>
              </div>
              <Paragraph 
                style={{ 
                  margin: 0,
                  fontSize: 14,
                  lineHeight: 1.5
                }}
              >
                {resena.comentario}
              </Paragraph>
              {index < resenas_recientes.length - 1 && (
                <Divider style={{ margin: '16px 0' }} />
              )}
            </div>
          </List.Item>
        )}
      />

      {/* Pie con enlace a todas las reseñas */}
      {total_resenas > 3 && (
        <div style={{ textAlign: 'center', marginTop: 24, paddingTop: 16 }}>
          <Link 
            onClick={handleViewAllReviews}
            style={{ fontSize: 14 }}
            aria-label={`Ver todas las ${total_resenas} reseñas del producto`}
          >
            Ver todas las reseñas
          </Link>
        </div>
      )}

      {/* Modal para crear reseña */}
      <CreateReviewModal
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onSuccess={handleModalSuccess}
        productId={productId}
      />
    </div>
  );
};

export default ProductReviews;
