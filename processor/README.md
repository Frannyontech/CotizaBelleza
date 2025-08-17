# Procesador de Normalización de Productos

Este módulo procesa archivos JSON "raw" de múltiples tiendas y genera un archivo unificado listo para el frontend.

## Uso

### Comando básico
```bash
python -m processor.normalize
```

### Con parámetros personalizados
```bash
python -m processor.normalize --min-strong 95 --min-prob 85 --out processed/unified_products.json
```

## Parámetros

- `--min-strong`: Umbral mínimo para match fuerte (default: 90)
- `--min-prob`: Umbral mínimo para match probable (default: 85)  
- `--out`: Archivo de salida (default: processed/unified_products.json)

## Archivos de entrada

El módulo busca automáticamente estos archivos:
- `scraper/data/dbs_maquillaje.json`
- `scraper/data/dbs_skincare.json`
- `scraper/data/maicao_maquillaje.json`
- `scraper/data/maicao_skincare.json`
- `scraper/data/preunic_maquillaje.json`
- `scraper/data/preunic_skincare.json`

## Esquema de salida

```json
{
  "product_id": "cb_ab12cd34",
  "nombre": "SuperStay Matte Ink 5 ml", 
  "marca": "Maybelline",
  "categoria": "maquillaje",
  "volumen": "5 ml",
  "tipo": "labial",
  "tiendas": [
    {
      "fuente": "dbs",
      "precio": 15990,
      "stock": "In stock", 
      "url": "...",
      "imagen": "...",
      "marca_origen": "MAYBELLINE"
    }
  ]
}
```

## Dependencias

```bash
pip install rapidfuzz scikit-learn unidecode
```

## Pipeline

1. **Carga**: Lee los 6 archivos JSON y agrega fuente
2. **Normalización**: Limpia texto, extrae volumen y tipo
3. **Deduplicación intra-tienda**: Elimina duplicados dentro de cada tienda
4. **Blocking**: Agrupa por categoría, marca y tipo para matching eficiente
5. **Matching**: Usa TF-IDF + coseno y rapidfuzz con reglas de consistencia
6. **Clustering**: Forma grupos de productos similares
7. **Canonicalización**: Genera productos unificados ordenados por precio
8. **Validación**: Verifica estructura y campos requeridos

