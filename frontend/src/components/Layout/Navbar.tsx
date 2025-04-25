import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { motion } from 'framer-motion';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <motion.nav 
      className="navbar"
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="navbar-logo">
        <Link to="/dashboard">
          <motion.div
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            🏦 FinanceManager
          </motion.div>
        </Link>
      </div>
      <div className="navbar-links">
        <Link to="/dashboard">
          <motion.div whileHover={{ y: -3 }} className="nav-link">Dashboard</motion.div>
        </Link>
        <Link to="/transactions">
          <motion.div whileHover={{ y: -3 }} className="nav-link">Transactions</motion.div>
        </Link>
        <Link to="/investments">
          <motion.div whileHover={{ y: -3 }} className="nav-link">Investments</motion.div>
        </Link>
        <Link to="/budget-advice">
          <motion.div whileHover={{ y: -3 }} className="nav-link">Budget Advice</motion.div>
        </Link>
        <Link to="/fraud-detection">
          <motion.div whileHover={{ y: -3 }} className="nav-link">Fraud Detection</motion.div>
        </Link>
      </div>
      <div className="navbar-user">
        {user ? (
          <div className="user-info">
            <span>Hello, {user.username}</span>
            <motion.button 
              whileHover={{ scale: 1.05 }} 
              whileTap={{ scale: 0.95 }}
              className="logout-button"
              onClick={handleLogout}
            >
              Logout
            </motion.button>
          </div>
        ) : (
          <Link to="/login">
            <motion.button 
              whileHover={{ scale: 1.05 }} 
              whileTap={{ scale: 0.95 }}
            >
              Login
            </motion.button>
          </Link>
        )}
      </div>
    </motion.nav>
  );
};

export default Navbar;
