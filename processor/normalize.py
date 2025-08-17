#!/usr/bin/env python3
"""
Módulo para normalizar y unificar productos de múltiples fuentes JSON.
Genera un archivo unificado listo para el frontend.
"""

import json
import re
import hashlib
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

try:
    from rapidfuzz import fuzz
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from unidecode import unidecode
except ImportError as e:
    print(f"Error: Falta instalar dependencias: {e}")
    print("Ejecute: pip install rapidfuzz scikit-learn unidecode")
    exit(1)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Patrones regex para extracción
VOLUME_PATTERN = re.compile(r'(\d+)\s?(ml|g|gr|kg|oz)', re.IGNORECASE)
TYPE_KEYWORDS = [
    'labial', 'serum', 'crema', 'limpiador', 'tónico', 'base', 'gel', 
    'mascara', 'máscara', 'sombra', 'rubor', 'polvo', 'corrector', 
    'delineador', 'primer', 'bronceador', 'iluminador'
]
TYPE_PATTERN = re.compile(r'\b(' + '|'.join(TYPE_KEYWORDS) + r')\b', re.IGNORECASE)

# Palabras de ruido a eliminar
NOISE_WORDS = [
    'nuevo', 'pack', 'set', '%', 'oferta', 'kit', 'mini', 'tester',
    'original', 'importado', 'sale', 'promo', 'promoción', 'descuento'
]

def load_raw_files(paths: List[str]) -> List[Dict]:
    """Carga todos los archivos JSON raw y agrega fuente si falta."""
    all_products = []
    
    for path in paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            products = data.get('productos', [])
            fuente = data.get('tienda', '').lower()
            
            # Inferir fuente del nombre del archivo si no está presente
            if not fuente:
                if 'dbs' in path.lower():
                    fuente = 'dbs'
                elif 'maicao' in path.lower():
                    fuente = 'maicao'
                elif 'preunic' in path.lower():
                    fuente = 'preunic'
            
            # Agregar fuente a cada producto
            for product in products:
                product['fuente'] = fuente
                all_products.append(product)
                
            logger.info(f"Cargados {len(products)} productos de {path}")
            
        except Exception as e:
            logger.error(f"Error cargando {path}: {e}")
            
    return all_products

def normalize_text(text: str) -> str:
    """Normaliza texto: minúsculas, sin tildes, limpia símbolos."""
    if not text:
        return ""
    
    # Convertir a minúsculas y quitar tildes
    normalized = unidecode(text.lower())
    
    # Normalizar unidades de volumen
    normalized = re.sub(r'(\d+)\s*ml\b', r'\1 ml', normalized)
    normalized = re.sub(r'(\d+)\s*gr?\b', r'\1 g', normalized)
    normalized = re.sub(r'(\d+)\s*kg\b', r'\1 kg', normalized)
    normalized = re.sub(r'(\d+)\s*oz\b', r'\1 oz', normalized)
    
    # Limpiar símbolos y espacios múltiples
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Quitar palabras de ruido
    words = normalized.split()
    clean_words = [w for w in words if w not in NOISE_WORDS]
    
    return ' '.join(clean_words).strip()

def extract_attrs(name_norm: str) -> Dict[str, Optional[str]]:
    """Extrae volumen y tipo del nombre normalizado."""
    attrs = {'volumen': None, 'tipo': None}
    
    # Extraer volumen
    volume_match = VOLUME_PATTERN.search(name_norm)
    if volume_match:
        cantidad, unidad = volume_match.groups()
        # Normalizar unidades
        if unidad.lower() in ['gr', 'g']:
            unidad = 'g'
        elif unidad.lower() == 'ml':
            unidad = 'ml'
        attrs['volumen'] = f"{cantidad} {unidad}"
    
    # Extraer tipo
    type_match = TYPE_PATTERN.search(name_norm)
    if type_match:
        attrs['tipo'] = type_match.group(1).lower()
        if attrs['tipo'] == 'máscara':
            attrs['tipo'] = 'mascara'
    
    return attrs

