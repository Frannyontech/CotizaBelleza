import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './DBSProductos.css';

const DBSProductos = () => {
    const navigate = useNavigate();
    const [productos, setProductos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filtros, setFiltros] = useState({
        categoria: '',
        search: '',
        marca: ''
    });
    const [categorias, setCategorias] = useState([]);

    useEffect(() => {
        cargarProductos();
        cargarCategorias();
    }, [filtros]);

    const cargarProductos = async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            
            if (filtros.categoria) params.append('categoria', filtros.categoria);
            if (filtros.search) params.append('search', filtros.search);
            if (filtros.marca) params.append('marca', filtros.marca);

            const response = await axios.get(`/api/productos-dbs/?${params}`);
            setProductos(response.data.productos);
            setError(null);
        } catch (err) {
            setError('Error al cargar los productos');
            console.error('Error:', err);
        } finally {
            setLoading(false);
        }
    };

    const cargarCategorias = async () => {
        try {
            const response = await axios.get('/api/categorias/');
            setCategorias(response.data);
        } catch (err) {
            console.error('Error al cargar categorías:', err);
        }
    };

    const handleFiltroChange = (campo, valor) => {
        setFiltros(prev => ({
            ...prev,
            [campo]: valor
        }));
    };

    const formatearPrecio = (precio) => {
        return new Intl.NumberFormat('es-CL', {
            style: 'currency',
            currency: 'CLP'
        }).format(precio);
    };

    const obtenerMarcasUnicas = () => {
        const marcas = productos.map(p => p.marca).filter(marca => marca);
        return [...new Set(marcas)].sort();
    };

    const esImagenValida = (imagenUrl) => {
        if (!imagenUrl || imagenUrl.trim() === '') return false;
        
        // Verificar si es base64 (muy largo)
        if (imagenUrl.startsWith('data:image/') && imagenUrl.length > 1000) {
            return false;
        }
        
        // Verificar si es una URL válida de DBS
        if (imagenUrl.startsWith('http') && imagenUrl.includes('dbs.cl')) {
            return true;
        }
        
        // Verificar si es una URL relativa que comienza con /
        if (imagenUrl.startsWith('/') && imagenUrl.includes('dbs.cl')) {
            return true;
        }
        
        // Verificar si contiene parámetros de imagen válidos
        if (imagenUrl.includes('optimize=low') || imagenUrl.includes('bg-color=')) {
            return true;
        }
        
        return false;
    };

    const getImageUrl = (product) => {
        // Si no hay imagen_url o está vacía, usar la imagen por defecto
        if (!product.imagen_url || product.imagen_url === '') {
            return '/image-not-found.png';
        }
        
        // Si la URL es muy larga o parece ser base64, usar imagen por defecto
        if (product.imagen_url.length > 200 || product.imagen_url.startsWith('data:')) {
            return '/image-not-found.png';
        }
        
        // Si es una URL válida de DBS, usarla directamente
        if (product.imagen_url.startsWith('http') && product.imagen_url.includes('dbs.cl')) {
            return product.imagen_url;
        }
        
        // Si es una URL relativa, agregar el dominio base
        if (product.imagen_url.startsWith('/')) {
            return `https://dbs.cl${product.imagen_url}`;
        }
        
        // Por defecto, usar la imagen por defecto
        return '/image-not-found.png';
    };

    if (loading) {
        return (
            <div className="dbs-loading">
                <div className="spinner"></div>
                <p>Cargando productos DBS...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="dbs-error">
                <h3>Error</h3>
                <p>{error}</p>
                <button onClick={cargarProductos}>Reintentar</button>
            </div>
        );
    }

    return (
        <div className="dbs-productos">
            <div className="dbs-header">
                <h2>Productos DBS</h2>
                <p>Encuentra los mejores productos de belleza en DBS</p>
            </div>

            <div className="dbs-filtros">
                <div className="filtro-grupo">
                    <label>Categoría:</label>
                    <select 
                        value={filtros.categoria} 
                        onChange={(e) => handleFiltroChange('categoria', e.target.value)}
                    >
                        <option value="">Todas las categorías</option>
                        {categorias.map(cat => (
                            <option key={cat.id} value={cat.nombre}>
                                {cat.nombre}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="filtro-grupo">
                    <label>Marca:</label>
                    <select 
                        value={filtros.marca} 
                        onChange={(e) => handleFiltroChange('marca', e.target.value)}
                    >
                        <option value="">Todas las marcas</option>
                        {obtenerMarcasUnicas().map(marca => (
                            <option key={marca} value={marca}>
                                {marca}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="filtro-grupo">
                    <label>Buscar:</label>
                    <input 
                        type="text" 
                        placeholder="Buscar productos..."
                        value={filtros.search}
                        onChange={(e) => handleFiltroChange('search', e.target.value)}
                    />
                </div>
            </div>

            <div className="dbs-resultados">
                <p className="resultados-info">
                    {productos.length} productos encontrados
                </p>

                <div className="productos-grid">
                    {productos.map(producto => (
                        <div 
                            key={producto.id} 
                            className="producto-card"
                            onClick={() => navigate(`/detalle-producto/${producto.id}`)}
                            style={{ cursor: 'pointer' }}
                        >
                            <div className="producto-imagen">
                                <img 
                                    src={getImageUrl(producto)} 
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
                                    <span className={`stock ${producto.stock ? 'en-stock' : 'sin-stock'}`}>
                                        {producto.stock ? 'En stock' : 'Sin stock'}
                                    </span>
                                </div>

                                {producto.url_producto && (
                                    <a 
                                        href={producto.url_producto} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="ver-producto-btn"
                                    >
                                        Ver en DBS
                                    </a>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {productos.length === 0 && (
                    <div className="sin-resultados">
                        <p>No se encontraron productos con los filtros seleccionados.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DBSProductos; 