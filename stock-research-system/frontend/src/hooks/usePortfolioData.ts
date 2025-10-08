import { useEffect, useState } from 'react';
import axios from 'axios';

export interface PortfolioMetrics {
  totalValue: number;
  dayChange: number;
  dayChangePercent: number;
  totalReturn: number;
  totalReturnPercent: number;
  winRate: number;
  sharpeRatio: number;
  profitablePositions: number;
  totalPositions: number;
}

export interface Holding {
  symbol: string;
  shares: number;
  avgCost: number;
  currentPrice: number;
  previousClose?: number;
  value: number;
  costBasis: number;
  gainLoss: number;
  gainLossPercent: number;
  totalReturnPercent: number;
  dayChangeValue: number;
  dayChangePercent: number;
  allocation: number;
  purchaseDate?: string;
  notes?: string;
}

export interface PortfolioData {
  holdings: Holding[];
  metrics: PortfolioMetrics;
}

const transformBackendData = (backendData: any): PortfolioData => {
  // Transform snake_case to camelCase
  const holdings = (backendData.holdings || []).map((h: any) => ({
    symbol: h.symbol,
    shares: h.shares,
    avgCost: h.avg_cost,
    currentPrice: h.current_price,
    previousClose: h.previous_close,
    value: h.value,
    costBasis: h.cost_basis,
    gainLoss: h.gain_loss,
    gainLossPercent: h.gain_loss_percent,
    totalReturnPercent: h.total_return_percent,
    dayChangeValue: h.day_change_value,
    dayChangePercent: h.day_change_percent,
    allocation: h.allocation,
    purchaseDate: h.purchase_date,
    notes: h.notes,
  }));

  const metrics: PortfolioMetrics = {
    totalValue: backendData.total_value || 0,
    dayChange: backendData.day_change || 0,
    dayChangePercent: backendData.day_change_percent || 0,
    totalReturn: backendData.total_return || 0,
    totalReturnPercent: backendData.total_return_percent || 0,
    winRate: backendData.win_rate || 0,
    sharpeRatio: backendData.sharpe_ratio || 0,
    profitablePositions: backendData.profitable_positions || 0,
    totalPositions: backendData.total_positions || 0,
  };

  return { holdings, metrics };
};

export const usePortfolioData = (userIdentifier: string) => {
  const [data, setData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Use query parameter for user_id or user_email lookup
      // API will try to find by user_id first, then user_email
      const response = await axios.get(`http://localhost:8000/api/v1/portfolio`, {
        params: { user_id: userIdentifier }
      });

      console.log('Portfolio API response:', response.data);

      const transformed = transformBackendData(response.data);
      setData(transformed);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching portfolio:', err);
      console.error('Error details:', err.response?.data);
      setError(err.message || 'Failed to load portfolio');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userIdentifier) {
      console.log('Fetching portfolio for user:', userIdentifier);
      fetchData();
    }
  }, [userIdentifier]);

  return { data, loading, error, refetch: fetchData };
};
