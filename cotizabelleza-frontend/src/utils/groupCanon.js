// Normaliza texto: minúsculas, sin tildes, sin símbolos, espacios colapsados
export const normalize = (s = "") =>
  s.toLowerCase()
   .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
   .replace(/[^a-z0-9\s]/g, " ")
   .replace(/\s+/g, " ")
   .trim();

// Quita la marca del inicio del nombre SOLO para construir la clave
const stripBrand = (nombre = "", marca = "") => {
  const n = normalize(nombre);
  const m = normalize(marca);
  return m && n.startsWith(m + " ") ? n.slice(m.length + 1) : n;
};

// Volumen si viene (para diferenciar variantes)
const extractVol = (nameNorm) => {
  const m = nameNorm.match(/(\d+)\s?(ml|g|gr|kg|oz)\b/);
  return m ? `${m[1]} ${m[2].replace("gr","g")}` : "";
};

// MISMA clave que debe usar el detalle si no hay product_id del backend
export const clientKey = (item = {}) => {
  if (item.product_id) return item.product_id;     // respeta canónico del backend
  const base = stripBrand(item.nombre, item.marca);
  const vol  = extractVol(base);
  const cat  = normalize(item.categoria || "");
  // token set (ordena y deduplica palabras)
  const tokens = base.split(" ").filter(Boolean).sort();
  const core = Array.from(new Set(tokens)).join(" ");
  return `${core}__${vol}__${cat}`.trim();
};

// Mapa { key -> array de items de distintas tiendas }
export const bucketize = (items = []) => {
  const map = new Map();
  for (const it of items) {
    const key = clientKey(it);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(it);
  }
  return map;
};

// Convierte a lista de tarjetas para el listing (una por grupo)
export const toListingCards = (buckets) => {
  const out = [];
  for (const [key, arr] of buckets.entries()) {
    // nombre sin marca para la tarjeta
   const nombreSinMarca = stripBrand(arr[0].nombre, arr[0].marca) || arr[0].nombre;
    const img = arr.find(x => x.imagen || x.imagen_url)?.imagen || arr.find(x => x.imagen || x.imagen_url)?.imagen_url || arr[0].imagen || arr[0].imagen_url;
    const precioMin = Math.min(...arr.map(x => Number(x.precio) || Infinity));
    out.push({
      product_id: key,
      nombre: nombreSinMarca,
      categoria: arr[0].categoria,
      imagen: img,
      tiendasCount: arr.length,
      precioMin
    });
  }
  // orden por precio
  return out.sort((a,b) => (a.precioMin||0) - (b.precioMin||0));
};
