/**
 * Utilidades para manejo de imágenes en CotizaBelleza
 * Proporciona funciones para resolver URLs de imágenes desde diferentes tiendas
 */

import logoCotizabellezaThumb from '../assets/logo_cotizabelleza_thumbnail.png';

/**
 * Resuelve la URL de imagen de un producto desde cualquier tienda
 * @param {any} product - Objeto producto que puede contener imagen_url, imageUrl, o media array
 * @returns {string} - URL de imagen resuelta o imagen por defecto
 */
export const resolveImageUrl = (product: any): string => {
  // Si no hay producto, retornar imagen por defecto
  if (!product) {
    return '/image-not-found.png';
  }

  // Prioridad 1: imageUrl (formato nuevo estandarizado)
  if (product.imageUrl && product.imageUrl.trim() !== '') {
    if (product.imageUrl.startsWith('http')) {
      return product.imageUrl;
    }
    if (product.imageUrl.startsWith('/')) {
      return product.imageUrl;
    }
  }

  // Prioridad 2: imagen_url (formato DBS/Preunic existente)
  if (product.imagen_url && product.imagen_url.trim() !== '') {
    if (product.imagen_url.startsWith('http')) {
      return product.imagen_url;
    }
    if (product.imagen_url.startsWith('/')) {
      // Para DBS, agregar el dominio
      if (product.tienda === 'DBS' || product.storeId === 'dbs') {
        return `https://dbs.cl${product.imagen_url}`;
      }
      return product.imagen_url;
    }
  }

  // Prioridad 3: media array (formato alternativo)
  if (product.media && Array.isArray(product.media) && product.media.length > 0) {
    const firstMedia = product.media[0];
    if (firstMedia && firstMedia.url) {
      return firstMedia.url;
    }
  }

  // Fallback: imagen por defecto
  return '/image-not-found.png';
};

/**
 * Obtiene el logo thumbnail por defecto de CotizaBelleza
 * @returns {string} - URL del logo thumbnail
 */
export const getDefaultThumbnail = (): string => {
  return logoCotizabellezaThumb;
};

/**
 * Verifica si una URL de imagen es válida
 * @param {string} url - URL a verificar
 * @returns {boolean} - true si la URL parece válida
 */
export const isValidImageUrl = (url: string): boolean => {
  if (!url || typeof url !== 'string') {
    return false;
  }
  
  return url.startsWith('http') || url.startsWith('/') || url.startsWith('data:');
};

/**
 * Obtiene las props estándar para el componente Image de Ant Design
 * @param {any} product - Producto del cual obtener la imagen
 * @param {Object} options - Opciones adicionales
 * @returns {Object} - Props para el componente Image
 */
export const getImageProps = (product: any, options: {
  height?: number | string;
  width?: number | string;
  objectFit?: 'contain' | 'cover' | 'fill' | 'scale-down';
  preview?: boolean;
} = {}) => {
  const {
    height = 200,
    width = '100%',
    objectFit = 'contain',
    preview = false
  } = options;

  return {
    src: resolveImageUrl(product),
    alt: product.productName || product.nombre || 'Producto',
    style: {
      objectFit,
      height,
      width
    },
    fallback: logoCotizabellezaThumb,
    preview
  };
};
