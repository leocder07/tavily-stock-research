/**
 * TavilyAI Pro - Theme Configuration
 * Modern color themes for financial intelligence platform
 */

export interface ThemeColors {
  // Background Layers
  bgPrimary: string;
  bgSecondary: string;
  bgTertiary: string;
  bgElevated: string;

  // Brand Colors
  brandPrimary: string;
  brandSecondary: string;
  brandAccent: string;

  // Semantic Colors
  success: string;
  warning: string;
  danger: string;
  info: string;

  // Text Hierarchy
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  textMuted: string;

  // Data Visualization
  chart1: string;
  chart2: string;
  chart3: string;
  chart4: string;
  chart5: string;
  chart6: string;

  // Interactive States
  hover: string;
  active: string;
  focus: string;

  // Borders
  borderSubtle: string;
  borderDefault: string;
  borderStrong: string;

  // Special Effects
  glassBackground: string;
  glassBlur: string;
  shadowColor: string;
  glowColor: string;
}

export interface Theme {
  name: string;
  description: string;
  colors: ThemeColors;
  isDark: boolean;
}

// 1. Midnight Intelligence - Professional Dark Theme
export const midnightTheme: Theme = {
  name: 'Midnight Intelligence',
  description: 'Professional dark theme inspired by Bloomberg Terminal',
  isDark: true,
  colors: {
    // Background Layers
    bgPrimary: '#0A0E1B',
    bgSecondary: '#101624',
    bgTertiary: '#1A2332',
    bgElevated: '#242B3D',

    // Brand Colors
    brandPrimary: '#00D4FF',
    brandSecondary: '#7C3AED',
    brandAccent: '#FFB800',

    // Semantic Colors
    success: '#10B981',
    warning: '#F59E0B',
    danger: '#EF4444',
    info: '#3B82F6',

    // Text Hierarchy
    textPrimary: '#FFFFFF',
    textSecondary: '#94A3B8',
    textTertiary: '#64748B',
    textMuted: '#475569',

    // Data Visualization
    chart1: '#00D4FF',
    chart2: '#7C3AED',
    chart3: '#10B981',
    chart4: '#F59E0B',
    chart5: '#EC4899',
    chart6: '#8B5CF6',

    // Interactive States
    hover: 'rgba(0, 212, 255, 0.1)',
    active: 'rgba(0, 212, 255, 0.2)',
    focus: 'rgba(0, 212, 255, 0.3)',

    // Borders
    borderSubtle: 'rgba(255, 255, 255, 0.06)',
    borderDefault: 'rgba(255, 255, 255, 0.12)',
    borderStrong: 'rgba(255, 255, 255, 0.24)',

    // Special Effects
    glassBackground: 'rgba(255, 255, 255, 0.02)',
    glassBlur: '40px',
    shadowColor: 'rgba(0, 0, 0, 0.3)',
    glowColor: 'rgba(0, 212, 255, 0.5)',
  },
};

// 2. Arctic Light - Clean Professional Light Theme
export const arcticTheme: Theme = {
  name: 'Arctic Light',
  description: 'Clean, professional light theme inspired by Stripe',
  isDark: false,
  colors: {
    // Background Layers
    bgPrimary: '#FFFFFF',
    bgSecondary: '#FAFBFC',
    bgTertiary: '#F6F8FA',
    bgElevated: '#FFFFFF',

    // Brand Colors
    brandPrimary: '#5E2BF7',
    brandSecondary: '#0EA5E9',
    brandAccent: '#F97316',

    // Semantic Colors
    success: '#22C55E',
    warning: '#EAB308',
    danger: '#DC2626',
    info: '#0EA5E9',

    // Text Hierarchy
    textPrimary: '#0F172A',
    textSecondary: '#475569',
    textTertiary: '#94A3B8',
    textMuted: '#CBD5E1',

    // Data Visualization
    chart1: '#5E2BF7',
    chart2: '#0EA5E9',
    chart3: '#22C55E',
    chart4: '#F97316',
    chart5: '#EC4899',
    chart6: '#8B5CF6',

    // Interactive States
    hover: 'rgba(94, 43, 247, 0.05)',
    active: 'rgba(94, 43, 247, 0.1)',
    focus: 'rgba(94, 43, 247, 0.15)',

    // Borders
    borderSubtle: '#F1F5F9',
    borderDefault: '#E2E8F0',
    borderStrong: '#CBD5E1',

    // Special Effects
    glassBackground: 'rgba(255, 255, 255, 0.7)',
    glassBlur: '20px',
    shadowColor: 'rgba(0, 0, 0, 0.1)',
    glowColor: 'rgba(94, 43, 247, 0.3)',
  },
};

