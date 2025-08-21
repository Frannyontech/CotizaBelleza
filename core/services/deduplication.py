"""
Sistema avanzado de deduplicación para productos de CotizaBelleza
Detecta y elimina duplicados usando múltiples estrategias
"""

import re
import difflib
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ProductoSimilitud:
    """Clase para almacenar información de similitud entre productos"""
    producto1: Dict
    producto2: Dict
    similitud_nombre: float
    similitud_marca: float
    misma_categoria: bool
    score_total: float
    razon: str


class AdvancedDeduplicator:
    """
    Deduplicador avanzado que usa múltiples estrategias para detectar duplicados
    """
    
    def __init__(self):
        self.umbral_similitud = 0.85  # Umbral para considerar productos similares
        self.umbral_nombre = 0.80     # Umbral específico para nombres
        self.productos_procesados = []
        self.duplicados_encontrados = []
        self.estadisticas = {
            'productos_originales': 0,
            'productos_unicos': 0,
            'duplicados_eliminados': 0,
            'grupos_duplicados': 0
        }
    
    def normalizar_texto_avanzado(self, texto: str) -> str:
        """
        Normalización avanzada de texto para comparación
        """
        if not texto:
            return ""
        
        # Convertir a minúsculas
        texto = texto.lower()
        
        # Eliminar caracteres especiales pero mantener números y letras
        texto = re.sub(r'[^\w\s]', ' ', texto)
        
        # Normalizar espacios
        texto = ' '.join(texto.split())
        
        # Eliminar palabras comunes que añaden ruido
        palabras_ruido = {
            'ml', 'gr', 'gramos', 'mililitros', 'und', 'unidades', 'pack',
            'x', 'de', 'del', 'la', 'el', 'para', 'con', 'sin', 'y'
        }
        
        palabras = texto.split()
        palabras_filtradas = [p for p in palabras if p not in palabras_ruido]
        
        return ' '.join(palabras_filtradas)
    
    def calcular_similitud_nombre(self, nombre1: str, nombre2: str) -> float:
        """
        Calcula similitud entre nombres usando múltiples métricas
        """
        if not nombre1 or not nombre2:
            return 0.0
        
        # Normalizar nombres
        norm1 = self.normalizar_texto_avanzado(nombre1)
        norm2 = self.normalizar_texto_avanzado(nombre2)
        
        if norm1 == norm2:
            return 1.0
        
        # Usar SequenceMatcher para similitud general
        similitud_secuencia = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        
        # Calcular similitud de palabras clave
        palabras1 = set(norm1.split())
        palabras2 = set(norm2.split())
        
        if not palabras1 or not palabras2:
            return similitud_secuencia
        
        # Jaccard similarity para palabras
        interseccion = len(palabras1.intersection(palabras2))
        union = len(palabras1.union(palabras2))
        similitud_jaccard = interseccion / union if union > 0 else 0
        
        # Combinar métricas (dando más peso a Jaccard para productos)
        similitud_final = (similitud_secuencia * 0.3) + (similitud_jaccard * 0.7)
        
        return min(similitud_final, 1.0)
    
    def normalizar_marca(self, marca: str) -> str:
        """
        Normaliza marca para comparación
        """
        if not marca:
            return "sin_marca"
        
        marca = marca.lower().strip()
        
        # Mapeo de variaciones comunes de marcas
        mapeo_marcas = {
            'loreal': 'l\'oreal',
            'l oreal': 'l\'oreal',
            'maybelline new york': 'maybelline',
            'maybelline ny': 'maybelline',
            'covergirl': 'cover girl',
            'wet n wild': 'wet n\' wild',
            'clinique': 'clinique',
            'estee lauder': 'estée lauder',
        }
        
        return mapeo_marcas.get(marca, marca)
    
    def son_productos_similares(self, producto1: Dict, producto2: Dict) -> ProductoSimilitud:
        """
        Determina si dos productos son similares y calcula métricas de similitud
        """
        # Extraer información de productos
        nombre1 = producto1.get('nombre', '')
        nombre2 = producto2.get('nombre', '')
        marca1 = self.normalizar_marca(producto1.get('marca', ''))
        marca2 = self.normalizar_marca(producto2.get('marca', ''))
        categoria1 = producto1.get('categoria', '').lower()
        categoria2 = producto2.get('categoria', '').lower()
        
        # Calcular similitudes
        similitud_nombre = self.calcular_similitud_nombre(nombre1, nombre2)
        similitud_marca = 1.0 if marca1 == marca2 else 0.0
        misma_categoria = categoria1 == categoria2
        
        # Calcular score total
        score_total = 0.0
        razon = ""
        
        # Productos idénticos en nombre y marca
        if similitud_nombre >= 0.95 and similitud_marca == 1.0 and misma_categoria:
            score_total = 1.0
            razon = "Producto idéntico (nombre, marca y categoría)"
        
        # Productos muy similares en nombre, misma marca
        elif similitud_nombre >= self.umbral_nombre and similitud_marca == 1.0 and misma_categoria:
            score_total = 0.9
            razon = f"Muy similar (nombre: {similitud_nombre:.2f}, misma marca)"
        
        # Productos similares en nombre, sin marca o marca diferente
        elif similitud_nombre >= 0.90 and misma_categoria:
            if marca1 == "sin_marca" or marca2 == "sin_marca":
                score_total = 0.8
                razon = f"Similar sin marca definida (nombre: {similitud_nombre:.2f})"
            else:
                score_total = 0.7
                razon = f"Similar con marcas diferentes (nombre: {similitud_nombre:.2f})"
        
        # Productos con nombres muy similares
        elif similitud_nombre >= self.umbral_similitud:
            score_total = similitud_nombre * 0.8
            razon = f"Similitud de nombre alta ({similitud_nombre:.2f})"
        
        return ProductoSimilitud(
            producto1=producto1,
            producto2=producto2,
            similitud_nombre=similitud_nombre,
            similitud_marca=similitud_marca,
            misma_categoria=misma_categoria,
            score_total=score_total,
            razon=razon
        )
    
    def encontrar_duplicados_en_grupo(self, productos: List[Dict]) -> List[List[int]]:
        """
        Encuentra grupos de productos duplicados dentro de una lista
        """
        n = len(productos)
        visitados = [False] * n
        grupos_duplicados = []
        
        for i in range(n):
            if visitados[i]:
                continue
            
            grupo_actual = [i]
            visitados[i] = True
            
            # Buscar productos similares al actual
            for j in range(i + 1, n):
                if visitados[j]:
                    continue
                
                similitud = self.son_productos_similares(productos[i], productos[j])
                
                if similitud.score_total >= self.umbral_similitud:
                    grupo_actual.append(j)
                    visitados[j] = True
                    
                    # Agregar información de por qué se consideran duplicados
                    self.duplicados_encontrados.append(similitud)
            
            # Solo agregar grupos con más de un producto
            if len(grupo_actual) > 1:
                grupos_duplicados.append(grupo_actual)
        
        return grupos_duplicados
    
    def seleccionar_mejor_producto_del_grupo(self, grupo_indices: List[int], 
                                           productos: List[Dict]) -> int:
        """
        Selecciona el mejor producto de un grupo de duplicados
        """
        if len(grupo_indices) == 1:
            return grupo_indices[0]
        
        mejores_scores = []
        
        for idx in grupo_indices:
            producto = productos[idx]
            score = 0
            
            # Preferir productos con más información
            if producto.get('marca') and producto.get('marca') != 'sin_marca':
                score += 20
            
            if producto.get('descripcion'):
                score += 10
            
            if producto.get('imagen_url') or any(t.get('imagen') for t in producto.get('tiendas', [])):
                score += 10
            
            # Preferir productos con más tiendas
            num_tiendas = len(producto.get('tiendas', []))
            score += num_tiendas * 5
            
            # Preferir productos con precios válidos
            tiendas_con_precio = sum(1 for t in producto.get('tiendas', []) 
                                   if t.get('precio', 0) > 0)
            score += tiendas_con_precio * 3
            
            # Preferir nombres más descriptivos (más largos)
            score += min(len(producto.get('nombre', '')), 50) * 0.1
            
            mejores_scores.append((score, idx))
        
        # Seleccionar el producto con mejor score
        mejores_scores.sort(reverse=True)
        mejor_idx = mejores_scores[0][1]
        
        return mejor_idx
    
    def combinar_productos_duplicados(self, grupo_indices: List[int], 
                                    productos: List[Dict]) -> Dict:
        """
        Combina productos duplicados en uno solo, preservando toda la información
        """
        mejor_idx = self.seleccionar_mejor_producto_del_grupo(grupo_indices, productos)
        producto_base = productos[mejor_idx].copy()
        
        # Combinar tiendas de todos los productos del grupo
        todas_tiendas = []
        tiendas_vistas = set()
        
        for idx in grupo_indices:
            producto = productos[idx]
            for tienda in producto.get('tiendas', []):
                tienda_key = f"{tienda.get('fuente', '')}_{tienda.get('precio', 0)}"
                if tienda_key not in tiendas_vistas:
                    todas_tiendas.append(tienda)
                    tiendas_vistas.add(tienda_key)
        
        # Actualizar producto base con toda la información combinada
        producto_base['tiendas'] = todas_tiendas
        
        # Combinar imágenes (usar la mejor disponible)
        for idx in grupo_indices:
            producto = productos[idx]
            if not producto_base.get('imagen_url') and producto.get('imagen_url'):
                producto_base['imagen_url'] = producto['imagen_url']
        
        # Combinar descripciones
        descripciones = []
        for idx in grupo_indices:
            producto = productos[idx]
            desc = producto.get('descripcion', '').strip()
            if desc and desc not in descripciones:
                descripciones.append(desc)
        
        if descripciones:
            producto_base['descripcion'] = ' | '.join(descripciones)
        
        return producto_base
    
    def deduplicar_productos(self, productos: List[Dict]) -> List[Dict]:
        """
        Función principal de deduplicación
        """
        if not productos:
            return []
        
        self.estadisticas['productos_originales'] = len(productos)
        
        # Agrupar productos por categoría para optimizar comparaciones
        productos_por_categoria = defaultdict(list)
        for i, producto in enumerate(productos):
            categoria = producto.get('categoria', 'sin_categoria').lower()
            productos_por_categoria[categoria].append((i, producto))
        
        productos_finales = []
        indices_procesados = set()
        
        # Procesar cada categoría por separado
        for categoria, productos_categoria in productos_por_categoria.items():
            if len(productos_categoria) <= 1:
                # No hay duplicados posibles en categorías con un solo producto
                for idx, producto in productos_categoria:
                    if idx not in indices_procesados:
                        productos_finales.append(producto)
                        indices_procesados.add(idx)
                continue
            
            # Extraer solo los productos para comparación
            productos_categoria_solo = [p[1] for p in productos_categoria]
            indices_originales = [p[0] for p in productos_categoria]
            
            # Encontrar grupos de duplicados
            grupos_duplicados = self.encontrar_duplicados_en_grupo(productos_categoria_solo)
            
            self.estadisticas['grupos_duplicados'] += len(grupos_duplicados)
            
            # Procesar grupos de duplicados
            indices_en_grupos = set()
            for grupo in grupos_duplicados:
                # Combinar productos del grupo
                producto_combinado = self.combinar_productos_duplicados(
                    grupo, productos_categoria_solo
                )
                productos_finales.append(producto_combinado)
                
                # Marcar índices como procesados
                for idx_grupo in grupo:
                    idx_original = indices_originales[idx_grupo]
                    indices_procesados.add(idx_original)
                    indices_en_grupos.add(idx_grupo)
                
                self.estadisticas['duplicados_eliminados'] += len(grupo) - 1
            
            # Agregar productos que no están en ningún grupo
            for i, (idx_original, producto) in enumerate(productos_categoria):
                if i not in indices_en_grupos and idx_original not in indices_procesados:
                    productos_finales.append(producto)
                    indices_procesados.add(idx_original)
        
        self.estadisticas['productos_unicos'] = len(productos_finales)
        
        return productos_finales
    
    def generar_reporte_deduplicacion(self) -> str:
        """
        Genera un reporte detallado del proceso de deduplicación
        """
        reporte = []
        reporte.append("REPORTE DE DEDUPLICACIÓN")
        reporte.append("=" * 50)
        reporte.append(f"Productos originales: {self.estadisticas['productos_originales']}")
        reporte.append(f"Productos únicos: {self.estadisticas['productos_unicos']}")
        reporte.append(f"Duplicados eliminados: {self.estadisticas['duplicados_eliminados']}")
        reporte.append(f"Grupos de duplicados: {self.estadisticas['grupos_duplicados']}")
        reporte.append("")
        
        if self.duplicados_encontrados:
            reporte.append("DUPLICADOS DETECTADOS:")
            reporte.append("-" * 30)
            
            for i, dup in enumerate(self.duplicados_encontrados[:10]):  # Mostrar solo los primeros 10
                reporte.append(f"{i+1}. {dup.razon}")
                reporte.append(f"   Producto 1: {dup.producto1.get('nombre', '')[:50]}...")
                reporte.append(f"   Producto 2: {dup.producto2.get('nombre', '')[:50]}...")
                reporte.append(f"   Score: {dup.score_total:.2f}")
                reporte.append("")
            
            if len(self.duplicados_encontrados) > 10:
                reporte.append(f"... y {len(self.duplicados_encontrados) - 10} duplicados más")
        
        return "\n".join(reporte)
    
    def obtener_estadisticas(self) -> Dict:
        """
        Retorna estadísticas del proceso de deduplicación
        """
        return self.estadisticas.copy()


