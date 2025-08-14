import axios from 'axios';

// Configuración base de axios
const API_BASE_URL = '/api/';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para manejar errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Servicios para el Dashboard
export const dashboardService = {
  // Obtener datos del dashboard
  getDashboardData: async () => {
    try {
      const response = await api.get('dashboard/');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  },

  // Obtener productos populares
  getPopularProducts: async () => {
    try {
      const response = await api.get('dashboard/');
      return response.data.productos_populares || [];
    } catch (error) {
      console.error('Error fetching popular products:', error);
      throw error;
    }
  },

  // Obtener estadísticas
  getStatistics: async () => {
    try {
      const response = await api.get('dashboard/');
      return response.data.estadisticas || {};
    } catch (error) {
      console.error('Error fetching statistics:', error);
      throw error;
    }
  }
};

// Servicios para Productos
export const productService = {
  // Obtener lista de productos con filtros
  getProducts: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      
      if (filters.categoria) params.append('categoria', filters.categoria);
      if (filters.tienda) params.append('tienda', filters.tienda);
      if (filters.search) params.append('search', filters.search);
      if (filters.marca) params.append('marca', filters.marca);
      
      console.log('Making API request to:', `productos-dbs/?${params.toString()}`);
      const response = await api.get(`productos-dbs/?${params.toString()}`);
      console.log('API response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching products:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  },

  // Obtener precios de un producto específico
  getProductPrices: async (productId) => {
    try {
      const response = await api.get(`precios/?producto=${productId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching product prices:', error);
      throw error;
    }
  },

  // Buscar productos
  searchProducts: async (searchTerm) => {
    try {
      const response = await api.get(`productos-dbs/?search=${encodeURIComponent(searchTerm)}`);
      return response.data;
    } catch (error) {
      console.error('Error searching products:', error);
      throw error;
    }
  }
};

// Servicios para Categorías
export const categoryService = {
  // Obtener todas las categorías
  getCategories: async () => {
    try {
      const response = await api.get('categorias/');
      return response.data;
    } catch (error) {
      console.error('Error fetching categories:', error);
      throw error;
    }
  }
};

// Servicios para Tiendas
export const storeService = {
  // Obtener todas las tiendas
  getStores: async () => {
    try {
      const response = await api.get('tiendas/');
      return response.data;
    } catch (error) {
      console.error('Error fetching stores:', error);
      throw error;
    }
  }
};

// Servicios para Usuarios
export const userService = {
  // Crear nuevo usuario
  createUser: async (userData) => {
    try {
      const response = await api.post('usuarios/', userData);
      return response.data;
    } catch (error) {
      console.error('Error creating user:', error);
      throw error;
    }
  }
};

// Función para cargar datos del scraper (solo para desarrollo)
export const loadScraperData = async () => {
  try {
    // Esta función podría llamar a un endpoint específico para cargar datos
    console.log('Loading scraper data...');
    // En producción, esto se haría a través de un comando de Django
  } catch (error) {
    console.error('Error loading scraper data:', error);
    throw error;
  }
};

export default api; 