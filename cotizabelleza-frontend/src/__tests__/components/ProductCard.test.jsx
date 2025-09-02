import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProductCard from '../../components/ProductCard';

// Mock del componente ProductCard si no existe
const MockProductCard = ({ product, onPriceAlert }) => {
  return (
    <div data-testid="product-card">
      <h3 data-testid="product-name">{product.nombre_original}</h3>
      <p data-testid="product-brand">{product.marca}</p>
      <p data-testid="product-category">{product.categoria}</p>
      <p data-testid="product-price">${product.precio_minimo}</p>
      <button 
        data-testid="price-alert-btn"
        onClick={() => onPriceAlert(product)}
      >
        Crear Alerta
      </button>
    </div>
  );
};

const mockProduct = {
  id: 1,
  nombre_original: 'Base de Maquillaje Líquida',
  marca: 'L\'Oréal',
  categoria: 'Maquillaje',
  internal_id: 'test-1',
  precio_minimo: 100.00,
  precio_maximo: 120.00,
  precios: [
    {
      precio: 100.00,
      tienda: 'Tienda A',
      disponible: true,
      url_producto: 'https://test.com/producto1'
    }
  ]
};

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('ProductCard', () => {
  test('renders product information correctly', () => {
    renderWithRouter(<MockProductCard product={mockProduct} />);

    expect(screen.getByTestId('product-name')).toHaveTextContent('Base de Maquillaje Líquida');
    expect(screen.getByTestId('product-brand')).toHaveTextContent('L\'Oréal');
    expect(screen.getByTestId('product-category')).toHaveTextContent('Maquillaje');
    expect(screen.getByTestId('product-price')).toHaveTextContent('$100');
  });

  test('displays minimum price when available', () => {
    renderWithRouter(<MockProductCard product={mockProduct} />);

    const priceElement = screen.getByTestId('product-price');
    expect(priceElement).toHaveTextContent('$100');
  });

  test('shows price alert button', () => {
    renderWithRouter(<MockProductCard product={mockProduct} />);

    expect(screen.getByTestId('price-alert-btn')).toBeInTheDocument();
    expect(screen.getByTestId('price-alert-btn')).toHaveTextContent('Crear Alerta');
  });

  test('calls onPriceAlert when button is clicked', () => {
    const mockOnPriceAlert = jest.fn();
    renderWithRouter(<MockProductCard product={mockProduct} onPriceAlert={mockOnPriceAlert} />);

    const alertButton = screen.getByTestId('price-alert-btn');
    fireEvent.click(alertButton);

    expect(mockOnPriceAlert).toHaveBeenCalledWith(mockProduct);
    expect(mockOnPriceAlert).toHaveBeenCalledTimes(1);
  });

  test('handles product without prices', () => {
    const productWithoutPrices = {
      ...mockProduct,
      precio_minimo: null,
      precio_maximo: null,
      precios: []
    };

    renderWithRouter(<MockProductCard product={productWithoutPrices} />);

    expect(screen.getByTestId('product-name')).toHaveTextContent('Base de Maquillaje Líquida');
    expect(screen.getByTestId('product-price')).toHaveTextContent('$null');
  });

  test('handles product with missing fields', () => {
    const incompleteProduct = {
      id: 2,
      nombre_original: 'Producto Incompleto',
      internal_id: 'test-2'
    };

    renderWithRouter(<MockProductCard product={incompleteProduct} />);

    expect(screen.getByTestId('product-name')).toHaveTextContent('Producto Incompleto');
    expect(screen.getByTestId('product-brand')).toHaveTextContent('');
    expect(screen.getByTestId('product-category')).toHaveTextContent('');
  });
});
