# CotizaBelleza Frontend

Frontend de React para la aplicación CotizaBelleza que consume la API de Django.

## Características

- **React 19** con Vite como bundler
- **Axios** para consumo de APIs
- **CSS moderno** con efectos visuales atractivos
- **Responsive design** para móviles y desktop
- **Integración completa** con el backend Django

## Componentes Creados

### ProductList.jsx
- Hace GET a `productos/` usando axios
- Muestra lista de productos en pantalla
- Maneja estados de loading y error
- Diseño en grid responsive

### Home.jsx
- Página principal que importa ProductList
- Header con título y descripción
- Layout estructurado

### App.jsx
- Renderiza Home como componente principal
- Configuración básica de la aplicación

## Instalación y Ejecución

1. **Instalar dependencias:**
   ```bash
   npm install
   ```

2. **Ejecutar en modo desarrollo:**
   ```bash
   npm run dev
   ```

3. **Abrir en el navegador:**
   - El servidor se ejecutará en `http://localhost:5173`
   - Asegúrate de que el backend Django esté corriendo en `http://localhost:8000`

## Configuración de la API

El archivo `src/services/api.js` está configurado para conectarse a:
- **Base URL:** `http://localhost:8000/api/`
- **Timeout:** 10 segundos
- **Headers:** JSON

## Endpoints Utilizados

- `GET /api/productos/` - Lista todos los productos
- `GET /api/productos/?categoria=<id>` - Filtra por categoría

## Estructura del Proyecto

```
src/
├── components/
│   └── ProductList.jsx    # Componente para mostrar productos
├── pages/
│   └── Home.jsx           # Página principal
├── services/
│   └── api.js             # Configuración de axios
├── App.jsx                # Componente raíz
└── App.css                # Estilos CSS
```

## Validación de Integración

Para validar que la integración React + Django funciona:

1. Asegúrate de que el backend Django esté ejecutándose
2. Ejecuta el frontend con `npm run dev`
3. Abre `http://localhost:5173` en el navegador
4. Deberías ver la lista de productos cargada desde la API

Si hay errores de conexión, verifica:
- Que Django esté corriendo en puerto 8000
- Que CORS esté configurado correctamente en Django
- Que la API `/api/productos/` esté funcionando
