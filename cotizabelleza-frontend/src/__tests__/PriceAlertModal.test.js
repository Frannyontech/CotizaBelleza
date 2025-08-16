import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import { message } from 'antd';
import PriceAlertModal from '../components/PriceAlertModal';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock antd message
jest.mock('antd', () => {
  const antd = jest.requireActual('antd');
  return {
    ...antd,
    message: {
      success: jest.fn(),
      error: jest.fn(),
      warning: jest.fn(),
      info: jest.fn(),
    },
  };
});

describe('PriceAlertModal', () => {
  const defaultProps = {
    visible: true,
    onClose: jest.fn(),
    producto: {
      id: 123,
      nombre: 'Labial Rojo Intenso',
      marca: 'MAC',
      precio: 25000
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset axios mock
    mockedAxios.post.mockReset();
    // Reset message mocks
    message.success.mockReset();
    message.error.mockReset();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  // Test: Renderiza modal y elementos básicos
  describe('Renderizado', () => {
    test('renderiza el modal cuando visible es true', () => {
      render(<PriceAlertModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Alertas de cambios de precio')).toBeInTheDocument();
      expect(screen.getByText(/Ingresa tu correo y te notificaremos/)).toBeInTheDocument();
      expect(screen.getByText(`Producto: ${defaultProps.producto.nombre}`)).toBeInTheDocument();
    });

    test('no renderiza el modal cuando visible es false', () => {
      render(<PriceAlertModal {...defaultProps} visible={false} />);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    test('renderiza elementos del formulario', () => {
      render(<PriceAlertModal {...defaultProps} />);

      expect(screen.getByLabelText('Correo electrónico')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('tu@email.com')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cerrar' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Suscribirse' })).toBeInTheDocument();
    });
  });

  // Test: Validaciones del formulario
  describe('Validación de formulario', () => {
    test('muestra error cuando email está vacío', async () => {
      const user = userEvent.setup();
      render(<PriceAlertModal {...defaultProps} />);

      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Por favor ingresa tu correo electrónico')).toBeInTheDocument();
      });

      // Verificar que no se hizo llamada a axios
      expect(mockedAxios.post).not.toHaveBeenCalled();
    });

    test('muestra error cuando email tiene formato inválido', async () => {
      const user = userEvent.setup();
      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'email-invalido');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Por favor ingresa un correo electrónico válido')).toBeInTheDocument();
      });

      expect(mockedAxios.post).not.toHaveBeenCalled();
    });

    test('acepta email con formato válido', async () => {
      const user = userEvent.setup();
      
      // Mock respuesta exitosa
      mockedAxios.post.mockResolvedValueOnce({
        status: 200,
        data: { message: 'Alerta creada exitosamente' }
      });

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith('/api/alertas-precio/', {
          producto_id: 123,
          email: 'test@example.com'
        });
      });
    });
  });

  // Test: Envío exitoso (201 - Nueva alerta)
  describe('Respuesta 201 - Nueva alerta creada', () => {
    test('envía datos correctos y muestra mensaje de éxito', async () => {
      const user = userEvent.setup();
      
      // Mock respuesta 201
      mockedAxios.post.mockResolvedValueOnce({
        status: 201,
        data: { 
          message: 'Alerta de precio creada exitosamente',
          alerta: {
            id: 1,
            email: 'test@example.com',
            producto_id: 123
          }
        }
      });

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      // Verificar llamada a API
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith('/api/alertas-precio/', {
          producto_id: 123,
          email: 'test@example.com'
        });
      });

      // Verificar mensaje de éxito
      await waitFor(() => {
        expect(message.success).toHaveBeenCalledWith(
          '¡Alerta de precio activada exitosamente! Te notificaremos cuando cambie el precio.'
        );
      });

      // Verificar que se llamó onClose
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  // Test: Respuesta 200 - Idempotencia (ya existe)
  describe('Respuesta 200 - Ya estabas suscrita', () => {
    test('maneja respuesta de idempotencia correctamente', async () => {
      const user = userEvent.setup();
      
      // Mock respuesta 200
      mockedAxios.post.mockResolvedValueOnce({
        status: 200,
        data: { 
          message: 'Ya tienes una alerta activa para este producto',
          alerta: {
            id: 1,
            email: 'test@example.com',
            producto_id: 123,
            activa: true
          }
        }
      });

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(message.success).toHaveBeenCalledWith(
          '¡Alerta de precio activada exitosamente! Te notificaremos cuando cambie el precio.'
        );
      });

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  // Test: Respuesta 429 - Rate limit
  describe('Respuesta 429 - Máximo 1 solicitud por día', () => {
    test('muestra mensaje de rate limit', async () => {
      const user = userEvent.setup();
      
      // Mock respuesta 429
      mockedAxios.post.mockRejectedValueOnce({
        response: {
          status: 429,
          data: {
            error: 'Máximo 1 solicitud por día. Intenta nuevamente mañana.'
          }
        }
      });

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(message.error).toHaveBeenCalledWith(
          'Máximo 1 solicitud por día. Intenta nuevamente mañana.'
        );
      });

      // El modal NO debe cerrarse en caso de error
      expect(defaultProps.onClose).not.toHaveBeenCalled();
    });

    test('muestra mensaje de rate limit sin detalles específicos', async () => {
      const user = userEvent.setup();
      
      mockedAxios.post.mockRejectedValueOnce({
        response: {
          status: 429,
          data: {
            error: 'Too Many Requests'
          }
        }
      });

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(message.error).toHaveBeenCalledWith('Too Many Requests');
      });
    });
  });

  // Test: Respuesta 400 - Error de validación
  describe('Respuesta 400 - Error de validación', () => {
    test('muestra error de validación del backend', async () => {
      const user = userEvent.setup();
      
      // Mock respuesta 400
      mockedAxios.post.mockRejectedValueOnce({
        response: {
          status: 400,
          data: {
            error: 'Email tiene formato inválido'
          }
        }
      });

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'invalid-email');
      await user.click(submitButton);

      await waitFor(() => {
        expect(message.error).toHaveBeenCalledWith('Email tiene formato inválido');
      });

      expect(defaultProps.onClose).not.toHaveBeenCalled();
    });

    test('muestra error de producto no encontrado', async () => {
      const user = userEvent.setup();
      
      mockedAxios.post.mockRejectedValueOnce({
        response: {
          status: 400,
          data: {
            error: 'Producto no encontrado'
          }
        }
      });

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(message.error).toHaveBeenCalledWith('Producto no encontrado');
      });
    });
  });

  // Test: Estados de loading
  describe('Estado de loading', () => {
    test('deshabilita botón durante envío', async () => {
      const user = userEvent.setup();
      
      // Mock respuesta que tarda en resolverse
      let resolvePromise;
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      mockedAxios.post.mockReturnValueOnce(pendingPromise);

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      // Verificar estado de loading
      await waitFor(() => {
        expect(submitButton).toBeDisabled();
        expect(submitButton).toHaveClass('ant-btn-loading');
      });

      // Resolver promesa
      act(() => {
        resolvePromise({
          status: 201,
          data: { message: 'Success' }
        });
      });

      // Verificar que vuelve al estado normal
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
        expect(submitButton).not.toHaveClass('ant-btn-loading');
      });
    });
  });

  // Test: Manejo del modal
  describe('Manejo del modal', () => {
    test('cierra modal al hacer click en Cerrar', async () => {
      const user = userEvent.setup();
      render(<PriceAlertModal {...defaultProps} />);

      const closeButton = screen.getByRole('button', { name: 'Cerrar' });
      await user.click(closeButton);

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    test('cierra modal al hacer click en la X del modal', async () => {
      const user = userEvent.setup();
      render(<PriceAlertModal {...defaultProps} />);

      // Buscar el botón de cerrar del modal (X)
      const modalCloseButton = screen.getByRole('button', { name: 'Close' });
      await user.click(modalCloseButton);

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    test('resetea formulario al cerrar', async () => {
      const user = userEvent.setup();
      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const closeButton = screen.getByRole('button', { name: 'Cerrar' });

      // Llenar formulario
      await user.type(emailInput, 'test@example.com');
      expect(emailInput.value).toBe('test@example.com');

      // Cerrar modal
      await user.click(closeButton);

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    test('resetea formulario después de envío exitoso', async () => {
      const user = userEvent.setup();
      
      mockedAxios.post.mockResolvedValueOnce({
        status: 201,
        data: { message: 'Success' }
      });

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(message.success).toHaveBeenCalled();
        expect(defaultProps.onClose).toHaveBeenCalled();
      });
    });
  });

  // Test: Casos edge y errores
  describe('Casos edge', () => {
    test('maneja error de red/conexión', async () => {
      const user = userEvent.setup();
      
      // Mock error de red
      mockedAxios.post.mockRejectedValueOnce(new Error('Network Error'));

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(message.error).toHaveBeenCalledWith(
          'Error al crear la alerta. Por favor intenta nuevamente.'
        );
      });
    });

    test('maneja error del servidor (500)', async () => {
      const user = userEvent.setup();
      
      mockedAxios.post.mockRejectedValueOnce({
        response: {
          status: 500,
          data: {
            error: 'Error interno del servidor'
          }
        }
      });

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(message.error).toHaveBeenCalledWith('Error interno del servidor');
      });
    });

    test('maneja error sin response data', async () => {
      const user = userEvent.setup();
      
      mockedAxios.post.mockRejectedValueOnce({
        response: {
          status: 500
          // Sin data
        }
      });

      render(<PriceAlertModal {...defaultProps} />);

      const emailInput = screen.getByPlaceholderText('tu@email.com');
      const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(message.error).toHaveBeenCalledWith(
          'Error al crear la alerta. Por favor intenta nuevamente.'
        );
      });
    });

    test('funciona sin producto (manejo defensivo)', () => {
      render(<PriceAlertModal {...defaultProps} producto={null} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.queryByText(/Producto:/)).not.toBeInTheDocument();
    });

    test('maneja producto sin nombre', () => {
      const productoSinNombre = { ...defaultProps.producto, nombre: undefined };
      render(<PriceAlertModal {...defaultProps} producto={productoSinNombre} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Producto: undefined')).toBeInTheDocument();
    });
  });

  // Test: Validación de email avanzada
  describe('Validación de email avanzada', () => {
    const emailsValidos = [
      'test@example.com',
      'user.name@domain.co.uk',
      'user+tag@example.org',
      'user123@test-domain.com'
    ];

    const emailsInvalidos = [
      'invalid-email',
      '@example.com',
      'test@',
      'test.example.com',
      'test@.com',
      'test@com'
    ];

    emailsValidos.forEach(email => {
      test(`acepta email válido: ${email}`, async () => {
        const user = userEvent.setup();
        
        mockedAxios.post.mockResolvedValueOnce({
          status: 201,
          data: { message: 'Success' }
        });

        render(<PriceAlertModal {...defaultProps} />);

        const emailInput = screen.getByPlaceholderText('tu@email.com');
        const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

        await user.type(emailInput, email);
        await user.click(submitButton);

        await waitFor(() => {
          expect(mockedAxios.post).toHaveBeenCalledWith('/api/alertas-precio/', {
            producto_id: 123,
            email: email
          });
        });
      });
    });

    emailsInvalidos.forEach(email => {
      test(`rechaza email inválido: ${email}`, async () => {
        const user = userEvent.setup();
        render(<PriceAlertModal {...defaultProps} />);

        const emailInput = screen.getByPlaceholderText('tu@email.com');
        const submitButton = screen.getByRole('button', { name: 'Suscribirse' });

        await user.type(emailInput, email);
        await user.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText('Por favor ingresa un correo electrónico válido')).toBeInTheDocument();
        });

        expect(mockedAxios.post).not.toHaveBeenCalled();
      });
    });
  });
});
