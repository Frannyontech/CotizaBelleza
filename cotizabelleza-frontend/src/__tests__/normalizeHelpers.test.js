import {
  normalizeToSlug,
  normalizeForComparison,
  deduplicateCategories,
  deduplicateStores,
  processCategoriesForFrontend,
  processStoresForFrontend
} from '../utils/normalizeHelpers';

describe('normalizeToSlug', () => {
  it('debería normalizar mayúsculas/minúsculas correctamente', () => {
    expect(normalizeToSlug('Maquillaje')).toBe('maquillaje');
    expect(normalizeToSlug('SKINCARE')).toBe('skincare');
    expect(normalizeToSlug('Base Liquida')).toBe('base-liquida');
  });

  it('debería eliminar acentos correctamente', () => {
    expect(normalizeToSlug('Skíncare')).toBe('skincare');
    expect(normalizeToSlug('Maquilláje')).toBe('maquillaje');
    expect(normalizeToSlug('Crema Hidratánte')).toBe('crema-hidratante');
  });

  it('debería manejar espacios extra correctamente', () => {
    expect(normalizeToSlug(' maquillaje ')).toBe('maquillaje');
    expect(normalizeToSlug('  skincare  ')).toBe('skincare');
  });

  it('debería manejar espacios múltiples intermedios correctamente', () => {
    expect(normalizeToSlug('Base Liquida')).toBe('base-liquida');
    expect(normalizeToSlug('Crema  Hidratante')).toBe('crema-hidratante');
    expect(normalizeToSlug('Máscara   de   Pestañas')).toBe('mascara-de-pestanas');
  });

  it('debería manejar caracteres especiales y números', () => {
    expect(normalizeToSlug('Producto 2.0')).toBe('producto-20');
    expect(normalizeToSlug('Crema & Gel')).toBe('crema-gel');
    expect(normalizeToSlug('Loción 50ml')).toBe('lotion-50ml');
  });

  it('debería manejar casos edge', () => {
    expect(normalizeToSlug('')).toBe('');
    expect(normalizeToSlug(null)).toBe('');
    expect(normalizeToSlug(undefined)).toBe('');
    expect(normalizeToSlug(123)).toBe('');
    expect(normalizeToSlug({})).toBe('');
  });
});

describe('normalizeForComparison', () => {
  it('debería normalizar para comparación sin crear slug', () => {
    expect(normalizeForComparison('Maquillaje')).toBe('maquillaje');
    expect(normalizeForComparison('SKINCARE')).toBe('skincare');
    expect(normalizeForComparison('Base Liquida')).toBe('base liquida');
  });

  it('debería eliminar acentos para comparación', () => {
    expect(normalizeForComparison('Skíncare')).toBe('skincare');
    expect(normalizeForComparison('Maquilláje')).toBe('maquillaje');
  });

  it('debería manejar espacios para comparación', () => {
    expect(normalizeForComparison(' maquillaje ')).toBe('maquillaje');
    expect(normalizeForComparison('Base  Liquida')).toBe('base liquida');
  });

  it('debería manejar casos edge', () => {
    expect(normalizeForComparison('')).toBe('');
    expect(normalizeForComparison(null)).toBe('');
    expect(normalizeForComparison(undefined)).toBe('');
  });
});

describe('deduplicateCategories', () => {
  it('debería deduplicar categorías con diferentes capitalizaciones', () => {
    const categories = ['Maquillaje', 'maquillaje', 'MAQUILLAJE'];
    const result = deduplicateCategories(categories);
    expect(result).toEqual(['Maquillaje']);
  });

  it('debería deduplicar categorías con acentos', () => {
    const categories = ['Skíncare', 'skincare', 'Skincare'];
    const result = deduplicateCategories(categories);
    expect(result).toEqual(['Skíncare']);
  });

  it('debería deduplicar categorías con espacios extra', () => {
    const categories = [' maquillaje ', 'maquillaje', '  maquillaje  '];
    const result = deduplicateCategories(categories);
    expect(result).toEqual([' maquillaje ']);
  });

  it('debería ordenar con "Todos" primero', () => {
    const categories = ['Skincare', 'Todos', 'Maquillaje'];
    const result = deduplicateCategories(categories);
    expect(result).toEqual(['Todos', 'Maquillaje', 'Skincare']);
  });

  it('debería manejar objetos con propiedad nombre', () => {
    const categories = [
      { nombre: 'Maquillaje' },
      { nombre: 'maquillaje' },
      { nombre: 'Skincare' }
    ];
    const result = deduplicateCategories(categories);
    expect(result).toEqual(['Maquillaje', 'Skincare']);
  });

  it('debería manejar arrays mixtos', () => {
    const categories = ['Maquillaje', { nombre: 'maquillaje' }, 'Skincare'];
    const result = deduplicateCategories(categories);
    expect(result).toEqual(['Maquillaje', 'Skincare']);
  });

  it('debería manejar casos edge', () => {
    expect(deduplicateCategories([])).toEqual([]);
    expect(deduplicateCategories(null)).toEqual([]);
    expect(deduplicateCategories(undefined)).toEqual([]);
    expect(deduplicateCategories(['', null, undefined])).toEqual([]);
  });
});

