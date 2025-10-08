import { configureStore } from '@reduxjs/toolkit';
import marketReducer from './slices/marketSlice';
import portfolioReducer from './slices/portfolioSlice';
import analysisReducer from './slices/analysisSlice';
import watchlistReducer from './slices/watchlistSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    market: marketReducer,
    portfolio: portfolioReducer,
    analysis: analysisReducer,
    watchlist: watchlistReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these field paths in all actions
        ignoredActionPaths: ['payload.timestamp', 'payload.date'],
        // Ignore these paths in the state
        ignoredPaths: ['market.lastUpdate', 'analysis.startTime'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;