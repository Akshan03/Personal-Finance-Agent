import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Text, Title, Badge, Button, Alert, List } from '@mantine/core';
import { IconAlertTriangle, IconShieldCheck } from '@tabler/icons-react';
import { fraudService } from '../api/fraudService';
import { transactionService } from '../api/transactionService';
import { Transaction } from '../types/transaction';
import { FraudScanResult, FraudDetection } from '../types/fraud';
import { Link } from 'react-router-dom';

const FraudDetectionPage: React.FC = () => {
  const [fraudResults, setFraudResults] = useState<FraudScanResult | null>(null);
  const [suspiciousTransactions, setSuspiciousTransactions] = useState<Array<Transaction & { fraudDetails?: FraudDetection }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Get fraud scan results
      const scanResults: FraudScanResult = await fraudService.scanTransactions();
      setFraudResults(scanResults);
      
      // If there are suspicious transactions, get their details
      if (scanResults.suspicious_transactions_found > 0 && scanResults.details.length > 0) {
        const transactionIds: string[] = scanResults.details.map((item: FraudDetection) => item.transaction_id);
        const promises: Promise<Transaction>[] = transactionIds.map((id: string) => transactionService.getTransaction(id));
        
        const transactions: Transaction[] = await Promise.all(promises);
        
        // Match transactions with their fraud details
        const enhancedTransactions: Array<Transaction & { fraudDetails?: FraudDetection }> = transactions.map((transaction: Transaction) => {
          const fraudDetails: FraudDetection | undefined = scanResults.details.find((detail: FraudDetection) => detail.transaction_id === transaction.id);
          return {
            ...transaction,
            fraudDetails
          };
        });
        
        setSuspiciousTransactions(enhancedTransactions);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching fraud detection data:', err);
      setError('Failed to load fraud detection data. Please try again.');
      setLoading(false);
    }
  };

  const handleScanForFraud = async () => {
    try {
      setScanning(true);
      setError('');
      
      // Run a new fraud scan
      const scanResults = await fraudService.scanTransactions();
      setFraudResults(scanResults);
      
      // Update suspicious transactions list
      if (scanResults.suspicious_transactions_found > 0 && scanResults.details.length > 0) {
        const transactionIds = scanResults.details.map((item: FraudDetection) => item.transaction_id);
        const promises = transactionIds.map((id: string) => transactionService.getTransaction(id));
        
        const transactions = await Promise.all(promises);
        
        // Match transactions with their fraud details
        const enhancedTransactions = transactions.map((transaction: Transaction) => {
          const fraudDetails = scanResults.details.find((detail: FraudDetection) => detail.transaction_id === transaction.id);
          return {
            ...transaction,
            fraudDetails
          };
        });
        
        setSuspiciousTransactions(enhancedTransactions);
      } else {
        setSuspiciousTransactions([]);
      }
      
      setScanning(false);
    } catch (err) {
      console.error('Error scanning for fraud:', err);
      setError('Failed to scan for fraud. Please try again.');
      setScanning(false);
    }
  };

  const handleReportTransaction = async (transactionId: string) => {
    if (window.confirm('Are you sure you want to report this transaction as fraudulent? This will flag it in the system for further investigation.')) {
      try {
        await fraudService.reportTransaction(transactionId);
        alert('Transaction reported successfully. Our fraud team will investigate it.');
        
        // Refresh data after reporting
        fetchData();
      } catch (err) {
        console.error('Error reporting transaction:', err);
        setError('Failed to report transaction. Please try again.');
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

  if (loading && !fraudResults) {
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
        <p>Loading fraud detection data...</p>
      </div>
    );
  }

  return (
    <div className="fraud-detection-page">
      <motion.div 
        className="fraud-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1>Fraud Detection Center</h1>
        <motion.button
          className="scan-button"
          onClick={handleScanForFraud}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          disabled={scanning}
        >
          {scanning ? 'Scanning...' : 'Scan for Fraud'}
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

      <motion.div 
        className="fraud-detection-section"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <h2 className="fraud-section-title">Fraud Scan Status</h2>
        <div className="fraud-status-box">
          {fraudResults && (
            <div className="status-content">
              <div className={`status-indicator ${fraudResults.suspicious_transactions_found > 0 ? 'warning' : 'safe'}`}>
                <span className="status-icon">
                  {fraudResults.suspicious_transactions_found > 0 ? '⚠️' : '✅'}
                </span>
                <div className="status-text">
                  <span className="status-label">
                    {fraudResults.suspicious_transactions_found > 0 ? 'Warning' : 'Safe'}
                  </span>
                  <span className="status-message">
                    {fraudResults.message}
                  </span>
                </div>
              </div>
              <div className="status-details">
                <p>
                  <strong>Suspicious Transactions:</strong> {fraudResults.suspicious_transactions_found}
                </p>
                <p>
                  <strong>Last Scan:</strong> {new Date().toLocaleString()}
                </p>
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {suspiciousTransactions.length > 0 ? (
        <motion.div 
          className="fraud-detection-section suspicious-transactions"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <h2 className="fraud-section-title">Suspicious Transactions</h2>
          <div className="transaction-list">
            {suspiciousTransactions.map((transaction, index) => (
              <motion.div 
                key={transaction.id}
                className="suspicious-transaction-item"
                variants={itemVariants}
                whileHover={{ scale: 1.01, boxShadow: '0 4px 8px rgba(0,0,0,0.1)' }}
              >
                <div className="transaction-info">
                  <div className="transaction-header">
                    <span className="transaction-date">
                      {new Date(transaction.timestamp).toLocaleDateString()}
                    </span>
                    <span className={`risk-level ${transaction.fraudDetails?.risk_level?.toLowerCase() || 'medium'}`}>
                      {transaction.fraudDetails?.risk_level || 'Medium'} Risk
                    </span>
                  </div>
                  <div className="transaction-details">
                    <h3>{transaction.description}</h3>
                    <div className="detail-row">
                      <span className="detail-label">Amount:</span>
                      <span className="detail-value">${transaction.amount.toFixed(2)}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Category:</span>
                      <span className="detail-value">{transaction.category}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Reason Flagged:</span>
                      <span className="detail-value fraud-reason">{transaction.fraudDetails?.reason}</span>
                    </div>
                  </div>
                </div>
                <div className="transaction-actions">
                  <motion.button
                    className="action-button report"
                    onClick={() => handleReportTransaction(transaction.id)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Report as Fraudulent
                  </motion.button>
                  <Link to={`/transactions?id=${transaction.id}`}>
                    <motion.button
                      className="action-button view"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      View Details
                    </motion.button>
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      ) : (
        <motion.div 
          className="fraud-detection-section no-suspicious-transactions"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <h2 className="fraud-section-title">Security Status</h2>
          <div className="safe-status">
            <div className="safe-icon">✅</div>
            <h3>No Suspicious Activity Detected</h3>
            <p>Your recent transactions appear to be normal. We'll continue to monitor your account for any unusual activity.</p>
          </div>
        </motion.div>
      )}

      <motion.div
        className="fraud-detection-section fraud-tips"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="fraud-section-title">Fraud Protection Tips</h2>
        <div className="fraud-tips-container">
          <div className="tip-item">
            <div className="tip-icon">🔒</div>
            <div className="tip-content">
              <h3>Secure Your Passwords</h3>
              <p>Use strong, unique passwords for each financial account and enable two-factor authentication when available.</p>
            </div>
          </div>
          <div className="tip-item">
            <div className="tip-icon">👁️</div>
            <div className="tip-content">
              <h3>Monitor Your Accounts</h3>
              <p>Regularly review your transaction history and immediately report any suspicious activity.</p>
            </div>
          </div>
          <div className="tip-item">
            <div className="tip-icon">⚠️</div>
            <div className="tip-content">
              <h3>Be Cautious of Phishing</h3>
              <p>Don't click on suspicious links or provide personal information in response to unsolicited emails or calls.</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default FraudDetectionPage;