// 3. Terminal Green - Hacker Mode Theme
export const terminalTheme: Theme = {
  name: 'Terminal Green',
  description: 'Matrix-inspired theme for power users',
  isDark: true,
  colors: {
    // Background Layers
    bgPrimary: '#000000',
    bgSecondary: '#0A0A0A',
    bgTertiary: '#141414',
    bgElevated: '#1A1A1A',

    // Brand Colors
    brandPrimary: '#00FF41',
    brandSecondary: '#39FF14',
    brandAccent: '#FFFF00',

    // Semantic Colors
    success: '#00FF41',
    warning: '#FFFF00',
    danger: '#FF0000',
    info: '#00FFFF',

    // Text Hierarchy
    textPrimary: '#00FF41',
    textSecondary: '#00CC33',
    textTertiary: '#009926',
    textMuted: '#006619',

    // Data Visualization
    chart1: '#00FF41',
    chart2: '#39FF14',
    chart3: '#FFFF00',
    chart4: '#FF00FF',
    chart5: '#00FFFF',
    chart6: '#FF6600',

    // Interactive States
    hover: 'rgba(0, 255, 65, 0.1)',
    active: 'rgba(0, 255, 65, 0.2)',
    focus: 'rgba(0, 255, 65, 0.3)',

    // Borders
    borderSubtle: 'rgba(0, 255, 65, 0.1)',
    borderDefault: 'rgba(0, 255, 65, 0.2)',
    borderStrong: 'rgba(0, 255, 65, 0.4)',

    // Special Effects
    glassBackground: 'rgba(0, 255, 65, 0.02)',
    glassBlur: '20px',
    shadowColor: 'rgba(0, 255, 65, 0.2)',
    glowColor: 'rgba(0, 255, 65, 0.6)',
  },
};

// 4. Sunset Trading - Warm Professional Theme
export const sunsetTheme: Theme = {
  name: 'Sunset Trading',
  description: 'Warm, comfortable theme for long trading sessions',
  isDark: true,
  colors: {
    // Background Layers
    bgPrimary: '#1A1418',
    bgSecondary: '#251F24',
    bgTertiary: '#2D2530',
    bgElevated: '#362E39',

    // Brand Colors
    brandPrimary: '#FF6B6B',
    brandSecondary: '#4ECDC4',
    brandAccent: '#FFE66D',

    // Semantic Colors
    success: '#4ECDC4',
    warning: '#FFE66D',
    danger: '#FF6B6B',
    info: '#95E1D3',

    // Text Hierarchy
    textPrimary: '#FFF5F5',
    textSecondary: '#FFB8B8',
    textTertiary: '#FF9999',
    textMuted: '#CC7777',

    // Data Visualization
    chart1: '#FF6B6B',
    chart2: '#4ECDC4',
    chart3: '#FFE66D',
    chart4: '#95E1D3',
    chart5: '#FFA502',
    chart6: '#A29BFE',

    // Interactive States
    hover: 'rgba(255, 107, 107, 0.1)',
    active: 'rgba(255, 107, 107, 0.2)',
    focus: 'rgba(255, 107, 107, 0.3)',

    // Borders
    borderSubtle: 'rgba(255, 245, 245, 0.06)',
    borderDefault: 'rgba(255, 245, 245, 0.12)',
    borderStrong: 'rgba(255, 245, 245, 0.24)',

    // Special Effects
    glassBackground: 'rgba(255, 107, 107, 0.02)',
    glassBlur: '30px',
    shadowColor: 'rgba(0, 0, 0, 0.4)',
    glowColor: 'rgba(255, 107, 107, 0.4)',
  },
};

