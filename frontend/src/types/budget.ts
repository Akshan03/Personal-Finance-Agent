export interface BudgetSummary {
  total_income: number;
  total_expenses: number;
  net_savings: number;
  savings_rate: number;
  category_breakdown: {
    [key: string]: {
      amount: number;
      percentage: number;
    };
  };
}

export interface BudgetAdvice {
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  category?: string;
}

export interface BudgetPlan {
  target_savings_percent: number;
  recommended_savings: number;
  category_limits: {
    [key: string]: number;
  };
  advice: BudgetAdvice[];
}
