import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { transactionService } from '../api/transactionService';
import { fraudService } from '../api/fraudService';
import { investmentService } from '../api/investmentService';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { TransactionStats } from '../types/transaction';
import { FraudScanResult } from '../types/fraud';
import { MarketTrend } from '../types/investment';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<TransactionStats | null>(null);
  const [fraudAlerts, setFraudAlerts] = useState<FraudScanResult | null>(null);
  const [marketTrends, setMarketTrends] = useState<MarketTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch transaction statistics
        const statsData = await transactionService.getTransactionStats();
        setStats(statsData);
        
        // Fetch fraud alerts
        const fraudData = await fraudService.scanTransactions();
        setFraudAlerts(fraudData);
        
        // Fetch market trends
        const trendsData = await investmentService.getMarketTrends();
        setMarketTrends(trendsData.trends || []);
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Prepare data for pie chart
  const preparePieChartData = () => {
    if (!stats || !stats.category_breakdown) return [];
    
    return Object.entries(stats.category_breakdown).map(([category, details]) => ({
      name: category,
      value: details.amount
    }));
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#83A6ED', '#8DD1E1', '#A4DE6C'];

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        delayChildren: 0.3,
        staggerChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <motion.div 
          className="loader"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Try Again</button>
      </div>
    );
  }

  return (
    <motion.div 
      className="dashboard"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.div className="dashboard-header" variants={itemVariants}>
        <h1>Welcome, {user?.username || 'User'}!</h1>
        <p className="dashboard-date">{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
      </motion.div>
      
      <div className="dashboard-grid">
        {/* Financial Summary Card */}
        <motion.div className="dashboard-card summary-card" variants={itemVariants}>
          <h2>Financial Summary</h2>
          {stats ? (
            <div className="summary-stats">
              <div className="stat-item">
                <h3>Income</h3>
                <p className="stat-value income">${stats.total_income.toFixed(2)}</p>
              </div>
              <div className="stat-item">
                <h3>Expenses</h3>
                <p className="stat-value expense">${stats.total_expenses.toFixed(2)}</p>
              </div>
              <div className="stat-item">
                <h3>Savings</h3>
                <p className="stat-value">${stats.net_savings.toFixed(2)}</p>
                <p className="stat-label">({stats.savings_rate.toFixed(1)}% of income)</p>
              </div>
            </div>
          ) : (
            <p>No financial data available yet.</p>
          )}
          <Link to="/transactions" className="card-link">View All Transactions</Link>
        </motion.div>
        
        {/* Expense Breakdown Card */}
        <motion.div className="dashboard-card" variants={itemVariants}>
          <h2>Expense Breakdown</h2>
          {stats && Object.keys(stats.category_breakdown).length > 0 ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={preparePieChartData()}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${typeof percent === 'number' ? (percent * 100).toFixed(0) : 0}%`}
                  >
                    {preparePieChartData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`$${typeof value === 'number' ? value.toFixed(2) : value}`, 'Amount']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p>No expense data available yet.</p>
          )}
        </motion.div>
        
        {/* Fraud Alerts Card */}
        <motion.div className="dashboard-card fraud-card" variants={itemVariants}>
          <h2>Fraud Alerts</h2>
          {fraudAlerts?.suspicious_transactions_found ? (
            <div className="fraud-alerts">
              <div className="alert-badge warning">
                {fraudAlerts.suspicious_transactions_found} suspicious transaction(s) detected
              </div>
              <ul className="fraud-list">
                {fraudAlerts.details.map((item, index) => (
                  <li key={index} className="fraud-item">
                    <span className="fraud-reason">{item.reason}</span>
                    <span className="fraud-risk">{item.risk_level || 'Medium'} Risk</span>
                    <Link to={`/transactions?id=${item.transaction_id}`} className="view-transaction">View</Link>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="no-fraud">
              <div className="alert-badge success">No suspicious activity detected</div>
              <p>Your recent transactions look normal.</p>
            </div>
          )}
          <Link to="/fraud-detection" className="card-link">Fraud Detection Center</Link>
        </motion.div>
        
        {/* Market Trends Card */}
        <motion.div className="dashboard-card" variants={itemVariants}>
          <h2>Market Trends</h2>
          {marketTrends && marketTrends.length > 0 ? (
            <div className="market-trends">
              <div className="trends-list">
                {marketTrends.map((trend, index) => (
                  <div 
                    key={index} 
                    className={`trend-item ${trend.trend_direction === 'up' ? 'positive' : trend.trend_direction === 'down' ? 'negative' : 'neutral'}`}
                  >
                    <span className="trend-name">{trend.index}</span>
                    <span className="trend-value">{trend.value.toFixed(2)}</span>
                    <span className="trend-change">
                      {trend.change_percent >= 0 ? '+' : ''}{trend.change_percent.toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p>No market trend data available.</p>
          )}
          <Link to="/investments" className="card-link">View Portfolio</Link>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default Dashboard;
