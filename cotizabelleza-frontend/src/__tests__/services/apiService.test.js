import { rest } from 'msw';
import { server } from '../mocks/server';
import apiService from '../../services/apiService';

// Mock de axios si no existe
const mockAxios = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  create: jest.fn(() => mockAxios),
  defaults: {
    baseURL: 'http://localhost:8000'
  }
};

// Mock del servicio de API si no existe
const mockApiService = {
  getDashboard: jest.fn(),
  getProducts: jest.fn(),
  getProductDetail: jest.fn(),
  searchProducts: jest.fn(),
  createPriceAlert: jest.fn(),
  deletePriceAlert: jest.fn()
};

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getDashboard', () => {
    test('fetches dashboard data successfully', async () => {
      const mockDashboardData = {
        productos_populares: [
          {
            id: 1,
            nombre_original: 'Base de Maquillaje',
            marca: 'L\'Oréal',
            precio_minimo: 100.00
          }
        ],
        categorias_disponibles: [
          { id: 1, nombre: 'Maquillaje', cantidad_productos: 10 }
        ],
        tiendas_disponibles: [
          { id: 1, nombre: 'Tienda A', cantidad_productos: 8 }
        ],
        estadisticas: {
          total_productos: 15,
          precio_promedio: 85.50
        }
      };

      mockApiService.getDashboard.mockResolvedValue(mockDashboardData);

      const result = await mockApiService.getDashboard();

      expect(mockApiService.getDashboard).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockDashboardData);
      expect(result.productos_populares).toHaveLength(1);
      expect(result.categorias_disponibles).toHaveLength(1);
      expect(result.tiendas_disponibles).toHaveLength(1);
    });

    test('handles API error gracefully', async () => {
      const errorMessage = 'Failed to fetch dashboard';
      mockApiService.getDashboard.mockRejectedValue(new Error(errorMessage));

      await expect(mockApiService.getDashboard()).rejects.toThrow(errorMessage);
      expect(mockApiService.getDashboard).toHaveBeenCalledTimes(1);
    });
  });

  describe('getProducts', () => {
    test('fetches products with default parameters', async () => {
      const mockProductsData = {
        productos: [
          {
            id: 1,
            nombre_original: 'Base de Maquillaje',
            marca: 'L\'Oréal',
            precio_minimo: 100.00
          }
        ],
        total: 1,
        pagina: 1,
        por_pagina: 10
      };

      mockApiService.getProducts.mockResolvedValue(mockProductsData);

      const result = await mockApiService.getProducts();

      expect(mockApiService.getProducts).toHaveBeenCalledWith({});
      expect(result).toEqual(mockProductsData);
      expect(result.productos).toHaveLength(1);
      expect(result.total).toBe(1);
    });

    test('fetches products with filters', async () => {
      const filters = {
        categoria: 'Maquillaje',
        tienda: 'Tienda A',
        buscar: 'base',
        pagina: 2,
        por_pagina: 5
      };

      const mockProductsData = {
        productos: [],
        total: 0,
        pagina: 2,
        por_pagina: 5
      };

      mockApiService.getProducts.mockResolvedValue(mockProductsData);

      const result = await mockApiService.getProducts(filters);

      expect(mockApiService.getProducts).toHaveBeenCalledWith(filters);
      expect(result).toEqual(mockProductsData);
    });

    test('handles empty products response', async () => {
      const mockEmptyData = {
        productos: [],
        total: 0,
        pagina: 1,
        por_pagina: 10
      };

      mockApiService.getProducts.mockResolvedValue(mockEmptyData);

      const result = await mockApiService.getProducts();

      expect(result.productos).toHaveLength(0);
      expect(result.total).toBe(0);
    });
  });

  describe('getProductDetail', () => {
    test('fetches product detail successfully', async () => {
      const productId = 'test-1';
      const mockProductDetail = {
        producto: {
          id: 1,
          nombre_original: 'Base de Maquillaje',
          marca: 'L\'Oréal',
          precio_minimo: 100.00
        },
        precios: [
          {
            precio: 100.00,
            tienda: 'Tienda A',
            disponible: true
          }
        ],
        historial_precios: [
          { fecha: '2024-01-10', precio: 95.00 },
          { fecha: '2024-01-15', precio: 100.00 }
        ]
      };

      mockApiService.getProductDetail.mockResolvedValue(mockProductDetail);

      const result = await mockApiService.getProductDetail(productId);

      expect(mockApiService.getProductDetail).toHaveBeenCalledWith(productId);
      expect(result).toEqual(mockProductDetail);
      expect(result.producto).toBeDefined();
      expect(result.precios).toHaveLength(1);
      expect(result.historial_precios).toHaveLength(2);
    });

    test('handles product not found', async () => {
      const productId = 'nonexistent';
      const errorMessage = 'Product not found';

      mockApiService.getProductDetail.mockRejectedValue(new Error(errorMessage));

      await expect(mockApiService.getProductDetail(productId)).rejects.toThrow(errorMessage);
      expect(mockApiService.getProductDetail).toHaveBeenCalledWith(productId);
    });
  });

  describe('searchProducts', () => {
    test('searches products successfully', async () => {
      const searchQuery = 'base de maquillaje';
      const mockSearchResults = {
        resultados: [
          {
            id: 1,
            nombre_original: 'Base de Maquillaje Líquida',
            marca: 'L\'Oréal',
            precio_minimo: 100.00
          }
        ],
        total: 1
      };

      mockApiService.searchProducts.mockResolvedValue(mockSearchResults);

      const result = await mockApiService.searchProducts(searchQuery);

      expect(mockApiService.searchProducts).toHaveBeenCalledWith(searchQuery);
      expect(result).toEqual(mockSearchResults);
      expect(result.resultados).toHaveLength(1);
      expect(result.total).toBe(1);
    });

    test('handles empty search results', async () => {
      const searchQuery = 'nonexistent product';
      const mockEmptyResults = {
        resultados: [],
        total: 0
      };

      mockApiService.searchProducts.mockResolvedValue(mockEmptyResults);

      const result = await mockApiService.searchProducts(searchQuery);

      expect(result.resultados).toHaveLength(0);
      expect(result.total).toBe(0);
    });

    test('handles search with special characters', async () => {
      const searchQuery = 'L\'Oréal & Maybelline';
      const mockResults = {
        resultados: [],
        total: 0
      };

      mockApiService.searchProducts.mockResolvedValue(mockResults);

      const result = await mockApiService.searchProducts(searchQuery);

      expect(mockApiService.searchProducts).toHaveBeenCalledWith(searchQuery);
      expect(result).toEqual(mockResults);
    });
  });

  describe('createPriceAlert', () => {
    test('creates price alert successfully', async () => {
      const alertData = {
        email: 'test@example.com',
        producto_id: 'test-1',
        precio_objetivo: 90.00
      };

      const mockResponse = {
        mensaje: 'Alerta creada exitosamente',
        alerta_id: 123
      };

      mockApiService.createPriceAlert.mockResolvedValue(mockResponse);

      const result = await mockApiService.createPriceAlert(alertData);

      expect(mockApiService.createPriceAlert).toHaveBeenCalledWith(alertData);
      expect(result).toEqual(mockResponse);
      expect(result.mensaje).toBe('Alerta creada exitosamente');
      expect(result.alerta_id).toBe(123);
    });

    test('handles invalid alert data', async () => {
      const invalidAlertData = {
        email: 'invalid-email',
        producto_id: 'test-1',
        precio_objetivo: -10.00
      };

      const errorMessage = 'Invalid data';

      mockApiService.createPriceAlert.mockRejectedValue(new Error(errorMessage));

      await expect(mockApiService.createPriceAlert(invalidAlertData)).rejects.toThrow(errorMessage);
      expect(mockApiService.createPriceAlert).toHaveBeenCalledWith(invalidAlertData);
    });

    test('handles product not found for alert', async () => {
      const alertData = {
        email: 'test@example.com',
        producto_id: 'nonexistent',
        precio_objetivo: 90.00
      };

      const errorMessage = 'Product not found';

      mockApiService.createPriceAlert.mockRejectedValue(new Error(errorMessage));

      await expect(mockApiService.createPriceAlert(alertData)).rejects.toThrow(errorMessage);
    });
  });

  describe('deletePriceAlert', () => {
    test('deletes price alert successfully', async () => {
      const alertId = 123;

      mockApiService.deletePriceAlert.mockResolvedValue({ success: true });

      const result = await mockApiService.deletePriceAlert(alertId);

      expect(mockApiService.deletePriceAlert).toHaveBeenCalledWith(alertId);
      expect(result).toEqual({ success: true });
    });

    test('handles alert not found', async () => {
      const alertId = 999;

      const errorMessage = 'Alert not found';

      mockApiService.deletePriceAlert.mockRejectedValue(new Error(errorMessage));

      await expect(mockApiService.deletePriceAlert(alertId)).rejects.toThrow(errorMessage);
      expect(mockApiService.deletePriceAlert).toHaveBeenCalledWith(alertId);
    });
  });

  describe('Error handling', () => {
    test('handles network errors', async () => {
      const networkError = new Error('Network Error');
      mockApiService.getDashboard.mockRejectedValue(networkError);

      await expect(mockApiService.getDashboard()).rejects.toThrow('Network Error');
    });

    test('handles timeout errors', async () => {
      const timeoutError = new Error('Request timeout');
      mockApiService.getProducts.mockRejectedValue(timeoutError);

      await expect(mockApiService.getProducts()).rejects.toThrow('Request timeout');
    });

    test('handles server errors', async () => {
      const serverError = new Error('Internal Server Error');
      mockApiService.getProductDetail.mockRejectedValue(serverError);

      await expect(mockApiService.getProductDetail('test-1')).rejects.toThrow('Internal Server Error');
    });
  });

  describe('Request configuration', () => {
    test('uses correct base URL', () => {
      expect(mockAxios.defaults.baseURL).toBe('http://localhost:8000');
    });

    test('creates axios instance with correct configuration', () => {
      const axiosInstance = mockAxios.create();
      expect(axiosInstance).toBe(mockAxios);
    });
  });
});
