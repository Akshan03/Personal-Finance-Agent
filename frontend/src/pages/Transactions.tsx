import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { transactionService } from '../api/transactionService';
import { Transaction, TransactionCreate } from '../types/transaction';
import { useLocation } from 'react-router-dom';

const Transactions: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<TransactionCreate>({
    amount: 0,
    category: 'food',
    description: ''
  });
  
  // Pagination
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  
  // Get transaction ID from URL if present
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const transactionIdFromUrl = queryParams.get('id');
  
  useEffect(() => {
    if (transactionIdFromUrl) {
      setHighlightedId(transactionIdFromUrl);
    }
  }, [transactionIdFromUrl]);

  useEffect(() => {
    fetchTransactions();
  }, [page]);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const skip = (page - 1) * limit;
      const data = await transactionService.getTransactions(limit, skip);
      setTransactions(data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setError('Failed to load transactions. Please try again.');
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'amount' ? parseFloat(value) : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await transactionService.createTransaction(formData);
      fetchTransactions();
      setShowForm(false);
      setFormData({ amount: 0, category: 'food', description: '' });
    } catch (err) {
      console.error('Error creating transaction:', err);
      setError('Failed to create transaction. Please try again.');
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      try {
        await transactionService.deleteTransaction(id);
        setTransactions(prev => prev.filter(t => t.id !== id));
      } catch (err) {
        console.error('Error deleting transaction:', err);
        setError('Failed to delete transaction. Please try again.');
      }
    }
  };

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 }
  };

  if (loading && transactions.length === 0) {
    return (
      <div className="loading-container">
        <motion.div 
          className="loader"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <p>Loading transactions...</p>
      </div>
    );
  }

  return (
    <div className="transactions-page">
      <motion.div 
        className="transactions-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1>Your Transactions</h1>
        <motion.button
          className="add-button"
          onClick={() => setShowForm(!showForm)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {showForm ? 'Cancel' : 'Add New Transaction'}
        </motion.button>
      </motion.div>

      {error && (
        <motion.div 
          className="error-message"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {error}
          <button onClick={() => setError('')}>Dismiss</button>
        </motion.div>
      )}

      <AnimatePresence>
        {showForm && (
          <motion.div 
            className="transaction-form-container"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <form onSubmit={handleSubmit} className="transaction-form">
              <div className="form-group">
                <label htmlFor="amount">Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  id="amount"
                  name="amount"
                  value={formData.amount}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="category">Category</label>
                <select
                  id="category"
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  required
                >
                  <option value="food">Food</option>
                  <option value="housing">Housing</option>
                  <option value="transport">Transportation</option>
                  <option value="utilities">Utilities</option>
                  <option value="entertainment">Entertainment</option>
                  <option value="shopping">Shopping</option>
                  <option value="health">Healthcare</option>
                  <option value="personal">Personal</option>
                  <option value="education">Education</option>
                  <option value="income">Income</option>
                  <option value="investment">Investment</option>
                  <option value="other">Other</option>
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="description">Description</label>
                <input
                  type="text"
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <motion.button 
                type="submit" 
                className="submit-button"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Add Transaction
              </motion.button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {transactions.length > 0 ? (
        <motion.div 
          className="transactions-list"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <div className="transaction-header">
            <div className="transaction-date">Date</div>
            <div className="transaction-description">Description</div>
            <div className="transaction-category">Category</div>
            <div className="transaction-amount">Amount</div>
            <div className="transaction-actions">Actions</div>
          </div>
          
          {transactions.map(transaction => (
            <motion.div 
              key={transaction.id}
              className={`transaction-item ${transaction.id === highlightedId ? 'highlighted' : ''}`}
              variants={itemVariants}
              whileHover={{ scale: 1.01, boxShadow: '0 4px 8px rgba(0,0,0,0.1)' }}
            >
              <div className="transaction-date">
                {new Date(transaction.timestamp).toLocaleDateString()}
              </div>
              <div className="transaction-description">{transaction.description}</div>
              <div className="transaction-category">
                <span className={`category-badge ${transaction.category}`}>
                  {transaction.category}
                </span>
              </div>
              <div className={`transaction-amount ${transaction.category === 'income' ? 'income' : 'expense'}`}>
                {transaction.category === 'income' ? '+' : '-'}${Math.abs(transaction.amount).toFixed(2)}
              </div>
              <div className="transaction-actions">
                <motion.button
                  className="action-button delete"
                  onClick={() => handleDelete(transaction.id)}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  Delete
                </motion.button>
              </div>
            </motion.div>
          ))}
          
          <div className="pagination">
            <button 
              disabled={page === 1} 
              onClick={() => setPage(prev => Math.max(prev - 1, 1))}
            >
              Previous
            </button>
            <span>Page {page}</span>
            <button 
              disabled={transactions.length < limit} 
              onClick={() => setPage(prev => prev + 1)}
            >
              Next
            </button>
          </div>
        </motion.div>
      ) : (
        <motion.div 
          className="no-transactions"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <p>No transactions found. Add your first transaction to get started!</p>
        </motion.div>
      )}
    </div>
  );
};

export default Transactions;
