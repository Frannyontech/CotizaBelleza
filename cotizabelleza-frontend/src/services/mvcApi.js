/**
 * Servicios API para la arquitectura MVC - Frontend
 * Servicios limpios que consumen la nueva API MVC del backend
 */
import axios from 'axios';

// Configuración para APIs MVC
const MVC_API_BASE_URL = 'http://localhost:8000/api/';  // o /mvc/api/ si usas setup híbrido
const ETL_API_BASE_URL = 'http://localhost:8000/api/etl/';

const mvcApi = axios.create({
  baseURL: MVC_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const etlApi = axios.create({
  baseURL: ETL_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para manejo de errores
mvcApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('MVC API Error:', error);
    return Promise.reject(error);
  }
);

etlApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('ETL API Error:', error);
    return Promise.reject(error);
  }
);

/**
 * SERVICIOS CORE MVC
 */

// Dashboard Service - Datos híbridos (BD + archivo unificado)
export const mvcDashboardService = {
  getDashboardData: async () => {
    const response = await mvcApi.get('dashboard/');
    return response.data;
  },

  getUnifiedDashboard: async () => {
    const response = await mvcApi.get('dashboard/unified/');
    return response.data;
  }
};

// Producto Service - Con datos híbridos
export const mvcProductoService = {
  getProductos: async (filtros = {}) => {
    const params = new URLSearchParams();
    
    if (filtros.categoria) params.append('categoria', filtros.categoria);
    if (filtros.tienda) params.append('tienda', filtros.tienda);
    if (filtros.search) params.append('search', filtros.search);
    
    const response = await mvcApi.get(`productos/?${params.toString()}`);
    return response.data;
  },

  getProductoDetalle: async (productoId) => {
    const response = await mvcApi.get(`productos/${productoId}/`);
    return response.data;
  },

  getProductosUnificados: async () => {
    const response = await mvcApi.get('productos/unified/');
    return response.data;
  }
};

// Tienda Service - Genérico para todas las tiendas
export const mvcTiendaService = {
  getTiendas: async () => {
    const response = await mvcApi.get('tiendas/');
    return response.data;
  },

  getProductosPorTienda: async (tiendaNombre, filtros = {}) => {
    const params = new URLSearchParams();
    
    if (filtros.categoria) params.append('categoria', filtros.categoria);
    if (filtros.search) params.append('search', filtros.search);
    if (filtros.marca) params.append('marca', filtros.marca);
    
    const response = await mvcApi.get(`${tiendaNombre}/productos/?${params.toString()}`);
    return response.data;
  },

  getProductoDetalleTienda: async (tiendaNombre, productoId) => {
    const response = await mvcApi.get(`${tiendaNombre}/productos/${productoId}/`);
    return response.data;
  },

  // Métodos específicos para compatibilidad
  getDBSProductos: async (filtros = {}) => {
    return mvcTiendaService.getProductosPorTienda('DBS', filtros);
  },

  getPREUNICProductos: async (filtros = {}) => {
    return mvcTiendaService.getProductosPorTienda('PREUNIC', filtros);
  },

  getMAICAOProductos: async (filtros = {}) => {
    return mvcTiendaService.getProductosPorTienda('MAICAO', filtros);
  }
};

// Categoria Service
export const mvcCategoriaService = {
  getCategorias: async () => {
    const response = await mvcApi.get('categorias/');
    return response.data;
  }
};

// Precio Service
export const mvcPrecioService = {
  getPreciosPorProducto: async (productoId) => {
    const response = await mvcApi.get(`precios/?producto=${productoId}`);
    return response.data;
  }
};

// Usuario Service
export const mvcUsuarioService = {
  crearUsuario: async (userData) => {
    const response = await mvcApi.post('usuarios/crear/', userData);
    return response.data;
  }
};

// Alerta Service
export const mvcAlertaService = {
  crearAlerta: async (alertaData) => {
    const response = await mvcApi.post('alertas/crear/', alertaData);
    return response.data;
  }
};

// Reseña Service
export const mvcResenaService = {
  getResenas: async (productoId) => {
    const response = await mvcApi.get(`productos/${productoId}/resenas/`);
    return response.data;
  },

  crearResena: async (productoId, resenaData) => {
    const response = await mvcApi.post(`productos/${productoId}/resenas/`, resenaData);
    return response.data;
  }
};

/**
 * SERVICIOS ETL
 */

export const etlService = {
  // Ejecutar pipeline completo
  runFullPipeline: async (config = {}) => {
    const response = await etlApi.post('control/', {
      action: 'full_pipeline',
      tiendas: config.tiendas || ['dbs', 'maicao', 'preunic'],
      categorias: config.categorias || ['maquillaje', 'skincare']
    });
    return response.data;
  },

  // Ejecutar solo scraper
  runScraper: async (tienda, categoria = null) => {
    const response = await etlApi.post('control/', {
      action: 'scraper',
      tienda,
      categoria
    });
    return response.data;
  },

  // Ejecutar solo procesador
  runProcessor: async (config = {}) => {
    const response = await etlApi.post('control/', {
      action: 'processor',
      min_strong: config.minStrong || 90,
      min_prob: config.minProb || 85,
      output_file: config.outputFile
    });
    return response.data;
  },

  // Sincronizar datos
  syncData: async () => {
    const response = await etlApi.post('control/', {
      action: 'sync'
    });
    return response.data;
  },

  // Obtener estado del ETL
  getStatus: async () => {
    const response = await etlApi.get('status/');
    return response.data;
  }
};

/**
 * SERVICIO UNIFICADO PARA MIGRACIÓN GRADUAL
 */
export const unifiedService = {
  // Combina datos de la API original y MVC
  getDashboard: async (useMVC = true) => {
    if (useMVC) {
      return mvcDashboardService.getDashboardData();
    } else {
      // Fallback a API original
      const response = await axios.get('http://localhost:8000/api/dashboard/');
      return response.data;
    }
  },

  getProductos: async (filtros = {}, useMVC = true) => {
    if (useMVC) {
      return mvcProductoService.getProductos(filtros);
    } else {
      // Fallback a API original
      const params = new URLSearchParams();
      if (filtros.categoria) params.append('categoria', filtros.categoria);
      if (filtros.tienda) params.append('tienda', filtros.tienda);
      if (filtros.search) params.append('search', filtros.search);
      
      const response = await axios.get(`http://localhost:8000/api/productos/?${params.toString()}`);
      return response.data;
    }
  }
};

export default {
  dashboard: mvcDashboardService,
  productos: mvcProductoService,
  tiendas: mvcTiendaService,
  categorias: mvcCategoriaService,
  precios: mvcPrecioService,
  usuarios: mvcUsuarioService,
  alertas: mvcAlertaService,
  resenas: mvcResenaService,
  etl: etlService,
  unified: unifiedService
};
