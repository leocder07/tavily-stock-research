/**
 * Performance Monitoring Utility
 * Tracks and reports application performance metrics
 */

import React from 'react';

interface PerformanceMetrics {
  pageLoadTime: number;
  timeToInteractive: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  firstInputDelay: number;
  cumulativeLayoutShift: number;
  totalBlockingTime: number;
  apiCallDuration: Map<string, number[]>;
  renderCount: Map<string, number>;
  errorCount: number;
  memoryUsage?: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  };
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics;
  private observers: Map<string, PerformanceObserver>;
  private startTime: number;
  private reportInterval: NodeJS.Timeout | null;

  constructor() {
    this.metrics = {
      pageLoadTime: 0,
      timeToInteractive: 0,
      firstContentfulPaint: 0,
      largestContentfulPaint: 0,
      firstInputDelay: 0,
      cumulativeLayoutShift: 0,
      totalBlockingTime: 0,
      apiCallDuration: new Map(),
      renderCount: new Map(),
      errorCount: 0,
    };
    
    this.observers = new Map();
    this.startTime = performance.now();
    this.reportInterval = null;
    
    this.initializeObservers();
    this.startPeriodicReporting();
  }

  /**
   * Initialize Performance Observers
   */
  private initializeObservers(): void {
    // Observe paint timing
    if ('PerformanceObserver' in window) {
      // First Contentful Paint
      try {
        const paintObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.name === 'first-contentful-paint') {
              this.metrics.firstContentfulPaint = entry.startTime;
            }
          }
        });
        paintObserver.observe({ entryTypes: ['paint'] });
        this.observers.set('paint', paintObserver);
      } catch (e) {
        console.warn('Paint observer not supported:', e);
      }

      // Largest Contentful Paint
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          this.metrics.largestContentfulPaint = lastEntry.startTime;
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.set('lcp', lcpObserver);
      } catch (e) {
        console.warn('LCP observer not supported:', e);
      }

      // First Input Delay
      try {
        const fidObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if ('processingStart' in entry && 'startTime' in entry) {
              const delay = (entry as any).processingStart - entry.startTime;
              this.metrics.firstInputDelay = Math.max(this.metrics.firstInputDelay, delay);
            }
          }
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.set('fid', fidObserver);
      } catch (e) {
        console.warn('FID observer not supported:', e);
      }

      // Cumulative Layout Shift
      try {
        let clsValue = 0;
        let clsEntries: any[] = [];
        
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsEntries.push(entry);
              clsValue += (entry as any).value;
            }
          }
          this.metrics.cumulativeLayoutShift = clsValue;
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.set('cls', clsObserver);
      } catch (e) {
        console.warn('CLS observer not supported:', e);
      }

      // Long Tasks (for Total Blocking Time approximation)
      try {
        let totalBlockingTime = 0;
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const blockingTime = entry.duration - 50; // Tasks longer than 50ms are considered blocking
            if (blockingTime > 0) {
              totalBlockingTime += blockingTime;
            }
          }
          this.metrics.totalBlockingTime = totalBlockingTime;
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.set('longtask', longTaskObserver);
      } catch (e) {
        console.warn('Long task observer not supported:', e);
      }
    }

    // Page load metrics
    if (window.performance && window.performance.timing) {
      window.addEventListener('load', () => {
        const timing = window.performance.timing;
        this.metrics.pageLoadTime = timing.loadEventEnd - timing.navigationStart;
        this.metrics.timeToInteractive = timing.domInteractive - timing.navigationStart;
      });
    }

    // Memory usage (Chrome only)
    if ((performance as any).memory) {
      setInterval(() => {
        const memory = (performance as any).memory;
        this.metrics.memoryUsage = {
          usedJSHeapSize: memory.usedJSHeapSize,
          totalJSHeapSize: memory.totalJSHeapSize,
          jsHeapSizeLimit: memory.jsHeapSizeLimit,
        };
      }, 5000);
    }
  }

  /**
   * Track API call performance
   */
  public trackApiCall(endpoint: string, duration: number): void {
    if (!this.metrics.apiCallDuration.has(endpoint)) {
      this.metrics.apiCallDuration.set(endpoint, []);
    }
    
    const durations = this.metrics.apiCallDuration.get(endpoint)!;
    durations.push(duration);
    
    // Keep only last 100 calls per endpoint
    if (durations.length > 100) {
      durations.shift();
    }
  }

  /**
   * Track component render
   */
  public trackRender(componentName: string): void {
    const current = this.metrics.renderCount.get(componentName) || 0;
    this.metrics.renderCount.set(componentName, current + 1);
  }

  /**
   * Track error occurrence
   */
  public trackError(): void {
    this.metrics.errorCount++;
  }

  /**
   * Get current metrics
   */
  public getMetrics(): PerformanceMetrics & { summary: any } {
    const apiStats = this.calculateApiStats();
    const renderStats = this.calculateRenderStats();
    
    return {
      ...this.metrics,
      summary: {
        apiStats,
        renderStats,
        vitals: this.getWebVitals(),
        health: this.calculateHealthScore(),
      },
    };
  }

  /**
   * Calculate API call statistics
   */
  private calculateApiStats(): any {
    const stats: any = {};
    
    this.metrics.apiCallDuration.forEach((durations, endpoint) => {
      if (durations.length === 0) return;
      
      const sorted = [...durations].sort((a, b) => a - b);
      const sum = sorted.reduce((acc, val) => acc + val, 0);
      
      stats[endpoint] = {
        avg: sum / sorted.length,
        min: sorted[0],
        max: sorted[sorted.length - 1],
        p50: sorted[Math.floor(sorted.length * 0.5)],
        p95: sorted[Math.floor(sorted.length * 0.95)],
        count: sorted.length,
      };
    });
    
    return stats;
  }

  /**
   * Calculate render statistics
   */
  private calculateRenderStats(): any {
    const stats: any = {
      totalRenders: 0,
      byComponent: {},
    };
    
    this.metrics.renderCount.forEach((count, component) => {
      stats.totalRenders += count;
      stats.byComponent[component] = count;
    });
    
    return stats;
  }

  /**
   * Get Web Vitals summary
   */
  private getWebVitals(): any {
    return {
      FCP: this.metrics.firstContentfulPaint,
      LCP: this.metrics.largestContentfulPaint,
      FID: this.metrics.firstInputDelay,
      CLS: this.metrics.cumulativeLayoutShift,
      TBT: this.metrics.totalBlockingTime,
      TTI: this.metrics.timeToInteractive,
    };
  }

  /**
   * Calculate overall health score (0-100)
   */
  private calculateHealthScore(): number {
    let score = 100;
    
    // Deduct points for poor metrics
    if (this.metrics.largestContentfulPaint > 4000) score -= 20;
    else if (this.metrics.largestContentfulPaint > 2500) score -= 10;
    
    if (this.metrics.firstInputDelay > 300) score -= 20;
    else if (this.metrics.firstInputDelay > 100) score -= 10;
    
    if (this.metrics.cumulativeLayoutShift > 0.25) score -= 20;
    else if (this.metrics.cumulativeLayoutShift > 0.1) score -= 10;
    
    if (this.metrics.totalBlockingTime > 600) score -= 20;
    else if (this.metrics.totalBlockingTime > 300) score -= 10;
    
    // Deduct for errors
    if (this.metrics.errorCount > 10) score -= 20;
    else if (this.metrics.errorCount > 5) score -= 10;
    else if (this.metrics.errorCount > 0) score -= 5;
    
    // Memory usage (if available)
    if (this.metrics.memoryUsage) {
      const usagePercent = (this.metrics.memoryUsage.usedJSHeapSize / 
                          this.metrics.memoryUsage.jsHeapSizeLimit) * 100;
      if (usagePercent > 90) score -= 15;
      else if (usagePercent > 75) score -= 10;
      else if (usagePercent > 60) score -= 5;
    }
    
    return Math.max(0, score);
  }

  /**
   * Start periodic reporting
   */
  private startPeriodicReporting(): void {
    // Report metrics every 30 seconds
    this.reportInterval = setInterval(() => {
      this.reportMetrics();
    }, 30000);
  }

  /**
   * Report metrics to console/monitoring service
   */
  private reportMetrics(): void {
    const metrics = this.getMetrics();
    
    // Console report (development)
    if (process.env.NODE_ENV === 'development') {
      console.group('📊 Performance Metrics Report');
      console.log('Web Vitals:', metrics.summary.vitals);
      console.log('Health Score:', metrics.summary.health);
      console.log('API Stats:', metrics.summary.apiStats);
      console.log('Render Stats:', metrics.summary.renderStats);
      if (metrics.memoryUsage) {
        console.log('Memory Usage:', {
          used: `${(metrics.memoryUsage.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
          total: `${(metrics.memoryUsage.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
          limit: `${(metrics.memoryUsage.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`,
        });
      }
      console.log('Error Count:', metrics.errorCount);
      console.groupEnd();
    }
    
    // Send to monitoring service (production)
    if (process.env.NODE_ENV === 'production') {
      this.sendToMonitoringService(metrics);
    }
  }

  /**
   * Send metrics to monitoring service
   */
  private sendToMonitoringService(metrics: any): void {
    // In production, send to service like Google Analytics, Sentry, or custom endpoint
    // Example:
    // fetch('/api/metrics', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     ...metrics,
    //     timestamp: new Date().toISOString(),
    //     userAgent: navigator.userAgent,
    //     url: window.location.href,
    //   }),
    // });
    
    // For now, just log
    console.log('Metrics ready to send:', metrics);
  }

  /**
   * Cleanup observers and intervals
   */
  public destroy(): void {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers.clear();
    
    if (this.reportInterval) {
      clearInterval(this.reportInterval);
    }
  }

  /**
   * Manual metric reporting
   */
  public report(): void {
    this.reportMetrics();
  }
}

// Singleton instance
let performanceMonitor: PerformanceMonitor | null = null;

/**
 * Get or create performance monitor instance
 */
export const getPerformanceMonitor = (): PerformanceMonitor => {
  if (!performanceMonitor) {
    performanceMonitor = new PerformanceMonitor();
  }
  return performanceMonitor;
};

/**
 * React hook for tracking component renders
 */
export const usePerformanceTracking = (componentName: string) => {
  const monitor = getPerformanceMonitor();
  
  React.useEffect(() => {
    monitor.trackRender(componentName);
  });
  
  return {
    trackApiCall: (endpoint: string, duration: number) => 
      monitor.trackApiCall(endpoint, duration),
    trackError: () => monitor.trackError(),
    getMetrics: () => monitor.getMetrics(),
  };
};

/**
 * Axios interceptor for API performance tracking
 */
export const createApiPerformanceInterceptor = () => {
  const monitor = getPerformanceMonitor();
  
  return {
    request: (config: any) => {
      config.metadata = { startTime: performance.now() };
      return config;
    },
    response: (response: any) => {
      if (response.config.metadata) {
        const duration = performance.now() - response.config.metadata.startTime;
        const endpoint = `${response.config.method?.toUpperCase()} ${response.config.url}`;
        monitor.trackApiCall(endpoint, duration);
      }
      return response;
    },
    error: (error: any) => {
      monitor.trackError();
      if (error.config?.metadata) {
        const duration = performance.now() - error.config.metadata.startTime;
        const endpoint = `${error.config.method?.toUpperCase()} ${error.config.url}`;
        monitor.trackApiCall(endpoint, duration);
      }
      return Promise.reject(error);
    },
  };
};

export default getPerformanceMonitor;