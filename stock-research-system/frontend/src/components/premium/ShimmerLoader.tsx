import React from 'react';
import { theme } from '../../styles/theme';

interface ShimmerLoaderProps {
  variant?: 'text' | 'card' | 'avatar' | 'chart' | 'table';
  width?: string | number;
  height?: string | number;
  rows?: number;
  className?: string;
}

const ShimmerLoader: React.FC<ShimmerLoaderProps> = ({
  variant = 'text',
  width,
  height,
  rows = 1,
  className = '',
}) => {
  const baseStyles: React.CSSProperties = {
    background: `linear-gradient(
      90deg,
      ${theme.colors.background.secondary} 25%,
      ${theme.colors.background.elevated} 50%,
      ${theme.colors.background.secondary} 75%
    )`,
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s infinite',
    borderRadius: '8px',
  };

  const renderVariant = () => {
    switch (variant) {
      case 'text':
        return Array.from({ length: rows }).map((_, index) => (
          <div
            key={index}
            style={{
              ...baseStyles,
              width: width || `${Math.random() * 30 + 70}%`,
              height: height || '16px',
              marginBottom: index < rows - 1 ? '8px' : 0,
            }}
            className={className}
          />
        ));

      case 'card':
        return (
          <div
            style={{
              ...baseStyles,
              width: width || '100%',
              height: height || '200px',
              padding: '20px',
            }}
            className={className}
          >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
              <div
                style={{
                  ...baseStyles,
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  marginRight: '12px',
                  background: theme.colors.background.primary,
                }}
              />
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    ...baseStyles,
                    width: '60%',
                    height: '12px',
                    marginBottom: '8px',
                    background: theme.colors.background.primary,
                  }}
                />
                <div
                  style={{
                    ...baseStyles,
                    width: '40%',
                    height: '10px',
                    background: theme.colors.background.primary,
                  }}
                />
              </div>
            </div>
            <div
              style={{
                ...baseStyles,
                width: '100%',
                height: '60px',
                background: theme.colors.background.primary,
              }}
            />
          </div>
        );

      case 'avatar':
        return (
          <div
            style={{
              ...baseStyles,
              width: width || '48px',
              height: height || '48px',
              borderRadius: '50%',
            }}
            className={className}
          />
        );

      case 'chart':
        return (
          <div
            style={{
              width: width || '100%',
              height: height || '300px',
              position: 'relative',
              overflow: 'hidden',
            }}
            className={className}
          >
            {/* Chart bars */}
            <div style={{ display: 'flex', alignItems: 'flex-end', height: '100%', gap: '8px' }}>
              {Array.from({ length: 12 }).map((_, index) => (
                <div
                  key={index}
                  style={{
                    ...baseStyles,
                    flex: 1,
                    height: `${Math.random() * 60 + 40}%`,
                    animationDelay: `${index * 0.1}s`,
                  }}
                />
              ))}
            </div>
          </div>
        );

      case 'table':
        return (
          <div className={className}>
            {/* Table header */}
            <div
              style={{
                display: 'flex',
                gap: '16px',
                padding: '12px',
                borderBottom: `1px solid ${theme.colors.background.elevated}`,
              }}
            >
              {Array.from({ length: 4 }).map((_, index) => (
                <div
                  key={index}
                  style={{
                    ...baseStyles,
                    flex: index === 0 ? 2 : 1,
                    height: '12px',
                  }}
                />
              ))}
            </div>
            {/* Table rows */}
            {Array.from({ length: rows || 5 }).map((_, rowIndex) => (
              <div
                key={rowIndex}
                style={{
                  display: 'flex',
                  gap: '16px',
                  padding: '16px 12px',
                  borderBottom: `1px solid ${theme.colors.background.elevated}`,
                }}
              >
                {Array.from({ length: 4 }).map((_, colIndex) => (
                  <div
                    key={colIndex}
                    style={{
                      ...baseStyles,
                      flex: colIndex === 0 ? 2 : 1,
                      height: '14px',
                      animationDelay: `${(rowIndex * 4 + colIndex) * 0.1}s`,
                    }}
                  />
                ))}
              </div>
            ))}
          </div>
        );

      default:
        return null;
    }
  };

  return <>{renderVariant()}</>;
};

// Skeleton Screen Component for full page loading
export const SkeletonScreen: React.FC<{ sections?: number }> = ({ sections = 3 }) => {
  return (
    <div style={{ padding: '24px' }}>
      {/* Header skeleton */}
      <div style={{ marginBottom: '32px' }}>
        <ShimmerLoader variant="text" width="200px" height="32px" />
        <div style={{ marginTop: '8px' }}>
          <ShimmerLoader variant="text" width="400px" height="16px" />
        </div>
      </div>

      {/* Content sections */}
      {Array.from({ length: sections }).map((_, index) => (
        <div key={index} style={{ marginBottom: '24px' }}>
          <ShimmerLoader variant="card" height="180px" />
        </div>
      ))}
    </div>
  );
};

// Loading Dots Component
export const LoadingDots: React.FC = () => {
  return (
    <div className="loading-dots" style={{ display: 'inline-flex', gap: '4px' }}>
      <span style={{ animationDelay: '0s' }}></span>
      <span style={{ animationDelay: '0.1s' }}></span>
      <span style={{ animationDelay: '0.2s' }}></span>
    </div>
  );
};

export default ShimmerLoader;