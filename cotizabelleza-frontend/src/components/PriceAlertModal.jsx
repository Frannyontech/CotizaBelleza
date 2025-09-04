import React, { useState } from 'react';
import { Modal, Form, Input, Button, App, notification } from 'antd';
import { MailOutlined } from '@ant-design/icons';
import axios from 'axios';

const PriceAlertModal = ({ visible, onClose, producto }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const { message } = App.useApp();
  const [api, contextHolder] = notification.useNotification();

  const validateEmail = (_, value) => {
    if (!value) {
      return Promise.reject(new Error('Por favor ingresa tu correo electrónico'));
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return Promise.reject(new Error('Por favor ingresa un correo electrónico válido'));
    }
    
    return Promise.resolve();
  };

  const handleSubmit = async (values) => {
    try {
      setLoading(true);
      
      console.log('🚀 Enviando alerta:', {
        producto_id: producto.product_id,
        email: values.email
      });
      
      console.log('🌐 URL de la petición:', '/api/alertas/');
      console.log('📤 Datos enviados:', {
        producto_id: producto.product_id,
        email: values.email
      });
      
      const response = await axios.post('/api/alertas/', {
        producto_id: producto.product_id,
        email: values.email
      });

             // Alerta creada exitosamente
       api.success({
         message: '¡Alerta creada exitosamente!',
         placement: 'topRight',
         duration: 5,
       });
      form.resetFields();
      onClose();
      
    } catch (error) {
      // Solo log del error principal, sin detalles técnicos
      console.error('❌ Error al crear alerta:', error.message || 'Error desconocido');
      
      if (error.response?.status === 400 && error.response?.data?.error === 'email_already_subscribed') {
        // Email ya está suscrito
        api.error({
          message: '¡El correo ya está suscrito a este producto!',
          placement: 'topRight',
          duration: 5,
        });
      } else {
        // Para todos los demás errores (429, otros 400, errores de red, etc.)
        // NO mostrar ningún mensaje al usuario, solo log en consola
        console.log('🔴 Error detectado pero no mostrando al usuario:', {
          status: error.response?.status,
          error: error.response?.data?.error || error.message
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onClose();
  };

  return (
    <>
      {contextHolder}
      <Modal
        title="Alertas de cambios de precio"
        open={visible}
        onCancel={handleCancel}
        footer={null}
        width={500}
        centered
        destroyOnClose
        role="dialog"
        aria-modal="true"
      >
      <div style={{ marginBottom: 16 }}>
        <p>
          Ingresa tu correo y te notificaremos cuando este producto cambie de precio o disponibilidad.
        </p>
        {producto && (
          <p style={{ fontWeight: 'bold', color: '#1890ff' }}>
            Producto: {producto.nombre}
          </p>
        )}
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
      >
        <Form.Item
          name="email"
          label="Correo electrónico"
          rules={[
            { required: true, message: 'Por favor ingresa tu correo electrónico' },
            { validator: validateEmail }
          ]}
        >
          <Input
            prefix={<MailOutlined />}
            placeholder="tu@email.com"
            size="large"
            autoFocus
          />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
          <Button
            type="default"
            onClick={handleCancel}
            style={{ marginRight: 8 }}
            size="large"
          >
            Cerrar
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            size="large"
            style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
          >
            Suscribirse
          </Button>
        </Form.Item>
      </Form>
      </Modal>
    </>
  );
};

export default PriceAlertModal;
