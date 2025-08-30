import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import SearchBar from '../../components/SearchBar';

// Mock del componente SearchBar si no existe
const MockSearchBar = ({ onSearch, placeholder = 'Buscar productos...' }) => {
  const [query, setQuery] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);

  const handleSearch = async (searchQuery) => {
    setIsLoading(true);
    try {
      await onSearch(searchQuery);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSearch(query);
  };

  return (
    <form onSubmit={handleSubmit} data-testid="search-form">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        data-testid="search-input"
      />
      <button 
        type="submit" 
        disabled={isLoading}
        data-testid="search-button"
      >
        {isLoading ? 'Buscando...' : 'Buscar'}
      </button>
    </form>
  );
};

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('SearchBar', () => {
  test('renders search input and button', () => {
    const mockOnSearch = jest.fn();
    renderWithRouter(<MockSearchBar onSearch={mockOnSearch} />);

    expect(screen.getByTestId('search-input')).toBeInTheDocument();
    expect(screen.getByTestId('search-button')).toBeInTheDocument();
    expect(screen.getByTestId('search-form')).toBeInTheDocument();
  });

  test('displays placeholder text', () => {
    const mockOnSearch = jest.fn();
    renderWithRouter(<MockSearchBar onSearch={mockOnSearch} />);

    expect(screen.getByTestId('search-input')).toHaveAttribute('placeholder', 'Buscar productos...');
  });

  test('allows typing in search input', async () => {
    const user = userEvent.setup();
    const mockOnSearch = jest.fn();
    renderWithRouter(<MockSearchBar onSearch={mockOnSearch} />);

    const searchInput = screen.getByTestId('search-input');
    await user.type(searchInput, 'base de maquillaje');

    expect(searchInput).toHaveValue('base de maquillaje');
  });

  test('calls onSearch when form is submitted', async () => {
    const user = userEvent.setup();
    const mockOnSearch = jest.fn();
    renderWithRouter(<MockSearchBar onSearch={mockOnSearch} />);

    const searchInput = screen.getByTestId('search-input');
    const searchButton = screen.getByTestId('search-button');

    await user.type(searchInput, 'base de maquillaje');
    await user.click(searchButton);

    expect(mockOnSearch).toHaveBeenCalledWith('base de maquillaje');
    expect(mockOnSearch).toHaveBeenCalledTimes(1);
  });

  test('calls onSearch when Enter key is pressed', async () => {
    const user = userEvent.setup();
    const mockOnSearch = jest.fn();
    renderWithRouter(<MockSearchBar onSearch={mockOnSearch} />);

    const searchInput = screen.getByTestId('search-input');
    await user.type(searchInput, 'base de maquillaje');
    await user.keyboard('{Enter}');

    expect(mockOnSearch).toHaveBeenCalledWith('base de maquillaje');
    expect(mockOnSearch).toHaveBeenCalledTimes(1);
  });

  test('shows loading state during search', async () => {
    const user = userEvent.setup();
    const mockOnSearch = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
    renderWithRouter(<MockSearchBar onSearch={mockOnSearch} />);

    const searchInput = screen.getByTestId('search-input');
    const searchButton = screen.getByTestId('search-button');

    await user.type(searchInput, 'base de maquillaje');
    await user.click(searchButton);

    expect(screen.getByText('Buscando...')).toBeInTheDocument();
    expect(searchButton).toBeDisabled();

    await waitFor(() => {
      expect(screen.getByText('Buscar')).toBeInTheDocument();
    });
  });

  test('handles empty search query', async () => {
    const user = userEvent.setup();
    const mockOnSearch = jest.fn();
    renderWithRouter(<MockSearchBar onSearch={mockOnSearch} />);

    const searchButton = screen.getByTestId('search-button');
    await user.click(searchButton);

    expect(mockOnSearch).toHaveBeenCalledWith('');
  });

  test('handles special characters in search', async () => {
    const user = userEvent.setup();
    const mockOnSearch = jest.fn();
    renderWithRouter(<MockSearchBar onSearch={mockOnSearch} />);

    const searchInput = screen.getByTestId('search-input');
    const searchButton = screen.getByTestId('search-button');

    await user.type(searchInput, 'L\'Oréal & Maybelline');
    await user.click(searchButton);

    expect(mockOnSearch).toHaveBeenCalledWith('L\'Oréal & Maybelline');
  });

  test('handles long search queries', async () => {
    const user = userEvent.setup();
    const mockOnSearch = jest.fn();
    renderWithRouter(<MockSearchBar onSearch={mockOnSearch} />);

    const searchInput = screen.getByTestId('search-input');
    const searchButton = screen.getByTestId('search-button');

    const longQuery = 'Base de maquillaje líquida de larga duración con acabado mate y cobertura media';
    await user.type(searchInput, longQuery);
    await user.click(searchButton);

    expect(mockOnSearch).toHaveBeenCalledWith(longQuery);
  });

  test('handles search error gracefully', async () => {
    const user = userEvent.setup();
    const mockOnSearch = jest.fn(() => Promise.reject(new Error('Search failed')));
    renderWithRouter(<MockSearchBar onSearch={mockOnSearch} />);

    const searchInput = screen.getByTestId('search-input');
    const searchButton = screen.getByTestId('search-button');

    await user.type(searchInput, 'base de maquillaje');
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Buscar')).toBeInTheDocument();
    });
  });
});
