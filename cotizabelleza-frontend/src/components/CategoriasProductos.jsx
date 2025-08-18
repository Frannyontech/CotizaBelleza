import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { unifiedProductsService } from '../services/unifiedApi';
import './CategoriasProductos.css';

const CategoriasProductos = () => {
  const navigate = useNavigate();
  const { categoria } = useParams();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');
  const [marcaFilter, setMarcaFilter] = useState('');
  const [tiendaFilter, setTiendaFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(25);

  // Formatear precio
  const formatPriceCLP = (price) => {
    if (!price || isNaN(price)) return 'Precio no disponible';
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      maximumFractionDigits: 0
    }).format(price);
  };

  // Obtener emoji para la categoría
  const getCategoryEmoji = (categoryName) => {
    switch (categoryName?.toLowerCase()) {
      case 'maquillaje': return '💄';
      case 'skincare': return '✨';
      default: return '🛍️';
    }
  };

  // Obtener emoji para la tienda
  const getStoreEmoji = (storeName) => {
    switch (storeName?.toLowerCase()) {
      case 'dbs': return '🛍️';
      case 'preunic': return '🛒';
      case 'maicao': return '💄';
      default: return '🏪';
    }
  };

  // Cargar productos por categoría
  useEffect(() => {
    const fetchData = async () => {
      if (!categoria) return;
      
      try {
        setLoading(true);
        const products = await unifiedProductsService.getProductsByCategory(categoria);
        const listingProducts = unifiedProductsService.convertToListingFormat({ productos: products });
        setData(listingProducts);
      } catch (error) {
        console.error('Error loading products by category:', error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [categoria]);

  // Filtrar productos
  const filteredProducts = useMemo(() => {
    let filtered = data;

    if (searchFilter) {
      const searchLower = searchFilter.toLowerCase();
      filtered = filtered.filter(product =>
        product.nombre?.toLowerCase().includes(searchLower) ||
        product.marca?.toLowerCase().includes(searchLower)
      );
    }

    if (marcaFilter) {
      filtered = filtered.filter(product => product.marca === marcaFilter);
    }

    if (tiendaFilter) {
      filtered = filtered.filter(product =>
        product.tiendas_disponibles?.includes(tiendaFilter.toUpperCase())
      );
    }

    return filtered;
  }, [data, searchFilter, marcaFilter, tiendaFilter]);

  // Lógica de paginación
  const paginatedProducts = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredProducts.slice(startIndex, endIndex);
  }, [filteredProducts, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
  const shouldShowPagination = filteredProducts.length > itemsPerPage;

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchFilter, marcaFilter, tiendaFilter, categoria]);

  // Obtener opciones únicas para filtros
  const marcas = useMemo(() => {
    const uniqueMarcas = [...new Set(data.map(p => p.marca).filter(Boolean))];
    return uniqueMarcas.sort();
  }, [data]);

  const tiendas = useMemo(() => {
    const uniqueTiendas = new Set();
    data.forEach(product => {
      product.tiendas_disponibles?.forEach(tienda => uniqueTiendas.add(tienda));
    });
    return Array.from(uniqueTiendas).sort();
  }, [data]);

  const handleProductClick = (product) => {
    navigate(`/detalle-producto/${encodeURIComponent(product.product_id)}`);
  };

  if (!categoria) {
    return (
      <div className="categorias-container">
        <div className="categorias-header">
          <h1>🛍️ Categorías</h1>
          <p>Selecciona una categoría para ver los productos</p>
        </div>
      </div>
    );
  }

  return (
    <div className="categorias-container">
      {/* Header */}
      <div className="categorias-header">
        <h1>{getCategoryEmoji(categoria)} {categoria.charAt(0).toUpperCase() + categoria.slice(1)}</h1>
        <p>Encuentra los mejores productos de {categoria} de todas las tiendas</p>
      </div>

      {/* Filtros */}
      <div className="filtros-container">
        <div className="filtro-grupo">
          <label>Buscar producto:</label>
          <input
            type="text"
            className="filtro-input"
            placeholder="Nombre del producto o marca..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
          />
        </div>
        
        <div className="filtro-grupo">
          <label>Marca:</label>
          <select
            className="filtro-select"
            value={marcaFilter}
            onChange={(e) => setMarcaFilter(e.target.value)}
          >
            <option value="">Todas las marcas</option>
            {marcas.map(marca => (
              <option key={marca} value={marca}>{marca}</option>
            ))}
          </select>
        </div>
        
        <div className="filtro-grupo">
          <label>Tienda:</label>
          <select
            className="filtro-select"
            value={tiendaFilter}
            onChange={(e) => setTiendaFilter(e.target.value)}
          >
            <option value="">Todas las tiendas</option>
            {tiendas.map(tienda => (
              <option key={tienda} value={tienda}>{tienda}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Contador de resultados */}
      {!loading && (
        <div className="resultados-contador">
          <p>
            {filteredProducts.length} producto{filteredProducts.length !== 1 ? 's' : ''} encontrado{filteredProducts.length !== 1 ? 's' : ''}
            {shouldShowPagination && (
              <span className="pagination-info">
                {' '}- Mostrando {(currentPage - 1) * itemsPerPage + 1} a {Math.min(currentPage * itemsPerPage, filteredProducts.length)} de {filteredProducts.length}
              </span>
            )}
          </p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Cargando productos de {categoria}...</p>
        </div>
      )}

      {/* Grid de productos */}
      {!loading && filteredProducts.length > 0 && (
        <>
          <div className="productos-grid">
            {paginatedProducts.map((product) => (
            <div
              key={product.product_id}
              className="producto-card"
              onClick={() => handleProductClick(product)}
            >
              <div className="producto-imagen">
                <img
                  src={product.imagen_url || '/image-not-found.png'}
                  alt={product.nombre}
                  onError={(e) => {
                    e.target.src = '/image-not-found.png';
                  }}
                />
              </div>
              
              <div className="producto-tiendas">
                {product.tiendas_disponibles?.map(tienda => (
                  <span key={tienda} className="tienda-badge">
                    {getStoreEmoji(tienda)} {tienda}
                  </span>
                ))}
              </div>
              
              <div className="producto-info">
                <h3 className="producto-nombre">{product.nombre}</h3>
                <p className="producto-marca">{product.marca}</p>
                <div className="producto-precio">
                  <span className="precio">
                    {product.tiendasCount > 1 ? 'Desde ' : ''}
                    {formatPriceCLP(product.precio_min)}
                  </span>
                </div>
                {product.tiendasCount > 1 && (
                  <p className="producto-tiendas-count">
                    Disponible en {product.tiendasCount} tienda{product.tiendasCount !== 1 ? 's' : ''}
                  </p>
                )}
              </div>
            </div>
          ))}
          </div>

          {/* Controles de paginación */}
          {shouldShowPagination && (
            <div className="pagination-container">
              <div className="pagination-controls">
                <button 
                  className="pagination-btn"
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                >
                  Primera
                </button>
                <button 
                  className="pagination-btn"
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  Anterior
                </button>
                
                <div className="pagination-numbers">
                  {(() => {
                    const startPage = Math.max(1, currentPage - 2);
                    const endPage = Math.min(totalPages, currentPage + 2);
                    const pages = [];
                    
                    for (let i = startPage; i <= endPage; i++) {
                      pages.push(
                        <button
                          key={i}
                          className={`pagination-number ${i === currentPage ? 'active' : ''}`}
                          onClick={() => setCurrentPage(i)}
                        >
                          {i}
                        </button>
                      );
                    }
                    return pages;
                  })()}
                </div>
                
                <button 
                  className="pagination-btn"
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  Siguiente
                </button>
                <button 
                  className="pagination-btn"
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={currentPage === totalPages}
                >
                  Última
                </button>
              </div>
              <div className="pagination-summary">
                Página {currentPage} de {totalPages}
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!loading && filteredProducts.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">{getCategoryEmoji(categoria)}</div>
          <h3>No se encontraron productos</h3>
          <p>
            {data.length === 0 
              ? `No hay productos disponibles en la categoría ${categoria}`
              : 'Intenta ajustar los filtros para ver más resultados'
            }
          </p>
        </div>
      )}
    </div>
  );
};

export default CategoriasProductos;
