// Normaliza texto: minúsculas, sin tildes, sin símbolos y colapsa espacios
export const normalize = (s = "") =>
  s.toLowerCase()
   .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
   .replace(/[^a-z0-9\s]/g, " ")
   .replace(/\s+/g, " ")
   .trim();

// Palabras de relleno comunes en cosmética que no definen producto
const STOP = new Set([
  "brillo","labial","lifter","gloss","labios","lip","brillo","de","para",
  "maquillaje","makeup","maybelline","kiko","milano","n","no","numero","°"
]);

// Quita marca del nombre solo para construir la clave
const stripBrandFromName = (nombre, marca) => {
  const n = normalize(nombre);
  const m = normalize(marca || "");
  return n.startsWith(m + " ") ? n.slice(m.length + 1) : n;
};

// Extrae volumen (si existe)
const extractVol = (nameNorm) => {
  const m = nameNorm.match(/(\d+)\s?(ml|g|gr|kg|oz)\b/);
  return m ? `${m[1]} ${m[2].replace("gr","g")}` : "";
};

// Construye una clave canónica robusta (token set, sin marca)
export const buildClientKey = (item) => {
  const base = stripBrandFromName(item?.nombre || "", item?.marca || "");
  const cat  = normalize(item?.categoria || "");
  const vol  = extractVol(base);
  // token-set (ordena y deduplica) quitando stopwords y números sueltos (excepto volumen)
  const tokens = base.split(" ")
    .filter(t => t && !STOP.has(t) && !/^\d+$/.test(t))
    .sort();
  const core = Array.from(new Set(tokens)).join(" ");
  return `${core}__${vol}__${cat}`.trim();
};

// Une ofertas de varias tiendas bajo una sola clave canónica
export const toCanonical = (items = []) => {
  if (!items || items.length === 0) return [];
  const map = new Map();
  for (const it of items) {
    const key = it.product_id || buildClientKey(it);
    const nombreSinMarca = stripBrandFromName(it.nombre, it.marca) || it.nombre;
    const oferta = {
      fuente: it.fuente || it.tienda || it.storeId || it.storeName || 'desconocido',
      precio: Number(it.precio) || 0,
      stock: it.stock || 'Desconocido',
      url: it.url || it.url_producto || '',
      imagen: it.imagen || it.imagen_url || it.imageUrl || '',
      marca_origen: it.marca || ''
    };
    if (!map.has(key)) {
      map.set(key, {
        product_id: key,
        nombre: nombreSinMarca,               // SIN marca (para el listing)
        categoria: it.categoria || it.category || '',
        imagen: it.imagen || it.imagen_url || it.imageUrl || '',
        ofertas: [oferta],
        precioMin: oferta.precio,
        tiendasCount: 1
      });
    } else {
      const p = map.get(key);
      p.ofertas.push(oferta);
      p.precioMin = Math.min(p.precioMin, oferta.precio || Infinity);
      p.tiendasCount = p.ofertas.length;
      // conserva primera imagen válida
      if (!p.imagen && oferta.imagen) {
        p.imagen = oferta.imagen;
      }
    }
  }
  
  // Devolver productos ordenados por precio
  const result = Array.from(map.values());
  return result.sort((a,b) => (a.precioMin || 0) - (b.precioMin || 0));
};

// Nueva función: devuelve solo productos que tienen múltiples tiendas (para comparación)
export const getMultiStoreProducts = (items = []) => {
  const canonical = toCanonical(items);
  return canonical.filter(product => product.tiendasCount > 1);
};

// Nueva función: convierte productos individuales a formato estándar
export const getSingleStoreProducts = (items = []) => {
  const canonical = toCanonical(items);
  return canonical.filter(product => product.tiendasCount === 1);
};

// Función inteligente que solo deduplica cuando hay coincidencias reales
export const smartDedupe = (items = []) => {
  const canonical = toCanonical(items);
  const multiStore = canonical.filter(p => p.tiendasCount > 1);
  const singleStore = canonical.filter(p => p.tiendasCount === 1);
  
  // Si no hay productos multi-tienda, devolver items originales en formato simple
  if (multiStore.length === 0) {
    return {
      hasMatches: false,
      products: items.map(item => ({
        ...item,
        product_id: item.id || buildClientKey(item),
        nombre: item.nombre,
        precio: item.precio,
        tiendasCount: 1,
        isOriginal: true
      }))
    };
  }
  
  return {
    hasMatches: true,
    multiStoreProducts: multiStore,
    singleStoreProducts: singleStore,
    allCanonical: canonical
  };
};

// Función para determinar si un producto específico tiene coincidencias
export const hasProductMatches = (productId, items = []) => {
  const canonical = toCanonical(items);
  const product = canonical.find(p => p.product_id === productId);
  return product ? product.tiendasCount > 1 : false;
};
