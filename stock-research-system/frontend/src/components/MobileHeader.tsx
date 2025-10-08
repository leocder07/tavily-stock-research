import React, { useState } from 'react';
import {
  Drawer,
  Space,
  Typography,
  
  Button,
  Input,
  Badge,
  Row,
  Col,
} from 'antd';
import {
  MenuOutlined,
  SearchOutlined,
  RocketOutlined,
  BellOutlined,
  CloseOutlined,
  HomeOutlined,
  LineChartOutlined,
  WalletOutlined,
  
  SettingOutlined,
  GlobalOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { theme } from '../styles/theme';
import { EnhancedAuthHeader } from './EnhancedAuthHeader';

const { Title, Text } = Typography;

interface MobileHeaderProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onSearch: (value: string) => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
  marketSentiment: string;
}

const navigationItems = [
  { key: 'overview', label: 'Dashboard', icon: <HomeOutlined /> },
  { key: 'analysis', label: 'Stock Analysis', icon: <LineChartOutlined /> },
  { key: 'portfolio', label: 'Portfolio', icon: <WalletOutlined /> },
  { key: 'signals', label: 'Trading Signals', icon: <TrophyOutlined /> },
  { key: 'market', label: 'Market Overview', icon: <GlobalOutlined /> },
  { key: 'settings', label: 'Settings', icon: <SettingOutlined /> },
];

export const MobileHeader: React.FC<MobileHeaderProps> = ({
  searchQuery,
  onSearchChange,
  onSearch,
  activeTab,
  onTabChange,
  marketSentiment,
}) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchExpanded, setSearchExpanded] = useState(false);

  return (
    <>
      {/* Mobile Header */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: '60px',
          background: 'rgba(0, 0, 0, 0.95)',
          backdropFilter: 'blur(20px)',
          borderBottom: `1px solid ${theme.colors.border}`,
          zIndex: 1000,
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Row style={{ width: '100%' }} align="middle" justify="space-between">
          {/* Left: Menu & Logo */}
          <Col>
            <Space size={12}>
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={() => setMenuOpen(true)}
                style={{
                  color: theme.colors.text.primary,
                  fontSize: '20px',
                  height: '40px',
                  width: '40px',
                }}
              />

              {!searchExpanded && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 10,
                      background: theme.colors.gradient.primary,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <RocketOutlined style={{ fontSize: 16, color: theme.colors.background.primary }} />
                  </div>
                  <Title level={5} style={{ margin: 0, color: theme.colors.text.primary, fontSize: '16px' }}>
                    StockAI
                  </Title>
                </div>
              )}
            </Space>
          </Col>

          {/* Center/Right: Search & Actions */}
          <Col>
            <Space size={8}>
              {searchExpanded ? (
                <Input
                  placeholder="Search stocks..."
                  value={searchQuery}
                  onChange={(e) => onSearchChange(e.target.value)}
                  onPressEnter={(e) => onSearch((e.target as HTMLInputElement).value)}
                  onBlur={() => setSearchExpanded(false)}
                  autoFocus
                  style={{
                    width: '200px',
                    borderRadius: '20px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    border: `1px solid ${theme.colors.border}`,
                  }}
                  suffix={
                    <CloseOutlined
                      onClick={() => setSearchExpanded(false)}
                      style={{ color: theme.colors.text.secondary }}
                    />
                  }
                />
              ) : (
                <>
                  <Button
                    type="text"
                    icon={<SearchOutlined />}
                    onClick={() => setSearchExpanded(true)}
                    style={{
                      color: theme.colors.text.primary,
                      fontSize: '18px',
                      height: '36px',
                      width: '36px',
                    }}
                  />

                  <Badge dot>
                    <Button
                      type="text"
                      icon={<BellOutlined />}
                      style={{
                        color: theme.colors.text.primary,
                        fontSize: '18px',
                        height: '36px',
                        width: '36px',
                      }}
                    />
                  </Badge>
                </>
              )}
            </Space>
          </Col>
        </Row>
      </div>

      {/* Mobile Navigation Drawer */}
      <Drawer
        placement="left"
        onClose={() => setMenuOpen(false)}
        open={menuOpen}
        width={280}
        styles={{
          body: {
            background: theme.colors.background.secondary,
            padding: 0,
          },
          header: {
            background: theme.colors.background.secondary,
            borderBottom: `1px solid ${theme.colors.border}`,
            padding: '16px',
          },
        }}
        closeIcon={<CloseOutlined style={{ color: theme.colors.text.secondary }} />}
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 12,
                background: theme.colors.gradient.primary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <RocketOutlined style={{ fontSize: 20, color: theme.colors.background.primary }} />
            </div>
            <div>
              <Title level={4} style={{ margin: 0, color: theme.colors.text.primary }}>
                StockAI Pro
              </Title>
              <Text style={{ fontSize: 10, color: theme.colors.text.muted }}>
                PREMIUM RESEARCH
              </Text>
            </div>
          </div>
        }
      >
        {/* Market Status Badge */}
        <div style={{ padding: '16px', borderBottom: `1px solid ${theme.colors.border}` }}>
          <Badge
            count={
              <div
                style={{
                  padding: '6px 12px',
                  background: marketSentiment === 'bullish'
                    ? theme.colors.gradient.success
                    : theme.colors.gradient.danger,
                  borderRadius: 20,
                  fontSize: 11,
                  fontWeight: 700,
                  color: '#fff',
                }}
              >
                {marketSentiment === 'bullish' ? '🔥 BULL MARKET' : '🐻 BEAR MARKET'}
              </div>
            }
          />
        </div>

        {/* Navigation Items */}
        <div style={{ padding: '8px 0' }}>
          {navigationItems.map((item) => (
            <div
              key={item.key}
              onClick={() => {
                onTabChange(item.key);
                setMenuOpen(false);
              }}
              style={{
                padding: '14px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                cursor: 'pointer',
                background: activeTab === item.key
                  ? `linear-gradient(90deg, ${theme.colors.primary}22, transparent)`
                  : 'transparent',
                borderLeft: activeTab === item.key
                  ? `3px solid ${theme.colors.primary}`
                  : '3px solid transparent',
                transition: 'all 0.3s ease',
              }}
            >
              <span style={{
                fontSize: 20,
                color: activeTab === item.key ? theme.colors.primary : theme.colors.text.secondary
              }}>
                {item.icon}
              </span>
              <Text style={{
                fontSize: 15,
                color: activeTab === item.key ? theme.colors.text.primary : theme.colors.text.secondary,
                fontWeight: activeTab === item.key ? 600 : 400,
              }}>
                {item.label}
              </Text>
            </div>
          ))}
        </div>

        {/* User Profile Section at Bottom */}
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          padding: '16px',
          borderTop: `1px solid ${theme.colors.border}`,
        }}>
          <EnhancedAuthHeader />
        </div>
      </Drawer>
    </>
  );
};