// 5. Ocean Depth - Deep Blue Professional
export const oceanTheme: Theme = {
  name: 'Ocean Depth',
  description: 'Deep blue theme for focused analysis',
  isDark: true,
  colors: {
    // Background Layers
    bgPrimary: '#0B1929',
    bgSecondary: '#112240',
    bgTertiary: '#1B3358',
    bgElevated: '#234570',

    // Brand Colors
    brandPrimary: '#64FFDA',
    brandSecondary: '#7AFFC1',
    brandAccent: '#FFD700',

    // Semantic Colors
    success: '#64FFDA',
    warning: '#FFD700',
    danger: '#FF647C',
    info: '#64B6FF',

    // Text Hierarchy
    textPrimary: '#E6F1FF',
    textSecondary: '#A8B2D1',
    textTertiary: '#8892B0',
    textMuted: '#495670',

    // Data Visualization
    chart1: '#64FFDA',
    chart2: '#7AFFC1',
    chart3: '#FFD700',
    chart4: '#64B6FF',
    chart5: '#FF647C',
    chart6: '#C778DD',

    // Interactive States
    hover: 'rgba(100, 255, 218, 0.1)',
    active: 'rgba(100, 255, 218, 0.2)',
    focus: 'rgba(100, 255, 218, 0.3)',

    // Borders
    borderSubtle: 'rgba(100, 255, 218, 0.06)',
    borderDefault: 'rgba(100, 255, 218, 0.12)',
    borderStrong: 'rgba(100, 255, 218, 0.24)',

    // Special Effects
    glassBackground: 'rgba(100, 255, 218, 0.02)',
    glassBlur: '40px',
    shadowColor: 'rgba(11, 25, 41, 0.5)',
    glowColor: 'rgba(100, 255, 218, 0.5)',
  },
};

// Theme Manager
export class ThemeManager {
  private static instance: ThemeManager;
  private currentTheme: Theme = midnightTheme;
  private themes: Map<string, Theme> = new Map();

  private constructor() {
    // Register all themes
    this.themes.set('midnight', midnightTheme);
    this.themes.set('arctic', arcticTheme);
    this.themes.set('terminal', terminalTheme);
    this.themes.set('sunset', sunsetTheme);
    this.themes.set('ocean', oceanTheme);
  }

  static getInstance(): ThemeManager {
    if (!ThemeManager.instance) {
      ThemeManager.instance = new ThemeManager();
    }
    return ThemeManager.instance;
  }

  getTheme(): Theme {
    return this.currentTheme;
  }

  setTheme(themeName: string): void {
    const theme = this.themes.get(themeName);
    if (theme) {
      this.currentTheme = theme;
      this.applyTheme(theme);
    }
  }

  getAllThemes(): Theme[] {
    return Array.from(this.themes.values());
  }

  private applyTheme(theme: Theme): void {
    const root = document.documentElement;

    // Apply CSS variables
    Object.entries(theme.colors).forEach(([key, value]) => {
      const cssVarName = `--color-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`;
      root.style.setProperty(cssVarName, value);
    });

    // Apply theme class
    document.body.className = theme.isDark ? 'theme-dark' : 'theme-light';
    document.body.setAttribute('data-theme', theme.name.toLowerCase().replace(/\s+/g, '-'));
  }

  // Get computed styles for components
  getComponentStyles() {
    const theme = this.currentTheme;

    return {
      card: {
        background: theme.colors.glassBackground,
        backdropFilter: `blur(${theme.colors.glassBlur})`,
        border: `1px solid ${theme.colors.borderDefault}`,
        borderRadius: '16px',
        boxShadow: `0 10px 40px ${theme.colors.shadowColor}`,
      },
      button: {
        primary: {
          background: `linear-gradient(135deg, ${theme.colors.brandPrimary} 0%, ${theme.colors.brandSecondary} 100%)`,
          color: theme.isDark ? '#FFFFFF' : '#FFFFFF',
          border: 'none',
        },
        secondary: {
          background: theme.colors.bgTertiary,
          color: theme.colors.textPrimary,
          border: `1px solid ${theme.colors.borderDefault}`,
        },
      },
      input: {
        background: theme.colors.bgSecondary,
        border: `1px solid ${theme.colors.borderDefault}`,
        color: theme.colors.textPrimary,
        placeholder: theme.colors.textMuted,
      },
      chart: {
        grid: theme.colors.borderSubtle,
        axis: theme.colors.textTertiary,
        tooltip: {
          background: theme.colors.bgElevated,
          border: theme.colors.borderDefault,
          text: theme.colors.textPrimary,
        },
      },
    };
  }
}

// Export singleton instance
export const themeManager = ThemeManager.getInstance();