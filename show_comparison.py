#!/usr/bin/env python3
import json

with open('data/processed/unified_products.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

multi_store = [p for p in data if len(p['tiendas']) > 1]

print("[OBJETIVO] RESULTADOS DEL ETL - COMPARACIÓN DE PRECIOS")
print("="*60)
print(f"[STATS] Total productos unificados: {len(data)}")
print(f"[EMOJI] Productos con múltiples tiendas: {len(multi_store)}")
print(f"[EMOJI] Productos únicos por tienda: {len(data) - len(multi_store)}")

if multi_store:
    print("\n[VALIDANDO] EJEMPLO DE COMPARACIÓN DE PRECIOS:")
    print("-"*60)
    
    product = multi_store[0]
    print(f"Producto: {product['nombre']}")
    print(f"Marca: {product['marca']}")
    print(f"Categoría: {product['categoria']}")
    print()
    print("PRECIOS POR TIENDA:")
    
    for i, tienda in enumerate(product['tiendas'], 1):
        precio = int(tienda['precio'])
        print(f"  {i}. {tienda['fuente'].upper():8} - ${precio:,} - {tienda['stock']}")
    
    precios = [t['precio'] for t in product['tiendas']]
    min_precio = min(precios)
    max_precio = max(precios)
    ahorro = max_precio - min_precio
    
    print()
    print(f"[EMOJI] Precio más bajo: ${int(min_precio):,}")
    print(f"[EMOJI] Precio más alto: ${int(max_precio):,}")
    if ahorro > 0:
        print(f"[EXITO] Ahorro potencial: ${int(ahorro):,} ({int(ahorro/max_precio*100)}%)")

print("\n[DATOS] ESTADÍSTICAS POR CATEGORÍA:")
categorias = {}
for product in data:
    cat = product['categoria']
    categorias[cat] = categorias.get(cat, 0) + 1

for cat, count in categorias.items():
    print(f"  {cat.title()}: {count} productos")

print("\n[EMOJI] ESTADÍSTICAS POR TIENDA:")
tiendas = {}
for product in data:
    for tienda in product['tiendas']:
        fuente = tienda['fuente']
        tiendas[fuente] = tiendas.get(fuente, 0) + 1

for tienda, count in tiendas.items():
    print(f"  {tienda.upper()}: {count} productos")

print("\n[OK] ETL COMPLETADO EXITOSAMENTE!")
print("[ARCHIVO] Archivo listo para el frontend: data/processed/unified_products.json")