def dedupe_intra_source(items: List[Dict]) -> List[Dict]:
    """Deduplicación dentro de cada fuente por similitud de nombre y volumen."""
    if not items:
        return items
    
    # Agrupar por (categoria, marca_cmp)
    groups = defaultdict(list)
    for item in items:
        key = (item['categoria'], item['marca_cmp'])
        groups[key].append(item)
    
    deduplicated = []
    
    for group_items in groups.values():
        if len(group_items) <= 1:
            deduplicated.extend(group_items)
            continue
        
        # Buscar duplicados dentro del grupo
        used_indices = set()
        
        for i, item1 in enumerate(group_items):
            if i in used_indices:
                continue
                
            duplicates = [item1]
            
            for j, item2 in enumerate(group_items[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # Comparar similitud de nombre
                similarity = fuzz.ratio(item1['nombre_norm'], item2['nombre_norm'])
                
                # Verificar mismo volumen si existe
                same_volume = (
                    item1.get('volumen') == item2.get('volumen') 
                    if item1.get('volumen') and item2.get('volumen') 
                    else True
                )
                
                if similarity >= 95 and same_volume:
                    duplicates.append(item2)
                    used_indices.add(j)
            
            # Conservar el mejor de los duplicados (mejor imagen/URL)
            best = max(duplicates, key=lambda x: (
                bool(x.get('imagen')), 
                bool(x.get('url')),
                len(x.get('nombre', ''))
            ))
            deduplicated.append(best)
            used_indices.add(i)
    
    return deduplicated

def block_items(items: List[Dict]) -> Dict[Tuple, List[Dict]]:
    """Agrupa productos por bloques (categoria, marca_cmp, tipo opcional)."""
    blocks = defaultdict(list)
    
    for item in items:
        # Usar tipo si está disponible para mejor blocking
        block_key = (
            item['categoria'], 
            item['marca_cmp'],
            item.get('tipo', '')
        )
        blocks[block_key].append(item)
    
    return dict(blocks)

def compute_similarity(names_norm: List[str]) -> Tuple[Any, Any, List[List[float]]]:
    """Calcula matrices de similitud TF-IDF y rapidfuzz."""
    if len(names_norm) < 2:
        return None, None, []
    
    # TF-IDF + coseno
    vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 2))
    try:
        tfidf_matrix = vectorizer.fit_transform(names_norm)
        cosine_matrix = cosine_similarity(tfidf_matrix)
    except ValueError:
        # Si no hay suficiente vocabulario
        cosine_matrix = [[0.0] * len(names_norm) for _ in range(len(names_norm))]
        tfidf_matrix = None
    
    # Rapidfuzz scores
    rapidfuzz_scores = []
    for i, name1 in enumerate(names_norm):
        row = []
        for j, name2 in enumerate(names_norm):
            if i == j:
                row.append(100.0)
            else:
                # Usar Token Sort Ratio para mejor matching
                score = max(
                    fuzz.ratio(name1, name2),
                    fuzz.token_sort_ratio(name1, name2),
                    fuzz.token_set_ratio(name1, name2)
                )
                row.append(score)
        rapidfuzz_scores.append(row)
    
    return tfidf_matrix, cosine_matrix, rapidfuzz_scores

def volumes_compatible(vol1: Optional[str], vol2: Optional[str], tolerance: float = 0.15) -> bool:
    """Verifica si dos volúmenes son compatibles con tolerancia."""
    if not vol1 or not vol2:
        return True  # Si alguno no tiene volumen, asumimos compatible
    
    # Extraer números y unidades
    def parse_volume(vol_str):
        match = re.match(r'(\d+(?:\.\d+)?)\s*(\w+)', vol_str.strip())
        if match:
            return float(match.group(1)), match.group(2).lower()
        return None, None
    
    num1, unit1 = parse_volume(vol1)
    num2, unit2 = parse_volume(vol2)
    
    if not (num1 and num2 and unit1 == unit2):
        return vol1.strip() == vol2.strip()  # Comparación exacta si no se puede parsear
    
    # Verificar tolerancia
    diff = abs(num1 - num2) / max(num1, num2)
    return diff <= tolerance

