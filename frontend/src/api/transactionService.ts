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
  getTransactionStats: async () => {
    const response = await axiosInstance.get('/transactions/stats');
    return response.data;
  }
};
