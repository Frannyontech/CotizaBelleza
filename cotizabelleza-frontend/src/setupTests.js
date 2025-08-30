import '@testing-library/jest-dom';
import { beforeAll, afterEach, afterAll } from 'vitest';
import { server } from './__tests__/mocks/server';

// Mock para fetch global si es necesario
global.fetch = jest.fn();

// Mock para console.error para evitar warnings en tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is deprecated')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
  
  // Start MSW server
  server.listen();
});

afterEach(() => {
  // Reset MSW handlers between tests
  server.resetHandlers();
});

afterAll(() => {
  console.error = originalError;
  
  // Stop MSW server
  server.close();
});