describe('deduplicateStores', () => {
  it('debería deduplicar tiendas con diferentes capitalizaciones', () => {
    const stores = ['DBS', 'dbs', 'Dbs'];
    const result = deduplicateStores(stores);
    expect(result).toEqual(['DBS']);
  });

  it('debería deduplicar tiendas con espacios extra', () => {
    const stores = [' DBS ', 'dbs', '  DBS  '];
    const result = deduplicateStores(stores);
    expect(result).toEqual([' DBS ']);
  });

  it('debería ordenar con "Todas" primero', () => {
    const stores = ['DBS', 'Todas', 'Farmacia'];
    const result = deduplicateStores(stores);
    expect(result).toEqual(['Todas', 'DBS', 'Farmacia']);
  });

  it('debería manejar objetos con propiedad nombre', () => {
    const stores = [
      { nombre: 'DBS' },
      { nombre: 'dbs' },
      { nombre: 'Farmacia' }
    ];
    const result = deduplicateStores(stores);
    expect(result).toEqual(['DBS', 'Farmacia']);
  });

  it('debería manejar casos edge', () => {
    expect(deduplicateStores([])).toEqual([]);
    expect(deduplicateStores(null)).toEqual([]);
    expect(deduplicateStores(undefined)).toEqual([]);
  });
});

describe('processCategoriesForFrontend', () => {
  it('debería agregar "Todos" si no existe', () => {
    const categories = ['Maquillaje', 'Skincare'];
    const result = processCategoriesForFrontend(categories);
    expect(result).toEqual(['Todos', 'Maquillaje', 'Skincare']);
  });

  it('debería mantener "Todos" al inicio si ya existe', () => {
    const categories = ['Skincare', 'Todos', 'Maquillaje'];
    const result = processCategoriesForFrontend(categories);
    expect(result).toEqual(['Todos', 'Maquillaje', 'Skincare']);
  });

  it('debería deduplicar y procesar correctamente', () => {
    const categories = ['Maquillaje', 'maquillaje', 'Skincare', 'skincare'];
    const result = processCategoriesForFrontend(categories);
    expect(result).toEqual(['Todos', 'Maquillaje', 'Skincare']);
  });

  it('debería manejar casos edge', () => {
    expect(processCategoriesForFrontend([])).toEqual(['Todos']);
    expect(processCategoriesForFrontend(null)).toEqual(['Todos']);
    expect(processCategoriesForFrontend(undefined)).toEqual(['Todos']);
  });
});

describe('processStoresForFrontend', () => {
  it('debería agregar "Todas" si no existe', () => {
    const stores = ['DBS', 'Farmacia'];
    const result = processStoresForFrontend(stores);
    expect(result).toEqual(['Todas', 'DBS', 'Farmacia']);
  });

  it('debería mantener "Todas" al inicio si ya existe', () => {
    const stores = ['Farmacia', 'Todas', 'DBS'];
    const result = processStoresForFrontend(stores);
    expect(result).toEqual(['Todas', 'DBS', 'Farmacia']);
  });

  it('debería deduplicar y procesar correctamente', () => {
    const stores = ['DBS', 'dbs', 'Farmacia'];
    const result = processStoresForFrontend(stores);
    expect(result).toEqual(['Todas', 'DBS', 'Farmacia']);
  });

  it('debería manejar casos edge', () => {
    expect(processStoresForFrontend([])).toEqual(['Todas']);
    expect(processStoresForFrontend(null)).toEqual(['Todas']);
    expect(processStoresForFrontend(undefined)).toEqual(['Todas']);
  });
});

describe('Casos de prueba mixtos con datos reales', () => {
  it('debería manejar el caso real de categorías duplicadas', () => {
    const categories = ['Maquillaje', 'maquillaje', 'skincare', 'Skincare'];
    const result = processCategoriesForFrontend(categories);
    expect(result).toEqual(['Todos', 'Maquillaje', 'Skincare']);
  });

  it('debería manejar el caso real de tiendas duplicadas', () => {
    const stores = ['DBS', 'dbs ', 'Farmacia'];
    const result = processStoresForFrontend(stores);
    expect(result).toEqual(['Todas', 'DBS', 'Farmacia']);
  });

  it('debería manejar estructura de datos real del API', () => {
    const categoriesFromAPI = [
      { nombre: 'Maquillaje' },
      { nombre: 'maquillaje' },
      { nombre: 'Skincare' },
      { nombre: 'skincare' }
    ];
    const result = processCategoriesForFrontend(categoriesFromAPI);
    expect(result).toEqual(['Todos', 'Maquillaje', 'Skincare']);
  });

  it('debería manejar estructura de datos real de tiendas del API', () => {
    const storesFromAPI = [
      { nombre: 'DBS' },
      { nombre: 'dbs' },
      { nombre: 'Farmacia Ahumada' }
    ];
    const result = processStoresForFrontend(storesFromAPI);
    expect(result).toEqual(['Todas', 'DBS', 'Farmacia Ahumada']);
  });
});
