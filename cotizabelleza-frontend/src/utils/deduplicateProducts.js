/**
 * Helper para deduplicación de productos en el frontend
 * Agrupa productos idénticos de diferentes tiendas en un solo objeto canónico
 */

import { normalizeForComparison } from './normalizeHelpers';

/**
 * Normaliza el nombre de un producto para comparación
 * Quita marca, caracteres especiales y normaliza el texto
 * @param {string} nombre - Nombre del producto 
 * @param {string} marca - Marca del producto
 * @returns {string} - Nombre normalizado
 */
export const normalizeProductName = (nombre, marca) => {
  if (!nombre || typeof nombre !== 'string') {
    return '';
  }

  let normalized = normalizeForComparison(nombre);
  
  // Quitar marca del nombre si está presente
  if (marca && typeof marca === 'string') {
    const marcaNormalizada = normalizeForComparison(marca);
    // Quitar marca del inicio o cualquier parte del nombre
    normalized = normalized.replace(new RegExp(`\\b${marcaNormalizada}\\b`, 'gi'), '').trim();
  }
  
  // Quitar caracteres especiales y normalizar espacios
  normalized = normalized
    .replace(/[^\w\s]/g, ' ') // Reemplazar caracteres especiales con espacios
    .replace(/\s+/g, ' ') // Normalizar espacios múltiples
    .trim();
  
  return normalized;
};

/**
 * Extrae volumen del nombre del producto usando regex
 * @param {string} nombre - Nombre del producto
 * @returns {string|null} - Volumen extraído o null
 */
export const extractVolume = (nombre) => {
  if (!nombre || typeof nombre !== 'string') {
    return null;
  }
  
  // Patrones para detectar volumen
  const volumePatterns = [
    /(\d+(?:\.\d+)?)\s?(ml|g|gr|kg|oz|litros?|l)\b/i,
    /(\d+(?:\.\d+)?)\s?(mililitros?|gramos?|kilogramos?|onzas?)\b/i
  ];
  
  for (const pattern of volumePatterns) {
    const match = nombre.match(pattern);
    if (match) {
      const cantidad = match[1];
      let unidad = match[2].toLowerCase();
      
      // Normalizar unidades
      if (unidad === 'gr' || unidad === 'gramos' || unidad === 'gramo') {
        unidad = 'g';
      } else if (unidad === 'mililitros' || unidad === 'mililitro') {
        unidad = 'ml';
      } else if (unidad === 'kilogramos' || unidad === 'kilogramo') {
        unidad = 'kg';
      } else if (unidad === 'onzas' || unidad === 'onza') {
        unidad = 'oz';
      } else if (unidad === 'litros' || unidad === 'litro' || unidad === 'l') {
        unidad = 'l';
      }
      
      return `${cantidad} ${unidad}`;
    }
  }
  
  return null;
};

/**
 * Genera una clave canónica para agrupar productos similares
 * @param {Object} product - Producto
 * @returns {string} - Clave canónica
 */
export const generateCanonicalKey = (product) => {
  // Si el producto ya tiene product_id del backend unificado, usarlo
  if (product.product_id) {
    return product.product_id;
  }
  
  // Generar clave basada en nombre normalizado, marca y volumen
  const marca = normalizeForComparison(product.marca || '');
  const nombreNorm = normalizeProductName(product.nombre || product.productName || '', product.marca);
  const volumen = extractVolume(product.nombre || product.productName || '') || '';
  const categoria = normalizeForComparison(product.categoria || product.category || '');
  
  // Crear hash simple de la combinación
  const keyString = `${marca}|${nombreNorm}|${volumen}|${categoria}`;
  
  // Generar hash simple (no criptográfico, solo para agrupación)
  let hash = 0;
  for (let i = 0; i < keyString.length; i++) {
    const char = keyString.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convertir a 32-bit integer
  }
  
  return `fe_${Math.abs(hash).toString(16)}`;
};

/**
 * Verifica si dos productos son similares y pueden ser agrupados
 * @param {Object} product1 - Primer producto
 * @param {Object} product2 - Segundo producto
 * @returns {boolean} - true si son similares
 */
export const areProductsSimilar = (product1, product2) => {
  // Si tienen el mismo product_id del backend, son iguales
  if (product1.product_id && product2.product_id) {
    return product1.product_id === product2.product_id;
  }
  
  // Comparar por nombre normalizado, marca y volumen
  const marca1 = normalizeForComparison(product1.marca || '');
  const marca2 = normalizeForComparison(product2.marca || '');
  
  if (marca1 !== marca2) {
    return false;
  }
  
  const nombre1 = normalizeProductName(product1.nombre || product1.productName || '', product1.marca);
  const nombre2 = normalizeProductName(product2.nombre || product2.productName || '', product2.marca);
  
  if (nombre1 !== nombre2) {
    return false;
  }
  
  const volumen1 = extractVolume(product1.nombre || product1.productName || '');
  const volumen2 = extractVolume(product2.nombre || product2.productName || '');
  
  // Si ambos tienen volumen, deben coincidir
  if (volumen1 && volumen2 && volumen1 !== volumen2) {
    return false;
  }
  
  return true;
};

/**
 * Obtiene el nombre del producto sin la marca para mostrar
 * @param {string} nombre - Nombre completo del producto
 * @param {string} marca - Marca del producto
 * @returns {string} - Nombre sin marca
 */
