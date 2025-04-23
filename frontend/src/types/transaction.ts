export interface Transaction {
  id: string;
  amount: number;
  category: TransactionCategory | string;
  description: string;
  timestamp: string;
  user_id: string;
  is_fraudulent: boolean;
}

export interface TransactionCreate {
  amount: number;
  category: string;
  description: string;
  timestamp?: string;
}

export interface TransactionStats {
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

export enum TransactionCategory {
  INCOME = 'income',
  HOUSING = 'housing',
  FOOD = 'food',
  TRANSPORT = 'transport',
  UTILITIES = 'utilities',
  ENTERTAINMENT = 'entertainment',
  SHOPPING = 'shopping',
  HEALTH = 'health',
  EDUCATION = 'education',
  PERSONAL = 'personal',
  DEBT = 'debt',
  INVESTMENT = 'investment',
  OTHER = 'other'
}
