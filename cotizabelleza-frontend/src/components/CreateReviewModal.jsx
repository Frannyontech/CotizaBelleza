import React, { useState } from 'react';
import { 
  Modal, 
  Form, 
  Rate, 
  Input, 
  message 
} from 'antd';
import { productService } from '../services/api';

const { TextArea } = Input;

const CreateReviewModal = ({ open, onCancel, onSuccess, productId }) => {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (values) => {
    try {
      setSubmitting(true);
      
      const reviewData = {
        productId: productId,
        rating: values.rating,
        comment: values.comment,
        author: values.author || null
      };

      await productService.createProductReview(reviewData);
      
      form.resetFields();
      onSuccess();
    } catch (error) {
      console.error('Error creating review:', error);
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.message || 
                          'Error al publicar la reseña';
      message.error(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title="Escribir reseña"
      open={open}
      onCancel={handleCancel}
      okText="Publicar"
      cancelText="Cancelar"
      confirmLoading={submitting}
      onOk={() => form.submit()}
      width={500}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
      >
        <Form.Item
          name="rating"
          label="Calificación"
          rules={[
            { 
              required: true, 
              message: 'Por favor selecciona una calificación' 
            }
          ]}
        >
          <Rate />
        </Form.Item>

        <Form.Item
          name="author"
          label="Nombre (opcional)"
        >
          <Input 
            placeholder="Tu nombre"
            maxLength={100}
          />
        </Form.Item>

        <Form.Item
          name="comment"
          label="Comentario"
          rules={[
            { 
              required: true, 
              message: 'Por favor escribe un comentario' 
            },
            { 
              min: 10, 
              message: 'El comentario debe tener al menos 10 caracteres' 
            }
          ]}
        >
          <TextArea
            rows={4}
            placeholder="Escribe tu reseña sobre este producto..."
            showCount
            maxLength={1000}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default CreateReviewModal;
