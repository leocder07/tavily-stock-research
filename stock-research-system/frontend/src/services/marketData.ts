/**
 * MarketData Service - CRED-style fintech data layer
 * Implements hybrid approach: Alpha Vantage + Yahoo Finance + Tavily
 * Production-grade with caching, error handling, and fallbacks
 */

import axios from 'axios';
import api from './api';

// Types
interface StockQuote {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  timestamp: string;
  source: 'alpha_vantage' | 'yahoo_finance' | 'fallback';
}

interface MarketDataCache {
  [symbol: string]: {
    data: StockQuote;
    timestamp: number;
    ttl: number;
  };
}

class MarketDataService {
  private cache: MarketDataCache = {};
  private readonly CACHE_TTL = 60000; // 1 minute cache
  private readonly ALPHA_VANTAGE_KEY = process.env.REACT_APP_ALPHA_VANTAGE_KEY;
  private readonly BASE_URL = 'https://www.alphavantage.co/query';


  /**
   * Get real-time stock quote with caching and fallbacks
   */
  async getStockQuote(symbol: string): Promise<StockQuote> {
    // Check cache first
    const cached = this.cache[symbol];
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data;
    }

    try {
      // Try our backend API first
      const stockData = await api.getStockPrice(symbol);
      if (stockData && stockData.price > 0) {
        const quote: StockQuote = {
          symbol: stockData.symbol,
          price: stockData.price,
          change: stockData.change,
          changePercent: stockData.changePercent,
          timestamp: stockData.timestamp || new Date().toISOString(),
          source: stockData.source as any || 'alpha_vantage'
        };
        this.updateCache(symbol, quote);
        return quote;
      }

      // Try Alpha Vantage if backend fails
      if (this.ALPHA_VANTAGE_KEY) {
        const quote = await this.fetchFromAlphaVantage(symbol);
        if (quote) {
          this.updateCache(symbol, quote);
          return quote;
        }
      }

      // Fallback to Yahoo Finance
      const yahooQuote = await this.fetchFromYahooFinance(symbol);
      if (yahooQuote) {
        this.updateCache(symbol, yahooQuote);
        return yahooQuote;
      }

      // No data available - throw error to be handled by caller
      throw new Error(`No market data available for ${symbol}`);
    } catch (error) {
      console.warn(`Market data fetch failed for ${symbol}:`, error);
      throw error;
    }
  }

  /**
   * Get multiple stock quotes efficiently
   */
  async getBatchQuotes(symbols: string[]): Promise<StockQuote[]> {
    const promises = symbols.map(symbol => this.getStockQuote(symbol));
    return Promise.all(promises);
  }

  /**
   * Fetch from Alpha Vantage API
   */
  private async fetchFromAlphaVantage(symbol: string): Promise<StockQuote | null> {
    try {
      const response = await axios.get(this.BASE_URL, {
        params: {
          function: 'GLOBAL_QUOTE',
          symbol: symbol,
          apikey: this.ALPHA_VANTAGE_KEY
        },
        timeout: 5000
      });

      const quote = response.data['Global Quote'];
      if (!quote || Object.keys(quote).length === 0) {
        return null;
      }

      const price = parseFloat(quote['05. price']);
      const change = parseFloat(quote['09. change']);
      const changePercent = parseFloat(quote['10. change percent'].replace('%', ''));

      return {
        symbol: symbol.toUpperCase(),
        price,
        change,
        changePercent,
        timestamp: new Date().toISOString(),
        source: 'alpha_vantage'
      };
    } catch (error) {
      console.warn(`Alpha Vantage fetch failed for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Fetch from Yahoo Finance (unofficial API)
   */
  private async fetchFromYahooFinance(symbol: string): Promise<StockQuote | null> {
    try {
      // Using a Yahoo Finance proxy service (free tier)
      const response = await axios.get(`https://query1.finance.yahoo.com/v8/finance/chart/${symbol}`, {
        timeout: 5000
      });

      const result = response.data.chart.result[0];
      if (!result) return null;

      const meta = result.meta;
      const price = meta.regularMarketPrice;
      const previousClose = meta.previousClose;
      const change = price - previousClose;
      const changePercent = (change / previousClose) * 100;

      return {
        symbol: symbol.toUpperCase(),
        price,
        change,
        changePercent,
        timestamp: new Date().toISOString(),
        source: 'yahoo_finance'
      };
    } catch (error) {
      console.warn(`Yahoo Finance fetch failed for ${symbol}:`, error);
      return null;
    }
  }


  /**
   * Update cache with fresh data
   */
  private updateCache(symbol: string, quote: StockQuote): void {
    this.cache[symbol] = {
      data: quote,
      timestamp: Date.now(),
      ttl: this.CACHE_TTL
    };
  }

  /**
   * Clear expired cache entries
   */
  clearExpiredCache(): void {
    const now = Date.now();
    Object.keys(this.cache).forEach(symbol => {
      if (now - this.cache[symbol].timestamp > this.cache[symbol].ttl) {
        delete this.cache[symbol];
      }
    });
  }

  /**
   * Get market indices
   */
  async getMarketIndices() {
    const indices = ['SPY', 'QQQ', 'DIA', 'IWM']; // ETFs representing major indices
    return this.getBatchQuotes(indices);
  }

  /**
   * Get trending stocks
   */
  async getTrendingStocks() {
    const trending = ['NVDA', 'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'META', 'AMZN', 'AMD'];
    return this.getBatchQuotes(trending);
  }
}

// Singleton instance
export const marketDataService = new MarketDataService();

// Helper function for components
export const formatPrice = (price: number): string => {
  return `$${price.toFixed(2)}`;
};

export const formatChange = (change: number, changePercent: number): string => {
  const sign = change >= 0 ? '+' : '';
  return `${sign}${change.toFixed(2)} (${sign}${changePercent.toFixed(2)}%)`;
};

export const getChangeColor = (change: number): string => {
  return change >= 0 ? '#00D4AA' : '#FF453A'; // CRED success/danger colors
};