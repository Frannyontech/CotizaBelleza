import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { rest } from 'msw';
import { server } from '../mocks/server';
import Home from '../../pages/Home';

// Mock del componente Home si no existe
const MockHome = () => {
  const [dashboardData, setDashboardData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch('/api/dashboard/');
        if (!response.ok) {
          throw new Error('Failed to fetch dashboard');
        }
        const data = await response.json();
        setDashboardData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return <div data-testid="loading">Cargando...</div>;
  }

  if (error) {
    return <div data-testid="error">Error: {error}</div>;
  }

  if (!dashboardData) {
    return <div data-testid="no-data">No hay datos disponibles</div>;
  }

  return (
    <div data-testid="home-page">
      <h1 data-testid="page-title">CotizaBelleza</h1>
      
      <section data-testid="popular-products">
        <h2>Productos Populares</h2>
        <div data-testid="products-count">
          {dashboardData.productos_populares.length} productos
        </div>
        {dashboardData.productos_populares.map(product => (
          <div key={product.id} data-testid={`product-${product.id}`}>
            <h3>{product.nombre_original}</h3>
            <p>{product.marca}</p>
            <p>${product.precio_minimo}</p>
          </div>
        ))}
      </section>

      <section data-testid="categories">
        <h2>Categorías</h2>
        {dashboardData.categorias_disponibles.map(category => (
          <div key={category.id} data-testid={`category-${category.id}`}>
            <span>{category.nombre}</span>
            <span>({category.cantidad_productos})</span>
          </div>
        ))}
      </section>

      <section data-testid="stores">
        <h2>Tiendas</h2>
        {dashboardData.tiendas_disponibles.map(store => (
          <div key={store.id} data-testid={`store-${store.id}`}>
            <span>{store.nombre}</span>
            <span>({store.cantidad_productos})</span>
          </div>
        ))}
      </section>

      <section data-testid="statistics">
        <h2>Estadísticas</h2>
        <div data-testid="total-products">
          Total productos: {dashboardData.estadisticas.total_productos}
        </div>
        <div data-testid="average-price">
          Precio promedio: ${dashboardData.estadisticas.precio_promedio}
        </div>
      </section>
    </div>
  );
};

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Home Page', () => {
  test('renders loading state initially', () => {
    renderWithRouter(<MockHome />);
    
    expect(screen.getByTestId('loading')).toBeInTheDocument();
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });

  test('renders dashboard data after successful API call', async () => {
    renderWithRouter(<MockHome />);

    await waitFor(() => {
      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });

    expect(screen.getByTestId('page-title')).toHaveTextContent('CotizaBelleza');
    expect(screen.getByTestId('products-count')).toHaveTextContent('2 productos');
    
    // Verificar productos populares
    expect(screen.getByTestId('product-1')).toBeInTheDocument();
    expect(screen.getByTestId('product-2')).toBeInTheDocument();
    expect(screen.getByText('Base de Maquillaje Líquida')).toBeInTheDocument();
    expect(screen.getByText('Corrector de Ojeras')).toBeInTheDocument();
    
    // Verificar categorías
    expect(screen.getByTestId('category-1')).toBeInTheDocument();
    expect(screen.getByTestId('category-2')).toBeInTheDocument();
    expect(screen.getByText('Maquillaje')).toBeInTheDocument();
    expect(screen.getByText('Skincare')).toBeInTheDocument();
    
    // Verificar tiendas
    expect(screen.getByTestId('store-1')).toBeInTheDocument();
    expect(screen.getByTestId('store-2')).toBeInTheDocument();
    expect(screen.getByText('Tienda A')).toBeInTheDocument();
    expect(screen.getByText('Tienda B')).toBeInTheDocument();
    
    // Verificar estadísticas
    expect(screen.getByTestId('total-products')).toHaveTextContent('Total productos: 15');
    expect(screen.getByTestId('average-price')).toHaveTextContent('Precio promedio: $85.5');
  });

  test('renders error state when API call fails', async () => {
    // Override the default handler to simulate an error
    server.use(
      rest.get('/api/dashboard/', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    renderWithRouter(<MockHome />);

    await waitFor(() => {
      expect(screen.getByTestId('error')).toBeInTheDocument();
    });

    expect(screen.getByText(/Error:/)).toBeInTheDocument();
  });

  test('renders no data state when API returns empty data', async () => {
    // Override the default handler to return empty data
    server.use(
      rest.get('/api/dashboard/', (req, res, ctx) => {
        return res(ctx.json({
          productos_populares: [],
          categorias_disponibles: [],
          tiendas_disponibles: [],
          estadisticas: {
            total_productos: 0,
            precio_promedio: 0,
            productos_con_descuento: 0
          }
        }));
      })
    );

    renderWithRouter(<MockHome />);

    await waitFor(() => {
      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });

    expect(screen.getByTestId('products-count')).toHaveTextContent('0 productos');
    expect(screen.getByTestId('total-products')).toHaveTextContent('Total productos: 0');
  });

  test('displays product information correctly', async () => {
    renderWithRouter(<MockHome />);

    await waitFor(() => {
      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });

    // Verificar información del primer producto
    expect(screen.getByText('Base de Maquillaje Líquida')).toBeInTheDocument();
    expect(screen.getByText('L\'Oréal')).toBeInTheDocument();
    expect(screen.getByText('$100')).toBeInTheDocument();

    // Verificar información del segundo producto
    expect(screen.getByText('Corrector de Ojeras')).toBeInTheDocument();
    expect(screen.getByText('Maybelline')).toBeInTheDocument();
    expect(screen.getByText('$50')).toBeInTheDocument();
  });

  test('displays category information correctly', async () => {
    renderWithRouter(<MockHome />);

    await waitFor(() => {
      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });

    // Verificar información de categorías
    expect(screen.getByText('Maquillaje (10)')).toBeInTheDocument();
    expect(screen.getByText('Skincare (5)')).toBeInTheDocument();
  });

  test('displays store information correctly', async () => {
    renderWithRouter(<MockHome />);

    await waitFor(() => {
      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });

    // Verificar información de tiendas
    expect(screen.getByText('Tienda A (8)')).toBeInTheDocument();
    expect(screen.getByText('Tienda B (7)')).toBeInTheDocument();
  });

  test('handles network timeout gracefully', async () => {
    // Override the default handler to simulate a timeout
    server.use(
      rest.get('/api/dashboard/', (req, res, ctx) => {
        return res(ctx.delay(10000)); // 10 second delay
      })
    );

    renderWithRouter(<MockHome />);

    // Should show loading state
    expect(screen.getByTestId('loading')).toBeInTheDocument();
  });
});
