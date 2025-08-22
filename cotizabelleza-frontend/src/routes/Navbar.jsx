import React, { useState } from 'react';
import { Layout, Input, Button, Space, Typography, Badge, Dropdown, Menu } from 'antd';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  AppstoreOutlined,
  UserOutlined,
  ShopOutlined
} from '@ant-design/icons';
import logoFull from '../assets/logo_cotizabelleza.png';
import logoThumbnail from '../assets/logo_cotizabelleza_thumbnail.png';
import './Navbar.css';

const { Header } = Layout;
const { Title } = Typography;
const { Search } = Input;

const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearch = (value) => {
    console.log('Search triggered with value:', value);
    if (value && value.trim()) {
      const searchUrl = `/search?search=${encodeURIComponent(value.trim())}`;
      console.log('Navigating to:', searchUrl);
      navigate(searchUrl);
    }
  };

  // Menú de tiendas
  const storeMenu = (
    <Menu>
      <Menu.Item key="dbs">
        <Link to="/productos-dbs">DBS</Link>
      </Menu.Item>
      <Menu.Item key="preunic">
        <Link to="/productos-preunic">Preunic</Link>
      </Menu.Item>
      <Menu.Item key="maicao">
        <Link to="/productos-maicao">Maicao</Link>
      </Menu.Item>
    </Menu>
  );

  // Menú de categorías
  const categoriesMenu = (
    <Menu>
      <Menu.Item key="maquillaje">
        <Link to="/categorias/maquillaje">Maquillaje</Link>
      </Menu.Item>
      <Menu.Item key="skincare">
        <Link to="/categorias/skincare">Skincare</Link>
      </Menu.Item>
    </Menu>
  );

  return (
    <Header className="navbar-header">
      <div className="navbar-container">
        {/* Brand Logo */}
        <div className="brand-section">
          <Link to="/" className="brand-link">
            <div className="brand-logo">
              {/* Logo completo para pantallas medianas y grandes */}
              <img 
                src={logoFull} 
                alt="CotizaBelleza" 
                className="brand-logo-full"
              />
              {/* Logo thumbnail para dispositivos móviles */}
              <img 
                src={logoThumbnail} 
                alt="CotizaBelleza" 
                className="brand-logo-thumbnail"
              />
            </div>
          </Link>
        </div>

        {/* Search Bar */}
        <div className="search-section">
          <Search
            placeholder="Buscar productos de belleza..."
            allowClear
            size="large"
            className="search-input"
            value={searchTerm}
            onChange={(e) => {
              console.log('Search input changed:', e.target.value);
              setSearchTerm(e.target.value);
            }}
            onSearch={handleSearch}
          />
        </div>

        {/* Navigation Icons */}
        <div className="nav-icons">
          <Space size="large">
            <Dropdown overlay={categoriesMenu} placement="bottomRight">
              <div className="nav-icon-item nav-icon-link">
                <AppstoreOutlined className="nav-icon" />
                <span className="nav-label">Categorías</span>
              </div>
            </Dropdown>
            
            <Dropdown overlay={storeMenu} placement="bottomRight">
              <div className="nav-icon-item nav-icon-link">
                <ShopOutlined className="nav-icon" />
                <span className="nav-label">Tiendas</span>
              </div>
            </Dropdown>
            
            <Link to="/perfil" className="nav-icon-link">
              <div className="nav-icon-item">
                <UserOutlined className="nav-icon" />
                <span className="nav-label">Perfil</span>
              </div>
            </Link>
          </Space>
        </div>
      </div>
    </Header>
  );
};

export default Navbar; 