import React from 'react';
import { Layout, Input, Button, Space, Typography, Badge } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import {
  SearchOutlined,
  AppstoreOutlined,
  HeartOutlined,
  BellOutlined,
  UserOutlined
} from '@ant-design/icons';
import './Navbar.css';

const { Header } = Layout;
const { Title } = Typography;
const { Search } = Input;

const Navbar = () => {
  const location = useLocation();

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
            suffix={<SearchOutlined style={{ color: '#ff69b4' }} />}
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
            
            <Link to="/favoritos" className="nav-icon-link">
              <div className="nav-icon-item">
                <HeartOutlined className="nav-icon" />
                <span className="nav-label">Favoritos</span>
              </div>
            </Link>
            
            <Link to="/alertas" className="nav-icon-link">
              <div className="nav-icon-item">
                <Badge count={3} size="small">
                  <BellOutlined className="nav-icon" />
                </Badge>
                <span className="nav-label">Alertas</span>
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