import { http, HttpResponse } from 'msw'

// Mock data
const mockProducts = [
  {
    id: 1,
    nombre_original: 'Base de Maquillaje Líquida',
    marca: 'L\'Oréal',
    categoria: 'Maquillaje',
    internal_id: 'test-1',
    precio_minimo: 100.00,
    precio_maximo: 120.00,
    precios: [
      {
        precio: 100.00,
        tienda: 'Tienda A',
        disponible: true,
        url_producto: 'https://test.com/producto1'
      }
    ]
  },
  {
    id: 2,
    nombre_original: 'Corrector de Ojeras',
    marca: 'Maybelline',
    categoria: 'Maquillaje',
    internal_id: 'test-2',
    precio_minimo: 50.00,
    precio_maximo: 60.00,
    precios: [
      {
        precio: 50.00,
        tienda: 'Tienda B',
        disponible: true,
        url_producto: 'https://test.com/producto2'
      }
    ]
  }
]

const mockDashboard = {
  productos_populares: mockProducts.slice(0, 2),
  categorias_disponibles: [
    { id: 1, nombre: 'Maquillaje', cantidad_productos: 10 },
    { id: 2, nombre: 'Skincare', cantidad_productos: 5 }
  ],
  tiendas_disponibles: [
    { id: 1, nombre: 'Tienda A', cantidad_productos: 8 },
    { id: 2, nombre: 'Tienda B', cantidad_productos: 7 }
  ],
  estadisticas: {
    total_productos: 15,
    precio_promedio: 85.50,
    productos_con_descuento: 3
  }
}

// API handlers
export const handlers = [
  // Dashboard API
  http.get('/api/dashboard/', () => {
    return HttpResponse.json(mockDashboard)
  }),

  // Products API
  http.get('/api/productos/', ({ request }) => {
    const url = new URL(request.url)
    const search = url.searchParams.get('buscar')
    const categoria = url.searchParams.get('categoria')
    const tienda = url.searchParams.get('tienda')
    const pagina = parseInt(url.searchParams.get('pagina') || '1')
    const por_pagina = parseInt(url.searchParams.get('por_pagina') || '10')

    let filteredProducts = [...mockProducts]

    // Apply filters
    if (search) {
      filteredProducts = filteredProducts.filter(product =>
        product.nombre_original.toLowerCase().includes(search.toLowerCase()) ||
        product.marca.toLowerCase().includes(search.toLowerCase())
      )
    }

    if (categoria) {
      filteredProducts = filteredProducts.filter(product =>
        product.categoria.toLowerCase() === categoria.toLowerCase()
      )
    }

    if (tienda) {
      filteredProducts = filteredProducts.filter(product =>
        product.precios.some(precio => precio.tienda.toLowerCase() === tienda.toLowerCase())
      )
    }

    // Pagination
    const start = (pagina - 1) * por_pagina
    const end = start + por_pagina
    const paginatedProducts = filteredProducts.slice(start, end)

    return HttpResponse.json({
      productos: paginatedProducts,
      total: filteredProducts.length,
      pagina,
      por_pagina
    })
  }),

  // Product detail API
  http.get('/api/productos/:internal_id/', ({ params }) => {
    const { internal_id } = params
    const product = mockProducts.find(p => p.internal_id === internal_id)

    if (!product) {
      return new HttpResponse(null, { status: 404 })
    }

    return HttpResponse.json({
      producto: product,
      precios: product.precios,
      historial_precios: [
        { fecha: '2024-01-10', precio: 95.00 },
        { fecha: '2024-01-15', precio: 100.00 }
      ]
    })
  }),

  // Search API
  http.get('/api/buscador/', ({ request }) => {
    const url = new URL(request.url)
    const query = url.searchParams.get('q')

    if (!query) {
      return HttpResponse.json({
        resultados: [],
        total: 0
      })
    }

    const results = mockProducts.filter(product =>
      product.nombre_original.toLowerCase().includes(query.toLowerCase()) ||
      product.marca.toLowerCase().includes(query.toLowerCase())
    )

    return HttpResponse.json({
      resultados: results,
      total: results.length
    })
  }),

  // Price alerts API
  http.post('/api/alertas-precio/', async ({ request }) => {
    const data = await request.json()

    // Validate data
    if (!data.email || !data.producto_id || !data.precio_objetivo) {
      return HttpResponse.json(
        { error: 'Datos incompletos' },
        { status: 400 }
      )
    }

    if (data.precio_objetivo <= 0) {
      return HttpResponse.json(
        { error: 'Precio objetivo inválido' },
        { status: 400 }
      )
    }

    // Check if product exists
    const product = mockProducts.find(p => p.internal_id === data.producto_id)
    if (!product) {
      return HttpResponse.json(
        { error: 'Producto no encontrado' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      mensaje: 'Alerta creada exitosamente',
      alerta_id: Math.floor(Math.random() * 1000) + 1
    }, { status: 201 })
  }),

  // Delete price alert API
  http.delete('/api/alertas-precio/:alerta_id/', ({ params }) => {
    const { alerta_id } = params

    if (parseInt(alerta_id) > 1000) {
      return new HttpResponse(null, { status: 404 })
    }

    return new HttpResponse(null, { status: 204 })
  }),

  // Error handlers
  http.get('/api/error-500/', () => {
    return HttpResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    )
  }),

  http.get('/api/error-404/', () => {
    return HttpResponse.json(
      { error: 'Not Found' },
      { status: 404 }
    )
  }),

  http.get('/api/error-403/', () => {
    return HttpResponse.json(
      { error: 'Forbidden' },
      { status: 403 }
    )
  })
]
