import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Error en la petición API:', error);
    return Promise.reject(error);
  }
);

export default api; 