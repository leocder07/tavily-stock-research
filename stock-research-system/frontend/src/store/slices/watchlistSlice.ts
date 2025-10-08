import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

interface WatchlistItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  addedAt: string;
  alerts: Alert[];
  notes: string;
}

interface Alert {
  id: string;
  type: 'price_above' | 'price_below' | 'volume_spike' | 'percentage_change';
  condition: number;
  enabled: boolean;
  triggered: boolean;
  lastTriggered?: string;
}

interface Watchlist {
  id: string;
  name: string;
  items: WatchlistItem[];
  createdAt: string;
  updatedAt: string;
}

interface WatchlistState {
  watchlists: Watchlist[];
  activeWatchlistId: string | null;
  alerts: Alert[];
  triggeredAlerts: Array<{
    alert: Alert;
    symbol: string;
    message: string;
    timestamp: string;
  }>;
  loading: boolean;
  error: string | null;
}

const initialState: WatchlistState = {
  watchlists: [],
  activeWatchlistId: null,
  alerts: [],
  triggeredAlerts: [],
  loading: false,
  error: null,
};

// Async thunks
export const fetchWatchlists = createAsyncThunk(
  'watchlist/fetchAll',
  async () => {
    const response = await axios.get(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/watchlists`);
    return response.data;
  }
);

export const createWatchlist = createAsyncThunk(
  'watchlist/create',
  async (data: { name: string; symbols?: string[] }) => {
    const response = await axios.post(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/watchlists`, data);
    return response.data;
  }
);

export const addToWatchlist = createAsyncThunk(
  'watchlist/addSymbol',
  async (data: { watchlistId: string; symbol: string; notes?: string }) => {
    const response = await axios.post(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/watchlists/${data.watchlistId}/symbols`,
      data
    );
    return response.data;
  }
);

export const removeFromWatchlist = createAsyncThunk(
  'watchlist/removeSymbol',
  async (data: { watchlistId: string; symbol: string }) => {
    const response = await axios.delete(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/watchlists/${data.watchlistId}/symbols/${data.symbol}`
    );
    return { ...response.data, symbol: data.symbol, watchlistId: data.watchlistId };
  }
);

export const createAlert = createAsyncThunk(
  'watchlist/createAlert',
  async (data: { 
    watchlistId: string; 
    symbol: string; 
    type: Alert['type']; 
    condition: number 
  }) => {
    const response = await axios.post(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/watchlists/${data.watchlistId}/alerts`,
      data
    );
    return response.data;
  }
);

export const toggleAlert = createAsyncThunk(
  'watchlist/toggleAlert',
  async (data: { alertId: string; enabled: boolean }) => {
    const response = await axios.patch(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/alerts/${data.alertId}`,
      { enabled: data.enabled }
    );
    return response.data;
  }
);

const watchlistSlice = createSlice({
  name: 'watchlist',
  initialState,
  reducers: {
    setActiveWatchlist: (state, action: PayloadAction<string>) => {
      state.activeWatchlistId = action.payload;
    },
    updateWatchlistItem: (state, action: PayloadAction<{ 
      watchlistId: string; 
      symbol: string; 
      data: Partial<WatchlistItem> 
    }>) => {
      const watchlist = state.watchlists.find(w => w.id === action.payload.watchlistId);
      if (watchlist) {
        const item = watchlist.items.find(i => i.symbol === action.payload.symbol);
        if (item) {
          Object.assign(item, action.payload.data);
          watchlist.updatedAt = new Date().toISOString();
        }
      }
    },
    addTriggeredAlert: (state, action: PayloadAction<{
      alert: Alert;
      symbol: string;
      message: string;
    }>) => {
      state.triggeredAlerts.unshift({
        ...action.payload,
        timestamp: new Date().toISOString(),
      });
      // Keep only latest 50 triggered alerts
      state.triggeredAlerts = state.triggeredAlerts.slice(0, 50);
    },
    clearTriggeredAlerts: (state) => {
      state.triggeredAlerts = [];
    },
    updateFromWebSocket: (state, action: PayloadAction<any>) => {
      const { type, data } = action.payload;
      
      if (type === 'watchlist_update') {
        // Update watchlist items with real-time price data
        state.watchlists.forEach(watchlist => {
          watchlist.items.forEach(item => {
            if (data[item.symbol]) {
              item.price = data[item.symbol].price;
              item.change = data[item.symbol].change;
              item.changePercent = data[item.symbol].changePercent;
              item.volume = data[item.symbol].volume;
            }
          });
        });
      } else if (type === 'alert_triggered') {
        state.triggeredAlerts.unshift({
          alert: data.alert,
          symbol: data.symbol,
          message: data.message,
          timestamp: new Date().toISOString(),
        });
        state.triggeredAlerts = state.triggeredAlerts.slice(0, 50);
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch watchlists
      .addCase(fetchWatchlists.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchWatchlists.fulfilled, (state, action) => {
        state.loading = false;
        state.watchlists = action.payload;
        if (!state.activeWatchlistId && action.payload.length > 0) {
          state.activeWatchlistId = action.payload[0].id;
        }
      })
      .addCase(fetchWatchlists.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch watchlists';
      })
      // Create watchlist
      .addCase(createWatchlist.fulfilled, (state, action) => {
        state.watchlists.push(action.payload);
        state.activeWatchlistId = action.payload.id;
      })
      // Add to watchlist
      .addCase(addToWatchlist.fulfilled, (state, action) => {
        const watchlist = state.watchlists.find(w => w.id === action.payload.watchlistId);
        if (watchlist) {
          watchlist.items.push(action.payload.item);
          watchlist.updatedAt = new Date().toISOString();
        }
      })
      // Remove from watchlist
      .addCase(removeFromWatchlist.fulfilled, (state, action) => {
        const watchlist = state.watchlists.find(w => w.id === action.payload.watchlistId);
        if (watchlist) {
          watchlist.items = watchlist.items.filter(i => i.symbol !== action.payload.symbol);
          watchlist.updatedAt = new Date().toISOString();
        }
      })
      // Create alert
      .addCase(createAlert.fulfilled, (state, action) => {
        state.alerts.push(action.payload);
        const watchlist = state.watchlists.find(w => w.id === action.payload.watchlistId);
        if (watchlist) {
          const item = watchlist.items.find(i => i.symbol === action.payload.symbol);
          if (item) {
            item.alerts.push(action.payload);
          }
        }
      })
      // Toggle alert
      .addCase(toggleAlert.fulfilled, (state, action) => {
        const alert = state.alerts.find(a => a.id === action.payload.alertId);
        if (alert) {
          alert.enabled = action.payload.enabled;
        }
      });
  },
});

export const { 
  setActiveWatchlist,
  updateWatchlistItem,
  addTriggeredAlert,
  clearTriggeredAlerts,
  updateFromWebSocket,
  clearError 
} = watchlistSlice.actions;

export default watchlistSlice.reducer;