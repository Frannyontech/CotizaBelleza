#!/usr/bin/env python3
"""
Script unificado para gestión de productos de CotizaBelleza
Combina funcionalidades de:
- Comparación de productos entre DBS y Preunic
- Análisis detallado de coincidencias
- Eliminación de duplicados
- Normalización de datos

Autor: CotizaBelleza Team
"""

import json
import os
import re
import difflib
from datetime import datetime
from typing import Dict, List, Tuple, Set
from collections import defaultdict


class ProductUnifier:
    """Clase principal para unificar y gestionar productos"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.dbs_file = os.path.join(self.data_dir, 'dbs_productos.json')
        self.preunic_file = os.path.join(self.data_dir, 'preunic_productos.json')
        
        self.dbs_data = None
        self.preunic_data = None
        
    def load_data(self):
        """Cargar datos de ambas tiendas"""
        print("📂 Cargando datos de productos...")
        
        # Cargar DBS
        if os.path.exists(self.dbs_file):
            with open(self.dbs_file, 'r', encoding='utf-8') as f:
                self.dbs_data = json.load(f)
            print(f"✅ DBS: {self.dbs_data.get('total_productos', 0)} productos cargados")
        else:
            print("❌ Archivo DBS no encontrado")
            return False
            
        # Cargar Preunic
        if os.path.exists(self.preunic_file):
            with open(self.preunic_file, 'r', encoding='utf-8') as f:
                self.preunic_data = json.load(f)
            print(f"✅ Preunic: {self.preunic_data.get('total_productos', 0)} productos cargados")
        else:
            print("❌ Archivo Preunic no encontrado")
            return False
            
        return True
    
    def normalize_text(self, text: str) -> str:
        """Normalizar texto para comparaciones"""
        if not text:
            return ""
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover caracteres especiales comunes
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        # Remover palabras comunes que no aportan valor
        stop_words = ['de', 'del', 'la', 'el', 'en', 'con', 'para', 'por', 'ml', 'gr', 'g']
        words = text.split()
        words = [w for w in words if w not in stop_words and len(w) > 2]
        
        return ' '.join(words).strip()
    
    def extract_products_list(self, data: Dict, tienda: str) -> List[Dict]:
        """Extraer lista plana de productos de cualquier estructura"""
        productos = []
        
        for categoria_key, categoria_data in data.items():
            if categoria_key in ['fecha_extraccion', 'total_productos']:
                continue
                
            if isinstance(categoria_data, dict) and 'productos' in categoria_data:
                for producto in categoria_data['productos']:
                    producto_normalizado = {
                        'nombre': producto.get('nombre', ''),
                        'marca': producto.get('marca', ''),
                        'precio': float(producto.get('precio', 0)),
                        'categoria': producto.get('categoria', categoria_key),
                        'stock': producto.get('stock', True),
                        'url': producto.get('url', ''),
                        'imagen': producto.get('imagen', ''),
                        'tienda': tienda,
                        'nombre_normalizado': self.normalize_text(producto.get('nombre', '')),
                        'marca_normalizada': self.normalize_text(producto.get('marca', ''))
                    }
                    productos.append(producto_normalizado)
        
        return productos
    
    def find_similar_products(self, threshold: float = 0.7) -> List[Dict]:
        """Encontrar productos similares entre tiendas"""
        print(f"\n🔍 Buscando productos similares (umbral: {threshold})...")
        
        dbs_productos = self.extract_products_list(self.dbs_data, 'DBS')
        preunic_productos = self.extract_products_list(self.preunic_data, 'PREUNIC')
        
        coincidencias = []
        
        for dbs_prod in dbs_productos:
            for preunic_prod in preunic_productos:
                # Comparar nombres normalizados
                nombre_similarity = difflib.SequenceMatcher(
                    None, 
                    dbs_prod['nombre_normalizado'],
                    preunic_prod['nombre_normalizado']
                ).ratio()
                
                # Comparar marcas
                marca_similarity = 0
                if dbs_prod['marca_normalizada'] and preunic_prod['marca_normalizada']:
                    marca_similarity = difflib.SequenceMatcher(
                        None,
                        dbs_prod['marca_normalizada'],
                        preunic_prod['marca_normalizada']
                    ).ratio()
                
                # Puntuación combinada
                score = (nombre_similarity * 0.7 + marca_similarity * 0.3)
                
                if score >= threshold:
                    diferencia_precio = abs(dbs_prod['precio'] - preunic_prod['precio'])
                    porcentaje_diferencia = 0
                    if dbs_prod['precio'] > 0:
                        porcentaje_diferencia = (diferencia_precio / dbs_prod['precio']) * 100
                    
                    coincidencia = {
                        'score': round(score, 3),
                        'dbs': {
                            'nombre': dbs_prod['nombre'],
                            'marca': dbs_prod['marca'],
                            'precio': dbs_prod['precio'],
                            'categoria': dbs_prod['categoria']
                        },
                        'preunic': {
                            'nombre': preunic_prod['nombre'],
                            'marca': preunic_prod['marca'],
                            'precio': preunic_prod['precio'],
                            'categoria': preunic_prod['categoria']
                        },
                        'diferencia_precio': round(diferencia_precio, 2),
                        'porcentaje_diferencia': round(porcentaje_diferencia, 2),
                        'mejor_precio': 'DBS' if dbs_prod['precio'] < preunic_prod['precio'] else 'PREUNIC'
                    }
                    coincidencias.append(coincidencia)
        
        # Ordenar por score descendente
        coincidencias.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"✅ Encontradas {len(coincidencias)} coincidencias")
        return coincidencias
    
    def analyze_market_data(self) -> Dict:
        """Análisis detallado del mercado"""
        print("\n📊 Analizando datos del mercado...")
        
        dbs_productos = self.extract_products_list(self.dbs_data, 'DBS')
        preunic_productos = self.extract_products_list(self.preunic_data, 'PREUNIC')
        
        # Análisis por categoría
        categorias_dbs = defaultdict(list)
        categorias_preunic = defaultdict(list)
        
        for prod in dbs_productos:
            categorias_dbs[prod['categoria']].append(prod['precio'])
            
        for prod in preunic_productos:
            categorias_preunic[prod['categoria']].append(prod['precio'])
        
        # Análisis por marca
        marcas_dbs = defaultdict(lambda: {'count': 0, 'precios': []})
        marcas_preunic = defaultdict(lambda: {'count': 0, 'precios': []})
        
        for prod in dbs_productos:
            if prod['marca']:
                marcas_dbs[prod['marca']]['count'] += 1
                marcas_dbs[prod['marca']]['precios'].append(prod['precio'])
                
        for prod in preunic_productos:
            if prod['marca']:
                marcas_preunic[prod['marca']]['count'] += 1
                marcas_preunic[prod['marca']]['precios'].append(prod['precio'])
        
        # Marcas comunes
        marcas_comunes = set(marcas_dbs.keys()) & set(marcas_preunic.keys())
        
        analisis = {
            'resumen': {
                'total_productos_dbs': len(dbs_productos),
                'total_productos_preunic': len(preunic_productos),
                'categorias_dbs': list(categorias_dbs.keys()),
                'categorias_preunic': list(categorias_preunic.keys()),
                'marcas_comunes': len(marcas_comunes),
                'marcas_solo_dbs': len(set(marcas_dbs.keys()) - marcas_comunes),
                'marcas_solo_preunic': len(set(marcas_preunic.keys()) - marcas_comunes)
            },
            'precios': {
                'dbs': {
                    'promedio': round(sum(p['precio'] for p in dbs_productos) / len(dbs_productos), 2),
                    'minimo': min(p['precio'] for p in dbs_productos),
                    'maximo': max(p['precio'] for p in dbs_productos)
                },
                'preunic': {
                    'promedio': round(sum(p['precio'] for p in preunic_productos) / len(preunic_productos), 2),
                    'minimo': min(p['precio'] for p in preunic_productos),
                    'maximo': max(p['precio'] for p in preunic_productos)
                }
            },
            'marcas_comunes': sorted(list(marcas_comunes)),
            'top_marcas_dbs': sorted(marcas_dbs.items(), key=lambda x: x[1]['count'], reverse=True)[:10],
            'top_marcas_preunic': sorted(marcas_preunic.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
        }
        
        return analisis
    
    def remove_duplicates_from_file(self, file_path: str, tienda: str) -> int:
        """Eliminar duplicados de un archivo específico"""
        print(f"\n🧹 Eliminando duplicados de {tienda}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_total = 0
        cleaned_total = 0
        
        for categoria_key, categoria_data in data.items():
            if categoria_key in ['fecha_extraccion', 'total_productos']:
                continue
                
            if isinstance(categoria_data, dict) and 'productos' in categoria_data:
                productos_originales = categoria_data['productos']
                original_count = len(productos_originales)
                original_total += original_count
                
                # Eliminar duplicados
                productos_unicos = []
                seen = set()
                
                for producto in productos_originales:
                    key = (
                        producto.get('nombre', '').strip().lower(),
                        producto.get('marca', '').strip().lower(),
                        producto.get('precio', 0)
                    )
                    
                    if key not in seen:
                        seen.add(key)
                        productos_unicos.append(producto)
                
                cleaned_count = len(productos_unicos)
                cleaned_total += cleaned_count
                
                # Actualizar datos
                categoria_data['productos'] = productos_unicos
                categoria_data['cantidad'] = cleaned_count
                
                duplicados_eliminados = original_count - cleaned_count
                if duplicados_eliminados > 0:
                    print(f"   📂 {categoria_key}: {duplicados_eliminados} duplicados eliminados")
        
        # Actualizar total general
        data['total_productos'] = cleaned_total
        data['fecha_extraccion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Guardar archivo limpio
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        total_duplicados = original_total - cleaned_total
        print(f"✅ {tienda}: {total_duplicados} duplicados eliminados")
        print(f"   📊 Original: {original_total} → Limpio: {cleaned_total}")
        
        return total_duplicados
    
    def generate_report(self, coincidencias: List[Dict], analisis: Dict, output_file: str = None):
        """Generar reporte completo"""
        if not output_file:
            output_file = os.path.join(self.base_dir, f'reporte_productos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        reporte = {
            'fecha_generacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'resumen_ejecutivo': {
                'total_coincidencias': len(coincidencias),
                'productos_dbs': analisis['resumen']['total_productos_dbs'],
                'productos_preunic': analisis['resumen']['total_productos_preunic'],
                'marcas_comunes': analisis['resumen']['marcas_comunes'],
                'precio_promedio_dbs': analisis['precios']['dbs']['promedio'],
                'precio_promedio_preunic': analisis['precios']['preunic']['promedio']
            },
            'coincidencias_productos': coincidencias[:20],  # Top 20
            'analisis_mercado': analisis,
            'recomendaciones': self._generate_recommendations(coincidencias, analisis)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Reporte generado: {output_file}")
        return output_file
    
    def _generate_recommendations(self, coincidencias: List[Dict], analisis: Dict) -> List[str]:
        """Generar recomendaciones basadas en el análisis"""
        recomendaciones = []
        
        if len(coincidencias) > 0:
            # Análisis de precios
            mejor_precio_dbs = sum(1 for c in coincidencias if c['mejor_precio'] == 'DBS')
            mejor_precio_preunic = len(coincidencias) - mejor_precio_dbs
            
            if mejor_precio_dbs > mejor_precio_preunic:
                recomendaciones.append("DBS tiende a tener mejores precios en productos similares")
            else:
                recomendaciones.append("Preunic tiende a tener mejores precios en productos similares")
            
            # Diferencias de precio significativas
            grandes_diferencias = [c for c in coincidencias if c['porcentaje_diferencia'] > 50]
            if grandes_diferencias:
                recomendaciones.append(f"Se encontraron {len(grandes_diferencias)} productos con diferencias de precio >50%")
        
        # Análisis de catálogo
        if analisis['resumen']['total_productos_dbs'] > analisis['resumen']['total_productos_preunic']:
            recomendaciones.append("DBS tiene un catálogo más amplio")
        else:
            recomendaciones.append("Preunic tiene un catálogo más amplio")
        
        # Marcas exclusivas
        if analisis['resumen']['marcas_solo_dbs'] > 0:
            recomendaciones.append(f"DBS tiene {analisis['resumen']['marcas_solo_dbs']} marcas exclusivas")
        
        if analisis['resumen']['marcas_solo_preunic'] > 0:
            recomendaciones.append(f"Preunic tiene {analisis['resumen']['marcas_solo_preunic']} marcas exclusivas")
        
        return recomendaciones
    
    def print_summary(self, coincidencias: List[Dict], analisis: Dict):
        """Imprimir resumen en consola"""
        print("\n" + "="*60)
        print("📊 RESUMEN EJECUTIVO - ANÁLISIS DE PRODUCTOS")
        print("="*60)
        
        print(f"\n🏪 TIENDAS:")
        print(f"   • DBS: {analisis['resumen']['total_productos_dbs']} productos")
        print(f"   • Preunic: {analisis['resumen']['total_productos_preunic']} productos")
        
        print(f"\n🔍 COINCIDENCIAS:")
        print(f"   • Total encontradas: {len(coincidencias)}")
        if coincidencias:
            print(f"   • Mejor coincidencia: {coincidencias[0]['score']:.1%}")
            mejor_dbs = sum(1 for c in coincidencias if c['mejor_precio'] == 'DBS')
            print(f"   • DBS mejor precio: {mejor_dbs}/{len(coincidencias)}")
            print(f"   • Preunic mejor precio: {len(coincidencias) - mejor_dbs}/{len(coincidencias)}")
        
        print(f"\n💰 PRECIOS PROMEDIO:")
        print(f"   • DBS: ${analisis['precios']['dbs']['promedio']:,.0f}")
        print(f"   • Preunic: ${analisis['precios']['preunic']['promedio']:,.0f}")
        
        print(f"\n🏷️ MARCAS:")
        print(f"   • Marcas comunes: {analisis['resumen']['marcas_comunes']}")
        print(f"   • Solo en DBS: {analisis['resumen']['marcas_solo_dbs']}")
        print(f"   • Solo en Preunic: {analisis['resumen']['marcas_solo_preunic']}")
        
        if coincidencias:
            print(f"\n🏆 TOP 5 COINCIDENCIAS:")
            for i, c in enumerate(coincidencias[:5], 1):
                print(f"   {i}. {c['dbs']['nombre'][:50]}...")
                print(f"      Similitud: {c['score']:.1%} | Diferencia: ${c['diferencia_precio']:,.0f}")
    
    def run_full_analysis(self, remove_duplicates: bool = True):
        """Ejecutar análisis completo"""
        print("🚀 Iniciando análisis unificado de productos...")
        print("="*60)
        
        # Cargar datos
        if not self.load_data():
            print("❌ Error al cargar datos")
            return
        
        # Eliminar duplicados si se solicita
        if remove_duplicates:
            print("\n🧹 FASE 1: Eliminación de duplicados")
            self.remove_duplicates_from_file(self.dbs_file, 'DBS')
            self.remove_duplicates_from_file(self.preunic_file, 'PREUNIC')
            # Recargar datos después de limpiar
            self.load_data()
        
        # Análisis de mercado
        print("\n📊 FASE 2: Análisis de mercado")
        analisis = self.analyze_market_data()
        
        # Búsqueda de coincidencias
        print("\n🔍 FASE 3: Búsqueda de coincidencias")
        coincidencias = self.find_similar_products(threshold=0.6)
        
        # Generar reporte
        print("\n📄 FASE 4: Generación de reporte")
        archivo_reporte = self.generate_report(coincidencias, analisis)
        
        # Mostrar resumen
        self.print_summary(coincidencias, analisis)
        
        print(f"\n✅ Análisis completado exitosamente!")
        print(f"📁 Reporte guardado en: {archivo_reporte}")


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unificador de productos CotizaBelleza')
    parser.add_argument('--no-clean', action='store_true', 
                       help='No eliminar duplicados antes del análisis')
    parser.add_argument('--threshold', type=float, default=0.6,
                       help='Umbral de similitud para coincidencias (0.0-1.0)')
    
    args = parser.parse_args()
    
    unifier = ProductUnifier()
    unifier.run_full_analysis(remove_duplicates=not args.no_clean)


if __name__ == "__main__":
    main()
