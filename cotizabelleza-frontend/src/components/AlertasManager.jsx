import React, { useState, useEffect } from 'react';
import { Card, List, Button, Modal, Form, Input, message, Popconfirm, Tag, Spin, Empty } from 'antd';
import { BellOutlined, EditOutlined, DeleteOutlined, DollarOutlined } from '@ant-design/icons';
import axios from '../config/axios';

const AlertasManager = ({ email = 'fran.galazojeda@gmail.com' }) => {
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingAlerta, setEditingAlerta] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchAlertas();
  }, [email]);

  const fetchAlertas = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/alertas/?email=${encodeURIComponent(email)}`);
      setAlertas(response.data.alertas || []);
    } catch (error) {
      console.error('Error fetching alertas:', error);
      message.error('Error al cargar las alertas');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (alerta) => {
    setEditingAlerta(alerta);
    form.setFieldsValue({
      precio_objetivo: alerta.precio_objetivo
    });
    setEditModalVisible(true);
  };

  const handleEditSubmit = async (values) => {
    try {
      await axios.put(`/api/alertas/${editingAlerta.id}/`, {
        precio_objetivo: parseFloat(values.precio_objetivo)
      });
      
      message.success('Alerta actualizada exitosamente');
      setEditModalVisible(false);
      setEditingAlerta(null);
      form.resetFields();
      fetchAlertas();
    } catch (error) {
      console.error('Error updating alerta:', error);
      message.error('Error al actualizar la alerta');
    }
  };

  const handleDelete = async (alertaId) => {
    try {
      await axios.delete(`/api/alertas/${alertaId}/`);
      message.success('Alerta eliminada exitosamente');
      fetchAlertas();
    } catch (error) {
      console.error('Error deleting alerta:', error);
      message.error('Error al eliminar la alerta');
    }
  };

  const handleToggleActive = async (alerta) => {
    try {
      await axios.put(`/api/alertas/${alerta.id}/`, {
        activa: !alerta.activa
      });
      message.success(`Alerta ${alerta.activa ? 'desactivada' : 'activada'} exitosamente`);
      fetchAlertas();
    } catch (error) {
      console.error('Error toggling alerta:', error);
      message.error('Error al cambiar el estado de la alerta');
    }
  };

  const formatPrice = (price) => {
    return price ? `$${price.toLocaleString()}` : 'N/A';
  };

  const getStatusTag = (alerta) => {
    if (!alerta.activa) {
      return <Tag color="default">Inactiva</Tag>;
    }
    if (alerta.notificada) {
      return <Tag color="orange">Notificada</Tag>;
    }
    return <Tag color="green">Activa</Tag>;
  };

  const getPriceStatus = (alerta) => {
    if (!alerta.precio_actual || !alerta.precio_objetivo) {
      return null;
    }
    
    const diferencia = alerta.precio_objetivo - alerta.precio_actual;
    if (diferencia > 0) {
      return <Tag color="red">Falta ${diferencia.toLocaleString()}</Tag>;
    } else {
      return <Tag color="green">¡Precio alcanzado!</Tag>;
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Cargando alertas...</p>
      </div>
    );
  }

  if (alertas.length === 0) {
    return (
      <Card title={<><BellOutlined /> Mis Alertas de Precio</>}>
        <Empty
          description="No tienes alertas de precio configuradas"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <p>Configura alertas de precio para recibir notificaciones cuando los productos bajen de precio.</p>
        </Empty>
      </Card>
    );
  }

  return (
    <>
      <Card title={<><BellOutlined /> Mis Alertas de Precio ({alertas.length})</>}>
        <List
          dataSource={alertas}
          renderItem={(alerta) => (
            <List.Item
              actions={[
                <Button
                  type="text"
                  icon={<EditOutlined />}
                  onClick={() => handleEdit(alerta)}
                  size="small"
                >
                  Editar
                </Button>,
                <Popconfirm
                  title="¿Estás seguro?"
                  description="Esta acción no se puede deshacer"
                  onConfirm={() => handleDelete(alerta.id)}
                  okText="Sí"
                  cancelText="No"
                >
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    size="small"
                  >
                    Eliminar
                  </Button>
                </Popconfirm>
              ]}
            >
              <List.Item.Meta
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span>{alerta.producto.nombre}</span>
                    {getStatusTag(alerta)}
                    {getPriceStatus(alerta)}
                  </div>
                }
                description={
                  <div>
                    <p style={{ margin: '4px 0' }}>
                      <strong>Marca:</strong> {alerta.producto.marca}
                    </p>
                    <p style={{ margin: '4px 0' }}>
                      <strong>Precio objetivo:</strong> {formatPrice(alerta.precio_objetivo)}
                    </p>
                    <p style={{ margin: '4px 0' }}>
                      <strong>Precio actual:</strong> {formatPrice(alerta.precio_actual)}
                    </p>
                    <p style={{ margin: '4px 0', fontSize: '12px', color: '#666' }}>
                      Creada: {new Date(alerta.fecha_creacion).toLocaleDateString()}
                    </p>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      <Modal
        title="Editar Alerta de Precio"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingAlerta(null);
          form.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        {editingAlerta && (
          <div style={{ marginBottom: 16 }}>
            <p><strong>Producto:</strong> {editingAlerta.producto.nombre}</p>
            <p><strong>Marca:</strong> {editingAlerta.producto.marca}</p>
          </div>
        )}
        
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEditSubmit}
        >
          <Form.Item
            name="precio_objetivo"
            label="Precio objetivo (CLP)"
            rules={[
              { required: true, message: 'Por favor ingresa el precio objetivo' },
              { type: 'number', min: 1, message: 'El precio debe ser mayor a 0' }
            ]}
          >
            <Input
              type="number"
              placeholder="Ej: 15000"
              addonAfter="CLP"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Button
              type="default"
              onClick={() => {
                setEditModalVisible(false);
                setEditingAlerta(null);
                form.resetFields();
              }}
              style={{ marginRight: 8 }}
            >
              Cancelar
            </Button>
            <Button type="primary" htmlType="submit">
              Actualizar
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default AlertasManager;
