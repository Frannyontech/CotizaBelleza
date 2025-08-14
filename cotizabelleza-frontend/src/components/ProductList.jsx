import React, { useState, useEffect } from 'react';
import { productService } from '../services/api';
import './ProductList.css';

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        const response = await productService.getProducts();
        setProducts(response.productos || []);
        setError(null);
      } catch (err) {
        console.error('Error fetching products:', err);
        setError('Error al cargar los productos');
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  if (loading) {
    return (
      <div className="product-list">
        <h2>Productos</h2>
        <p>Cargando productos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="product-list">
        <h2>Productos</h2>
        <p className="error">{error}</p>
      </div>
    );
  }

  return (
    <div className="product-list">
      <h2>Productos</h2>
      {products.length === 0 ? (
        <p>No hay productos disponibles</p>
      ) : (
        <div className="products-grid">
          {products.map((product) => (
            <div key={product.id} className="product-card">
              <div className="product-image">
                <img 
                  src={product.imagen_url || '/image-not-found.png'} 
                  alt={product.nombre}
                  onError={(e) => {
                    e.target.src = '/image-not-found.png';
                  }}
                />
              </div>
              <div className="product-info">
                <h3 className="product-name">{product.nombre}</h3>
                <p className="product-brand"><strong>Marca:</strong> {product.marca}</p>
                <p className="product-price"><strong>Precio:</strong> ${product.precio}</p>
                <p className="product-category"><strong>Categoría:</strong> {product.categoria}</p>
                <p className="product-stock"><strong>Stock:</strong> {product.stock ? 'Disponible' : 'No disponible'}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProductList; 