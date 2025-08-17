// src/utils/matchSameProduct.js
export const normalize = (s = "") =>
  s.toLowerCase()
   .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
   .replace(/[^a-z0-9\s]/g, " ")
   .replace(/\s+/g, " ")
   .trim();

const stripBrandFromName = (nombre = "", marca = "") => {
  const n = normalize(nombre);
  const m = normalize(marca);
  return m && n.startsWith(m + " ") ? n.slice(m.length + 1) : n;
};

const extractVol = (nameNorm) => {
  const m = nameNorm.match(/(\d+)\s?(ml|g|gr|kg|oz)\b/);
  return m ? `${m[1]} ${m[2].replace("gr","g")}` : "";
};

const clientKey = (item) => {
  if (item.product_id) return item.product_id; // respetar ID si viene del backend
  const base = stripBrandFromName(item.nombre || "", item.marca || "");
  const vol  = extractVol(base);
  const cat  = normalize(item.categoria || "");
  return `${base}__${vol}__${cat}`;
};

// Agrupa por clave canónica pero **no rompe** los items individuales
export const groupForComparator = (items = []) => {
  const buckets = new Map();
  for (const it of items) {
    const key = clientKey(it);
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(it);
  }
  return buckets; // Map<key, item[]>
};

// Construye una lista mixta para el listing:
// - Si grupo >=2 → 1 card con flag hasComparador=true y precio mínimo
// - Si grupo ==1 → devuelve tal cual el item original (hasComparador=false)
export const buildListingFromGroups = (groupsMap) => {
  const list = [];
  for (const [key, arr] of groupsMap.entries()) {
    if (arr.length >= 2) {
      const nombreSinMarca = stripBrandFromName(arr[0].nombre, arr[0].marca) || arr[0].nombre;
      const precioMin = Math.min(...arr.map(x => Number(x.precio) || Infinity));
      const imagen = arr.find(x => x.imagen || x.imagen_url)?.imagen || arr.find(x => x.imagen || x.imagen_url)?.imagen_url || arr[0].imagen || arr[0].imagen_url;
      list.push({
        product_id: key,
        nombre: nombreSinMarca,
        categoria: arr[0].categoria,
        imagen,
        tiendasCount: arr.length,
        precioMin,
        hasComparador: true
      });
    } else {
      const it = arr[0];
      list.push({
        ...it,
        product_id: clientKey(it),
        hasComparador: false,
        tiendasCount: 1,
        precioMin: Number(it.precio) || 0,
      });
    }
  }
  // ordena por precio mínimo cuando exista
  return list.sort((a,b) => (a.precioMin||0) - (b.precioMin||0));
};

// Para detalle: dado un product_id, devuelve { hasComparador, ofertas? , item? }
export const buildDetailById = (groupsMap, productId) => {
  const arr = groupsMap.get(productId) || [];
  if (arr.length >= 2) {
    // Comparador: listar tiendas ordenadas
    const ofertas = arr
      .map(x => ({
        fuente: x.fuente || x.tienda?.toLowerCase() || 'desconocido',
        precio: Number(x.precio) || 0,
        stock: x.stock || 'Desconocido',
        url: x.url || x.url_producto || '',
        imagen: x.imagen || x.imagen_url || '',
        marca_origen: x.marca || ''
      }))
      .sort((a,b) => a.precio - b.precio);
    const nombreSinMarca = stripBrandFromName(arr[0].nombre, arr[0].marca) || arr[0].nombre;
    return {
      hasComparador: true,
      nombre: nombreSinMarca,
      categoria: arr[0].categoria,
      imagen: arr.find(x => x.imagen || x.imagen_url)?.imagen || arr.find(x => x.imagen || x.imagen_url)?.imagen_url || '',
      ofertas
    };
  }
  // Legacy: devolver el item único (si existe)
  return {
    hasComparador: false,
    item: arr[0] || null
  };
};
