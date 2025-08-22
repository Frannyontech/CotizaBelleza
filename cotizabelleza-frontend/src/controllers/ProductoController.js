/**
 * Producto Controller - Frontend MVC
 * Controla la lógica de negocio de productos en el frontend
 */
import mvcApi from '../services/mvcApi.js';

class ProductoController {
  constructor() {
    this.data = {
      productos: [],
      productoActual: null,
      categorias: [],
      tiendas: [],
      filtros: {
        categoria: '',
        tienda: '',
        search: '',
        marca: ''
      },
      paginacion: {
        page: 1,
        limit: 20,
        total: 0
      },
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
   * Cargar productos con filtros
   */
  async loadProductos(filtros = {}, useMVC = true) {
    this.setState({ loading: true, error: null });

    try {
      const filtrosCompletos = { ...this.data.filtros, ...filtros };
      
      let productos;
      if (useMVC) {
        productos = await mvcApi.productos.getProductos(filtrosCompletos);
      } else {
        productos = await mvcApi.unified.getProductos(filtrosCompletos, false);
      }

      // Asegurar que productos sea un array
      const productosArray = Array.isArray(productos) ? productos : productos.productos || [];

      this.setState({
        productos: productosArray,
        filtros: filtrosCompletos,
        paginacion: {
          ...this.data.paginacion,
          total: productos.total || productosArray.length
        },
        loading: false
      });

      return productosArray;

    } catch (error) {
      console.error('Error loading productos:', error);
      this.setState({
        error: 'Error cargando productos',
        loading: false
      });
      throw error;
    }
  }

  /**
   * Cargar productos por tienda específica
   */
  async loadProductosPorTienda(tiendaNombre, filtros = {}) {
    this.setState({ loading: true, error: null });

    try {
      const resultado = await mvcApi.tiendas.getProductosPorTienda(tiendaNombre, filtros);
      
      this.setState({
        productos: resultado.productos || [],
        filtros: { ...this.data.filtros, tienda: tiendaNombre, ...filtros },
        paginacion: {
          ...this.data.paginacion,
          total: resultado.total || 0
        },
        loading: false
      });

      return resultado;

    } catch (error) {
      console.error(`Error loading productos from ${tiendaNombre}:`, error);
      this.setState({
        error: `Error cargando productos de ${tiendaNombre}`,
        loading: false
      });
      throw error;
    }
  }

  /**
   * Cargar detalle de producto
   */
  async loadProductoDetalle(productoId, tiendaNombre = null) {
    this.setState({ loading: true, error: null });

    try {
      let producto;
      
      if (tiendaNombre) {
        producto = await mvcApi.tiendas.getProductoDetalleTienda(tiendaNombre, productoId);
      } else {
        producto = await mvcApi.productos.getProductoDetalle(productoId);
      }

      this.setState({
        productoActual: producto,
        loading: false
      });

      return producto;

    } catch (error) {
      console.error('Error loading producto detalle:', error);
      this.setState({
        error: 'Error cargando detalle del producto',
        loading: false
      });
      throw error;
    }
  }

  /**
   * Buscar productos
   */
  async buscarProductos(query) {
    return this.loadProductos({ search: query });
  }

  /**
   * Filtrar por categoría
   */
  async filtrarPorCategoria(categoria) {
    return this.loadProductos({ categoria });
  }

  /**
   * Filtrar por tienda
   */
  async filtrarPorTienda(tienda) {
    return this.loadProductos({ tienda });
  }

  /**
   * Limpiar filtros
   */
  async limpiarFiltros() {
    return this.loadProductos({
      categoria: '',
      tienda: '',
      search: '',
      marca: ''
    });
  }

  /**
   * Cargar categorías disponibles
   */
  async loadCategorias() {
    try {
      const categorias = await mvcApi.categorias.getCategorias();
      this.setState({ categorias });
      return categorias;
    } catch (error) {
      console.error('Error loading categorias:', error);
      throw error;
    }
  }

  /**
   * Cargar tiendas disponibles
   */
  async loadTiendas() {
    try {
      const tiendas = await mvcApi.tiendas.getTiendas();
      this.setState({ tiendas });
      return tiendas;
    } catch (error) {
      console.error('Error loading tiendas:', error);
      throw error;
    }
  }

  /**
   * Obtener productos formateados para visualización
   */
  getFormattedProductos() {
    return this.data.productos.map(producto => ({
      id: producto.id || producto.product_id,
      nombre: producto.nombre,
      marca: producto.marca || '',
      categoria: producto.categoria,
      precio: producto.precio_min || producto.precio || 0,
      precioOriginal: producto.precio_max || producto.precio_original || 0,
      tiendas: producto.tiendas_disponibles || [],
      imagen: producto.imagen_url || '',
      descripcion: producto.descripcion || '',
      stock: producto.stock || 'unknown',
      url: producto.url || producto.url_producto || '',
      source: producto.source || 'database'
    }));
  }

  /**
   * Obtener productos por rango de precio
   */
  getProductosByPrecio(minPrecio, maxPrecio) {
    return this.getFormattedProductos().filter(producto => {
      const precio = parseFloat(producto.precio);
      return precio >= minPrecio && precio <= maxPrecio;
    });
  }

  /**
   * Obtener productos por marca
   */
  getProductosByMarca(marca) {
    if (!marca) return this.getFormattedProductos();
    
    return this.getFormattedProductos().filter(producto =>
      producto.marca.toLowerCase().includes(marca.toLowerCase())
    );
  }

  /**
   * Ordenar productos
   */
  sortProductos(criterio = 'precio') {
    const productos = [...this.data.productos];
    
    productos.sort((a, b) => {
      switch (criterio) {
        case 'precio':
          return (a.precio_min || a.precio || 0) - (b.precio_min || b.precio || 0);
        case 'precio_desc':
          return (b.precio_min || b.precio || 0) - (a.precio_min || a.precio || 0);
        case 'nombre':
          return a.nombre.localeCompare(b.nombre);
        case 'marca':
          return (a.marca || '').localeCompare(b.marca || '');
        default:
          return 0;
      }
    });

    this.setState({ productos });
    return productos;
  }

  /**
   * Obtener estadísticas de productos actuales
   */
  getEstadisticas() {
    const productos = this.getFormattedProductos();
    const precios = productos.map(p => parseFloat(p.precio)).filter(p => p > 0);
    
    return {
      total: productos.length,
      conPrecio: precios.length,
      precioMin: precios.length > 0 ? Math.min(...precios) : 0,
      precioMax: precios.length > 0 ? Math.max(...precios) : 0,
      precioPromedio: precios.length > 0 ? precios.reduce((a, b) => a + b, 0) / precios.length : 0,
      marcas: [...new Set(productos.map(p => p.marca).filter(m => m))].length,
      categorias: [...new Set(productos.map(p => p.categoria))].length
    };
  }

  /**
   * Cambiar página
   */
  async changePage(page) {
    this.setState({
      paginacion: { ...this.data.paginacion, page }
    });
    return this.loadProductos();
  }

  /**
   * Obtener filtros activos
   */
  getFiltrosActivos() {
    const { filtros } = this.data;
    return Object.entries(filtros)
      .filter(([key, value]) => value && value !== '')
      .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});
  }

  /**
   * Verificar si hay filtros aplicados
   */
  hasFiltros() {
    return Object.keys(this.getFiltrosActivos()).length > 0;
  }

  /**
   * Refrescar datos
   */
  async refresh() {
    return this.loadProductos(this.data.filtros);
  }

  /**
   * Limpiar estado
   */
  clear() {
    this.setState({
      productos: [],
      productoActual: null,
      filtros: {
        categoria: '',
        tienda: '',
        search: '',
        marca: ''
      },
      paginacion: {
        page: 1,
        limit: 20,
        total: 0
      },
      loading: false,
      error: null
    });
  }
}

// Instancia singleton para el controlador
const productoController = new ProductoController();

export default productoController;
