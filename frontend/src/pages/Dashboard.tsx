import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { transactionService } from '../api/transactionService';
import { fraudService } from '../api/fraudService';
import { investmentService } from '../api/investmentService';
import budgetService, { BudgetPlan } from '../api/budgetService';
import { useAuth } from '../context/AuthContext';
import { TransactionStats } from '../types/transaction';
import { FraudScanResult } from '../types/fraud';
import { MarketTrend } from '../types/investment';
import { Link } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<TransactionStats | null>(null);
  const [budgetPlan, setBudgetPlan] = useState<BudgetPlan | null>(null);
  const [fraudAlerts, setFraudAlerts] = useState<FraudScanResult | null>(null);
  const [marketTrends, setMarketTrends] = useState<MarketTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [period, setPeriod] = useState<'monthly' | 'yearly' | 'all'>('monthly');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        // Fetch budget plan for the summary card (matches BudgetAdvice)
        const budgetData = await budgetService.generateBudgetPlan(period);
        setBudgetPlan(budgetData);
        // Optionally, still fetch transaction stats for charts, but not for summary card
        const statsData = await transactionService.getTransactionStats(period);
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
  }, [period]);

  const handlePeriodChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPeriod(e.target.value as 'monthly' | 'yearly' | 'all');
  };


  // Prepare data for pie chart
  const preparePieChartData = () => {
    if (!stats || !stats.category_breakdown) return [];
    
    // Make sure we have proper data to display
    const entries = Object.entries(stats.category_breakdown);
    if (entries.length === 0) return [];
    
    // Map the entries to a format that recharts can use
    const chartData = entries.map(([category, details]) => {
      // Safely handle the amount field which could be various types
      let amount = 0;
      if (typeof details === 'object' && details !== null) {
        const detailsAmount = (details as any).amount;
        if (typeof detailsAmount === 'number') {
          amount = detailsAmount;
        } else if (typeof detailsAmount === 'string') {
          amount = parseFloat(detailsAmount);
        }
      }
      return {
        name: category,
        value: amount
      };
    });
    
    // Remove any entries with zero or invalid values
    return chartData.filter(item => item.value > 0);
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
          className="loading-indicator"
          initial={{ opacity: 0.5 }}
          animate={{ 
            opacity: [0.5, 1, 0.5],
            scale: [1, 1.05, 1] 
          }}
          transition={{ 
            duration: 1.5, 
            repeat: Infinity, 
            ease: "easeInOut" 
          }}
        >
          <div className="loading-pulse"></div>
        </motion.div>
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <h2 style={{ margin: 0 }}>Financial Summary</h2>
            <div className="dashboard-period-selector" style={{ minWidth: 0 }}>
              <select
                id="dashboard-period"
                value={period}
                onChange={handlePeriodChange}
                style={{ padding: '2px 8px', borderRadius: '6px', fontSize: '0.95rem', border: '1px solid #e5e7eb', background: '#f9f9fb', minWidth: 0 }}
              >
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
                <option value="all">All Time</option>
              </select>
            </div>
          </div>
          {budgetPlan && budgetPlan.summary ? (
            <div className="summary-stats" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'stretch', gap: '1.5rem', width: '100%' }}>
              <div className="stat-item">
                <h3>Income</h3>
                <p className="stat-value income">${budgetPlan.summary.total_income.toFixed(2)}</p>
              </div>
              <div className="stat-item">
                <h3>Expenses</h3>
                <p className="stat-value expense">${budgetPlan.summary.total_expenses.toFixed(2)}</p>
              </div>
              <div className="stat-item">
                <h3>Savings</h3>
                <p className="stat-value savings">${budgetPlan.summary.net_savings.toFixed(2)}</p>
                <p className="stat-label">{budgetPlan.summary.savings_rate.toFixed(1)}% of income</p>
              </div>
            </div>
          ) : (
            <p>No financial data available yet.</p>
          )}
          <Link to="/transactions" className="card-link">View All Transactions</Link>
        </motion.div>
        
        {/* Expense Breakdown Card */}
        <motion.div className="dashboard-card">
          <div className="expense-breakdown panel">
            <h2>Expense Breakdown</h2>
            {stats && stats.category_breakdown && Object.keys(stats.category_breakdown).length > 0 && preparePieChartData().length > 0 ? (
              <div className="pie-chart-container">
                <PieChart width={250} height={250}>
                  <Pie
                    data={preparePieChartData()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {preparePieChartData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `$${parseFloat(value.toString()).toFixed(2)}`} />
                  <Legend />
                </PieChart>
              </div>
            ) : (
              <div className="no-data-container">
                <p className="no-data">No expense data available yet.</p>
                <p className="no-data-hint">Add transactions with negative amounts to see your expense breakdown.</p>
                <Link to="/transactions" className="add-transaction-btn">
                  Add Expense Transaction
                </Link>
              </div>
            )}
          </div>
        </motion.div>
        
        {/* Fraud Alerts Card */}
        <motion.div className="dashboard-card fraud-card" variants={itemVariants}>
          <h2>Fraud Alerts</h2>
          {fraudAlerts?.last_scan_time && (
            <div className="last-scan-time" style={{ fontSize: '0.95rem', color: '#888', marginBottom: '0.5rem' }}>
              Last scan: {new Date(fraudAlerts.last_scan_time).toLocaleString('en-US', {
                year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
              })}
            </div>
          )}

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
