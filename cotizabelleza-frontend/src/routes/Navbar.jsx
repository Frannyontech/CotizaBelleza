import React, { useState } from 'react';
import { Layout, Input, Button, Space, Typography, Badge } from 'antd';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  AppstoreOutlined,
  UserOutlined
} from '@ant-design/icons';
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

  return (
    <Header className="navbar-header">
      <div className="navbar-container">
        {/* Brand Logo */}
        <div className="brand-section">
          <Link to="/" className="brand-link">
            <div className="brand-logo">
              <Title level={3} className="brand-text">
                CotizaBelleza
              </Title>
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
            <Link to="/buscador" className="nav-icon-link">
              <div className="nav-icon-item">
                <AppstoreOutlined className="nav-icon" />
                <span className="nav-label">Categorías</span>
              </div>
            </Link>
            
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