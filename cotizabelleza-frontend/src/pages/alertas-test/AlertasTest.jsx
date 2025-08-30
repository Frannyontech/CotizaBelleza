import React, { useState } from 'react';
import { Card, Button, Input, Form, message, Divider, Typography, Space } from 'antd';
import { BellOutlined, MailOutlined, SendOutlined } from '@ant-design/icons';
import AlertasManager from '../../components/AlertasManager';
import PriceAlertModal from '../../components/PriceAlertModal';
import axios from 'axios';

const { Title, Paragraph } = Typography;

const AlertasTest = () => {
  const [emailTestForm] = Form.useForm();
  const [alertModalVisible, setAlertModalVisible] = useState(false);
  const [testProduct] = useState({
    id: 'test-product-1',
    nombre: 'Producto de Prueba - Crema Hidratante',
    marca: 'Marca Test',
    precio: 25000
  });

  const handleEmailTest = async (values) => {
    try {
      const response = await axios.post('/api/email-test/', {
        email: values.email,
        tipo: values.tipo || 'welcome'
      });
      
      message.success(response.data.message);
      emailTestForm.resetFields();
    } catch (error) {
      console.error('Error sending test email:', error);
      message.error('Error enviando email de prueba');
    }
  };

  const handleCreateTestAlert = () => {
    setAlertModalVisible(true);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>
        <BellOutlined /> Sistema de Alertas por Email - Pruebas
      </Title>
      
      <Paragraph>
        Esta página permite probar el sistema de alertas por email de CotizaBelleza.
        Puedes crear alertas de prueba, enviar emails de prueba y gestionar alertas existentes.
      </Paragraph>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* Panel de Pruebas de Email */}
        <Card title={<><MailOutlined /> Pruebas de Email</>}>
          <Form
            form={emailTestForm}
            layout="vertical"
            onFinish={handleEmailTest}
          >
            <Form.Item
              name="email"
              label="Email de prueba"
              rules={[
                { required: true, message: 'Ingresa un email' },
                { type: 'email', message: 'Email inválido' }
              ]}
            >
              <Input placeholder="tu@email.com" />
            </Form.Item>

            <Form.Item
              name="tipo"
              label="Tipo de email"
              initialValue="dev_test"
            >
              <Input.Group compact>
                <Button
                  type="default"
                  style={{ width: '33%' }}
                  onClick={() => emailTestForm.setFieldsValue({ tipo: 'dev_test' })}
                >
                  Prueba DEV
                </Button>
                <Button
                  type="default"
                  style={{ width: '33%' }}
                  onClick={() => emailTestForm.setFieldsValue({ tipo: 'welcome' })}
                >
                  Bienvenida
                </Button>
                <Button
                  type="default"
                  style={{ width: '33%' }}
                  onClick={() => emailTestForm.setFieldsValue({ tipo: 'price_alert' })}
                >
                  Alerta de Precio
                </Button>
              </Input.Group>
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SendOutlined />}
                block
              >
                Enviar Email de Prueba
              </Button>
            </Form.Item>
          </Form>

          <Divider />

          <Space direction="vertical" style={{ width: '100%' }}>
            <Button
              type="default"
              onClick={handleCreateTestAlert}
              icon={<BellOutlined />}
              block
            >
              Crear Alerta de Prueba
            </Button>
            
            <Paragraph style={{ fontSize: '12px', color: '#666', margin: 0 }}>
              <strong>Nota:</strong> Para las pruebas, se usa el usuario ID=1 por defecto.
              En producción, esto debería usar el usuario autenticado.
            </Paragraph>
          </Space>
        </Card>

        {/* Panel de Información */}
        <Card title="Información del Sistema">
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Title level={5}>Funcionalidades Implementadas:</Title>
              <ul>
                <li>✅ Creación de alertas de precio</li>
                <li>✅ Gestión de alertas (editar, eliminar)</li>
                <li>✅ Envío de emails de alerta</li>
                <li>✅ Plantillas de email personalizadas</li>
                <li>✅ Integración con ETL</li>
                <li>✅ Tareas de Celery programadas</li>
              </ul>
            </div>

            <div>
              <Title level={5}>Endpoints API:</Title>
              <ul>
                <li><code>GET /api/alertas/</code> - Listar alertas</li>
                <li><code>POST /api/alertas/</code> - Crear alerta</li>
                <li><code>PUT /api/alertas/{id}/</code> - Actualizar alerta</li>
                <li><code>DELETE /api/alertas/{id}/</code> - Eliminar alerta</li>
                <li><code>POST /api/email-test/</code> - Probar emails</li>
              </ul>
            </div>

            <div>
              <Title level={5}>Comandos de Prueba:</Title>
              <ul>
                <li><code>python manage.py test_email_alerts --create-templates</code></li>
                <li><code>python manage.py test_email_alerts --create-test-alerts</code></li>
                <li><code>python manage.py test_email_alerts --trigger-alerts</code></li>
                <li><code>python manage.py test_email_alerts --send-test-email tu@email.com</code></li>
              </ul>
            </div>
          </Space>
        </Card>
      </div>

      {/* Gestor de Alertas */}
                  <AlertasManager email="fran.galazojeda@gmail.com" />

      {/* Modal para crear alerta de prueba */}
      <PriceAlertModal
        visible={alertModalVisible}
        onClose={() => setAlertModalVisible(false)}
        producto={testProduct}
      />
    </div>
  );
};

export default AlertasTest;
