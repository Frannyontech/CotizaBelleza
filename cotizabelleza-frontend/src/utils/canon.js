export const normalize = (s = "") =>
  s.toLowerCase()
   .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
   .replace(/[^a-z0-9\s]/g, " ")
   .replace(/\s+/g, " ")
   .trim();

const normCategory = (c = "") => {
  const n = normalize(c);
  if (n.includes("piel") || n.includes("skincare")) return "skincare";
  return "maquillaje";
};

const stripBrand = (nombre = "", marca = "") => {
  const n = normalize(nombre);
  const m = normalize(marca);
  return m && n.startsWith(m + " ") ? n.slice(m.length + 1) : n;
};

const extractVol = (nameNorm) => {
  const m = nameNorm.match(/(\d+)\s?(ml|g|gr|kg|oz)\b/);
  return m ? `${m[1]} ${m[2].replace("gr","g")}` : "";
};

// Clave canónica: misma para search y detalle
export const canonKey = (item = {}) => {
  if (item.product_id) return String(item.product_id);
  const cat = normCategory(item.categoria || "");
  const base = stripBrand(item.nombre || "", item.marca || "");
  const vol  = extractVol(base);
  const tokens = base.split(" ").filter(Boolean).sort();
  const core = Array.from(new Set(tokens)).join(" ");
  // Importante: categoría normalizada
  return `${core}__${vol}__${cat}`.trim();
};

export const addCanonicalId = (items = []) =>
  (items || []).map(it => ({ ...it, product_id: canonKey(it) }));

export const bucketize = (items = []) => {
  const map = new Map();
  for (const it of items) {
    const key = it.product_id || canonKey(it);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(it);
  }
  return map;
};

export const toListingCards = (buckets) => {
  const out = [];
  for (const [key, arr] of buckets.entries()) {
    const nombreSinMarca =
      stripBrand(arr[0].nombre, arr[0].marca) || arr[0].nombre;
    
    // Buscar la mejor imagen disponible
    const img = arr.find(x => x.imagen_url)?.imagen_url || 
                arr.find(x => x.imagen)?.imagen || 
                arr[0].imagen_url || 
                arr[0].imagen;
    
    const precioMin = Math.min(...arr.map(x => Number(x.precio) || Infinity));
    
    // Crear lista de tiendas únicas
    const tiendas = [...new Set(arr.map(x => 
      x.fuente ? x.fuente.toUpperCase() : 
      x.tienda ? x.tienda.toUpperCase() : 'TIENDA'
    ))];
    
    // Para productos individuales, usar ID original; para grupos, usar ID canónico
    const finalProductId = arr.length === 1 ? arr[0].id : key;
    
    out.push({
      product_id: finalProductId,
      nombre: nombreSinMarca,
      marca: arr[0].marca, // Preservar marca para mostrar
      categoria: normCategory(arr[0].categoria),
      imagen: img,
      tiendasCount: arr.length,
      precioMin,
      tiendas: tiendas, // Lista de tiendas
      originalItems: arr, // Mantener items originales para referencia
      isCanonical: arr.length > 1 // Indicar si es ID canónico o no
    });
  }
  return out.sort((a,b) => (a.precioMin||0) - (b.precioMin||0));
};

export const buildDetail = (buckets, productIdRaw) => {
  const productId = decodeURIComponent(productIdRaw || "");
  const arr = buckets.get(productId) || [];
  if (arr.length === 0) return null;
  const nombreSinMarca =
    stripBrand(arr[0].nombre, arr[0].marca) || arr[0].nombre;
  const ofertas = arr
    .map(x => ({
      fuente: x.fuente,
      precio: Number(x.precio) || 0,
      stock: x.stock,
      url: x.url,
      imagen: x.imagen,
      marca_origen: x.marca
    }))
    .sort((a,b) => a.precio - b.precio);
  return {
    product_id: productId,
    nombre: nombreSinMarca,
    categoria: normCategory(arr[0].categoria),
    imagen: arr.find(x => x.imagen)?.imagen || arr[0].imagen,
    ofertas,
    tiendasCount: ofertas.length,
    precioMin: Math.min(...ofertas.map(o => o.precio || Infinity))
  };
};
