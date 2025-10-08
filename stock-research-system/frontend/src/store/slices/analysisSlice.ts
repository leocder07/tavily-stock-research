import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

interface AnalysisResult {
  id: string;
  symbol: string;
  type: 'fundamental' | 'technical' | 'sentiment' | 'comprehensive';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  result?: {
    summary: string;
    score: number;
    recommendation: 'strong_buy' | 'buy' | 'hold' | 'sell' | 'strong_sell';
    insights: Array<{
      type: string;
      title: string;
      description: string;
      importance: 'high' | 'medium' | 'low';
    }>;
    metrics: Record<string, any>;
    risks: string[];
    opportunities: string[];
  };
  error?: string;
  startTime: string;
  endTime?: string;
}

interface AISignal {
  id: string;
  symbol: string;
  type: 'entry' | 'exit' | 'alert';
  strength: number;
  message: string;
  reasoning: string;
  timestamp: string;
  confidence: number;
  action?: {
    type: 'buy' | 'sell' | 'hold';
    quantity?: number;
    price?: number;
  };
}

interface AnalysisState {
  analyses: Record<string, AnalysisResult>;
  activeAnalysis: string | null;
  aiSignals: AISignal[];
  recentSearches: string[];
  loading: boolean;
  error: string | null;
}

const initialState: AnalysisState = {
  analyses: {},
  activeAnalysis: null,
  aiSignals: [],
  recentSearches: [],
  loading: false,
  error: null,
};

// Async thunks
export const startAnalysis = createAsyncThunk(
  'analysis/start',
  async (params: { symbol: string; type: string; depth?: string }) => {
    const response = await axios.post(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/analyze`,
      params
    );
    return response.data;
  }
);

export const fetchAnalysisStatus = createAsyncThunk(
  'analysis/fetchStatus',
  async (analysisId: string) => {
    const response = await axios.get(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/analyze/${analysisId}/status`
    );
    return response.data;
  }
);

export const fetchAnalysisResult = createAsyncThunk(
  'analysis/fetchResult',
  async (analysisId: string) => {
    const response = await axios.get(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/analyze/${analysisId}/result`
    );
    return response.data;
  }
);

export const fetchAISignals = createAsyncThunk(
  'analysis/fetchAISignals',
  async (symbols?: string[]) => {
    const url = symbols 
      ? `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/ai-signals?symbols=${symbols.join(',')}`
      : `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/ai-signals`;
    const response = await axios.get(url);
    return response.data;
  }
);

export const generateAIInsights = createAsyncThunk(
  'analysis/generateInsights',
  async (params: { symbol: string; context: string }) => {
    const response = await axios.post(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/ai-insights`,
      params
    );
    return response.data;
  }
);

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setActiveAnalysis: (state, action: PayloadAction<string>) => {
      state.activeAnalysis = action.payload;
    },
    updateAnalysisProgress: (state, action: PayloadAction<{ id: string; progress: number; status?: string }>) => {
      const analysis = state.analyses[action.payload.id];
      if (analysis) {
        analysis.progress = action.payload.progress;
        if (action.payload.status) {
          analysis.status = action.payload.status as any;
        }
      }
    },
    addAISignal: (state, action: PayloadAction<AISignal>) => {
      state.aiSignals.unshift(action.payload);
      // Keep only latest 100 signals
      state.aiSignals = state.aiSignals.slice(0, 100);
    },
    addRecentSearch: (state, action: PayloadAction<string>) => {
      if (!state.recentSearches.includes(action.payload)) {
        state.recentSearches.unshift(action.payload);
        // Keep only latest 10 searches
        state.recentSearches = state.recentSearches.slice(0, 10);
      }
    },
    updateFromWebSocket: (state, action: PayloadAction<any>) => {
      const { type, data } = action.payload;
      
      switch (type) {
        case 'analysis_progress':
          if (data.analysisId && state.analyses[data.analysisId]) {
            state.analyses[data.analysisId].progress = data.progress;
            state.analyses[data.analysisId].status = data.status;
          }
          break;
        case 'analysis_complete':
          if (data.analysisId && state.analyses[data.analysisId]) {
            state.analyses[data.analysisId].status = 'completed';
            state.analyses[data.analysisId].result = data.result;
            state.analyses[data.analysisId].endTime = new Date().toISOString();
          }
          break;
        case 'ai_signal':
          if (data.signal) {
            state.aiSignals.unshift(data.signal);
            state.aiSignals = state.aiSignals.slice(0, 100);
          }
          break;
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Start analysis
      .addCase(startAnalysis.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(startAnalysis.fulfilled, (state, action) => {
        state.loading = false;
        const analysis: AnalysisResult = {
          id: action.payload.analysisId,
          symbol: action.payload.symbol,
          type: action.payload.type,
          status: 'pending',
          progress: 0,
          startTime: new Date().toISOString(),
        };
        state.analyses[analysis.id] = analysis;
        state.activeAnalysis = analysis.id;
        
        // Add to recent searches
        if (!state.recentSearches.includes(action.payload.symbol)) {
          state.recentSearches.unshift(action.payload.symbol);
          state.recentSearches = state.recentSearches.slice(0, 10);
        }
      })
      .addCase(startAnalysis.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to start analysis';
      })
      // Fetch analysis status
      .addCase(fetchAnalysisStatus.fulfilled, (state, action) => {
        const analysis = state.analyses[action.payload.analysisId];
        if (analysis) {
          analysis.status = action.payload.status;
          analysis.progress = action.payload.progress;
        }
      })
      // Fetch analysis result
      .addCase(fetchAnalysisResult.fulfilled, (state, action) => {
        const analysis = state.analyses[action.payload.analysisId];
        if (analysis) {
          analysis.status = 'completed';
          analysis.result = action.payload.result;
          analysis.endTime = new Date().toISOString();
        }
      })
      // Fetch AI signals
      .addCase(fetchAISignals.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAISignals.fulfilled, (state, action) => {
        state.loading = false;
        state.aiSignals = action.payload;
      })
      .addCase(fetchAISignals.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch AI signals';
      })
      // Generate AI insights
      .addCase(generateAIInsights.fulfilled, (state, action) => {
        // Add insights as a new AI signal
        const signal: AISignal = {
          id: Date.now().toString(),
          symbol: action.payload.symbol,
          type: 'alert',
          strength: action.payload.strength || 0.5,
          message: action.payload.message,
          reasoning: action.payload.reasoning,
          timestamp: new Date().toISOString(),
          confidence: action.payload.confidence || 0.7,
        };
        state.aiSignals.unshift(signal);
        state.aiSignals = state.aiSignals.slice(0, 100);
      });
  },
});

export const { 
  setActiveAnalysis,
  updateAnalysisProgress,
  addAISignal,
  addRecentSearch,
  updateFromWebSocket,
  clearError 
} = analysisSlice.actions;

export default analysisSlice.reducer;