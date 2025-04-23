import axiosInstance from './axiosConfig';
import { FraudScanResult } from '../types/fraud';

export const fraudService = {
  // Scan transactions for potential fraud
  scanTransactions: async (): Promise<FraudScanResult> => {
    const response = await axiosInstance.post('/fraud/scan-transactions');
    return response.data;
  },

  // Report a transaction as suspicious
  reportTransaction: async (transactionId: string): Promise<{message: string}> => {
    const response = await axiosInstance.post(`/fraud/report-transaction/${transactionId}`);
    return response.data;
  }
};
