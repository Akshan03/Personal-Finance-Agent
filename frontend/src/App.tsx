import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Import enhanced styling
import './styles/AppTheme.css';
import './styles/LoadingStyles.css';
import './styles/QualityAssessment.css';
import './styles/Animations.css';
import './styles/TransactionsTable.css';

// Context providers
import { AuthProvider } from './context/AuthContext';

// Components
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Investments from './pages/Investments';
import FraudDetection from './pages/FraudDetection';
import BudgetAdvice from './pages/BudgetAdvice';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/investments" element={<Investments />} />
              <Route path="/budget-advice" element={<BudgetAdvice />} />
              <Route path="/fraud-detection" element={<FraudDetection />} />
            </Route>
          </Route>
          
          {/* Redirect to dashboard if authenticated, otherwise to login */}
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
