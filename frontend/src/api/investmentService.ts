import axiosInstance from './axiosConfig';
import { PortfolioItem, RecommendationRequest } from '../types/investment';

export const investmentService = {
  // Get user's investment portfolio
  getPortfolio: async () => {
    const response = await axiosInstance.get('/investment/portfolio');
    return response.data;
  },

  // Add a stock to portfolio
  addToPortfolio: async (portfolioItem: PortfolioItem) => {
    const response = await axiosInstance.post('/investment/portfolio', portfolioItem);
    return response.data;
  },

  // Update a portfolio item
  updatePortfolioItem: async (id: string, portfolioItem: Partial<PortfolioItem>) => {
    const response = await axiosInstance.put(`/investment/portfolio/${id}`, portfolioItem);
    return response.data;
  },

  // Remove a stock from portfolio
  removeFromPortfolio: async (id: string) => {
    const response = await axiosInstance.delete(`/investment/portfolio/${id}`);
    return response.data;
  },

  // Get investment recommendations
  getRecommendations: async (request?: RecommendationRequest) => {
    const response = await axiosInstance.post('/investment/recommendations', request || {});
    return response.data;
  },

  // Get market trends data
  getMarketTrends: async () => {
    const response = await axiosInstance.get('/investment/market-trends');
    return response.data;
  },

  // Get portfolio quality assessment
  getPortfolioQuality: async () => {
    const response = await axiosInstance.get('/investment/portfolio-quality');
    return response.data;
  }
};
