import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import './App.css';

// Import Navbar
import Navbar from './routes/Navbar';

// Import pages
import Dashboard from './pages/dashboard/Dashboard';
import Buscador from './pages/buscador/Buscador';
import DetalleProducto from './pages/detalle-producto/DetalleProducto';
import Login from './pages/login/Login';
import Perfil from './pages/perfil/Perfil';
import DBSProductos from './components/DBSProductos';

const { Content } = Layout;

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Navbar />
        <Content style={{ padding: '0', background: '#f5f5f5' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/buscador" element={<Buscador />} />
            <Route path="/productos-dbs" element={<DBSProductos />} />
            <Route path="/detalle-producto" element={<DetalleProducto />} />
            <Route path="/login" element={<Login />} />
            <Route path="/perfil" element={<Perfil />} />
          </Routes>
        </Content>
      </Layout>
    </Router>
  );
}

export default App;
