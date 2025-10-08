/**
 * Custom React Hook for Real-time Data Fetching
 * Handles WebSocket connections, polling, and data synchronization
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import api, { StockData, PortfolioData } from '../services/api';

interface UseRealTimeDataOptions {
  symbols?: string[];
  pollInterval?: number;
  enableWebSocket?: boolean;
}

interface RealTimeData {
  stocks: Map<string, StockData>;
  portfolio: PortfolioData | null;
  loading: boolean;
  error: string | null;
  lastUpdate: Date;
  isConnected: boolean;
}

export const useRealTimeData = (options: UseRealTimeDataOptions = {}) => {
  const {
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA'],
    pollInterval = 30000, // 30 seconds
    enableWebSocket = false // WebSocket disabled - using polling only
  } = options;

  const [data, setData] = useState<RealTimeData>({
    stocks: new Map(),
    portfolio: null,
    loading: true,
    error: null,
    lastUpdate: new Date(),
    isConnected: false
  });

  const wsRef = useRef<WebSocket | null>(null);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch stock prices
  const fetchStockPrices = useCallback(async () => {
    try {
      const stockData = await api.getMultipleStockPrices(symbols);
      const stockMap = new Map<string, StockData>();
      stockData.forEach(stock => {
        stockMap.set(stock.symbol, stock);
      });

      setData(prev => ({
        ...prev,
        stocks: stockMap,
        loading: false,
        error: null,
        lastUpdate: new Date()
      }));
    } catch (error) {
      console.error('Error fetching stock prices:', error);
      setData(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch stock prices'
      }));
    }
  }, [symbols]);

  // Fetch portfolio data
  const fetchPortfolio = useCallback(async () => {
    try {
      const portfolioData = await api.getPortfolio();
      setData(prev => ({
        ...prev,
        portfolio: portfolioData,
        loading: false,
        error: null
      }));
    } catch (error) {
      console.error('Error fetching portfolio:', error);
      setData(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch portfolio'
      }));
    }
  }, []);

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    setData(prev => ({ ...prev, loading: true }));
    await Promise.all([fetchStockPrices(), fetchPortfolio()]);
  }, [fetchStockPrices, fetchPortfolio]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'price_update') {
      const { symbol, price, change, changePercent } = message.data;
      setData(prev => {
        const newStocks = new Map(prev.stocks);
        const existingStock = newStocks.get(symbol);
        if (existingStock) {
          newStocks.set(symbol, {
            ...existingStock,
            price,
            change,
            changePercent,
            timestamp: new Date().toISOString()
          });
        }
        return {
          ...prev,
          stocks: newStocks,
          lastUpdate: new Date()
        };
      });
    } else if (message.type === 'portfolio_update') {
      setData(prev => ({
        ...prev,
        portfolio: message.data,
        lastUpdate: new Date()
      }));
    }
  }, []);

  // Setup WebSocket connection - fixed: removed handleWebSocketMessage from deps
  useEffect(() => {
    if (enableWebSocket) {
      try {
        // WebSocket removed
        const ws = null; // api.connectWebSocket(handleWebSocketMessage);
        if (ws) {
          wsRef.current = ws;
          setData(prev => ({ ...prev, isConnected: true }));

          // Subscribe to market data when connection opens
          ws.addEventListener('open', () => {
            if (symbols.length > 0) {
              ws.send(JSON.stringify({
                type: 'subscribe_market_data',
                symbols: symbols
              }));
              console.log('Subscribed to market data for:', symbols);
            }
          });
        } else {
          // WebSocket disabled in api.ts - use dedicated hooks instead
          setData(prev => ({ ...prev, isConnected: false }));
        }
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setData(prev => ({ ...prev, isConnected: false }));
      }

      return () => {
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enableWebSocket, symbols]); // Added symbols to deps for subscription

  // Setup polling - fixed: removed fetchAllData from deps
  useEffect(() => {
    // Initial fetch
    fetchAllData();

    // Setup polling interval
    if (pollInterval > 0) {
      pollTimerRef.current = setInterval(() => {
        fetchAllData();
      }, pollInterval);
    }

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pollInterval]); // Fixed: only depend on pollInterval to prevent infinite loop

  // Refresh function
  const refresh = useCallback(async () => {
    api.clearCache();
    await fetchAllData();
  }, [fetchAllData]);

  // Add symbol to watch list - fixed: don't mutate props array
  const addSymbol = useCallback((symbol: string) => {
    if (!symbols.includes(symbol)) {
      // Don't mutate symbols array - just fetch prices
      fetchStockPrices();
    }
  }, [symbols, fetchStockPrices]);

  // Remove symbol from watch list - fixed: only update local state
  const removeSymbol = useCallback((symbol: string) => {
    setData(prev => {
      const newStocks = new Map(prev.stocks);
      newStocks.delete(symbol);
      return { ...prev, stocks: newStocks };
    });
  }, []);

  return {
    ...data,
    refresh,
    addSymbol,
    removeSymbol,
    symbols
  };
};

// Hook for single stock real-time data
export const useStockRealTime = (symbol: string) => {
  const [stockData, setStockData] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStock = async () => {
      try {
        setLoading(true);
        const data = await api.getStockPrice(symbol);
        setStockData(data);
        setError(null);
      } catch (err) {
        console.error(`Error fetching ${symbol}:`, err);
        setError(err instanceof Error ? err.message : 'Failed to fetch stock data');
      } finally {
        setLoading(false);
      }
    };

    fetchStock();
    const interval = setInterval(fetchStock, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [symbol]);

  return { data: stockData, loading, error };
};

// Hook for market overview data
export const useMarketOverview = () => {
  const [marketData, setMarketData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setLoading(true);
        const [news, sectors, topStocks] = await Promise.all([
          api.getMarketNews(5),
          api.getSectorPerformance(),
          api.getTopStocks()
        ]);

        setMarketData({
          news,
          sectors,
          topStocks,
          timestamp: new Date()
        });
        setError(null);
      } catch (err) {
        console.error('Error fetching market data:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch market data');
      } finally {
        setLoading(false);
      }
    };

    fetchMarketData();
    const interval = setInterval(fetchMarketData, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  return { data: marketData, loading, error, refresh: () => api.clearCache() };
};

export default useRealTimeData;