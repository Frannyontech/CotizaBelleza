import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { productService } from '../services/api';
import './MaicaoProductos.css';

const MaicaoProductos = () => {
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
      const response = await productService.getMaicaoProducts(nuevosFiltros);
      setProductos(response.productos || []);
      setTotal(response.total || 0);
    } catch (error) {
      console.error('Error cargando productos de Maicao:', error);
      setError('Error al cargar los productos de Maicao');
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

  const manejarClickProducto = (producto) => {
    // Usar directamente el ID unificado (product_id o id)
    const productId = producto.product_id || producto.id;
    navigate(`/detalle-producto/${encodeURIComponent(productId)}`);
  };

  const obtenerImagenProducto = (producto) => {
    return producto.imagen_url || '/image-not-found.png';
  };

  if (loading) {
    return (
      <div className="maicao-productos-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Cargando productos de Maicao...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="maicao-productos-container">
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button onClick={() => cargarProductos()} className="retry-button">
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="maicao-productos-container">
      {/* Header */}
      <div className="maicao-header">
        <h1>💄 Productos Maicao</h1>
        <p>Descubre los mejores productos de belleza en Maicao</p>
      </div>

      {/* Filtros */}
      <div className="filtros-container">
        <div className="filtro-grupo">
          <label>Categoría:</label>
          <select 
            value={filtros.categoria} 
            onChange={(e) => manejarCambioFiltro('categoria', e.target.value)}
            className="filtro-select"
          >
            <option value="">Todas las categorías</option>
            <option value="maquillaje">Maquillaje</option>
            <option value="skincare">Skincare</option>
          </select>
        </div>

        <div className="filtro-grupo">
          <label>Buscar:</label>
          <input
            type="text"
            placeholder="Buscar por nombre..."
            value={filtros.search}
            onChange={(e) => manejarCambioFiltro('search', e.target.value)}
            className="filtro-input"
          />
        </div>

        <div className="filtro-grupo">
          <label>Marca:</label>
          <input
            type="text"
            placeholder="Buscar por marca..."
            value={filtros.marca}
            onChange={(e) => manejarCambioFiltro('marca', e.target.value)}
            className="filtro-input"
          />
        </div>
      </div>

      {/* Grid de productos */}
      <div className="productos-grid">
        {productos.map((producto) => (
          <div 
            key={producto.id}
            className="producto-card"
            onClick={() => manejarClickProducto(producto)}
          >
            <div className="producto-imagen">
              <img
                src={obtenerImagenProducto(producto)}
                alt={producto.nombre}
                onError={(e) => {
                  e.target.src = '/image-not-found.png';
                }}
              />
              <div className="producto-tienda">💄 Maicao</div>
            </div>
            
            <div className="producto-info">
              <h3 className="producto-nombre">{producto.nombre}</h3>
              <p className="producto-marca">{producto.marca}</p>
              <div className="producto-precio">
                {formatearPrecio(producto.precio)}
              </div>
              <div className="producto-stock">
                <span className={`stock ${producto.stock ? 'disponible' : 'agotado'}`}>
                  {producto.stock ? '✓ Disponible' : '✗ Agotado'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {productos.length === 0 && !loading && (
        <div className="no-productos">
          <p>No se encontraron productos con los filtros aplicados</p>
        </div>
      )}
    </div>
  );
};

export default MaicaoProductos;
