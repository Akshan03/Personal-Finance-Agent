import axiosInstance from './axiosConfig';
import { Transaction, TransactionCreate } from '../types/transaction';

export const transactionService = {
  // Get all transactions with optional pagination
  getTransactions: async (limit = 50, skip = 0) => {
    const response = await axiosInstance.get('/transactions', {
      params: { limit, skip }
    });
    return response.data;
  },

  // Get a single transaction by ID
  getTransaction: async (id: string) => {
    const response = await axiosInstance.get(`/transactions/${id}`);
    return response.data;
  },

  // Create a new transaction
  createTransaction: async (data: TransactionCreate) => {
    const response = await axiosInstance.post('/transactions', data);
    return response.data;
  },

  // Update an existing transaction
  updateTransaction: async (id: string, data: Partial<Transaction>) => {
    const response = await axiosInstance.put(`/transactions/${id}`, data);
    return response.data;
  },

  // Delete a transaction
  deleteTransaction: async (id: string) => {
    const response = await axiosInstance.delete(`/transactions/${id}`);
    return response.data;
  },

  // Get transaction statistics
  getTransactionStats: async (period: string = 'all') => {
    const response = await axiosInstance.get('/transactions/stats', {
      params: { period }
    });
    console.log('Transaction stats response:', response.data);
    
    // Enhanced: Ensure all numeric values are properly parsed with additional validation
    const stats = {
      ...response.data,
      total_income: parseFloat(String(response.data.total_income || 0)),
      total_expenses: parseFloat(String(response.data.total_expenses || 0)),
      net_savings: parseFloat(String(response.data.net_savings || 0)),
      savings_rate: parseFloat(String(response.data.savings_rate || 0)),
      category_breakdown: response.data.category_breakdown || {}
    };
    
    // Double-check to ensure calculations match
    if (stats.total_income > 0 || stats.total_expenses > 0) {
      // Verify savings calculation
      const calculatedSavings = stats.total_income - stats.total_expenses;
      if (Math.abs(calculatedSavings - stats.net_savings) > 0.01) {
        console.warn('Savings calculation mismatch. Fixing:', {
          received: stats.net_savings,
          calculated: calculatedSavings
        });
        stats.net_savings = calculatedSavings;
      }
      
      // Verify savings rate calculation
      const calculatedRate = stats.total_income > 0 
        ? (stats.net_savings / stats.total_income) * 100 
        : 0;
      if (Math.abs(calculatedRate - stats.savings_rate) > 0.1) {
        console.warn('Savings rate calculation mismatch. Fixing:', {
          received: stats.savings_rate,
          calculated: calculatedRate
        });
        stats.savings_rate = calculatedRate;
      }
    }
    
    console.log('Processed stats:', stats);
    return stats;
  }
};
