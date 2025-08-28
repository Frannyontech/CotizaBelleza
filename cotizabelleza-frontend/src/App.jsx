import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout, App as AntApp } from 'antd';
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

import PreunicProductos from './components/PreunicProductos';
import MaicaoProductos from './components/MaicaoProductos';
import CategoriasProductos from './components/CategoriasProductos';

const { Content } = Layout;

function App() {
  return (
    <AntApp>
      <Router>
        <Routes>
        <Route path="/" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <Dashboard />
            </Content>
          </Layout>
        } />
        <Route path="/buscador" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <Buscador />
            </Content>
          </Layout>
        } />
        <Route path="/productos-dbs" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <DBSProductos />
            </Content>
          </Layout>
        } />
        <Route path="/productos-preunic" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <PreunicProductos />
            </Content>
          </Layout>
        } />
        <Route path="/productos-maicao" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <MaicaoProductos />
            </Content>
          </Layout>
        } />
        <Route path="/categorias/:categoria" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <CategoriasProductos />
            </Content>
          </Layout>
        } />
        {/* Rutas de detalle CON Layout restaurado */}
        <Route path="/detalle-producto/:id" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <DetalleProducto />
            </Content>
          </Layout>
        } />
        <Route path="/producto/:id" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <DetalleProducto />
            </Content>
          </Layout>
        } />
        <Route path="/login" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <Login />
            </Content>
          </Layout>
        } />
        <Route path="/perfil" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <Perfil />
            </Content>
          </Layout>
        } />
        <Route path="/search" element={
          <Layout style={{ minHeight: '100vh' }}>
            <Navbar />
            <Content style={{ padding: '0', background: '#f5f5f5' }}>
              <Buscador />
            </Content>
          </Layout>
        } />
        </Routes>
      </Router>
    </AntApp>
  );
}

export default App;
