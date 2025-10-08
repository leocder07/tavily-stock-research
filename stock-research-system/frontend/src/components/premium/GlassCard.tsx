import React, { ReactNode, CSSProperties } from 'react';
import { theme } from '../../styles/theme';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  hoverable?: boolean;
  glowOnHover?: boolean;
  borderGradient?: boolean;
  onClick?: () => void;
  intensity?: 'light' | 'medium' | 'heavy';
}

const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  style = {},
  hoverable = false,
  glowOnHover = false,
  borderGradient = false,
  onClick,
  intensity = 'medium',
}) => {
  const getIntensityStyles = () => {
    switch (intensity) {
      case 'light':
        return {
          background: 'rgba(255, 255, 255, 0.03)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
        };
      case 'heavy':
        return {
          background: 'rgba(255, 255, 255, 0.08)',
          backdropFilter: 'blur(30px)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
        };
      default:
        return {
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        };
    }
  };

  const baseStyles: CSSProperties = {
    ...getIntensityStyles(),
    borderRadius: '16px',
    padding: '24px',
    position: 'relative',
    overflow: 'hidden',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
    ...style,
  };

  const hoverStyles: CSSProperties = hoverable
    ? {
        cursor: 'pointer',
      }
    : {};

  const handleMouseEnter = (e: React.MouseEvent<HTMLDivElement>) => {
    if (hoverable) {
      e.currentTarget.style.transform = 'translateY(-4px) scale(1.02)';
      e.currentTarget.style.boxShadow = '0 16px 48px rgba(0, 0, 0, 0.5)';
    }
    if (glowOnHover) {
      e.currentTarget.style.boxShadow = '0 0 30px rgba(212, 175, 55, 0.4)';
      e.currentTarget.style.borderColor = 'rgba(212, 175, 55, 0.5)';
    }
  };

  const handleMouseLeave = (e: React.MouseEvent<HTMLDivElement>) => {
    if (hoverable) {
      e.currentTarget.style.transform = 'translateY(0) scale(1)';
    }
    e.currentTarget.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.4)';
    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
  };

  return (
    <div
      className={`glass-card ${className}`}
      style={{ ...baseStyles, ...hoverStyles }}
      onClick={onClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {borderGradient && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: '16px',
            padding: '1px',
            background: theme.colors.gradient.primary,
            WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
            WebkitMaskComposite: 'exclude',
            maskComposite: 'exclude',
            pointerEvents: 'none',
          }}
        />
      )}
      
      {/* Shimmer effect overlay */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: '-100%',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.05), transparent)',
          transition: 'left 0.6s ease',
          pointerEvents: 'none',
        }}
        className="shimmer-overlay"
      />
      
      <div style={{ position: 'relative', zIndex: 1 }}>
        {children}
      </div>
    </div>
  );
};

export default GlassCard;