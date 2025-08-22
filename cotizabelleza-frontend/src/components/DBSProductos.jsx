import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Empty, Button } from 'antd';
import { LinkOutlined } from '@ant-design/icons';
import { unifiedProductsService } from '../services/unifiedApi';
import './DBSProductos.css';



const DBSProductos = () => {
  const navigate = useNavigate();
  const [data, setData] = useState({ items: [] });
  const [loading, setLoading] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [searchFilter, setSearchFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(25);

  // Formatear precio en formato CLP sin decimales
  const formatPriceCLP = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      maximumFractionDigits: 0
    }).format(price);
  };

  // Cargar productos al montar el componente
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Obtener productos de DBS únicamente
        const dbsProducts = await unifiedProductsService.getProductsByStore('dbs');
        
        // Convertir a formato de listing
        const listingProducts = unifiedProductsService.convertToListingFormat({ productos: dbsProducts });
        
        setData({ items: listingProducts });
        
      } catch (error) {
        console.error('Error loading DBS products:', error);
        setData({ items: [] });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Filtrar productos por categoría y búsqueda
  const filteredProducts = useMemo(() => {
    let filtered = data.items || [];

    // Filtro por categoría
    if (categoryFilter) {
      filtered = filtered.filter(product => product.categoria === categoryFilter);
    }

    // Filtro por búsqueda en nombre o marca
    if (searchFilter.trim()) {
      const searchLower = searchFilter.toLowerCase();
      filtered = filtered.filter(product => 
        product.nombre?.toLowerCase().includes(searchLower) ||
        product.marca?.toLowerCase().includes(searchLower)
      );
    }

    return filtered;
  }, [data.items, categoryFilter, searchFilter]);

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
  }, [categoryFilter, searchFilter]);

  // Obtener categorías únicas
  const categories = useMemo(() => {
    const cats = new Set((data.items || []).map(p => p.categoria).filter(Boolean));
    return Array.from(cats);
  }, [data.items]);

  return (
    <div className="dbs-productos-container">
      
      {/* Header */}
      <div className="dbs-header">
        <h1>🛍️ Productos DBS</h1>
        <p>Encuentra los mejores productos de belleza en DBS</p>
      </div>

      {/* Filtros */}
      <div className="filtros-container">
        <div className="filtro-grupo">
          <label>Categoría:</label>
          <select 
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="filtro-select"
          >
            <option value="">Todas las categorías</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div className="filtro-grupo">
          <label>Buscar:</label>
          <input
            type="text"
            placeholder="Buscar por nombre..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="filtro-input"
          />
        </div>

        <div className="filtro-grupo">
          <label>Marca:</label>
          <input
            type="text"
            placeholder="Buscar por marca..."
            value=""
            className="filtro-input"
          />
        </div>
      </div>

      {/* Contador de resultados */}
      {!loading && filteredProducts.length > 0 && (
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

      {loading ? (
        <div className="loading-container">
          <span className="loading-text">Cargando productos de DBS...</span>
        </div>
      ) : filteredProducts.length > 0 ? (
        <>
          <div className="productos-grid">
            {paginatedProducts.map((product) => (
            <div 
              key={product.product_id}
              className="producto-card" 
              onClick={() => navigate(`/detalle-producto/${encodeURIComponent(product.product_id)}`)}
            >
              <div className="producto-imagen">
                <img 
                  src={product.imagen_url || '/image-not-found.png'} 
                  alt={product.nombre}
                  onError={(e) => {
                    e.target.src = '/image-not-found.png';
                  }}
                />
                <div className="producto-tienda">🛍️ DBS</div>
              </div>
              
              <div className="producto-info">
                <h3 className="producto-nombre">{product.nombre}</h3>
                <p className="producto-marca">{product.marca}</p>
                <div className="producto-precio">
                  <span className="precio">{formatPriceCLP(product.precio_min || 0)}</span>
                </div>
                <div className="producto-stock">
                  <span className="stock disponible">✓ Disponible</span>
                </div>
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
      ) : (
        <div className="no-productos">
          <p>No se encontraron productos de DBS con los filtros aplicados</p>
        </div>
      )}
    </div>
  );
};

export default DBSProductos;
