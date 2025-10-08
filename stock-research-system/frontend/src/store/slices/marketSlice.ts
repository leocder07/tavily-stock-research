import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

interface StockPrice {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  dayHigh: number;
  dayLow: number;
  timestamp: string;
}

interface MarketOverview {
  indices: Array<{
    name: string;
    value: number;
    change: number;
    changePercent: number;
  }>;
  sectors: Array<{
    name: string;
    change: number;
  }>;
  timestamp: string;
}

interface MarketNews {
  title: string;
  summary: string;
  url: string;
  source: string;
  published: string;
  relevance_score: number;
}

interface MarketState {
  stocks: Record<string, StockPrice>;
  overview: MarketOverview | null;
  news: MarketNews[];
  loading: boolean;
  error: string | null;
  lastUpdate: string | null;
}

const initialState: MarketState = {
  stocks: {},
  overview: null,
  news: [],
  loading: false,
  error: null,
  lastUpdate: null,
};

// Async thunks
export const fetchStockPrice = createAsyncThunk(
  'market/fetchStockPrice',
  async (symbol: string) => {
    const response = await axios.get(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/market/stock/${symbol}`);
    return response.data;
  }
);

export const fetchMarketOverview = createAsyncThunk(
  'market/fetchMarketOverview',
  async () => {
    const response = await axios.get(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/market/overview`);
    return response.data;
  }
);

export const fetchMarketNews = createAsyncThunk(
  'market/fetchMarketNews',
  async (symbols: string[]) => {
    const response = await axios.post(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/market/news`, {
      symbols,
      limit: 10
    });
    return response.data;
  }
);

export const fetchBatchPrices = createAsyncThunk(
  'market/fetchBatchPrices',
  async (symbols: string[]) => {
    const response = await axios.post(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/market/batch-prices`, {
      symbols
    });
    return response.data;
  }
);

const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    updateStockPrice: (state, action: PayloadAction<StockPrice>) => {
      state.stocks[action.payload.symbol] = action.payload;
      state.lastUpdate = new Date().toISOString();
    },
    updateMarketOverview: (state, action: PayloadAction<MarketOverview>) => {
      state.overview = action.payload;
      state.lastUpdate = new Date().toISOString();
    },
    addNews: (state, action: PayloadAction<MarketNews[]>) => {
      state.news = [...action.payload, ...state.news].slice(0, 50); // Keep latest 50
      state.lastUpdate = new Date().toISOString();
    },
    clearError: (state) => {
      state.error = null;
    },
    updateFromWebSocket: (state, action: PayloadAction<any>) => {
      const { type, data } = action.payload;
      
      switch (type) {
        case 'market_update':
          if (data.symbol && data.price) {
            state.stocks[data.symbol] = {
              ...state.stocks[data.symbol],
              ...data,
              timestamp: new Date().toISOString()
            };
          }
          break;
        case 'sector_update':
          if (state.overview && data.sectors) {
            state.overview.sectors = data.sectors;
          }
          break;
        case 'news_update':
          if (data.news && Array.isArray(data.news)) {
            state.news = [...data.news, ...state.news].slice(0, 50);
          }
          break;
      }
      state.lastUpdate = new Date().toISOString();
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch stock price
      .addCase(fetchStockPrice.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStockPrice.fulfilled, (state, action) => {
        state.loading = false;
        state.stocks[action.payload.symbol] = action.payload;
        state.lastUpdate = new Date().toISOString();
      })
      .addCase(fetchStockPrice.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch stock price';
      })
      // Fetch market overview
      .addCase(fetchMarketOverview.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMarketOverview.fulfilled, (state, action) => {
        state.loading = false;
        state.overview = action.payload;
        state.lastUpdate = new Date().toISOString();
      })
      .addCase(fetchMarketOverview.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch market overview';
      })
      // Fetch market news
      .addCase(fetchMarketNews.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMarketNews.fulfilled, (state, action) => {
        state.loading = false;
        state.news = action.payload;
        state.lastUpdate = new Date().toISOString();
      })
      .addCase(fetchMarketNews.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch market news';
      })
      // Fetch batch prices
      .addCase(fetchBatchPrices.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBatchPrices.fulfilled, (state, action) => {
        state.loading = false;
        Object.entries(action.payload).forEach(([symbol, data]) => {
          state.stocks[symbol] = data as StockPrice;
        });
        state.lastUpdate = new Date().toISOString();
      })
      .addCase(fetchBatchPrices.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch batch prices';
      });
  },
});

export const { 
  updateStockPrice, 
  updateMarketOverview, 
  addNews, 
  clearError,
  updateFromWebSocket 
} = marketSlice.actions;

export default marketSlice.reducer;