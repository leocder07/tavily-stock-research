import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  timestamp: string;
}

interface Modal {
  id: string;
  type: string;
  props?: any;
  isOpen: boolean;
}

interface UIState {
  theme: 'dark' | 'light';
  sidebarCollapsed: boolean;
  activeTab: string;
  notifications: Notification[];
  modals: Modal[];
  loading: {
    global: boolean;
    [key: string]: boolean;
  };
  preferences: {
    autoRefresh: boolean;
    refreshInterval: number;
    showNotifications: boolean;
    soundEnabled: boolean;
    compactView: boolean;
    chartType: 'line' | 'candlestick' | 'area';
    timeframe: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL';
  };
}

const initialState: UIState = {
  theme: 'dark',
  sidebarCollapsed: false,
  activeTab: 'dashboard',
  notifications: [],
  modals: [],
  loading: {
    global: false,
  },
  preferences: {
    autoRefresh: true,
    refreshInterval: 30000, // 30 seconds
    showNotifications: true,
    soundEnabled: false,
    compactView: false,
    chartType: 'line',
    timeframe: '1D',
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleTheme: (state) => {
      state.theme = state.theme === 'dark' ? 'light' : 'dark';
    },
    setTheme: (state, action: PayloadAction<'dark' | 'light'>) => {
      state.theme = action.payload;
    },
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
    setActiveTab: (state, action: PayloadAction<string>) => {
      state.activeTab = action.payload;
    },
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
      };
      state.notifications.unshift(notification);
      
      // Keep only latest 10 notifications
      state.notifications = state.notifications.slice(0, 10);
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    openModal: (state, action: PayloadAction<Omit<Modal, 'isOpen'>>) => {
      const modal: Modal = {
        ...action.payload,
        isOpen: true,
      };
      state.modals.push(modal);
    },
    closeModal: (state, action: PayloadAction<string>) => {
      state.modals = state.modals.filter(m => m.id !== action.payload);
    },
    closeAllModals: (state) => {
      state.modals = [];
    },
    setLoading: (state, action: PayloadAction<{ key: string; value: boolean }>) => {
      state.loading[action.payload.key] = action.payload.value;
    },
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.global = action.payload;
    },
    updatePreference: (state, action: PayloadAction<Partial<UIState['preferences']>>) => {
      state.preferences = {
        ...state.preferences,
        ...action.payload,
      };
    },
    setChartType: (state, action: PayloadAction<UIState['preferences']['chartType']>) => {
      state.preferences.chartType = action.payload;
    },
    setTimeframe: (state, action: PayloadAction<UIState['preferences']['timeframe']>) => {
      state.preferences.timeframe = action.payload;
    },
    toggleAutoRefresh: (state) => {
      state.preferences.autoRefresh = !state.preferences.autoRefresh;
    },
    toggleNotifications: (state) => {
      state.preferences.showNotifications = !state.preferences.showNotifications;
    },
    toggleSound: (state) => {
      state.preferences.soundEnabled = !state.preferences.soundEnabled;
    },
    toggleCompactView: (state) => {
      state.preferences.compactView = !state.preferences.compactView;
    },
  },
});

export const {
  toggleTheme,
  setTheme,
  toggleSidebar,
  setSidebarCollapsed,
  setActiveTab,
  addNotification,
  removeNotification,
  clearNotifications,
  openModal,
  closeModal,
  closeAllModals,
  setLoading,
  setGlobalLoading,
  updatePreference,
  setChartType,
  setTimeframe,
  toggleAutoRefresh,
  toggleNotifications,
  toggleSound,
  toggleCompactView,
} = uiSlice.actions;

export default uiSlice.reducer;