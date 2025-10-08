// CRED-inspired Design System
export const theme = {
  colors: {
    // Primary palette - Modern premium colors
    primary: '#00D9FF', // Electric cyan - modern and premium
    secondary: '#1C1C1E', // Premium black
    success: '#00D4AA', // Emerald green for profits
    danger: '#FF453A', // Vibrant red for losses
    warning: '#FF9F0A', // Orange for caution

    // Dark theme - CRED's premium black
    background: {
      primary: '#000000', // Pure black like CRED
      secondary: '#1C1C1E', // CRED's signature black
      elevated: '#2C2C2E', // Elevated surfaces
      overlay: 'rgba(0, 0, 0, 0.8)',
    },
    
    // Text hierarchy
    text: {
      primary: '#FFFFFF',
      secondary: '#8E8E93', // iOS-style secondary text
      muted: '#636366', // Subtle text
      inverse: '#000000',
    },

    // Trading specific
    bullish: '#00D4AA', // CRED-style emerald
    bearish: '#FF453A', // CRED-style red
    neutral: '#8E8E93', // Neutral gray

    // Additional colors
    error: '#FF453A', // Error red (same as danger)
    accent: '#AF52DE', // Purple accent
    border: 'rgba(255, 255, 255, 0.1)', // Default border color

    // Gradients - Modern premium feel
    gradient: {
      primary: 'linear-gradient(135deg, #00D9FF 0%, #00F0FF 100%)', // Cyan gradient
      success: 'linear-gradient(135deg, #00D4AA 0%, #40E0D0 100%)', // Emerald gradient
      danger: 'linear-gradient(135deg, #FF453A 0%, #FF6B6B 100%)', // Red gradient
      cyan: 'linear-gradient(135deg, #00D9FF 0%, #00F5FF 100%)', // Electric cyan
      glass: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)', // Glass morphism
    },
  },
  
  typography: {
    fontFamily: {
      primary: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif',
      mono: 'SF Mono, Monaco, "Courier New", monospace',
    },
    fontSize: {
      xs: '12px',
      sm: '14px',
      base: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px',
      '3xl': '32px',
      '4xl': '48px',
    },
    fontWeight: {
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      black: 900,
    },
  },
  
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
  },
  
  borderRadius: {
    sm: '6px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    full: '9999px',
  },
  
  shadows: {
    sm: '0 2px 4px rgba(0, 0, 0, 0.2)',
    md: '0 4px 12px rgba(0, 0, 0, 0.25)',
    lg: '0 8px 24px rgba(0, 0, 0, 0.3)',
    xl: '0 16px 48px rgba(0, 0, 0, 0.4)',
    glow: '0 0 20px rgba(0, 217, 255, 0.3)', // Cyan glow
    cyanGlow: '0 0 30px rgba(0, 217, 255, 0.4)',
    glass: '0 8px 32px rgba(31, 38, 135, 0.37)', // Glass morphism shadow
  },

  // CRED-specific effects
  effects: {
    glassMorphism: {
      background: 'rgba(255, 255, 255, 0.05)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
    },
    cardHover: {
      transform: 'translateY(-2px)',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    },
  },
  
  animation: {
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
    },
    easing: {
      default: 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    },
  },
  
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
};

export default theme;