export interface PortfolioItem {
  id?: string;
  symbol: string;
  shares: number;
  purchase_price: number;
  purchase_date?: string;
  user_id?: string;
}

export interface StockPrice {
  symbol: string;
  price: number;
  change_percent: number;
  last_updated: string;
}

export interface MarketTrend {
  index: string;
  value: number;
  change_percent: number;
  trend_direction: 'up' | 'down' | 'neutral';
}

export interface InvestmentRecommendation {
  symbol: string;
  name: string;
  type: string;
  price: number;
  growth_potential: string;
  risk_level: string;
  recommendation_reason: string;
}

export interface RecommendationRequest {
  risk_tolerance?: 'low' | 'medium' | 'high';
  investment_amount?: number;
  sectors_of_interest?: string[];
}

export interface PortfolioQuality {
  overall_rating: number;
  holdings_analysis: {
    [symbol: string]: {
      rating: number;
      strengths: string[];
      risks: string[];
      recommendation: string;
    }
  };
  portfolio_assessment: {
    diversification: string;
    risk_level: string;
    growth_potential: string;
    improvement_opportunities: string[];
  };
  diversification_score: number;
}
