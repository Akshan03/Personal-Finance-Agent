import axios from './axiosConfig';

export interface CategoryDetails {
  amount: number;
  percentage: number;
}

export interface CategoryAnalysis {
  amount: number;
  percentage_of_income: number;
  benchmark_min: number;
  benchmark_max: number;
  status: 'below' | 'normal' | 'above';
  advice: string;
}

export interface BudgetSummary {
  total_income: number;
  total_expenses: number;
  net_savings: number;
  savings_rate: number;
  category_breakdown: {
    [category: string]: CategoryDetails;
  };
}

export interface FixedVsDiscretionary {
  fixed: {
    total: number;
    percentage_of_income: number;
    breakdown: {
      [category: string]: CategoryDetails;
    };
  };
  discretionary: {
    total: number;
    percentage_of_income: number;
    breakdown: {
      [category: string]: CategoryDetails;
    };
  };
}

export interface Benchmarks {
  needs: number;
  wants: number;
  savings: number;
  rule: string;
}

export interface BudgetPlan {
  summary: BudgetSummary;
  insights: string[];
  recommendations: string[];
  fixed_vs_discretionary: FixedVsDiscretionary;
  benchmarks: Benchmarks;
  category_analysis: {
    [category: string]: CategoryAnalysis;
  };
  budget_allocation: {
    [category: string]: CategoryDetails;
  };
  savings_recommendations: string[];
  spending_insights: string[];
}

const budgetService = {
  /**
   * Generate a budget plan based on transaction history
   */
  generateBudgetPlan: async (timeframe: string = 'monthly'): Promise<BudgetPlan> => {
    try {
      const response = await axios.post('/budget/generate-plan', { timeframe });
      return response.data;
    } catch (error) {
      console.error('Error generating budget plan:', error);
      throw error;
    }
  },

  /**
   * Get budget summary information
   */
  getBudgetSummary: async (): Promise<any> => {
    try {
      const response = await axios.get('/budget/summary');
      return response.data;
    } catch (error) {
      console.error('Error fetching budget summary:', error);
      throw error;
    }
  },

  /**
   * Get budget advice
   */
  getBudgetAdvice: async (): Promise<any> => {
    try {
      const response = await axios.post('/budget/advice');
      return response.data;
    } catch (error) {
      console.error('Error fetching budget advice:', error);
      throw error;
    }
  }
};

export default budgetService;
