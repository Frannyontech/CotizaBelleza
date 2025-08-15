import React, { useState } from 'react';
import { Modal, Form, Input, Button, message } from 'antd';
import { MailOutlined } from '@ant-design/icons';
import axios from 'axios';

const PriceAlertModal = ({ visible, onClose, producto }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

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
      
      const response = await axios.post('/api/alertas-precio/', {
        producto_id: producto.id,
        email: values.email
      });

      message.success('¡Alerta de precio activada exitosamente! Te notificaremos cuando cambie el precio.');
      form.resetFields();
      onClose();
      
    } catch (error) {
      console.error('Error al crear alerta:', error);
      
      if (error.response?.data?.error) {
        message.error(error.response.data.error);
      } else {
        message.error('Error al crear la alerta. Por favor intenta nuevamente.');
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
  );
};

export default PriceAlertModal;
