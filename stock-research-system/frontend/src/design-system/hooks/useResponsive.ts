import { useState, useEffect } from 'react';
import { designTokens } from '../tokens';

// Breakpoint values
const breakpoints = {
  xs: parseInt(designTokens.breakpoints.xs),
  sm: parseInt(designTokens.breakpoints.sm),
  md: parseInt(designTokens.breakpoints.md),
  lg: parseInt(designTokens.breakpoints.lg),
  xl: parseInt(designTokens.breakpoints.xl),
  '2xl': parseInt(designTokens.breakpoints['2xl']),
  '3xl': parseInt(designTokens.breakpoints['3xl']),
};

export type Breakpoint = keyof typeof breakpoints;

interface ResponsiveState {
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLargeDesktop: boolean;
  currentBreakpoint: Breakpoint;
  isTouch: boolean;
}

export const useResponsive = (): ResponsiveState => {
  const [state, setState] = useState<ResponsiveState>(() => {
    if (typeof window === 'undefined') {
      return {
        width: 1920,
        height: 1080,
        isMobile: false,
        isTablet: false,
        isDesktop: true,
        isLargeDesktop: false,
        currentBreakpoint: 'lg',
        isTouch: false,
      };
    }

    const width = window.innerWidth;
    const height = window.innerHeight;

    return {
      width,
      height,
      isMobile: width < breakpoints.md,
      isTablet: width >= breakpoints.md && width < breakpoints.lg,
      isDesktop: width >= breakpoints.lg,
      isLargeDesktop: width >= breakpoints['2xl'],
      currentBreakpoint: getCurrentBreakpoint(width),
      isTouch: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
    };
  });

  useEffect(() => {
    let rafId: number;

    const updateDimensions = () => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        const width = window.innerWidth;
        const height = window.innerHeight;

        setState({
          width,
          height,
          isMobile: width < breakpoints.md,
          isTablet: width >= breakpoints.md && width < breakpoints.lg,
          isDesktop: width >= breakpoints.lg,
          isLargeDesktop: width >= breakpoints['2xl'],
          currentBreakpoint: getCurrentBreakpoint(width),
          isTouch: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
        });
      });
    };

    window.addEventListener('resize', updateDimensions);
    window.addEventListener('orientationchange', updateDimensions);

    // Initial check
    updateDimensions();

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('resize', updateDimensions);
      window.removeEventListener('orientationchange', updateDimensions);
    };
  }, []);

  return state;
};

// Helper function to get current breakpoint
function getCurrentBreakpoint(width: number): Breakpoint {
  if (width < breakpoints.xs) return 'xs';
  if (width < breakpoints.sm) return 'xs';
  if (width < breakpoints.md) return 'sm';
  if (width < breakpoints.lg) return 'md';
  if (width < breakpoints.xl) return 'lg';
  if (width < breakpoints['2xl']) return 'xl';
  if (width < breakpoints['3xl']) return '2xl';
  return '3xl';
}

// Media query hook
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const handleChange = (e: MediaQueryListEvent) => setMatches(e.matches);

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
    // Legacy browsers
    else {
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, [query]);

  return matches;
};

// Breakpoint-specific hooks
export const useIsMobile = () => useMediaQuery(`(max-width: ${breakpoints.md - 1}px)`);
export const useIsTablet = () => useMediaQuery(`(min-width: ${breakpoints.md}px) and (max-width: ${breakpoints.lg - 1}px)`);
export const useIsDesktop = () => useMediaQuery(`(min-width: ${breakpoints.lg}px)`);
export const useIsLargeDesktop = () => useMediaQuery(`(min-width: ${breakpoints['2xl']}px)`);