export const getProductNameWithoutBrand = (nombre, marca) => {
  if (!nombre || typeof nombre !== 'string') {
    return '';
  }
  
  let nameWithoutBrand = nombre;
  
  // Quitar marca del inicio si está presente
  if (marca && typeof marca === 'string') {
    const marcaPattern = new RegExp(`^\\s*${marca}\\s*`, 'i');
    nameWithoutBrand = nameWithoutBrand.replace(marcaPattern, '').trim();
  }
  
  return nameWithoutBrand || nombre; // Fallback al nombre original si queda vacío
};

/**
 * Deduplica una lista de productos agrupándolos por similitud
 * @param {Array} products - Lista de productos
 * @returns {Array} - Lista de productos deduplicados
 */
export const deduplicateProducts = (products) => {
  if (!Array.isArray(products) || products.length === 0) {
    return [];
  }
  
  // Si los productos ya vienen con structure unificada del backend, procesarlos directamente
  if (products.length > 0 && products[0].tiendas) {
    return products.map(product => ({
      product_id: product.product_id,
      nombre: getProductNameWithoutBrand(product.nombre, product.marca),
      marca: product.marca,
      categoria: product.categoria,
      precioMin: Math.min(...product.tiendas.map(t => t.precio)),
      precioMax: Math.max(...product.tiendas.map(t => t.precio)),
      tiendasCount: product.tiendas.length,
      imagen: product.tiendas[0]?.imagen || '',
      volumen: product.volumen || extractVolume(product.nombre),
      tipo: product.tipo,
      ofertas: product.tiendas.map(tienda => ({
        fuente: tienda.fuente,
        precio: tienda.precio,
        stock: tienda.stock,
        url: tienda.url,
        imagen: tienda.imagen,
        marcaOrigen: tienda.marca_origen || product.marca
      })).sort((a, b) => a.precio - b.precio) // Ordenar por precio ascendente
    }));
  }
  
  // Para productos del formato anterior (múltiples tiendas separadas)
  const groupedProducts = new Map();
  
  products.forEach(product => {
    const key = generateCanonicalKey(product);
    
    if (!groupedProducts.has(key)) {
      groupedProducts.set(key, {
        product_id: key,
        nombre: getProductNameWithoutBrand(product.nombre || product.productName, product.marca),
        marca: product.marca || '',
        categoria: product.categoria || product.category || '',
        volumen: extractVolume(product.nombre || product.productName || ''),
        ofertas: [],
        precios: []
      });
    }
    
    const group = groupedProducts.get(key);
    
    // Agregar oferta de esta tienda
    group.ofertas.push({
      fuente: product.tienda || product.storeId || product.storeName || '',
      precio: product.precio || product.precio_min || 0,
      stock: product.stock || product.availability || 'Desconocido',
      url: product.url || product.url_producto || '',
      imagen: product.imagen_url || product.imageUrl || '',
      marcaOrigen: product.marca || ''
    });
    
    group.precios.push(product.precio || product.precio_min || 0);
  });
  
  // Convertir a array y calcular estadísticas
  return Array.from(groupedProducts.values()).map(group => {
    // Ordenar ofertas por precio ascendente
    group.ofertas.sort((a, b) => a.precio - b.precio);
    
    return {
      product_id: group.product_id,
      nombre: group.nombre,
      marca: group.marca,
      categoria: group.categoria,
      volumen: group.volumen,
      precioMin: Math.min(...group.precios),
      precioMax: Math.max(...group.precios),
      tiendasCount: group.ofertas.length,
      imagen: group.ofertas[0]?.imagen || '', // Usar imagen de la primera oferta
      ofertas: group.ofertas
    };
  });
};

/**
 * Filtra productos deduplicados según criterios de búsqueda
 * @param {Array} deduplicatedProducts - Productos deduplicados
 * @param {Object} filters - Filtros a aplicar
 * @returns {Array} - Productos filtrados
 */
export const filterDeduplicatedProducts = (deduplicatedProducts, filters = {}) => {
  if (!Array.isArray(deduplicatedProducts)) {
    return [];
  }
  
  return deduplicatedProducts.filter(product => {
    // Filtrar por rango de precio
    if (filters.priceRange) {
      const [minPrice, maxPrice] = filters.priceRange;
      if (product.precioMin < minPrice || product.precioMin > maxPrice) {
        return false;
      }
    }
    
    // Filtrar por tiendas específicas
    if (filters.selectedStores && filters.selectedStores.length > 0) {
      const hasSelectedStore = product.ofertas.some(oferta => 
        filters.selectedStores.includes(oferta.fuente.toUpperCase())
      );
      if (!hasSelectedStore) {
        return false;
      }
    }
    
    // Filtrar por disponibilidad
    if (filters.availableOnly) {
      const hasAvailableStock = product.ofertas.some(oferta => 
        oferta.stock && oferta.stock.toLowerCase().includes('stock')
      );
      if (!hasAvailableStock) {
        return false;
      }
    }
    
    return true;
  });
};

export default {
  normalizeProductName,
  extractVolume,
  generateCanonicalKey,
  areProductsSimilar,
  getProductNameWithoutBrand,
  deduplicateProducts,
  filterDeduplicatedProducts
};

