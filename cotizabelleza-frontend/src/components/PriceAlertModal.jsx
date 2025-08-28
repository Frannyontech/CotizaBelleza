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

      console.log('✅ Respuesta exitosa:', response.data);
      console.log('📊 Status:', response.status);
      console.log('📋 Headers:', response.headers);

      // Si llegamos aquí, la alerta se creó exitosamente (201 Created)
      console.log('🎉 Mostrando mensaje de éxito');
      api.success({
        message: '¡Alerta creada exitosamente!',
        placement: 'topRight',
        duration: 5,
      });
      console.log('✅ Mensaje mostrado, cerrando modal');
      form.resetFields();
      onClose();
      
    } catch (error) {
      console.error('❌ Error al crear alerta:', error);
      console.error('❌ Error status:', error.response?.status);
      console.error('❌ Error data:', error.response?.data);
      
      if (error.response?.status === 400 && error.response?.data?.error === 'email_already_subscribed') {
        // Email ya está suscrito
        console.log('🔴 Mostrando mensaje: Email ya suscrito');
        api.error({
          message: '¡El correo ya está suscrito a este producto!',
          placement: 'topRight',
          duration: 5,
        });
      } else if (error.response?.data?.error) {
        // Otros errores del backend
        console.log('🔴 Mostrando mensaje: Otro error del backend');
        api.error({
          message: 'Error',
          description: error.response.data.error,
          placement: 'topRight',
          duration: 5,
        });
      } else {
        // Error genérico
        console.log('🔴 Mostrando mensaje: Error genérico');
        api.error({
          message: 'Error al crear la alerta',
          description: 'Por favor intenta nuevamente',
          placement: 'topRight',
          duration: 5,
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
