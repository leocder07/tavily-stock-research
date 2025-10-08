import React, { useState } from 'react';
import {
  Layout,
  Row,
  Col,
  Input,
  Space,
  Statistic,
  Badge,
  Avatar,
  Tabs,
  Tag,
  Progress,
  message,
  Drawer,
  Button,
  Dropdown,
  Menu,
  Typography,
} from 'antd';
import {
  SearchOutlined,
  RocketOutlined,
  ThunderboltOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  LineChartOutlined,
  SafetyOutlined,
  GlobalOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useUser, useClerk } from '@clerk/clerk-react';
import { theme } from '../styles/theme';
import MarketOverview from './MarketOverview';
import Portfolio from './Portfolio';
import GlassCard from './premium/GlassCard';
import { useRealTimeData } from '../hooks/useRealTimeData';
import { useResponsive } from '../hooks/useResponsive';
import { MobileHeader } from './MobileHeader';
import DeepAnalysis from './DeepAnalysis';
import { usePortfolioData } from '../hooks/usePortfolioData';
import { UserProfile } from './UserProfile';

const { Text } = Typography;

const { Header, Sider, Content } = Layout;

const PremiumDashboard: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deepAnalysisOpen, setDeepAnalysisOpen] = useState(false);
  const [analysisSymbol, setAnalysisSymbol] = useState('');
  const [marketSentiment] = useState<'bullish' | 'bearish'>('bullish');
  const [showProfileDrawer, setShowProfileDrawer] = useState(false);

  // Responsive hooks
  const { isMobile, isTablet } = useResponsive();

  // Get authenticated user from Clerk or test user from localStorage
  const { user } = useUser();
  const { signOut: clerkSignOut } = useClerk();

  // Check for test user session
  const testUserSession = localStorage.getItem('testUserSession');
  const testUser = testUserSession ? JSON.parse(testUserSession) : null;

  // Use test user if available, otherwise use Clerk user
  const userId = testUser?.id || user?.id || '';
  const userEmail = testUser?.email || user?.emailAddresses[0]?.emailAddress || '';

  // Custom signOut handler that works for both test users and Clerk users
  const handleSignOut = async () => {
    if (testUser) {
      // Test user: clear localStorage and reload
      localStorage.removeItem('testUserSession');
      window.location.reload();
    } else {
      // Clerk user: use Clerk's signOut
      await clerkSignOut();
    }
  };

  // Real-time data - include trending stocks
  const watchlist = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN'];
  const { stocks, portfolio, loading, error, refresh } = useRealTimeData({
    symbols: watchlist,
    pollInterval: 30000,
    enableWebSocket: false, // FIX: Disabled WebSocket to prevent infinite loop at useRealTimeData.ts:133
  });

  // Portfolio metrics - using new usePortfolioData hook with userId
  const { data: portfolioData, loading: portfolioLoading } = usePortfolioData(userId);

  // Portfolio metrics - now properly typed and transformed
  const portfolioMetrics = portfolioData ? {
    totalValue: portfolioData.metrics.totalValue,
    dayChange: portfolioData.metrics.dayChange,
    dayChangePercent: portfolioData.metrics.dayChangePercent,
    totalReturn: portfolioData.metrics.totalReturnPercent,
    winRate: portfolioData.metrics.winRate,
    sharpeRatio: portfolioData.metrics.sharpeRatio,
  } : {
    totalValue: 0,
    dayChange: 0,
    dayChangePercent: 0,
    totalReturn: 0,
    winRate: 0,
    sharpeRatio: 0,
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      message.warning('Please enter a stock symbol or company name');
      return;
    }
    // Extract symbol from query (simple extraction)
    const symbol = searchQuery.trim().toUpperCase().split(' ')[0];
    setAnalysisSymbol(symbol);
    setDeepAnalysisOpen(true);
    message.success(`Starting deep analysis for ${symbol}...`);
  };

  // Simplified navigation - only 2 main sections
  const navigationItems = [
    { key: 'overview', icon: <GlobalOutlined />, label: 'Market Overview' },
    { key: 'portfolio', icon: <SafetyOutlined />, label: 'Portfolio' },
  ];

  // Desktop only - Mobile handled separately
  if (isMobile) {
    return (
      <MobileHeader
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onSearch={handleSearch}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        marketSentiment={marketSentiment}
      />
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', background: theme.colors.background.primary }}>
      {/* Fixed Header - 64px height */}
      <Header
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          width: '100%',
          height: 64,
          zIndex: 1001,
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          background: 'rgba(17, 17, 17, 0.98)',
          borderBottom: `1px solid ${theme.colors.border}`,
          backdropFilter: 'blur(10px)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', width: '100%', gap: 24 }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 200, flex: '0 0 auto', overflow: 'visible' }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: 8,
              background: theme.colors.gradient.primary,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              <RocketOutlined style={{ fontSize: 20, color: '#000' }} />
            </div>
            <div style={{ whiteSpace: 'nowrap', overflow: 'visible' }}>
              <div style={{ fontSize: 16, fontWeight: 600, margin: 0, lineHeight: 1.2, color: theme.colors.primary }}>
                StockAI Pro
              </div>
              <div style={{ fontSize: 10, color: theme.colors.text.muted, letterSpacing: 1, marginTop: 2, lineHeight: 1.2 }}>
                INSTITUTIONAL-GRADE RESEARCH
              </div>
            </div>
          </div>

          {/* Search Bar - Centered */}
          <div style={{ flex: 1, maxWidth: 700, margin: '0 auto' }}>
            <Space.Compact style={{ width: '100%' }}>
              <Input
                placeholder="Enter stock symbol (e.g., AAPL, GOOGL, TSLA)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onPressEnter={handleSearch}
                size="large"
                style={{
                  borderRadius: '8px 0 0 8px',
                }}
                prefix={<SearchOutlined />}
              />
              <Button
                type="primary"
                size="large"
                icon={<RocketOutlined />}
                onClick={handleSearch}
                style={{
                  background: theme.colors.gradient.primary,
                  borderColor: theme.colors.primary,
                  borderRadius: '0 8px 8px 0',
                  fontWeight: 600,
                  minWidth: 160,
                  boxShadow: theme.shadows.cyanGlow,
                }}
              >
                Deep Analysis
              </Button>
            </Space.Compact>
          </div>

          {/* Right Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* Market Status */}
            <Tag color={marketSentiment === 'bullish' ? 'success' : 'error'}>
              {marketSentiment === 'bullish' ? '🔥 BULL MARKET' : '🐻 BEAR MARKET'}
            </Tag>

            {/* Notifications */}
            <Badge dot>
              <Button
                shape="circle"
                icon={<BellOutlined />}
                style={{
                  background: 'transparent',
                  border: `1px solid ${theme.colors.border}`,
                }}
              />
            </Badge>

            {/* Profile Dropdown */}
            <Dropdown
              overlay={
                <Menu
                  style={{
                    background: theme.colors.background.elevated,
                    border: `1px solid ${theme.colors.border}`,
                    borderRadius: 8,
                    minWidth: 200,
                  }}
                  items={[
                    {
                      key: 'user-info',
                      label: (
                        <div style={{ padding: '8px 0', borderBottom: `1px solid ${theme.colors.border}` }}>
                          <div style={{ color: theme.colors.text.primary, fontWeight: 600 }}>
                            {testUser?.firstName || user?.firstName || user?.emailAddresses[0]?.emailAddress?.split('@')[0]}
                          </div>
                          <div style={{ color: theme.colors.text.secondary, fontSize: 12 }}>
                            {testUser?.email || user?.emailAddresses[0]?.emailAddress}
                          </div>
                        </div>
                      ),
                      disabled: true,
                    },
                    {
                      key: 'profile',
                      label: 'View Profile',
                      icon: <UserOutlined style={{ color: theme.colors.primary }} />,
                      onClick: () => setShowProfileDrawer(true),
                    },
                    {
                      key: 'settings',
                      label: 'Settings',
                      icon: <SettingOutlined style={{ color: theme.colors.text.secondary }} />,
                      onClick: () => message.info('Settings coming soon!'),
                    },
                    {
                      type: 'divider',
                    },
                    {
                      key: 'signout',
                      label: 'Sign Out',
                      icon: <LogoutOutlined style={{ color: theme.colors.error }} />,
                      onClick: () => handleSignOut(),
                      danger: true,
                    },
                  ]}
                />
              }
              trigger={['click']}
              placement="bottomRight"
            >
              <Avatar
                size={40}
                icon={<UserOutlined />}
                style={{
                  background: theme.colors.gradient.primary,
                  cursor: 'pointer',
                }}
              />
            </Dropdown>
          </div>
        </div>
      </Header>

      <Layout style={{ marginTop: 64 }}>
        {/* Fixed Sidebar - 260px width */}
        <Sider
          width={260}
          collapsedWidth={80}
          collapsed={sidebarCollapsed}
          onCollapse={setSidebarCollapsed}
          style={{
            position: 'fixed',
            left: 0,
            top: 64,
            height: 'calc(100vh - 64px)',
            background: 'rgba(17, 17, 17, 0.98)',
            borderRight: `1px solid ${theme.colors.border}`,
            overflow: 'auto',
            zIndex: 1000,
          }}
        >
          <div style={{ padding: 24 }}>
            {/* Portfolio Summary Card */}
            <div style={{
              background: theme.colors.background.elevated,
              borderRadius: 8,
              padding: 20,
              marginBottom: 24,
              border: `1px solid ${theme.colors.border}`,
            }}>
              <div style={{ color: theme.colors.text.muted, fontSize: 12 }}>
                Portfolio Value
              </div>
              {portfolioData !== null ? (
                <>
                  <div style={{ fontSize: 24, fontWeight: 700, margin: '8px 0', color: theme.colors.primary }}>
                    ${portfolioMetrics.totalValue.toLocaleString()}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {portfolioMetrics.dayChange >= 0 ? (
                      <RiseOutlined style={{ color: theme.colors.success }} />
                    ) : (
                      <FallOutlined style={{ color: theme.colors.error }} />
                    )}
                    <div style={{ color: portfolioMetrics.dayChange >= 0 ? theme.colors.success : theme.colors.error, fontSize: 14 }}>
                      {portfolioMetrics.dayChange >= 0 ? '+' : ''}{portfolioMetrics.dayChange.toFixed(2)} ({portfolioMetrics.dayChangePercent >= 0 ? '+' : ''}{portfolioMetrics.dayChangePercent}%)
                    </div>
                  </div>
                  <Progress
                    percent={portfolioMetrics.winRate}
                    strokeColor={theme.colors.success}
                    trailColor="rgba(255, 255, 255, 0.1)"
                    showInfo={false}
                    style={{ marginTop: 16 }}
                  />
                  <div style={{ color: theme.colors.text.muted, fontSize: 11 }}>
                    Win Rate: {portfolioMetrics.winRate}%
                  </div>
                </>
              ) : (
                <div style={{ fontSize: 14, color: theme.colors.text.muted, margin: '16px 0', textAlign: 'center' }}>
                  {portfolioLoading ? 'Loading portfolio...' : 'No portfolio data available'}
                </div>
              )}
            </div>

            {/* Navigation */}
            {!sidebarCollapsed && (
              <div>
                {navigationItems.map((item) => (
                  <div
                    key={item.key}
                    onClick={() => setActiveTab(item.key)}
                    style={{
                      padding: '12px 16px',
                      marginBottom: 8,
                      borderRadius: 8,
                      background: activeTab === item.key ? theme.colors.background.elevated : 'transparent',
                      border: activeTab === item.key ? `1px solid ${theme.colors.primary}33` : '1px solid transparent',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      transition: 'all 0.3s',
                      color: activeTab === item.key ? theme.colors.primary : theme.colors.text.primary,
                    }}
                  >
                    <span style={{ fontSize: 18 }}>{item.icon}</span>
                    <span style={{
                      fontSize: 14,
                      fontWeight: activeTab === item.key ? 600 : 400,
                      color: 'inherit',
                    }}>
                      {item.label}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Trending Stocks */}
            {!sidebarCollapsed && (
              <div style={{ marginTop: 32 }}>
                <div style={{ color: theme.colors.text.muted, fontSize: 12, fontWeight: 600 }}>
                  🔥 TRENDING NOW
                </div>
                <div style={{ marginTop: 16 }}>
                  {['NVDA', 'META', 'AMZN'].map((symbol, index) => {
                    const stockData = stocks?.get(symbol);
                    const hasData = stockData && stockData.price > 0;

                    return (
                      <div
                        key={symbol}
                        style={{
                          padding: '12px 0',
                          borderBottom: index < 2 ? `1px solid ${theme.colors.border}` : 'none',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ color: theme.colors.text.primary, fontWeight: 500 }}>
                            {symbol}
                          </div>
                          <div style={{ color: hasData ? theme.colors.text.muted : theme.colors.error, fontSize: 11 }}>
                            {hasData ? `$${stockData.price.toFixed(2)}` : 'Data unavailable'}
                          </div>
                        </div>
                        {hasData ? (
                          <Tag color={stockData.changePercent >= 0 ? 'success' : 'error'} style={{ margin: 0 }}>
                            {stockData.changePercent >= 0 ? '+' : ''}{stockData.changePercent.toFixed(2)}%
                          </Tag>
                        ) : (
                          <Tag color="default" style={{ margin: 0 }}>—</Tag>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </Sider>

        {/* Main Content Area */}
        <Content
          style={{
            marginLeft: sidebarCollapsed ? 80 : 260,
            padding: 24,
            background: theme.colors.background.primary,
            minHeight: 'calc(100vh - 64px)',
            transition: 'margin-left 0.3s',
          }}
        >
          {/* Hero Portfolio Value Card - Above Fold */}
          <GlassCard
            style={{
              padding: isMobile ? '24px 20px' : '40px 48px',
              marginBottom: 32,
              background: `linear-gradient(135deg, ${theme.colors.background.elevated} 0%, rgba(0, 229, 255, 0.08) 100%)`,
              border: `1px solid ${theme.colors.primary}33`,
              borderRadius: 16,
              position: 'relative',
              overflow: 'hidden',
              boxShadow: theme.shadows.cyanGlow,
            }}
          >
            {/* Background gradient overlay */}
            <div style={{
              position: 'absolute',
              top: 0,
              right: 0,
              width: '40%',
              height: '100%',
              background: `radial-gradient(circle at top right, ${theme.colors.primary}15, transparent)`,
              pointerEvents: 'none',
            }} />

            {/* Content */}
            <div style={{ position: 'relative', zIndex: 1 }}>
              {/* Greeting */}
              <div style={{ marginBottom: 16 }}>
                <Text style={{
                  fontSize: isMobile ? 18 : 24,
                  fontWeight: 300,
                  color: theme.colors.text.secondary,
                  display: 'block',
                  letterSpacing: '0.5px'
                }}>
                  {(() => {
                    const hour = new Date().getHours();
                    if (hour < 12) return 'Good Morning';
                    if (hour < 18) return 'Good Afternoon';
                    return 'Good Evening';
                  })()}, {user?.firstName || testUser?.email?.split('@')[0] || 'Investor'}
                </Text>
              </div>

              {/* Portfolio Value */}
              <Row gutter={[32, 16]} align="middle">
                <Col xs={24} md={12}>
                  <div>
                    <Text style={{
                      fontSize: 14,
                      color: theme.colors.text.muted,
                      display: 'block',
                      marginBottom: 8,
                      fontWeight: 500,
                      letterSpacing: '1px',
                      textTransform: 'uppercase'
                    }}>
                      Total Portfolio Value
                    </Text>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
                      <Text style={{
                        fontSize: isMobile ? 36 : 56,
                        fontWeight: 700,
                        color: theme.colors.primary,
                        lineHeight: 1,
                        textShadow: `0 0 20px ${theme.colors.primary}40`
                      }}>
                        ${portfolioMetrics.totalValue.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </Text>
                    </div>
                  </div>
                </Col>

                <Col xs={24} md={12}>
                  {/* Today's P&L */}
                  <div style={{
                    background: portfolioMetrics.dayChange >= 0
                      ? `${theme.colors.success}15`
                      : `${theme.colors.error}15`,
                    border: `1px solid ${portfolioMetrics.dayChange >= 0 ? theme.colors.success : theme.colors.error}33`,
                    borderRadius: 12,
                    padding: isMobile ? '16px' : '20px 24px',
                    backdropFilter: 'blur(10px)',
                  }}>
                    <Text style={{
                      fontSize: 12,
                      color: theme.colors.text.muted,
                      display: 'block',
                      marginBottom: 8,
                      fontWeight: 500,
                      letterSpacing: '1px',
                      textTransform: 'uppercase'
                    }}>
                      Today's Change
                    </Text>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      {portfolioMetrics.dayChange >= 0 ? (
                        <RiseOutlined style={{
                          fontSize: isMobile ? 24 : 32,
                          color: theme.colors.success
                        }} />
                      ) : (
                        <FallOutlined style={{
                          fontSize: isMobile ? 24 : 32,
                          color: theme.colors.error
                        }} />
                      )}
                      <div>
                        <div style={{
                          fontSize: isMobile ? 24 : 32,
                          fontWeight: 700,
                          color: portfolioMetrics.dayChange >= 0 ? theme.colors.success : theme.colors.error,
                          lineHeight: 1.2
                        }}>
                          {portfolioMetrics.dayChange >= 0 ? '+' : ''}${Math.abs(portfolioMetrics.dayChange).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                        <div style={{
                          fontSize: 14,
                          color: portfolioMetrics.dayChange >= 0 ? theme.colors.success : theme.colors.error,
                          fontWeight: 600,
                          marginTop: 4
                        }}>
                          {portfolioMetrics.dayChangePercent >= 0 ? '+' : ''}{portfolioMetrics.dayChangePercent.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </div>
                </Col>
              </Row>
            </div>
          </GlassCard>

          {/* Stats Cards Row */}
          <Row gutter={[24, 24]} style={{ marginBottom: 32 }}>
            {[
              { title: 'Win Rate', value: portfolioMetrics.winRate, suffix: '%', precision: 2, icon: <TrophyOutlined />, color: theme.colors.success },
              { title: 'Total Return', value: portfolioMetrics.totalReturn, suffix: '%', precision: 2, icon: <RiseOutlined />, color: theme.colors.primary },
              { title: 'Sharpe Ratio', value: portfolioMetrics.sharpeRatio, precision: 2, icon: <LineChartOutlined />, color: theme.colors.warning },
              { title: 'AI Confidence', value: 85, suffix: '%', precision: 0, icon: <ThunderboltOutlined />, color: theme.colors.primary },
            ].map((stat, index) => (
              <Col key={index} xs={24} sm={12} md={6}>
                <GlassCard
                  style={{
                    padding: 24,
                    height: '100%',
                    background: theme.colors.background.elevated,
                    border: `1px solid ${theme.colors.border}`,
                    borderRadius: 8,
                  }}
                >
                  <Statistic
                    title={
                      <span style={{ color: theme.colors.text.muted, fontSize: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                        {stat.icon} {stat.title}
                      </span>
                    }
                    value={stat.value}
                    suffix={stat.suffix}
                    precision={stat.precision}
                    valueStyle={{ color: stat.color, fontSize: 32, fontWeight: 700 }}
                  />
                </GlassCard>
              </Col>
            ))}
          </Row>

          {/* Main Content Tabs - Updated to v5 API */}
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            size="large"
            tabBarStyle={{
              borderBottom: `1px solid ${theme.colors.border}`,
              marginBottom: 24,
            }}
            items={[
              {
                key: 'overview',
                label: (
                  <span style={{ fontSize: 14, fontWeight: 500 }}>
                    <GlobalOutlined /> Market Overview
                  </span>
                ),
                children: <MarketOverview watchlist={watchlist} />
              },
              {
                key: 'portfolio',
                label: (
                  <span style={{ fontSize: 14, fontWeight: 500 }}>
                    <SafetyOutlined /> Portfolio
                  </span>
                ),
                children: <Portfolio metrics={portfolioMetrics} />
              },
            ]}
          />
        </Content>
      </Layout>

      {/* Deep Analysis Drawer */}
      <Drawer
        placement="right"
        width={isMobile ? '100%' : isTablet ? '92%' : '85%'}
        open={deepAnalysisOpen}
        onClose={() => setDeepAnalysisOpen(false)}
        closable={false}
        mask={false}
        keyboard={true}
        zIndex={1000}
        bodyStyle={{
          padding: 0,
          background: theme.colors.background.primary,
          overflow: 'auto',
          height: '100vh',
        }}
      >
        {analysisSymbol && <DeepAnalysis symbol={analysisSymbol} onClose={() => setDeepAnalysisOpen(false)} />}
      </Drawer>

      {/* User Profile Drawer */}
      <UserProfile
        visible={showProfileDrawer}
        onClose={() => setShowProfileDrawer(false)}
      />
    </Layout>
  );
};

export default PremiumDashboard;