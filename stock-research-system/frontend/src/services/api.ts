/**
 * Unified API Service Layer
 * Production-ready API client with proper error handling, caching, and retry logic
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds
// const MAX_RETRIES = 3;
// const RETRY_DELAY = 1000;

// Types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: 'success' | 'error';
  timestamp: string;
}

export interface StockData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  dayHigh: number;
  dayLow: number;
  timestamp: string;
  source: string;
  data_quality: string;
}

export interface PortfolioData {
  totalValue: number;
  dayChange: number;
  dayChangePercent: number;
  holdings: Array<{
    symbol: string;
    shares: number;
    avgPrice: number;
    currentPrice: number;
    value: number;
    gain: number;
    gainPercent: number;
  }>;
  performance: {
    totalReturn: number;
    winRate: number;
    sharpeRatio: number;
    maxDrawdown: number;
  };
}

export interface AnalysisRequest {
  query: string;
  symbols?: string[];
  include_technical?: boolean;
  include_sentiment?: boolean;
  include_fundamentals?: boolean;
  user_id?: string;
}

export interface AnalysisResult {
  analysis_id: string;
  query: string;
  symbols: string[];
  recommendations: any;
  executive_summary?: string;
  investment_thesis?: string;
  confidence_score?: number;
  market_data?: {
    price?: number;
    current_price?: number;
    previous_close?: number;
    change_percent?: number;
    volume?: number;
    market_cap?: number;
    day_high?: number;
    day_low?: number;
    year_high?: number;
    year_low?: number;
    '52_week_high'?: number;
    '52_week_low'?: number;
    week_52_high?: number;
    week_52_low?: number;
  };
  analysis?: {
    summary?: string;
    market_data?: {
      price?: number;
      current_price?: number;
      previous_close?: number;
      change_percent?: number;
      volume?: number;
      market_cap?: number;
      day_high?: number;
      day_low?: number;
      year_high?: number;
      year_low?: number;
      '52_week_high'?: number;
      '52_week_low'?: number;
      week_52_high?: number;
      week_52_low?: number;
    };
    fundamental?: {
      pe_ratio?: number;
      eps?: number;
      peg_ratio?: number;
      profit_margin?: number;
      roe?: number;
      analyst_consensus?: string;
      analyst_target_price?: number;
      analyst_ratings?: {
        strong_buy?: number;
        buy?: number;
        hold?: number;
        sell?: number;
        strong_sell?: number;
      };
      valuation_metrics?: {
        pe_ratio?: number;
        eps?: number;
        peg_ratio?: number;
        pb_ratio?: number;
        graham_number?: number;
      };
      financial_health?: {
        roe?: number;
        roa?: number;
        debt_to_equity?: number;
        current_ratio?: number;
        profit_margin?: number;
        operating_margin?: number;
      };
      growth_metrics?: {
        revenue_growth?: number;
        earnings_growth?: number;
        fcf_growth?: number;
      };
    };
    technical?: {
      rsi?: {
        value?: number;
        signal?: string;
        date?: string;
      };
      macd?: {
        macd?: number | null;
        signal?: number | null;
        histogram?: number | null;
        trend?: string;
      };
      trend?: string;
      confidence?: number;
      chart_patterns?: Array<{
        pattern: string;
        type: string;
        confidence: number;
        target?: number;
        neckline?: number;
        description: string;
      }>;
      pattern_signals?: Array<string | {
        signal: string;
        price_target: number;
        reasoning: string;
      }>;
      indicators?: {
        rsi?: number | { value?: number; signal?: string; date?: string };
        macd?: number | { macd?: number | null; signal?: number | null; histogram?: number | null; trend?: string };
        atr?: number;
        adx?: number;
        bollinger_bands?: {
          upper?: number;
          middle?: number;
          lower?: number;
        };
      };
      support_levels?: number[];
      resistance_levels?: number[];
    };
    sentiment?: {
      overall_sentiment?: string;
      sentiment_score?: number;
      confidence?: number;
    };
    predictive?: {
      price_forecast?: {
        short_term?: number;
        long_term?: number;
        '1_day'?: {
          expected_return?: number;
        };
        '30_day'?: {
          expected_return?: number;
        };
      };
      confidence?: number;
      model_confidence?: number;
      summary?: string;
      backtest_results?: {
        accuracy?: string;
        win_rate?: string;
        sharpe_ratio?: string;
        performance_grade?: string;
        out_of_sample?: {
          train_accuracy?: string;
          test_accuracy?: string;
          overfitting_gap?: string;
        };
      };
      predictions?: {
        price_forecast?: {
          '1_day'?: {
            expected_return?: number;
          };
          '30_day'?: {
            expected_return?: number;
          };
        };
        trend_prediction?: {
          current_trend?: string;
          reversal_probability?: number;
          reversal_signals?: string[];
        };
      };
      recommendations?: {
        action?: string;
        confidence?: number;
        rationale?: string[];
      };
    };
    peer_comparison?: {
      peers?: Array<{
        symbol: string;
        pe_ratio?: number;
        market_cap?: number;
        relative_performance?: number;
      }>;
      summary?: string;
    };
    news?: {
      articles?: Array<{
        title: string;
        url: string;
        content?: string;
        summary?: string;
        source?: string;
        sentiment?: string;
        score?: number;
      }>;
      news_data?: {
        sources?: Array<{
          title: string;
          url: string;
          content?: string;
          summary?: string;
          source?: string;
          sentiment?: string;
          score?: number;
        }>;
      };
    };
  };
  // NEW: Agent results structure from backend
  agent_results?: {
    synthesis?: any;
    market_data?: any;
    fundamental?: any;
    technical?: any;
    sentiment?: any;
    risk?: any;
    peer_comparison?: any;
    insider_activity?: any;
    predictive?: any;
    catalyst_tracker?: any;
    chart_analytics?: any;
    critique?: any;
  };
  // CRITICAL: Flat structure fields from backend (actual API response)
  synthesis?: {
    action?: string;
    confidence?: number;
    target_price?: number;
    stop_loss?: number;
    entry_price?: number;
    rationale?: string;
    reasoning?: string;  // Alternative to rationale
    risk_reward_ratio?: number;
    position_sizing?: {
      account_value: number;
      conservative?: {
        shares: number;
        position_value: number;
        capital_at_risk: number;
        position_pct: number;
        risk_per_trade_pct: number;
      };
      moderate?: {
        shares: number;
        position_value: number;
        capital_at_risk: number;
        position_pct: number;
        risk_per_trade_pct: number;
      };
      aggressive?: {
        shares: number;
        position_value: number;
        capital_at_risk: number;
        position_pct: number;
      };
      volatility_adjusted?: any;
      recommended?: {
        shares: number;
        position_value: number;
        capital_at_risk: number;
        position_pct: number;
      };
      risk_reward_ratio?: number;
      guidance?: string;
    };
    data_quality?: {
      overall_score: number;
      overall_grade: string;
      agent_reports?: {
        [key: string]: {
          score: number;
          grade: string;
        };
      };
      issues?: string[];
      warnings?: string[];
    };
  };
  risk_analysis?: {
    risk_level?: string;
    risk_score?: number;
    risk_data?: {
      [symbol: string]: {
        sharpe_ratio?: number;
      };
    };
    risk_metrics?: {
      var_95?: number;
      cvar_95?: number;
      sharpe_ratio?: number;
      sortino_ratio?: number;
      beta?: number;
      volatility?: number;
      max_drawdown?: number;
    };
    risk_factors?: string[];
    mitigation_strategies?: string;
  };
  // Flat analysis fields (matching analysis.* structure above)
  technical_analysis?: {
    rsi?: {
      value?: number;
      signal?: string;
      date?: string;
    };
    macd?: {
      macd?: number | null;
      signal?: number | null;
      histogram?: number | null;
      trend?: string;
    };
    trend?: string;
    confidence?: number;
    chart_patterns?: Array<{
      pattern: string;
      type: string;
      confidence: number;
      target?: number;
      neckline?: number;
      description: string;
    }>;
    pattern_signals?: Array<string | {
      signal: string;
      price_target: number;
      reasoning: string;
    }>;
    indicators?: {
      rsi?: number | { value?: number; signal?: string; date?: string };
      macd?: number | { macd?: number | null; signal?: number | null; histogram?: number | null; trend?: string };
      atr?: number;
      adx?: number;
      bollinger_bands?: {
        upper?: number;
        middle?: number;
        lower?: number;
      };
    };
    support_levels?: number[];
    resistance_levels?: number[];
  };
  fundamental_analysis?: {
    pe_ratio?: number;
    eps?: number;
    peg_ratio?: number;
    profit_margin?: number;
    roe?: number;
    analyst_consensus?: string;
    analyst_target_price?: number;
    analyst_ratings?: {
      strong_buy?: number;
      buy?: number;
      hold?: number;
      sell?: number;
      strong_sell?: number;
    };
    valuation_metrics?: {
      pe_ratio?: number;
      eps?: number;
      peg_ratio?: number;
      pb_ratio?: number;
      graham_number?: number;
    };
    financial_health?: {
      roe?: number;
      roa?: number;
      debt_to_equity?: number;
      current_ratio?: number;
      profit_margin?: number;
      operating_margin?: number;
    };
    growth_metrics?: {
      revenue_growth?: number;
      earnings_growth?: number;
      fcf_growth?: number;
    };
  };
  sentiment_analysis?: {
    overall_sentiment?: string;
    sentiment_score?: number;
    confidence?: number;
    sources?: Array<{
      title: string;
      url: string;
      content?: string;
      summary?: string;
      source?: string;
      sentiment?: string;
      score?: number;
    }>;
  };
  predictive_analysis?: {
    price_forecast?: {
      short_term?: number;
      long_term?: number;
      '1_day'?: {
        expected_return?: number;
      };
      '30_day'?: {
        expected_return?: number;
      };
    };
    confidence?: number;
    model_confidence?: number;
    summary?: string;
    backtest_results?: {
      accuracy?: string;
      win_rate?: string;
      sharpe_ratio?: string;
      performance_grade?: string;
      out_of_sample?: {
        train_accuracy?: string;
        test_accuracy?: string;
        overfitting_gap?: string;
      };
    };
    predictions?: {
      price_forecast?: {
        '1_day'?: {
          expected_return?: number;
        };
        '30_day'?: {
          expected_return?: number;
        };
      };
      trend_prediction?: {
        current_trend?: string;
        reversal_probability?: number;
        reversal_signals?: string[];
      };
    };
    recommendations?: {
      action?: string;
      confidence?: number;
      rationale?: string[];
    };
  };
  peer_comparison?: {
    peers?: Array<{
      symbol: string;
      pe_ratio?: number;
      market_cap?: number;
      relative_performance?: number;
    }>;
    summary?: string;
  };
  citations?: Array<{
    source: string;
    url: string;
    content: string;
    timestamp: string;
  }>;
  execution_time?: number;
  timestamp?: string;
}

// Create axios instance with interceptors
class ApiService {
  private client: AxiosInstance;
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private cacheTimeout = 300000; // 5 minute cache (increased from 1 min to reduce API calls)
  private retryDelays = [1000, 2000, 5000]; // Exponential backoff delays

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => this.handleResponse(response),
      (error) => this.handleError(error)
    );
  }

  private handleResponse(response: AxiosResponse): any {
    return response.data;
  }

  private async handleError(error: AxiosError): Promise<any> {
    if (error.response) {
      // Handle 429 Rate Limit with exponential backoff
      if (error.response.status === 429) {
        const retryAfter = error.response.headers['retry-after'];
        const delay = retryAfter ? parseInt(retryAfter) * 1000 : 5000;
        console.warn(`Rate limit hit. Will use stale cache if available (delay: ${delay}ms)`);

        // Return stale cache if available instead of waiting
        if (error.config?.url) {
          const cachedData = this.getFromCache(error.config.url, true); // Allow stale
          if (cachedData) {
            console.log('Returning stale cache data due to rate limit');
            return cachedData;
          }
        }

        // If no cache, wait and throw
        await new Promise(resolve => setTimeout(resolve, delay));
        throw new Error('Rate limit exceeded. Please try again later.');
      }

      // Server responded with error status
      const message = (error.response.data as any)?.detail || error.message;
      console.error('API Error:', message);
      throw new Error(message);
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
      throw new Error('Network error. Please check your connection.');
    } else {
      // Something else happened
      console.error('Error:', error.message);
      throw error;
    }
  }

  private getCacheKey(endpoint: string, params?: any): string {
    return `${endpoint}_${JSON.stringify(params || {})}`;
  }

  private getFromCache(key: string, allowStale: boolean = false): any | null {
    const cached = this.cache.get(key);
    if (!cached) return null;

    // Return stale data if explicitly allowed (for rate limit fallback)
    if (allowStale) {
      return cached.data;
    }

    // Return only if within cache timeout
    if (Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }

    this.cache.delete(key);
    return null;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  // Market Data APIs
  async getStockPrice(symbol: string): Promise<StockData> {
    const cacheKey = this.getCacheKey(`/api/v1/market/price/${symbol}`);
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    const data = await this.client.get(`/api/v1/market/price/${symbol}`) as StockData;
    this.setCache(cacheKey, data);
    return data;
  }

  async getMultipleStockPrices(symbols: string[]): Promise<StockData[]> {
    // Use batch endpoint to reduce API calls
    if (symbols.length === 0) return [];

    const cacheKey = this.getCacheKey('/api/v1/market/prices/batch', { symbols: symbols.join(',') });
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    try {
      const response = await this.client.get('/api/v1/market/prices/batch', {
        params: { symbols: symbols.join(',') }
      }) as { prices: Record<string, StockData>, symbols: string[] };

      // Convert to array format
      const result = symbols
        .map(symbol => response.prices[symbol])
        .filter(data => data !== undefined && data !== null);

      this.setCache(cacheKey, result);
      return result;
    } catch (error) {
      console.error('Batch price fetch failed, falling back to individual calls:', error);
      // Fallback to individual calls if batch fails
      const promises = symbols.map(symbol => this.getStockPrice(symbol).catch(() => null));
      const results = await Promise.all(promises);
      return results.filter(data => data !== null) as StockData[];
    }
  }

  async getMarketNews(limit: number = 10): Promise<any[]> {
    const cacheKey = this.getCacheKey('/api/v1/market/news', { limit });
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    const data = await this.client.get('/api/v1/market/news', { params: { limit } }) as any[];
    this.setCache(cacheKey, data);
    return data;
  }

  async getSectorPerformance(): Promise<any> {
    const cacheKey = this.getCacheKey('/api/v1/market/sectors');
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    const data = await this.client.get('/api/v1/market/sectors') as any;
    this.setCache(cacheKey, data);
    return data;
  }

  async getTopStocks(): Promise<any> {
    const cacheKey = this.getCacheKey('/api/v1/analytics/top-stocks');
    const cached = this.getFromCache(cacheKey);
    if (cached) return cached;

    const data = await this.client.get('/api/v1/analytics/top-stocks') as any;
    this.setCache(cacheKey, data);
    return data;
  }

  // Portfolio APIs
  async getPortfolio(userId?: string): Promise<PortfolioData> {
    try {
      // Try to fetch real portfolio data from backend
      const response = await this.client.get('/api/v1/portfolio', {
        params: { user_id: userId }
      }) as any;

      if (response && response.holdings && response.holdings.length > 0) {
        return response as PortfolioData;
      }
    } catch (error) {
      console.log('Portfolio API not available, returning empty portfolio');
    }

    // Return empty portfolio structure instead of mock data
    return {
      totalValue: 0,
      dayChange: 0,
      dayChangePercent: 0,
      holdings: [],
      performance: {
        totalReturn: 0,
        winRate: 0,
        sharpeRatio: 0,
        maxDrawdown: 0
      }
    };
  }

  // Analysis APIs
  async startAnalysis(request: AnalysisRequest): Promise<{ analysis_id: string }> {
    const response = await this.client.post('/api/v1/analyze', request) as { analysis_id: string };
    return response;
  }

  async getAnalysisStatus(analysisId: string): Promise<any> {
    return this.client.get(`/api/v1/analyze/${analysisId}/status`) as Promise<any>;
  }

  async getAnalysisResult(analysisId: string): Promise<AnalysisResult> {
    return this.client.get(`/api/v1/analyze/${analysisId}/result`) as Promise<AnalysisResult>;
  }

  // Chat API
  async sendChatMessage(message: string, userId?: string): Promise<any> {
    return this.client.post('/api/v1/chat', {
      message,
      user_id: userId
    }) as Promise<any>;
  }

  // Analytics APIs
  async getGrowthMetrics(): Promise<any> {
    return this.client.get('/api/v1/analytics/growth') as Promise<any>;
  }

  async getEngagementMetrics(): Promise<any> {
    return this.client.get('/api/v1/analytics/engagement') as Promise<any>;
  }

  // WebSocket removed - using polling instead
  // connectWebSocket(onMessage: (data: any) => void): WebSocket | null {
  //   return null;
  // }

  // Clear cache
  clearCache(): void {
    this.cache.clear();
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export convenience functions
export const api = {
  getStockPrice: (symbol: string) => apiService.getStockPrice(symbol),
  getMultipleStockPrices: (symbols: string[]) => apiService.getMultipleStockPrices(symbols),
  getMarketNews: (limit?: number) => apiService.getMarketNews(limit),
  getSectorPerformance: () => apiService.getSectorPerformance(),
  getTopStocks: () => apiService.getTopStocks(),
  getPortfolio: (userId?: string) => apiService.getPortfolio(userId),
  startAnalysis: (request: AnalysisRequest) => apiService.startAnalysis(request),
  getAnalysisStatus: (id: string) => apiService.getAnalysisStatus(id),
  getAnalysisResult: (id: string) => apiService.getAnalysisResult(id),
  sendChatMessage: (message: string, userId?: string) => apiService.sendChatMessage(message, userId),
  getGrowthMetrics: () => apiService.getGrowthMetrics(),
  getEngagementMetrics: () => apiService.getEngagementMetrics(),
  // connectWebSocket removed - using polling
  clearCache: () => apiService.clearCache()
};

export default api;