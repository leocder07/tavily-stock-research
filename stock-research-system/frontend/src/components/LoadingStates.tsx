import React from 'react';
import { Skeleton, Space, Card, Spin, Row, Col } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import { theme } from '../styles/theme';

// Custom loading spinner
export const PremiumSpinner: React.FC<{ size?: 'small' | 'default' | 'large' }> = ({
  size = 'default'
}) => {
  const sizes = {
    small: 24,
    default: 40,
    large: 60
  };

  return (
    <Spin
      indicator={
        <LoadingOutlined
          style={{
            fontSize: sizes[size],
            background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.warning})`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
          spin
        />
      }
    />
  );
};

// Stock card skeleton
export const StockCardSkeleton: React.FC = () => (
  <Card
    style={{
      background: 'rgba(255, 255, 255, 0.03)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      borderRadius: '16px',
    }}
  >
    <Skeleton active paragraph={{ rows: 2 }} />
  </Card>
);

// Portfolio skeleton
export const PortfolioSkeleton: React.FC = () => (
  <Card
    style={{
      background: 'rgba(255, 255, 255, 0.03)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      borderRadius: '16px',
      padding: '24px',
    }}
  >
    <Skeleton.Avatar active size="large" shape="circle" />
    <Skeleton active title paragraph={{ rows: 3 }} />
  </Card>
);

// Dashboard skeleton
export const DashboardSkeleton: React.FC = () => (
  <div style={{ padding: '24px' }}>
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={16}>
        <PortfolioSkeleton />
      </Col>
      <Col xs={24} lg={8}>
        <Space direction="vertical" style={{ width: '100%' }} size={16}>
          <StockCardSkeleton />
          <StockCardSkeleton />
          <StockCardSkeleton />
        </Space>
      </Col>
    </Row>
    <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
      {[1, 2, 3, 4].map(key => (
        <Col xs={24} sm={12} lg={6} key={key}>
          <StockCardSkeleton />
        </Col>
      ))}
    </Row>
  </div>
);

// Chart skeleton
export const ChartSkeleton: React.FC<{ height?: number }> = ({ height = 400 }) => (
  <Card
    style={{
      background: 'rgba(255, 255, 255, 0.03)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      borderRadius: '16px',
      height,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <PremiumSpinner size="large" />
  </Card>
);

// Table skeleton
export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <Card
    style={{
      background: 'rgba(255, 255, 255, 0.03)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      borderRadius: '16px',
    }}
  >
    <Space direction="vertical" style={{ width: '100%' }} size={16}>
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} active paragraph={{ rows: 1 }} />
      ))}
    </Space>
  </Card>
);

// Full page loading
export const FullPageLoader: React.FC<{ message?: string }> = ({
  message = 'Loading...'
}) => (
  <div
    style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: theme.colors.background.primary,
      zIndex: 9999,
    }}
  >
    <PremiumSpinner size="large" />
    <div
      style={{
        marginTop: '24px',
        fontSize: '18px',
        color: theme.colors.text.secondary,
        fontWeight: 500,
      }}
    >
      {message}
    </div>
  </div>
);

// Inline loader
export const InlineLoader: React.FC<{ text?: string }> = ({
  text = 'Loading'
}) => (
  <Space>
    <PremiumSpinner size="small" />
    <span style={{ color: theme.colors.text.secondary }}>{text}</span>
  </Space>
);

// Shimmer effect
export const ShimmerEffect: React.FC<{ width?: string; height?: string }> = ({
  width = '100%',
  height = '20px',
}) => (
  <div
    style={{
      width,
      height,
      background: `linear-gradient(
        90deg,
        rgba(255, 255, 255, 0.05) 25%,
        rgba(255, 255, 255, 0.1) 50%,
        rgba(255, 255, 255, 0.05) 75%
      )`,
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite',
      borderRadius: '4px',
    }}
  />
);

// Add shimmer animation to global styles
const shimmerStyle = document.createElement('style');
shimmerStyle.textContent = `
  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
`;
document.head.appendChild(shimmerStyle);

export default {
  PremiumSpinner,
  StockCardSkeleton,
  PortfolioSkeleton,
  DashboardSkeleton,
  ChartSkeleton,
  TableSkeleton,
  FullPageLoader,
  InlineLoader,
  ShimmerEffect,
};