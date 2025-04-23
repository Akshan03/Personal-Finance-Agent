import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import { motion } from 'framer-motion';

const Layout: React.FC = () => {
  return (
    <div className="app-container">
      <Navbar />
      <motion.main 
        className="main-content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <Outlet />
      </motion.main>
      <footer className="footer">
        <p>&copy; {new Date().getFullYear()} FinanceManager - Personal Finance Management</p>
      </footer>
    </div>
  );
};

export default Layout;
