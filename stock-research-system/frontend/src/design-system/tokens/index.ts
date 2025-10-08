// Unified Design Token System - CRED-Inspired Premium Design
export const designTokens = {
  // Spacing System - 4px base unit
  spacing: {
    0: '0',
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    5: '20px',
    6: '24px',
    7: '28px',
    8: '32px',
    10: '40px',
    12: '48px',
    16: '64px',
    20: '80px',
    24: '96px',
    32: '128px',
  },

  // Typography Scale - Modular Scale 1.25
  typography: {
    fontFamily: {
      sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      mono: 'JetBrains Mono, "SF Mono", Consolas, monospace',
    },
    fontSize: {
      '2xs': '10px',
      xs: '12px',
      sm: '14px',
      base: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px',
      '3xl': '30px',
      '4xl': '36px',
      '5xl': '48px',
      '6xl': '60px',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
      black: 900,
    },
    lineHeight: {
      none: 1,
      tight: 1.25,
      snug: 1.375,
      normal: 1.5,
      relaxed: 1.625,
      loose: 2,
    },
  },

  // Color System - CRED Premium Palette
  colors: {
    // Brand Colors
    brand: {
      gold: '#D4AF37',
      goldLight: '#F7DC6F',
      goldDark: '#B8941F',
      black: '#000000',
      white: '#FFFFFF',
    },

    // Semantic Colors
    semantic: {
      success: '#00D4AA',
      successLight: '#40E0D0',
      successDark: '#00A88A',

      danger: '#FF453A',
      dangerLight: '#FF6B6B',
      dangerDark: '#CC3628',

      warning: '#FF9F0A',
      warningLight: '#FFBF40',
      warningDark: '#CC7F08',

      info: '#5AC8FA',
      infoLight: '#8DD8FC',
      infoDark: '#48A2C8',
    },

    // Trading Specific
    trading: {
      bullish: '#00D4AA',
      bearish: '#FF453A',
      neutral: '#8E8E93',
    },

    // Background Colors
    background: {
      primary: '#000000',
      secondary: '#0A0A0A',
      tertiary: '#141414',
      elevated: '#1C1C1E',
      card: '#242426',
      overlay: 'rgba(0, 0, 0, 0.85)',
      glass: 'rgba(255, 255, 255, 0.04)',
      glassHeavy: 'rgba(255, 255, 255, 0.08)',
    },

    // Text Colors
    text: {
      primary: '#FFFFFF',
      secondary: '#A8A8A8',
      tertiary: '#6B6B6B',
      disabled: '#3A3A3A',
      inverse: '#000000',
    },

    // Border Colors
    border: {
      default: 'rgba(255, 255, 255, 0.08)',
      light: 'rgba(255, 255, 255, 0.06)',
      medium: 'rgba(255, 255, 255, 0.12)',
      heavy: 'rgba(255, 255, 255, 0.16)',
      gold: 'rgba(212, 175, 55, 0.3)',
    },
  },

  // Border Radius
  borderRadius: {
    none: '0',
    sm: '4px',
    default: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '32px',
    full: '9999px',
  },

  // Shadows
  shadows: {
    none: 'none',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
    default: '0 2px 4px 0 rgba(0, 0, 0, 0.35)',
    md: '0 4px 8px 0 rgba(0, 0, 0, 0.4)',
    lg: '0 8px 16px 0 rgba(0, 0, 0, 0.45)',
    xl: '0 12px 24px 0 rgba(0, 0, 0, 0.5)',
    '2xl': '0 20px 40px 0 rgba(0, 0, 0, 0.6)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.3)',

    // Glow Effects
    glowGold: '0 0 20px rgba(212, 175, 55, 0.4)',
    glowGoldStrong: '0 0 40px rgba(212, 175, 55, 0.6)',
    glowSuccess: '0 0 20px rgba(0, 212, 170, 0.4)',
    glowDanger: '0 0 20px rgba(255, 69, 58, 0.4)',
  },

  // Animation
  animation: {
    duration: {
      instant: '0ms',
      fast: '150ms',
      normal: '250ms',
      slow: '350ms',
      slower: '500ms',
      slowest: '1000ms',
    },
    easing: {
      linear: 'linear',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
    },
  },

  // Breakpoints
  breakpoints: {
    xs: '375px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
    '3xl': '1920px',
  },

  // Z-Index Scale
  zIndex: {
    hide: -1,
    base: 0,
    dropdown: 1000,
    sticky: 1100,
    fixed: 1200,
    overlay: 1300,
    modal: 1400,
    popover: 1500,
    tooltip: 1600,
    toast: 1700,
    maximum: 9999,
  },

  // Layout
  layout: {
    headerHeight: '72px',
    headerHeightMobile: '60px',
    sidebarWidth: '280px',
    sidebarWidthCollapsed: '80px',
    contentMaxWidth: '1440px',
    containerPadding: '24px',
    containerPaddingMobile: '16px',
  },
} as const;

export type DesignTokens = typeof designTokens;

// Helper function to get CSS variables
export const getCSSVariable = (path: string): string => {
  const keys = path.split('.');
  let value: any = designTokens;

  for (const key of keys) {
    value = value[key];
    if (!value) return '';
  }

  return String(value);
};

// Generate CSS custom properties
export const generateCSSVariables = (): string => {
  const cssVars: string[] = [];

  const processObject = (obj: any, prefix: string = '') => {
    Object.entries(obj).forEach(([key, value]) => {
      const varName = prefix ? `${prefix}-${key}` : key;

      if (typeof value === 'object' && !Array.isArray(value)) {
        processObject(value, varName);
      } else {
        cssVars.push(`--${varName}: ${value};`);
      }
    });
  };

  processObject(designTokens);
  return cssVars.join('\n  ');
};