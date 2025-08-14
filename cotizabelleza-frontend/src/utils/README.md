# Utils - Funciones Helper

Este directorio contiene funciones utilitarias para el proyecto CotizaBelleza.

## normalizeHelpers.js

Funciones para normalización y deduplicación de categorías y tiendas.

### Funciones disponibles:

#### `normalizeToSlug(text)`
Normaliza un string para crear un slug consistente.
- Convierte a minúsculas
- Elimina acentos
- Reemplaza espacios con guiones
- Elimina caracteres especiales

**Ejemplo:**
```javascript
normalizeToSlug('Base Liquida') // → 'base-liquida'
normalizeToSlug('Skíncare') // → 'skincare'
```

#### `normalizeForComparison(text)`
Normaliza un string para comparación (sin crear slug).
- Convierte a minúsculas
- Elimina acentos
- Normaliza espacios

**Ejemplo:**
```javascript
normalizeForComparison('Maquillaje') // → 'maquillaje'
normalizeForComparison('Skíncare') // → 'skincare'
```

#### `deduplicateCategories(categories)`
Deduplica una lista de categorías eliminando duplicados con diferentes capitalizaciones.

**Ejemplo:**
```javascript
const categories = ['Maquillaje', 'maquillaje', 'Skincare', 'skincare'];
deduplicateCategories(categories) // → ['Maquillaje', 'Skincare']
```

#### `deduplicateStores(stores)`
Deduplica una lista de tiendas eliminando duplicados con diferentes capitalizaciones.

**Ejemplo:**
```javascript
const stores = ['DBS', 'dbs', 'Farmacia'];
deduplicateStores(stores) // → ['DBS', 'Farmacia']
```

#### `processCategoriesForFrontend(categories)`
Procesa categorías para el frontend, agregando "Todos" si no existe.

**Ejemplo:**
```javascript
const categories = ['Maquillaje', 'maquillaje', 'Skincare'];
processCategoriesForFrontend(categories) // → ['Todos', 'Maquillaje', 'Skincare']
```

#### `processStoresForFrontend(stores)`
Procesa tiendas para el frontend, agregando "Todas" si no existe.

**Ejemplo:**
```javascript
const stores = ['DBS', 'dbs', 'Farmacia'];
processStoresForFrontend(stores) // → ['Todas', 'DBS', 'Farmacia']
```

## Uso en componentes

```javascript
import { processCategoriesForFrontend, processStoresForFrontend } from '../../utils/normalizeHelpers';

// En tu componente
const categoriesList = processCategoriesForFrontend(categories);
const storesList = processStoresForFrontend(stores);
```

## Casos de uso

Estas funciones resuelven el problema de categorías y tiendas duplicadas que aparecen en el frontend con diferentes capitalizaciones:

- "Maquillaje" vs "maquillaje"
- "Skincare" vs "skincare"
- "DBS" vs "dbs"

Las funciones mantienen la primera versión encontrada y eliminan las duplicadas, asegurando una experiencia de usuario consistente.
