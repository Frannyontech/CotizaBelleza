import axios from 'axios';

// Configuration for unified products API
const API_BASE_URL = 'http://localhost:8000/api/';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercept responses for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Unified API Error:', error);
    return Promise.reject(error);
  }
);

export const unifiedProductsService = {
  // Get all unified products from backend
  getUnifiedProducts: async () => {
    try {
      const response = await api.get('unified/');
      return response.data;
    } catch (error) {
      console.error('Error fetching unified products:', error);
      throw error;
    }
  },

  // Get dashboard data from backend
  getDashboardData: async () => {
    try {
      const response = await api.get('dashboard/');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  },

  // Get product by ID (supports multiple ID formats)
  getProductById: async (productId) => {
    try {
      // Usar la nueva API unificada que maneja tanto productos persistentes como unificados
      const response = await api.get(`producto/${productId}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching product by ID:', error);
      throw error;
    }
  },

  // Get products by store
  getProductsByStore: async (storeName) => {
    try {
      const unifiedData = await unifiedProductsService.getUnifiedProducts();
      const productos = unifiedData.productos || [];
      
      return productos.filter(product => {
        const tiendas = product.tiendas || [];
        return tiendas.some(tienda => 
          tienda.fuente && tienda.fuente.toLowerCase() === storeName.toLowerCase()
        );
      });
    } catch (error) {
      console.error('Error fetching products by store:', error);
      throw error;
    }
  },

  // Search unified products
  searchUnifiedProducts: async (searchTerm) => {
    try {
      const unifiedData = await unifiedProductsService.getUnifiedProducts();
      const productos = unifiedData.productos || [];
      
      const searchLower = searchTerm.toLowerCase();
      return productos.filter(product => 
        (product.nombre || '').toLowerCase().includes(searchLower) ||
        (product.marca || '').toLowerCase().includes(searchLower) ||
        (product.categoria || '').toLowerCase().includes(searchLower)
      );
    } catch (error) {
      console.error('Error searching unified products:', error);
      throw error;
    }
  },

  // Get products by category
  getProductsByCategory: async (categoryName) => {
    try {
      const unifiedData = await unifiedProductsService.getUnifiedProducts();
      const productos = unifiedData.productos || [];
      
      return productos.filter(product => 
        product.categoria && product.categoria.toLowerCase() === categoryName.toLowerCase()
      );
    } catch (error) {
      console.error('Error fetching products by category:', error);
      throw error;
    }
  },

  // Convert unified products to listing format used by components
  convertToListingFormat: (unifiedData) => {
    try {
      const productos = unifiedData.productos || [];
      
      return productos.map(product => {
        const tiendas = product.tiendas || [];
        
        const tiendasArray = tiendas;
        
        // Find the best image and price
        let imagen = product.imagen || '';
        let precioMin = null;
        let tiendas_disponibles = [];
        
        tiendasArray.forEach(tienda => {
          if (tienda.imagen && !imagen) {
            imagen = tienda.imagen;
          }
          
          const precio = parseFloat(tienda.precio);
          if (!isNaN(precio) && (precioMin === null || precio < precioMin)) {
            precioMin = precio;
          }
          
          if (tienda.fuente) {
            tiendas_disponibles.push(tienda.fuente.toUpperCase());
          }
        });
        
        return {
          id: product.product_id || product.id,
          product_id: product.product_id || product.id,
          nombre: product.nombre || '',
          marca: product.marca || '',
          categoria: product.categoria || '',
          precio_min: precioMin,
          imagen_url: imagen,
          tiendas_disponibles: [...new Set(tiendas_disponibles)], // Remove duplicates
          tiendasCount: tiendasArray.length,
          tiendas: tiendasArray
        };
      });
    } catch (error) {
      console.error('Error converting to listing format:', error);
      return [];
    }
  }
};

export default unifiedProductsService;