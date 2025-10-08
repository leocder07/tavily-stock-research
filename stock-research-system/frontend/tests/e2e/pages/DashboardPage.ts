import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for the Premium Dashboard
 * Encapsulates all dashboard interactions
 */
export class DashboardPage {
  readonly page: Page;

  // Header elements
  readonly logo: Locator;
  readonly searchInput: Locator;
  readonly analyzeButton: Locator;
  readonly notificationIcon: Locator;

  // Dashboard sections
  readonly marketOverview: Locator;
  readonly portfolio: Locator;
  readonly watchlist: Locator;
  readonly aiChat: Locator;
  readonly growthAnalytics: Locator;

  // Connection status
  readonly connectionStatus: Locator;
  readonly wsIndicator: Locator;

  // Analysis results
  readonly analysisResults: Locator;
  readonly loadingSpinner: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.logo = page.locator('[data-testid="app-logo"]');
    this.searchInput = page.locator('[data-testid="stock-search-input"]');
    this.analyzeButton = page.locator('[data-testid="analyze-button"]');
    this.notificationIcon = page.locator('[data-testid="notification-icon"]');

    // Dashboard sections
    this.marketOverview = page.locator('[data-testid="market-overview"]');
    this.portfolio = page.locator('[data-testid="portfolio-section"]');
    this.watchlist = page.locator('[data-testid="watchlist-section"]');
    this.aiChat = page.locator('[data-testid="ai-chat"]');
    this.growthAnalytics = page.locator('[data-testid="growth-analytics"]');

    // Connection
    this.connectionStatus = page.locator('[data-testid="connection-status"]');
    this.wsIndicator = page.locator('[data-testid="ws-indicator"]');

    // Results
    this.analysisResults = page.locator('[data-testid="analysis-results"]');
    this.loadingSpinner = page.locator('.shimmer-loader');
    this.errorMessage = page.locator('[data-testid="error-message"]');
  }

  async goto() {
    await this.page.goto('/');
  }

  async searchStock(symbol: string) {
    await this.searchInput.fill(symbol);
    await this.analyzeButton.click();
  }

  async waitForAnalysis() {
    await this.analysisResults.waitFor({ state: 'visible', timeout: 30000 });
  }

  async isConnected(): Promise<boolean> {
    const status = await this.wsIndicator.getAttribute('data-status');
    return status === 'connected';
  }

  async getMarketData(symbol: string) {
    const priceLocator = this.page.locator(`[data-symbol="${symbol}"] .price`);
    const price = await priceLocator.textContent();
    const changeLocator = this.page.locator(`[data-symbol="${symbol}"] .change`);
    const change = await changeLocator.textContent();

    return { price, change };
  }

  async addToWatchlist(symbol: string) {
    const addButton = this.page.locator(`[data-symbol="${symbol}"] [data-action="add-watchlist"]`);
    await addButton.click();
  }

  async sendChatMessage(message: string) {
    const chatInput = this.aiChat.locator('input[type="text"]');
    await chatInput.fill(message);
    await chatInput.press('Enter');
  }

  async getChatResponse(): Promise<string> {
    const responseLocator = this.aiChat.locator('.chat-message:last-child .message-content');
    await responseLocator.waitFor({ state: 'visible' });
    return await responseLocator.textContent() || '';
  }

  async checkNotifications(): Promise<number> {
    const badge = this.notificationIcon.locator('.notification-badge');
    const count = await badge.textContent();
    return parseInt(count || '0', 10);
  }

  async openNotifications() {
    await this.notificationIcon.click();
  }

  async waitForWebSocketConnection() {
    await this.page.waitForFunction(
      () => {
        const wsStatus = document.querySelector('[data-testid="ws-indicator"]');
        return wsStatus?.getAttribute('data-status') === 'connected';
      },
      { timeout: 10000 }
    );
  }

  async getAnalysisResult(section: string) {
    const sectionLocator = this.analysisResults.locator(`[data-section="${section}"]`);
    return await sectionLocator.textContent();
  }

  async checkGlassMorphism(): Promise<boolean> {
    const glassCard = this.page.locator('.glass-card').first();
    const backdrop = await glassCard.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.backdropFilter || styles.webkitBackdropFilter;
    });
    return backdrop !== 'none' && backdrop !== undefined;
  }

  async checkAnimations(): Promise<boolean> {
    const animatedElement = this.page.locator('[data-animate="true"]').first();
    const hasAnimation = await animatedElement.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.animation !== 'none' || styles.transition !== 'none';
    });
    return hasAnimation;
  }
}