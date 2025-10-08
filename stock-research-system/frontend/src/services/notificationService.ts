/**
 * Notification Service - Real-time notifications system
 * Handles API calls and WebSocket connections for notifications
 */

interface Notification {
  id: string;
  type: 'price_alert' | 'ai_insight' | 'portfolio_change' | 'market_news';
  title: string;
  message: string;
  timestamp: string | Date;
  read: boolean;
  priority: 'low' | 'medium' | 'high';
  data?: any;
}

interface NotificationRequest {
  type: string;
  title: string;
  message: string;
  priority?: string;
  user_id?: string;
  data?: any;
}

interface PriceAlertRequest {
  symbol: string;
  target_price: number;
  condition: 'above' | 'below';
  user_id?: string;
}

class NotificationService {
  private baseUrl: string;
  private websocket: WebSocket | null = null;
  private listeners: Set<(notification: Notification) => void> = new Set();

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  }

  /**
   * Get notifications from API
   */
  async getNotifications(userId?: string, limit: number = 20): Promise<Notification[]> {
    try {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      params.append('limit', limit.toString());

      const response = await fetch(`${this.baseUrl}/api/v1/notifications?${params}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch notifications: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notifications:', error);
      return [];
    }
  }

  /**
   * Create a new notification
   */
  async createNotification(notification: NotificationRequest): Promise<Notification | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/notifications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(notification),
      });

      if (!response.ok) {
        throw new Error(`Failed to create notification: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating notification:', error);
      return null;
    }
  }

  /**
   * Mark notification as read
   */
  async markAsRead(notificationId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/notifications/${notificationId}/read`, {
        method: 'PUT',
      });

      return response.ok;
    } catch (error) {
      console.error('Error marking notification as read:', error);
      return false;
    }
  }

  /**
   * Create a price alert
   */
  async createPriceAlert(alert: PriceAlertRequest): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/notifications/price-alert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(alert),
      });

      return response.ok;
    } catch (error) {
      console.error('Error creating price alert:', error);
      return false;
    }
  }

  /**
   * Connect to WebSocket for real-time notifications
   */
  connectWebSocket(): void {
    try {
      const wsUrl = this.baseUrl.replace('http', 'ws') + '/ws/notifications';
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log('Notification WebSocket connected');
      };

      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'notification' && data.data) {
            const notification: Notification = {
              id: data.data.id,
              type: data.data.type,
              title: data.data.title,
              message: data.data.message,
              timestamp: data.data.timestamp,
              read: false,
              priority: data.data.priority || 'medium'
            };

            // Notify all listeners
            this.listeners.forEach(listener => listener(notification));
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.websocket.onclose = () => {
        console.log('Notification WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(() => this.connectWebSocket(), 5000);
      };

      this.websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnectWebSocket(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  }

  /**
   * Add listener for real-time notifications
   */
  addListener(listener: (notification: Notification) => void): void {
    this.listeners.add(listener);
  }

  /**
   * Remove listener
   */
  removeListener(listener: (notification: Notification) => void): void {
    this.listeners.delete(listener);
  }

  /**
   * Generate sample notifications for demo purposes
   */
  async generateSampleNotifications(userId: string = 'demo'): Promise<void> {
    const sampleNotifications = [
      {
        type: 'price_alert',
        title: 'NVDA Price Alert',
        message: 'NVIDIA has reached your target price of $185.00',
        priority: 'high',
        user_id: userId,
        data: { symbol: 'NVDA', price: 185.00 }
      },
      {
        type: 'ai_insight',
        title: 'AI Market Insight',
        message: 'Strong bullish signals detected for tech sector with 85% confidence',
        priority: 'medium',
        user_id: userId,
        data: { sector: 'technology', confidence: 85 }
      },
      {
        type: 'portfolio_change',
        title: 'Portfolio Rebalancing',
        message: 'Your portfolio allocation has shifted. Tech sector now 65% (+5%)',
        priority: 'medium',
        user_id: userId,
        data: { sector: 'tech', change: 5 }
      },
      {
        type: 'market_news',
        title: 'Breaking Market News',
        message: 'Fed announces interest rate decision - Markets react positively',
        priority: 'high',
        user_id: userId,
        data: { source: 'Federal Reserve', impact: 'positive' }
      }
    ];

    // Create sample notifications
    for (const notification of sampleNotifications) {
      await this.createNotification(notification);
    }
  }
}

// Singleton instance
export const notificationService = new NotificationService();

// Export types
export type { Notification, NotificationRequest, PriceAlertRequest };