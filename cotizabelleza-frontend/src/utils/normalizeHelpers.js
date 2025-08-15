/**
 * Normaliza un string para crear un slug consistente
 * @param {string} text - Texto a normalizar
 * @returns {string} - Texto normalizado
 */
export const normalizeToSlug = (text) => {
  if (!text || typeof text !== 'string') {
    return '';
  }

  return text
    .toLowerCase()
    .trim()
    .normalize('NFD') // Normaliza caracteres Unicode
    .replace(/[\u0300-\u036f]/g, '') // Elimina acentos
    .replace(/\s+/g, '-') // Reemplaza espacios múltiples con guiones
    .replace(/[^a-z0-9-]/g, '') // Solo permite letras, números y guiones
    .replace(/-+/g, '-') // Reemplaza múltiples guiones con uno solo
    .replace(/^-|-$/g, ''); // Elimina guiones al inicio y final
};

/**
 * Normaliza un string para comparación (sin crear slug)
 * @param {string} text - Texto a normalizar
 * @returns {string} - Texto normalizado para comparación
 */
export const normalizeForComparison = (text) => {
  if (!text || typeof text !== 'string') {
    return '';
  }

  return text
    .toLowerCase()
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ');
};

/**
 * Deduplica y normaliza una lista de categorías
 * @param {Array} categories - Lista de categorías
 * @returns {Array} - Lista deduplicada y normalizada
 */
export const deduplicateCategories = (categories) => {
  if (!Array.isArray(categories)) {
    return [];
  }

  const normalizedMap = new Map();
  const result = [];

  // Procesar cada categoría
  categories.forEach(category => {
    const originalName = typeof category === 'string' ? category : category.nombre || category;
    if (!originalName) return;

    const normalized = normalizeForComparison(originalName);
    
    // Si no existe la versión normalizada, agregar la original
    if (!normalizedMap.has(normalized)) {
      normalizedMap.set(normalized, originalName);
      result.push(originalName);
    }
  });

  // Ordenar con "Todos" primero si existe
  return result.sort((a, b) => {
    if (a.toLowerCase() === 'todos') return -1;
    if (b.toLowerCase() === 'todos') return 1;
    return a.localeCompare(b, 'es', { sensitivity: 'base' });
  });
};

/**
 * Deduplica y normaliza una lista de tiendas
 * @param {Array} stores - Lista de tiendas
 * @returns {Array} - Lista deduplicada y normalizada
 */
export const deduplicateStores = (stores) => {
  if (!Array.isArray(stores)) {
    return [];
  }

  const normalizedMap = new Map();
  const result = [];

  // Procesar cada tienda
  stores.forEach(store => {
    const originalName = typeof store === 'string' ? store : store.nombre || store;
    if (!originalName) return;

    const normalized = normalizeForComparison(originalName);
    
    // Si no existe la versión normalizada, agregar la original
    if (!normalizedMap.has(normalized)) {
      normalizedMap.set(normalized, originalName);
      result.push(originalName);
    }
  });

  // Ordenar con "Todas" primero si existe
  return result.sort((a, b) => {
    if (a.toLowerCase() === 'todas') return -1;
    if (b.toLowerCase() === 'todas') return 1;
    return a.localeCompare(b, 'es', { sensitivity: 'base' });
  });
};

/**
 * Procesa categorías para el frontend (agrega "Todos" si no existe)
 * @param {Array} categories - Lista de categorías
 * @returns {Array} - Lista procesada para el frontend
 */
export const processCategoriesForFrontend = (categories) => {
  const deduplicated = deduplicateCategories(categories);
  
  // Agregar "Todos" al inicio si no existe
  if (!deduplicated.some(cat => cat.toLowerCase() === 'todos')) {
    return ['Todos', ...deduplicated];
  }
  
  return deduplicated;
};

/**
 * Procesa tiendas para el frontend (agrega "Todas" si no existe)
 * @param {Array} stores - Lista de tiendas
 * @returns {Array} - Lista procesada para el frontend
 */
export const processStoresForFrontend = (stores) => {
  const deduplicated = deduplicateStores(stores);
  
  // Agregar "Todas" al inicio si no existe
  if (!deduplicated.some(store => store.toLowerCase() === 'todas')) {
    return ['Todas', ...deduplicated];
  }
  
  return deduplicated;
};
