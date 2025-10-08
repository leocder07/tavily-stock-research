import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

interface Position {
  symbol: string;
  quantity: number;
  averageCost: number;
  currentPrice: number;
  value: number;
  gain: number;
  gainPercent: number;
  dayChange: number;
  dayChangePercent: number;
}

interface Portfolio {
  id: string;
  name: string;
  totalValue: number;
  totalCost: number;
  totalGain: number;
  totalGainPercent: number;
  dayChange: number;
  dayChangePercent: number;
  positions: Position[];
  cash: number;
  lastUpdated: string;
}

interface Transaction {
  id: string;
  type: 'BUY' | 'SELL';
  symbol: string;
  quantity: number;
  price: number;
  total: number;
  timestamp: string;
  portfolioId: string;
}

interface PortfolioState {
  portfolios: Portfolio[];
  activePortfolioId: string | null;
  transactions: Transaction[];
  performance: {
    daily: Array<{ date: string; value: number }>;
    monthly: Array<{ month: string; value: number }>;
  };
  loading: boolean;
  error: string | null;
}

const initialState: PortfolioState = {
  portfolios: [],
  activePortfolioId: null,
  transactions: [],
  performance: {
    daily: [],
    monthly: [],
  },
  loading: false,
  error: null,
};

// Async thunks
export const fetchPortfolios = createAsyncThunk(
  'portfolio/fetchPortfolios',
  async () => {
    const response = await axios.get(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/portfolio`);
    return response.data;
  }
);

export const createPortfolio = createAsyncThunk(
  'portfolio/createPortfolio',
  async (data: { name: string; initialCash: number }) => {
    const response = await axios.post(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/portfolio`, data);
    return response.data;
  }
);

export const addPosition = createAsyncThunk(
  'portfolio/addPosition',
  async (data: { portfolioId: string; symbol: string; quantity: number; price: number }) => {
    const response = await axios.post(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/portfolio/${data.portfolioId}/position`,
      data
    );
    return response.data;
  }
);

export const sellPosition = createAsyncThunk(
  'portfolio/sellPosition',
  async (data: { portfolioId: string; symbol: string; quantity: number; price: number }) => {
    const response = await axios.post(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/portfolio/${data.portfolioId}/sell`,
      data
    );
    return response.data;
  }
);

export const fetchTransactions = createAsyncThunk(
  'portfolio/fetchTransactions',
  async (portfolioId: string) => {
    const response = await axios.get(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/portfolio/${portfolioId}/transactions`
    );
    return response.data;
  }
);

export const fetchPortfolioPerformance = createAsyncThunk(
  'portfolio/fetchPerformance',
  async (portfolioId: string) => {
    const response = await axios.get(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/portfolio/${portfolioId}/performance`
    );
    return response.data;
  }
);

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    setActivePortfolio: (state, action: PayloadAction<string>) => {
      state.activePortfolioId = action.payload;
    },
    updatePortfolioValue: (state, action: PayloadAction<{ portfolioId: string; value: number }>) => {
      const portfolio = state.portfolios.find(p => p.id === action.payload.portfolioId);
      if (portfolio) {
        portfolio.totalValue = action.payload.value;
        portfolio.totalGain = action.payload.value - portfolio.totalCost;
        portfolio.totalGainPercent = (portfolio.totalGain / portfolio.totalCost) * 100;
        portfolio.lastUpdated = new Date().toISOString();
      }
    },
    updatePositionPrice: (state, action: PayloadAction<{ portfolioId: string; symbol: string; price: number }>) => {
      const portfolio = state.portfolios.find(p => p.id === action.payload.portfolioId);
      if (portfolio) {
        const position = portfolio.positions.find(p => p.symbol === action.payload.symbol);
        if (position) {
          position.currentPrice = action.payload.price;
          position.value = position.quantity * action.payload.price;
          position.gain = position.value - (position.quantity * position.averageCost);
          position.gainPercent = (position.gain / (position.quantity * position.averageCost)) * 100;
        }
      }
    },
    updateFromWebSocket: (state, action: PayloadAction<any>) => {
      const { type, data } = action.payload;
      
      if (type === 'portfolio_update' && data.portfolioId) {
        const portfolio = state.portfolios.find(p => p.id === data.portfolioId);
        if (portfolio) {
          Object.assign(portfolio, data.portfolio);
        }
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch portfolios
      .addCase(fetchPortfolios.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPortfolios.fulfilled, (state, action) => {
        state.loading = false;
        state.portfolios = action.payload;
        if (!state.activePortfolioId && action.payload.length > 0) {
          state.activePortfolioId = action.payload[0].id;
        }
      })
      .addCase(fetchPortfolios.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch portfolios';
      })
      // Create portfolio
      .addCase(createPortfolio.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createPortfolio.fulfilled, (state, action) => {
        state.loading = false;
        state.portfolios.push(action.payload);
        state.activePortfolioId = action.payload.id;
      })
      .addCase(createPortfolio.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to create portfolio';
      })
      // Add position
      .addCase(addPosition.fulfilled, (state, action) => {
        const portfolio = state.portfolios.find(p => p.id === action.payload.portfolioId);
        if (portfolio) {
          const existingPosition = portfolio.positions.find(p => p.symbol === action.payload.symbol);
          if (existingPosition) {
            // Update existing position
            const totalCost = (existingPosition.averageCost * existingPosition.quantity) + 
                            (action.payload.price * action.payload.quantity);
            const totalQuantity = existingPosition.quantity + action.payload.quantity;
            existingPosition.quantity = totalQuantity;
            existingPosition.averageCost = totalCost / totalQuantity;
          } else {
            // Add new position
            portfolio.positions.push(action.payload.position);
          }
        }
      })
      // Sell position
      .addCase(sellPosition.fulfilled, (state, action) => {
        const portfolio = state.portfolios.find(p => p.id === action.payload.portfolioId);
        if (portfolio) {
          const position = portfolio.positions.find(p => p.symbol === action.payload.symbol);
          if (position) {
            position.quantity -= action.payload.quantity;
            if (position.quantity <= 0) {
              portfolio.positions = portfolio.positions.filter(p => p.symbol !== action.payload.symbol);
            }
          }
          portfolio.cash += action.payload.total;
        }
      })
      // Fetch transactions
      .addCase(fetchTransactions.fulfilled, (state, action) => {
        state.transactions = action.payload;
      })
      // Fetch performance
      .addCase(fetchPortfolioPerformance.fulfilled, (state, action) => {
        state.performance = action.payload;
      });
  },
});

export const { 
  setActivePortfolio, 
  updatePortfolioValue, 
  updatePositionPrice,
  updateFromWebSocket,
  clearError 
} = portfolioSlice.actions;

export default portfolioSlice.reducer;