def cluster_matches(group: List[Dict], min_strong: float = 90, min_prob: float = 85) -> List[List[Dict]]:
    """Forma clusters de productos similares usando umbrales."""
    if len(group) <= 1:
        return [group] if group else []
    
    names_norm = [item['nombre_norm'] for item in group]
    _, cosine_matrix, rapidfuzz_scores = compute_similarity(names_norm)
    
    # Crear matriz de adyacencia para matches fuertes
    n = len(group)
    adjacency = [[False] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(i + 1, n):
            item1, item2 = group[i], group[j]
            
            # Calcular score máximo
            rapidfuzz_score = rapidfuzz_scores[i][j]
            cosine_score = (cosine_matrix[i][j] * 100) if cosine_matrix is not None else 0
            max_score = max(rapidfuzz_score, cosine_score)
            
            # Verificar reglas de consistencia
            types_match = (
                item1.get('tipo') == item2.get('tipo') 
                if item1.get('tipo') and item2.get('tipo')
                else True
            )
            
            volumes_match = volumes_compatible(
                item1.get('volumen'), 
                item2.get('volumen')
            )
            
            # Excluir matches problemáticos
            skip_match = False
            for keyword in ['kit', 'mini', 'tester', 'pack']:
                has_keyword1 = keyword in item1['nombre_norm']
                has_keyword2 = keyword in item2['nombre_norm']
                if has_keyword1 != has_keyword2:  # Solo uno tiene la keyword
                    skip_match = True
                    break
            
            # Match fuerte
            if (max_score >= min_strong and 
                types_match and 
                volumes_match and 
                not skip_match):
                adjacency[i][j] = adjacency[j][i] = True
    
    # Formar clusters usando DFS
    visited = [False] * n
    clusters = []
    
    def dfs(node, cluster):
        visited[node] = True
        cluster.append(group[node])
        for neighbor in range(n):
            if adjacency[node][neighbor] and not visited[neighbor]:
                dfs(neighbor, cluster)
    
    for i in range(n):
        if not visited[i]:
            cluster = []
            dfs(i, cluster)
            clusters.append(cluster)
    
    return clusters

def build_canonical(cluster: List[Dict]) -> Dict[str, Any]:
    """Construye producto canónico a partir de un cluster."""
    if not cluster:
        return {}
    
    # Obtener atributos más comunes/informativos
    categorias = [item['categoria'] for item in cluster]
    categoria = max(set(categorias), key=categorias.count)
    
    marcas_originales = [item['marca'] for item in cluster]
    marca = max(set(marcas_originales), key=marcas_originales.count)
    
    # Nombre más informativo (más largo y descriptivo)
    nombres = [item['nombre'] for item in cluster]
    nombre = max(nombres, key=lambda x: (len(x.split()), len(x)))
    
    # Atributos del primer elemento que los tenga
    volumen = next((item.get('volumen') for item in cluster if item.get('volumen')), None)
    tipo = next((item.get('tipo') for item in cluster if item.get('tipo')), None)
    
    # Crear clave para product_id
    marca_cmp = cluster[0]['marca_cmp']
    nombre_base = normalize_text(nombre)
    key_parts = [marca_cmp, nombre_base]
    if volumen:
        key_parts.append(volumen)
    if tipo:
        key_parts.append(tipo)
    
    key_string = '|'.join(key_parts)
    product_id = 'cb_' + hashlib.sha1(key_string.encode('utf-8')).hexdigest()[:8]
    
    # Crear lista de tiendas ordenada por precio
    tiendas = []
    for item in cluster:
        tienda_info = {
            'fuente': item['fuente'],
            'precio': item['precio'],
            'stock': item.get('stock', 'Desconocido'),
            'url': item.get('url', ''),
            'imagen': item.get('imagen', ''),
            'marca_origen': item['marca']  # Marca original sin modificar
        }
        tiendas.append(tienda_info)
    
    # Ordenar por precio ascendente
    tiendas.sort(key=lambda x: x['precio'])
    
    canonical = {
        'product_id': product_id,
        'nombre': nombre,
        'marca': marca,
        'categoria': categoria,
        'tiendas': tiendas
    }
    
    if volumen:
        canonical['volumen'] = volumen
    if tipo:
        canonical['tipo'] = tipo
    
    return canonical

def save_json(path: str, data: Any) -> None:
    """Guarda datos en archivo JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def validate_output(path: str) -> bool:
    """Valida que el archivo de salida sea correcto."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.error("El archivo debe contener una lista de productos")
            return False
        
        for i, product in enumerate(data):
            required_fields = ['product_id', 'nombre', 'marca', 'categoria', 'tiendas']
            for field in required_fields:
                if field not in product:
                    logger.error(f"Producto {i}: falta campo requerido '{field}'")
                    return False
            
            if not isinstance(product['tiendas'], list) or not product['tiendas']:
                logger.error(f"Producto {i}: 'tiendas' debe ser una lista no vacía")
                return False
            
            for j, tienda in enumerate(product['tiendas']):
                tienda_required = ['fuente', 'precio', 'url']
                for field in tienda_required:
                    if field not in tienda:
                        logger.error(f"Producto {i}, tienda {j}: falta campo '{field}'")
                        return False
        
        logger.info(f"Validación exitosa: {len(data)} productos válidos")
        return True
        
    except Exception as e:
        logger.error(f"Error validando archivo: {e}")
        return False

def main():
    """Función principal del pipeline de normalización."""
    parser = argparse.ArgumentParser(description='Normaliza productos de múltiples fuentes JSON')
    parser.add_argument('--min-strong', type=float, default=90, 
                       help='Umbral mínimo para match fuerte (default: 90)')
    parser.add_argument('--min-prob', type=float, default=85,
                       help='Umbral mínimo para match probable (default: 85)')
    parser.add_argument('--out', default='processed/unified_products.json',
                       help='Archivo de salida (default: processed/unified_products.json)')
    
    args = parser.parse_args()
    
    # Archivos de entrada
    input_files = [
        'scraper/data/dbs_maquillaje.json',
        'scraper/data/dbs_skincare.json',
        'scraper/data/maicao_maquillaje.json',
        'scraper/data/maicao_skincare.json',
        'scraper/data/preunic_maquillaje.json',
        'scraper/data/preunic_skincare.json'
    ]
    
    logger.info("Iniciando pipeline de normalización...")
    
    # 1. Cargar archivos raw
    logger.info("Paso 1: Cargando archivos raw...")
    raw_products = load_raw_files(input_files)
    logger.info(f"Total productos cargados: {len(raw_products)}")
    
    # 2. Limpieza y normalización
    logger.info("Paso 2: Limpieza y normalización...")
    for product in raw_products:
        product['nombre_norm'] = normalize_text(product.get('nombre', ''))
        product['marca_cmp'] = normalize_text(product.get('marca', ''))
        
        # Extraer atributos
        attrs = extract_attrs(product['nombre_norm'])
        product.update(attrs)
    
    # 3. Deduplicación intra-tienda
    logger.info("Paso 3: Deduplicación intra-tienda...")
    sources = defaultdict(list)
    for product in raw_products:
        sources[product['fuente']].append(product)
    
    deduplicated_products = []
    for source, products in sources.items():
        deduped = dedupe_intra_source(products)
        logger.info(f"Fuente {source}: {len(products)} -> {len(deduped)} productos")
        deduplicated_products.extend(deduped)
    
    # 4. Blocking inter-tienda
    logger.info("Paso 4: Blocking inter-tienda...")
    blocks = block_items(deduplicated_products)
    logger.info(f"Creados {len(blocks)} bloques para matching")
    
    # 5. Matching y clustering
    logger.info("Paso 5: Matching y clustering...")
    all_clusters = []
    multi_store_count = 0
    
    for block_key, block_products in blocks.items():
        if len(block_products) <= 1:
            all_clusters.extend([[p] for p in block_products])
            continue
        
        clusters = cluster_matches(block_products, args.min_strong, args.min_prob)
        all_clusters.extend(clusters)
        
        # Contar clusters con múltiples tiendas
        for cluster in clusters:
            sources_in_cluster = set(p['fuente'] for p in cluster)
            if len(sources_in_cluster) > 1:
                multi_store_count += 1
    
    logger.info(f"Formados {len(all_clusters)} clusters")
    logger.info(f"Productos con 2+ tiendas: {multi_store_count} ({multi_store_count/len(all_clusters)*100:.1f}%)")
    
    # 6. Generar productos canónicos
    logger.info("Paso 6: Generando productos canónicos...")
    canonical_products = []
    for cluster in all_clusters:
        canonical = build_canonical(cluster)
        if canonical:
            canonical_products.append(canonical)
    
    # 7. Guardar resultado
    logger.info(f"Paso 7: Guardando {len(canonical_products)} productos en {args.out}")
    save_json(args.out, canonical_products)
    
    # 8. Validación
    logger.info("Paso 8: Validando salida...")
    if validate_output(args.out):
        logger.info("Pipeline completado exitosamente!")
    else:
        logger.error("Error en la validación del archivo de salida")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
