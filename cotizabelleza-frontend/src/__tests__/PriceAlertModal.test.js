import React from 'react';
import { render, screen } from '@testing-library/react';
import PriceAlertModal from '../components/PriceAlertModal';

// Mock axios
jest.mock('axios', () => ({
  post: jest.fn(),
}));

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
  });

  // Test básico de renderizado
    test('renderiza el modal cuando visible es true', () => {
      render(<PriceAlertModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Alertas de cambios de precio')).toBeInTheDocument();
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

  test('muestra el nombre del producto', () => {
      render(<PriceAlertModal {...defaultProps} />);

    expect(screen.getByText('Producto: Labial Rojo Intenso')).toBeInTheDocument();
    });

    test('maneja producto sin nombre', () => {
    const propsWithoutName = {
      ...defaultProps,
      producto: {
        ...defaultProps.producto,
        nombre: undefined
      }
    };
    
    render(<PriceAlertModal {...propsWithoutName} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Producto:')).toBeInTheDocument();
  });
});
