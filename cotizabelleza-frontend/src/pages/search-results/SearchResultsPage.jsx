import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

const SearchResultsPage = () => {
  console.log('SearchResultsPage component mounted - SIMPLIFIED VERSION');
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(12);
  const [favorites, setFavorites] = useState([]);
  const [sortBy, setSortBy] = useState('price_asc');
  
  // Estados de filtros
  const [priceRange, setPriceRange] = useState([0, 100000]);
  const [selectedStores, setSelectedStores] = useState([]);
  const [selectedAvailability, setSelectedAvailability] = useState([]);
  
  // Estados de filtros colapsables
  const [priceExpanded, setPriceExpanded] = useState(true);
  const [storesExpanded, setStoresExpanded] = useState(true);
  const [availabilityExpanded, setAvailabilityExpanded] = useState(true);
  
  console.log('Search params:', searchParams.toString());

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const searchTerm = searchParams.get('search') || '';
        console.log('Searching for:', searchTerm);
        
        const response = await fetch(`/api/productos-dbs/?search=${encodeURIComponent(searchTerm)}`);
        const data = await response.json();
        
        console.log('API Response:', data);
        
        const productsData = data.productos || data || [];
        console.log('Products data:', productsData);
        setProducts(productsData);
        
      } catch (error) {
        console.error('Error loading data:', error);
        setError(error.message || 'Error al cargar los datos');
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [searchParams]);

  // Formatear precio
  const formatPrice = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP'
    }).format(price);
  };

  // Obtener imagen del producto
  const getImageUrl = (product) => {
    if (!product.imagen_url || product.imagen_url === '') {
      return '/image-not-found.png';
    }
    
    if (product.imagen_url.startsWith('http')) {
      return product.imagen_url;
    }
    
    if (product.imagen_url.startsWith('/')) {
      return `https://dbs.cl${product.imagen_url}`;
    }
    
    return '/image-not-found.png';
  };

  // Manejar favoritos
  const toggleFavorite = (productId) => {
    setFavorites(prev => 
      prev.includes(productId) 
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  };

  // Ordenar productos
  const sortedProducts = [...products].sort((a, b) => {
    const priceA = a.precio || a.precio_min || 0;
    const priceB = b.precio || b.precio_min || 0;
    
    switch (sortBy) {
      case 'price_asc':
        return priceA - priceB;
      case 'price_desc':
        return priceB - priceA;
      default:
        return 0;
    }
  });

  // Calcular productos para la página actual
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const currentProducts = sortedProducts.slice(startIndex, endIndex);
  const totalPages = Math.ceil(sortedProducts.length / pageSize);

  // Opciones de tiendas
  const storeOptions = [
    'MAC Chile', 'Falabella', 'Paris', 'NYX', 'Revlon', 'Clinique', 'Dior', 'Chanel'
  ];

  // Opciones de disponibilidad
  const availabilityOptions = [
    { label: 'Disponible', value: 'disponible' },
    { label: 'No disponible', value: 'no-disponible' }
  ];

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h3 style={{ color: '#ff4d4f' }}>Error</h3>
        <p>{error}</p>
        <button 
          onClick={() => window.location.reload()}
          style={{
            padding: '12px 24px',
            background: '#ff69b4',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '1rem',
            fontWeight: '500',
            marginTop: '16px'
          }}
        >
          Recargar página
        </button>
      </div>
    );
  }
  
  return (
    <div className="search-results-layout">
      {/* Sidebar de filtros */}
      <div className="search-sider">
        <div className="filters-container">
          <h4 className="filters-title">Filtros</h4>
          
          {/* Filtro de Precio */}
          <div className="filter-section">
            <div 
              className="filter-header"
              onClick={() => setPriceExpanded(!priceExpanded)}
            >
              <span style={{ fontWeight: 'bold' }}>Precio</span>
              <span className={`filter-arrow ${priceExpanded ? 'expanded' : ''}`}>
                ▼
              </span>
            </div>
            {priceExpanded && (
              <div className="filter-content">
                <div className="price-range">
                  <div className="price-labels">
                    <span>$0</span>
                    <span>$100.000</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100000"
                    step="1000"
                    value={priceRange[1]}
                    onChange={(e) => setPriceRange([priceRange[0], parseInt(e.target.value)])}
                    className="price-slider"
                  />
                  <div className="price-inputs">
                    <span>{priceRange[0]}</span>
                    <span>{priceRange[1]}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Filtro de Tiendas */}
          <div className="filter-section">
            <div 
              className="filter-header"
              onClick={() => setStoresExpanded(!storesExpanded)}
            >
              <span style={{ fontWeight: 'bold' }}>Tiendas</span>
              <span className={`filter-arrow ${storesExpanded ? 'expanded' : ''}`}>
                ▼
              </span>
            </div>
            {storesExpanded && (
              <div className="filter-content">
                <div className="store-checkboxes">
                  {storeOptions.map(store => (
                    <label key={store} style={{ display: 'block', marginBottom: '8px' }}>
                      <input
                        type="checkbox"
                        checked={selectedStores.includes(store)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedStores([...selectedStores, store]);
                          } else {
                            setSelectedStores(selectedStores.filter(s => s !== store));
                          }
                        }}
                        style={{ marginRight: '8px' }}
                      />
                      {store}
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Filtro de Disponibilidad */}
          <div className="filter-section">
            <div 
              className="filter-header"
              onClick={() => setAvailabilityExpanded(!availabilityExpanded)}
            >
              <span style={{ fontWeight: 'bold' }}>Disponibilidad</span>
              <span className={`filter-arrow ${availabilityExpanded ? 'expanded' : ''}`}>
                ▼
              </span>
            </div>
            {availabilityExpanded && (
              <div className="filter-content">
                <div className="availability-checkboxes">
                  {availabilityOptions.map(option => (
                    <label key={option.value} style={{ display: 'block', marginBottom: '8px' }}>
                      <input
                        type="checkbox"
                        checked={selectedAvailability.includes(option.value)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedAvailability([...selectedAvailability, option.value]);
                          } else {
                            setSelectedAvailability(selectedAvailability.filter(a => a !== option.value));
                          }
                        }}
                        style={{ marginRight: '8px' }}
                      />
                      {option.label}
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="search-content">
        <div className="results-container">
          {/* Header de resultados */}
          <div className="results-header">
            <h2 className="results-title">
              Resultados para "{searchParams.get('search') || ''}"
            </h2>
            <div className="sort-controls">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="sort-select"
              >
                <option value="price_asc">Precio: menor a mayor</option>
                <option value="price_desc">Precio: mayor a menor</option>
              </select>
            </div>
          </div>

          {/* Estados de carga y resultados */}
          {loading ? (
            <div className="loading-container">
              <div className="spinner"></div>
              <p>Cargando resultados...</p>
            </div>
          ) : currentProducts.length === 0 ? (
            <div className="no-results-container">
              <h2>🔍</h2>
              <p>No se encontraron productos</p>
            </div>
          ) : (
            <>
              {/* Grid de productos */}
              <div className="products-grid">
                {currentProducts.map(product => (
                  <div 
                    key={product.id} 
                    className="product-card"
                  >
                    {/* Icono de favorito */}
                    <div className="favorite-icon">
                      {favorites.includes(product.id) ? (
                        <span 
                          className="heart-filled"
                          onClick={() => toggleFavorite(product.id)}
                        >
                          ❤️
                        </span>
                      ) : (
                        <span 
                          className="heart-outlined"
                          onClick={() => toggleFavorite(product.id)}
                        >
                          🤍
                        </span>
                      )}
                    </div>

                    {/* Imagen del producto */}
                    <div className="product-image-container">
                      <img
                        alt={product.nombre}
                        src={getImageUrl(product)}
                        className="product-image"
                        onError={(e) => {
                          e.target.src = '/image-not-found.png';
                        }}
                      />
                    </div>

                    {/* Información del producto */}
                    <div className="product-info">
                      <div className="product-name-section">
                        <p className="product-brand">{product.marca || 'Sin marca'}</p>
                        <h3 className="product-name">{product.nombre}</h3>
                      </div>
                      
                      <p className="product-category">{product.categoria || 'Sin categoría'}</p>
                      
                      <p className="product-price">
                        {formatPrice(product.precio || product.precio_min || 0)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Paginación */}
              {totalPages > 1 && (
                <div className="pagination-container">
                  <div className="pagination">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="pagination-btn"
                    >
                      ←
                    </button>
                    <span className="pagination-info">
                      Página {currentPage} de {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="pagination-btn"
                    >
                      →
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchResultsPage;
