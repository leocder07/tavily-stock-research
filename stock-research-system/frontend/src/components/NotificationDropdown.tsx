/**
 * NotificationDropdown - CRED-style notification system
 * Real-time alerts for market movements, portfolio changes, and AI insights
 */

import React, { useState, useEffect } from 'react';
import {
  Dropdown,
  List,
  Badge,
  Typography,
  Space,
  Tag,
  Avatar,
  Button,
  Divider,
  Empty,
  message,
} from 'antd';
import {
  BellOutlined,
  RiseOutlined,
  FallOutlined,
  ThunderboltOutlined,
  AlertOutlined,
  CheckOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import { theme } from '../styles/theme';
import { notificationService, Notification } from '../services/notificationService';

const { Text } = Typography;

interface NotificationDropdownProps {
  onNotificationClick?: (notification: Notification) => void;
}

const NotificationDropdown: React.FC<NotificationDropdownProps> = ({
  onNotificationClick,
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [visible, setVisible] = useState(false);

  // Load notifications from API and connect to WebSocket for real-time updates
  useEffect(() => {
    const loadNotifications = async () => {
      try {
        const fetchedNotifications = await notificationService.getNotifications('demo', 20);
        setNotifications(fetchedNotifications);
        setUnreadCount(fetchedNotifications.filter(n => !n.read).length);
      } catch (error) {
        console.error('Failed to load notifications:', error);
        // Fallback to sample data if API fails
        const sampleNotifications: Notification[] = [
          {
            id: '1',
            type: 'price_alert',
            title: 'NVDA Price Alert',
            message: 'NVDA has reached your target price of $185.00',
            timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
            read: false,
            priority: 'high',
            data: { symbol: 'NVDA', price: 185.00, change: 2.41 }
          },
          {
            id: '2',
            type: 'ai_insight',
            title: 'AI Market Insight',
            message: 'Strong bullish pattern detected in tech sector',
            timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
            read: false,
            priority: 'medium',
            data: { sector: 'technology', confidence: 87 }
          },
          {
            id: '3',
            type: 'portfolio_change',
            title: 'Portfolio Update',
            message: 'Your portfolio gained +2.3% today ($2,840)',
            timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
            read: true,
            priority: 'low',
            data: { change: 2.3, amount: 2840 }
          },
        ];
        setNotifications(sampleNotifications);
        setUnreadCount(sampleNotifications.filter(n => !n.read).length);
      }
    };

    loadNotifications();

    // Connect to WebSocket for real-time notifications
    notificationService.connectWebSocket();

    // Add listener for new notifications
    const handleNewNotification = (notification: Notification) => {
      setNotifications(prev => [notification, ...prev]);
      setUnreadCount(prev => prev + 1);
      message.info(`New notification: ${notification.title}`);
    };

    notificationService.addListener(handleNewNotification);

    // Cleanup on unmount
    return () => {
      notificationService.removeListener(handleNewNotification);
      notificationService.disconnectWebSocket();
    };
  }, []);

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'price_alert':
        return <RiseOutlined style={{ color: theme.colors.success }} />;
      case 'ai_insight':
        return <ThunderboltOutlined style={{ color: theme.colors.primary }} />;
      case 'portfolio_change':
        return <FallOutlined style={{ color: theme.colors.warning }} />;
      case 'market_news':
        return <AlertOutlined style={{ color: theme.colors.text.secondary }} />;
      default:
        return <BellOutlined />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return theme.colors.danger;
      case 'medium': return theme.colors.warning;
      case 'low': return theme.colors.text.secondary;
      default: return theme.colors.text.secondary;
    }
  };

  const formatTimestamp = (timestamp: Date | string) => {
    const now = new Date();
    const timestampDate = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    const diff = now.getTime() - timestampDate.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const markAsRead = async (notificationId: string) => {
    // Update local state immediately for better UX
    setNotifications(prev =>
      prev.map(n =>
        n.id === notificationId ? { ...n, read: true } : n
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));

    // Update on backend
    try {
      await notificationService.markAsRead(notificationId);
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      // Revert local state on error
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, read: false } : n
        )
      );
      setUnreadCount(prev => prev + 1);
    }
  };

  const markAllAsRead = async () => {
    const unreadNotifications = notifications.filter(n => !n.read);

    // Update local state immediately for better UX
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);

    // Update each notification on backend
    try {
      await Promise.all(
        unreadNotifications.map(notification =>
          notificationService.markAsRead(notification.id)
        )
      );
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      // Revert local state on error
      setNotifications(prev =>
        prev.map(n => {
          const originalNotification = unreadNotifications.find(orig => orig.id === n.id);
          return originalNotification ? { ...n, read: false } : n;
        })
      );
      setUnreadCount(unreadNotifications.length);
    }
  };

  const removeNotification = (notificationId: string) => {
    const notification = notifications.find(n => n.id === notificationId);
    setNotifications(prev => prev.filter(n => n.id !== notificationId));
    if (notification && !notification.read) {
      setUnreadCount(prev => Math.max(0, prev - 1));
    }
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    onNotificationClick?.(notification);
    setVisible(false);
  };

  const dropdownContent = (
    <div
      style={{
        width: 380,
        maxHeight: 500,
        background: theme.colors.background.secondary,
        borderRadius: theme.borderRadius.lg,
        border: `1px solid rgba(255, 255, 255, 0.1)`,
        boxShadow: theme.shadows.xl,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: `1px solid rgba(255, 255, 255, 0.1)`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Space>
          <ThunderboltOutlined style={{ color: theme.colors.primary }} />
          <Text strong style={{ color: theme.colors.text.primary }}>
            Notifications
          </Text>
          {unreadCount > 0 && (
            <Badge
              count={unreadCount}
              style={{
                backgroundColor: theme.colors.primary,
                color: '#000',
                fontWeight: 600,
              }}
            />
          )}
        </Space>
        {unreadCount > 0 && (
          <Button
            type="text"
            size="small"
            onClick={markAllAsRead}
            style={{
              color: theme.colors.primary,
              fontSize: 12,
            }}
          >
            Mark all read
          </Button>
        )}
      </div>

      {/* Notifications List */}
      <div style={{ maxHeight: 400, overflowY: 'auto' }}>
        {notifications.length === 0 ? (
          <div style={{ padding: 40 }}>
            <Empty
              description={
                <Text style={{ color: theme.colors.text.secondary }}>
                  No notifications yet
                </Text>
              }
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </div>
        ) : (
          <List
            dataSource={notifications}
            renderItem={(notification) => (
              <List.Item
                style={{
                  padding: '12px 20px',
                  borderBottom: `1px solid rgba(255, 255, 255, 0.05)`,
                  background: notification.read
                    ? 'transparent'
                    : `${theme.colors.primary}08`,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = `${theme.colors.primary}15`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = notification.read
                    ? 'transparent'
                    : `${theme.colors.primary}08`;
                }}
                onClick={() => handleNotificationClick(notification)}
                actions={[
                  <Button
                    type="text"
                    size="small"
                    icon={<CloseOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      removeNotification(notification.id);
                    }}
                    style={{
                      color: theme.colors.text.muted,
                      opacity: 0.6,
                    }}
                  />,
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <Avatar
                      size="small"
                      style={{
                        background: 'transparent',
                        border: `1px solid ${getPriorityColor(notification.priority)}`,
                      }}
                      icon={getNotificationIcon(notification.type)}
                    />
                  }
                  title={
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Text
                        strong={!notification.read}
                        style={{
                          color: theme.colors.text.primary,
                          fontSize: 13,
                        }}
                      >
                        {notification.title}
                      </Text>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        {!notification.read && (
                          <div
                            style={{
                              width: 6,
                              height: 6,
                              borderRadius: '50%',
                              background: theme.colors.primary,
                            }}
                          />
                        )}
                        <Text
                          style={{
                            fontSize: 10,
                            color: theme.colors.text.muted,
                          }}
                        >
                          {formatTimestamp(notification.timestamp)}
                        </Text>
                      </div>
                    </div>
                  }
                  description={
                    <div>
                      <Text
                        style={{
                          color: theme.colors.text.secondary,
                          fontSize: 12,
                          lineHeight: 1.4,
                        }}
                      >
                        {notification.message}
                      </Text>
                      <div style={{ marginTop: 4 }}>
                        <Tag
                          color={getPriorityColor(notification.priority)}
                          style={{
                            fontSize: 10,
                            padding: '0 6px',
                            lineHeight: '16px',
                            height: 16,
                          }}
                        >
                          {notification.priority.toUpperCase()}
                        </Tag>
                      </div>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </div>

      {/* Footer */}
      <div
        style={{
          padding: '12px 20px',
          borderTop: `1px solid rgba(255, 255, 255, 0.1)`,
          textAlign: 'center',
        }}
      >
        <Button
          type="text"
          style={{
            color: theme.colors.primary,
            fontSize: 12,
          }}
        >
          View All Notifications
        </Button>
      </div>
    </div>
  );

  return (
    <Dropdown
      overlay={dropdownContent}
      trigger={['click']}
      visible={visible}
      onVisibleChange={setVisible}
      placement="bottomRight"
      arrow
    >
      <Badge count={unreadCount} offset={[-5, 5]}>
        <Button
          shape="circle"
          icon={<BellOutlined />}
          size="large"
          style={{
            background: theme.colors.background.elevated,
            border: `1px solid rgba(255, 255, 255, 0.1)`,
            color: theme.colors.text.primary,
          }}
        />
      </Badge>
    </Dropdown>
  );
};

export default NotificationDropdown;