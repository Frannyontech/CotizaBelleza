import React from 'react';
import ProductList from '../components/ProductList';

const Home = () => {
  return (
    <div className="home">
      <header className="home-header">
        <h1>CotizaBelleza</h1>
        <p>Tu plataforma para cotizar productos de belleza</p>
      </header>
      
      <main className="home-main">
        <ProductList />
      </main>
    </div>
  );
};

export default Home; 