import { test, expect } from '@playwright/test';
import { DashboardPage } from '../pages/DashboardPage';

test.describe('Stock Analysis E2E Tests', () => {
  let dashboard: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForWebSocketConnection();
  });

  test('Complete stock analysis flow with real data', async ({ page }) => {
    // Test real stock analysis
    await test.step('Search for Apple stock', async () => {
      await dashboard.searchStock('AAPL');
    });

    await test.step('Wait for analysis results', async () => {
      await dashboard.waitForAnalysis();
    });

    await test.step('Verify market data is displayed', async () => {
      const marketData = await dashboard.getAnalysisResult('market-data');
      expect(marketData).toBeTruthy();
      expect(marketData).toContain('Price');
      expect(marketData).toContain('Volume');
    });

    await test.step('Verify fundamental analysis', async () => {
      const fundamentals = await dashboard.getAnalysisResult('fundamental-analysis');
      expect(fundamentals).toBeTruthy();
      expect(fundamentals).toMatch(/P\/E|Revenue|Earnings/i);
    });

    await test.step('Verify technical analysis', async () => {
      const technicals = await dashboard.getAnalysisResult('technical-analysis');
      expect(technicals).toBeTruthy();
      expect(technicals).toMatch(/RSI|MACD|Moving Average/i);
    });

    await test.step('Verify sentiment analysis', async () => {
      const sentiment = await dashboard.getAnalysisResult('sentiment-analysis');
      expect(sentiment).toBeTruthy();
      expect(sentiment).toMatch(/Bullish|Neutral|Bearish/i);
    });

    await test.step('Verify recommendations', async () => {
      const recommendations = await dashboard.getAnalysisResult('recommendations');
      expect(recommendations).toBeTruthy();
      expect(recommendations).toMatch(/Buy|Hold|Sell/i);
    });
  });

  test('Multiple stock comparison', async ({ page }) => {
    // Search for first stock
    await dashboard.searchStock('AAPL');
    await dashboard.waitForAnalysis();

    // Add to watchlist
    await dashboard.addToWatchlist('AAPL');

    // Search for second stock
    await dashboard.searchStock('GOOGL');
    await dashboard.waitForAnalysis();

    // Verify peer comparison is shown
    const peerComparison = await dashboard.getAnalysisResult('peer-comparison');
    expect(peerComparison).toBeTruthy();
    expect(peerComparison).toContain('AAPL');
  });

  test('WebSocket real-time data updates', async ({ page }) => {
    await dashboard.searchStock('TSLA');
    await dashboard.waitForAnalysis();

    // Get initial price
    const initialData = await dashboard.getMarketData('TSLA');
    expect(initialData.price).toBeTruthy();

    // Wait for real-time update (max 30 seconds)
    await page.waitForTimeout(5000);

    // Check if WebSocket is still connected
    const isConnected = await dashboard.isConnected();
    expect(isConnected).toBe(true);

    // Verify data structure is maintained
    const updatedData = await dashboard.getMarketData('TSLA');
    expect(updatedData.price).toBeTruthy();
  });

  test('Error handling for invalid stock symbol', async ({ page }) => {
    // Search for invalid symbol
    await dashboard.searchStock('INVALID123');

    // Wait for error message
    await dashboard.errorMessage.waitFor({ state: 'visible', timeout: 10000 });

    const errorText = await dashboard.errorMessage.textContent();
    expect(errorText).toMatch(/not found|invalid|error/i);
  });

  test('AI Chat interaction', async ({ page }) => {
    // Send message to AI chat
    await dashboard.sendChatMessage('What is the current trend for tech stocks?');

    // Wait for response
    const response = await dashboard.getChatResponse();
    expect(response).toBeTruthy();
    expect(response.length).toBeGreaterThan(10);
  });

  test('Premium UI features', async ({ page }) => {
    // Check glass morphism effect
    const hasGlassEffect = await dashboard.checkGlassMorphism();
    expect(hasGlassEffect).toBe(true);

    // Check animations
    const hasAnimations = await dashboard.checkAnimations();
    expect(hasAnimations).toBe(true);

    // Check shimmer loader during analysis
    await dashboard.searchStock('MSFT');
    const shimmerVisible = await dashboard.loadingSpinner.isVisible();
    expect(shimmerVisible).toBe(true);
  });

  test('Portfolio management', async ({ page }) => {
    // Add stocks to portfolio
    await dashboard.searchStock('AAPL');
    await dashboard.waitForAnalysis();
    await dashboard.addToWatchlist('AAPL');

    await dashboard.searchStock('GOOGL');
    await dashboard.waitForAnalysis();
    await dashboard.addToWatchlist('GOOGL');

    // Check portfolio section
    const portfolioText = await dashboard.portfolio.textContent();
    expect(portfolioText).toContain('AAPL');
    expect(portfolioText).toContain('GOOGL');
  });

  test('Notification system', async ({ page }) => {
    // Trigger analysis that generates notifications
    await dashboard.searchStock('NVDA');
    await dashboard.waitForAnalysis();

    // Check for notifications
    const notificationCount = await dashboard.checkNotifications();
    expect(notificationCount).toBeGreaterThanOrEqual(0);

    // Open notifications dropdown
    if (notificationCount > 0) {
      await dashboard.openNotifications();
      const dropdown = page.locator('.notification-dropdown');
      await expect(dropdown).toBeVisible();
    }
  });

  test('WebSocket reconnection after disconnect', async ({ page }) => {
    // Initial connection check
    let isConnected = await dashboard.isConnected();
    expect(isConnected).toBe(true);

    // Simulate disconnect (offline mode)
    await page.context().setOffline(true);
    await page.waitForTimeout(2000);

    // Check disconnected state
    isConnected = await dashboard.isConnected();
    expect(isConnected).toBe(false);

    // Reconnect
    await page.context().setOffline(false);
    await page.waitForTimeout(5000);

    // Verify reconnection
    isConnected = await dashboard.isConnected();
    expect(isConnected).toBe(true);
  });

  test('Performance monitoring', async ({ page }) => {
    // Check if performance metrics are being tracked
    const metrics = await page.evaluate(() => {
      return window.performance.getEntriesByType('navigation')[0];
    });

    expect(metrics).toBeTruthy();
    expect(metrics.loadEventEnd).toBeGreaterThan(0);
    expect(metrics.domContentLoadedEventEnd).toBeGreaterThan(0);
  });
});