def deduplicar_productos_avanzado(productos: List[Dict], 
                                umbral_similitud: float = 0.85) -> Tuple[List[Dict], Dict]:
    """
    Función principal para deduplicar productos usando el sistema avanzado
    
    Args:
        productos: Lista de productos a deduplicar
        umbral_similitud: Umbral de similitud para considerar duplicados
        
    Returns:
        Tuple[List[Dict], Dict]: (productos_unicos, estadisticas)
    """
    deduplicator = AdvancedDeduplicator()
    deduplicator.umbral_similitud = umbral_similitud
    
    productos_unicos = deduplicator.deduplicar_productos(productos)
    estadisticas = deduplicator.obtener_estadisticas()
    
    # Agregar reporte al resultado
    estadisticas['reporte'] = deduplicator.generar_reporte_deduplicacion()
    
    return productos_unicos, estadisticas


if __name__ == "__main__":
    # Ejemplo de uso
    productos_ejemplo = [
        {
            "nombre": "Máscara de Pestañas Maybelline Great Lash Waterproof Negro",
            "marca": "MAYBELLINE",
            "categoria": "maquillaje",
            "tiendas": [{"fuente": "preunic", "precio": 3679.0}]
        },
        {
            "nombre": "Mascara Maybelline Great Lash WaterProof Black",
            "marca": "Maybelline",
            "categoria": "Maquillaje", 
            "tiendas": [{"fuente": "dbs", "precio": 3890.0}]
        },
        {
            "nombre": "Labial Revlon ColorStay",
            "marca": "REVLON",
            "categoria": "maquillaje",
            "tiendas": [{"fuente": "maicao", "precio": 2500.0}]
        }
    ]
    
    productos_unicos, stats = deduplicar_productos_avanzado(productos_ejemplo)
    
    print(f"Productos originales: {len(productos_ejemplo)}")
    print(f"Productos únicos: {len(productos_unicos)}")
    print(f"Duplicados eliminados: {stats['duplicados_eliminados']}")
    print("\nReporte completo:")
    print(stats['reporte'])



