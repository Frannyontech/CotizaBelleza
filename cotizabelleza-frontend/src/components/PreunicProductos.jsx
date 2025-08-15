import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { productService } from '../services/api';
import './PreunicProductos.css';

const Preunic = () => {
  const navigate = useNavigate();
  const [productos, setProductos] = useState([]);
  const [filtros, setFiltros] = useState({
    categoria: '',
    search: '',
    marca: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);

  // Cargar productos al montar el componente
  useEffect(() => {
    cargarProductos();
  }, []);

  const cargarProductos = async (nuevosFiltros = filtros) => {
    setLoading(true);
    setError(null);
    try {
      const response = await productService.getPreunicProducts(nuevosFiltros);
      setProductos(response.productos || []);
      setTotal(response.total || 0);
    } catch (error) {
      console.error('Error cargando productos de Preunic:', error);
      setError('Error al cargar los productos de Preunic');
    } finally {
      setLoading(false);
    }
  };

  const manejarCambioFiltro = (campo, valor) => {
    const nuevosFiltros = { ...filtros, [campo]: valor };
    setFiltros(nuevosFiltros);
    cargarProductos(nuevosFiltros);
  };

  const formatearPrecio = (precio) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0
    }).format(precio);
  };

  const abrirDetalle = (productoId) => {
    navigate(`/detalle-producto/${productoId}`);
  };

  // Función para procesar URLs de imagen (idéntica a DetalleProducto.jsx)
  const getImageUrl = (imagenUrl) => {
    if (!imagenUrl || imagenUrl === '') {
      return '/image-not-found.png';
    }
    
    // Si la URL ya es completa (incluyendo Preunic), usarla directamente
    if (imagenUrl.startsWith('http')) {
      return imagenUrl;
    }
    
    // Si es una ruta relativa, agregar el dominio de DBS
    if (imagenUrl.startsWith('/')) {
      return `https://dbs.cl${imagenUrl}`;
    }
    
    return '/image-not-found.png';
  };

  return (
    <div className="preunic-page">
      <div className="preunic-header">
        <h1>🛒 Productos Preunic</h1>
        <p>Descubre los mejores productos de belleza en Preunic</p>
      </div>

      {/* Filtros */}
      <div className="filtros-container">
        <div className="filtro-group">
          <label htmlFor="busqueda">Buscar producto:</label>
          <input
            id="busqueda"
            type="text"
            placeholder="Nombre del producto..."
            value={filtros.search}
            onChange={(e) => manejarCambioFiltro('search', e.target.value)}
            className="filtro-input"
          />
        </div>

        <div className="filtro-group">
          <label htmlFor="categoria">Categoría:</label>
          <select
            id="categoria"
            value={filtros.categoria}
            onChange={(e) => manejarCambioFiltro('categoria', e.target.value)}
            className="filtro-select"
          >
            <option value="">Todas las categorías</option>
            <option value="maquillaje">Maquillaje</option>
            <option value="skincare">Skincare</option>
          </select>
        </div>

        <div className="filtro-group">
          <label htmlFor="marca">Marca:</label>
          <input
            id="marca"
            type="text"
            placeholder="Nombre de la marca..."
            value={filtros.marca}
            onChange={(e) => manejarCambioFiltro('marca', e.target.value)}
            className="filtro-input"
          />
        </div>
      </div>

      {/* Estadísticas */}
      <div className="estadisticas">
        <div className="estadistica-item">
          <span className="numero">{total}</span>
          <span className="label">Productos encontrados</span>
        </div>
        <div className="estadistica-item">
          <span className="numero">{productos.filter(p => p.categoria === 'maquillaje').length}</span>
          <span className="label">Maquillaje</span>
        </div>
        <div className="estadistica-item">
          <span className="numero">{productos.filter(p => p.categoria === 'skincare').length}</span>
          <span className="label">Skincare</span>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Cargando productos...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={() => cargarProductos()} className="retry-button">
            Reintentar
          </button>
        </div>
      )}

      {/* Lista de productos */}
      {!loading && !error && (
        <div className="productos-grid">
          {productos.length > 0 ? (
            productos.map((producto, index) => (
              <div 
                key={index} 
                className="producto-card"
                onClick={() => abrirDetalle(producto.id)}
                style={{ cursor: 'pointer' }}
              >
                <div className="producto-imagen">
                  <img 
                    src={getImageUrl(producto.imagen_url)} 
                    alt={producto.nombre}
                    onError={(e) => {
                      e.target.src = '/image-not-found.png';
                    }}
                  />
                </div>

                <div className="producto-info">
                  <h3 className="producto-nombre">{producto.nombre}</h3>
                  <p className="producto-marca">{producto.marca}</p>
                  <p className="producto-categoria">{producto.categoria}</p>
                  
                  <div className="producto-precio">
                    <span className="precio">{formatearPrecio(producto.precio)}</span>
                    <span className={`stock ${producto.stock ? 'disponible' : 'agotado'}`}>
                      {producto.stock ? '✅ Disponible' : '❌ Agotado'}
                    </span>
                  </div>

                  <button 
                    className="btn-ver-producto"
                    onClick={(e) => {
                      e.stopPropagation();
                      abrirDetalle(producto.id);
                    }}
                  >
                    Ver detalle
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="no-productos">
              <h3>No se encontraron productos</h3>
              <p>Intenta ajustar los filtros de búsqueda</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Preunic;

