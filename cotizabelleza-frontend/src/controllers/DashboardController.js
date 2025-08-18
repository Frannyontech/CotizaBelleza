/**
 * Dashboard Controller - Frontend MVC
 * Controla la lógica de negocio del dashboard en el frontend
 */
import mvcApi from '../services/mvcApi.js';

class DashboardController {
  constructor() {
    this.data = {
      estadisticas: {},
      productosPopulares: [],
      productosPorCategoria: [],
      tiendas: [],
      loading: false,
      error: null
    };
    this.subscribers = new Set();
  }

  /**
   * Suscribirse a cambios de estado
   */
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  /**
   * Notificar cambios a suscriptores
   */
  notify() {
    this.subscribers.forEach(callback => callback(this.data));
  }

  /**
   * Actualizar estado
   */
  setState(newState) {
    this.data = { ...this.data, ...newState };
    this.notify();
  }

  /**
   * Cargar datos del dashboard
   */
  async loadDashboardData(useMVC = true) {
    this.setState({ loading: true, error: null });

    try {
      let dashboardData;
      
      if (useMVC) {
        // Usar nueva API MVC con datos híbridos
        dashboardData = await mvcApi.dashboard.getDashboardData();
      } else {
        // Fallback a API unificada
        dashboardData = await mvcApi.dashboard.getUnifiedDashboard();
      }

      this.setState({
        estadisticas: dashboardData.estadisticas || {},
        productosPopulares: dashboardData.productos_populares || [],
        productosPorCategoria: dashboardData.productos_por_categoria || [],
        tiendas: dashboardData.tiendas_disponibles || [],
        categorias: dashboardData.categorias_disponibles || [],
        loading: false
      });

      return dashboardData;

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      this.setState({
        error: 'Error cargando datos del dashboard',
        loading: false
      });
      throw error;
    }
  }

  /**
   * Obtener estadísticas procesadas
   */
  getProcessedStats() {
    const { estadisticas } = this.data;
    
    return {
      totalProductos: estadisticas.total_productos || estadisticas.total_productos_bd || 0,
      totalTiendas: estadisticas.total_tiendas || 0,
      totalCategorias: estadisticas.total_categorias || 0,
      precioPromedio: estadisticas.precio_promedio || 0,
      precioMin: estadisticas.precio_min || 0,
      precioMax: estadisticas.precio_max || 0,
      productosConPrecio: estadisticas.productos_con_precios || estadisticas.total_productos_unified || 0
    };
  }

  /**
   * Obtener productos populares con formato consistente
   */
  getFormattedProductosPopulares() {
    return this.data.productosPopulares.map(producto => ({
      id: producto.id || producto.product_id,
      nombre: producto.nombre,
      marca: producto.marca || '',
      categoria: producto.categoria,
      precioMin: producto.precio_min || (producto.tiendas && producto.tiendas.length > 0 ? 
        Math.min(...producto.tiendas.map(t => t.precio)) : 0),
      tiendas: producto.tiendas_disponibles || 
        (producto.tiendas ? producto.tiendas.map(t => t.fuente) : []),
      imagen: producto.imagen_url || '',
      numPrecios: producto.num_precios || (producto.tiendas ? producto.tiendas.length : 0)
    }));
  }

  /**
   * Obtener datos de categorías para gráficos
   */
  getCategoriaChartData() {
    return this.data.productosPorCategoria.map(cat => ({
      name: cat.nombre,
      value: cat.cantidad_productos,
      label: `${cat.nombre} (${cat.cantidad_productos})`
    }));
  }

  /**
   * Filtrar productos populares por categoría
   */
  filterProductosByCategoria(categoria) {
    if (!categoria) return this.getFormattedProductosPopulares();
    
    return this.getFormattedProductosPopulares().filter(
      producto => producto.categoria.toLowerCase() === categoria.toLowerCase()
    );
  }

  /**
   * Buscar productos populares
   */
  searchProductosPopulares(query) {
    if (!query) return this.getFormattedProductosPopulares();
    
    const lowerQuery = query.toLowerCase();
    return this.getFormattedProductosPopulares().filter(
      producto => 
        producto.nombre.toLowerCase().includes(lowerQuery) ||
        producto.marca.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Obtener resumen de tiendas
   */
  getTiendasSummary() {
    const { tiendas, estadisticas } = this.data;
    
    return {
      total: estadisticas.total_tiendas || tiendas.length,
      nombres: tiendas,
      activas: tiendas.length
    };
  }

  /**
   * Verificar estado de datos
   */
  getDataStatus() {
    const stats = this.getProcessedStats();
    
    return {
      hasData: stats.totalProductos > 0,
      isEmpty: stats.totalProductos === 0,
      isLoading: this.data.loading,
      hasError: !!this.data.error,
      lastUpdate: new Date().toISOString(),
      dataSources: {
        database: stats.totalProductos > 0,
        unifiedFile: stats.productosConPrecio > 0
      }
    };
  }

  /**
   * Refrescar datos
   */
  async refresh(useMVC = true) {
    return this.loadDashboardData(useMVC);
  }

  /**
   * Limpiar datos
   */
  clear() {
    this.setState({
      estadisticas: {},
      productosPopulares: [],
      productosPorCategoria: [],
      tiendas: [],
      loading: false,
      error: null
    });
  }
}

// Instancia singleton para el controlador
const dashboardController = new DashboardController();

export default dashboardController;
