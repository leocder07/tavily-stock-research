import React, { useState, ReactNode } from 'react';
import { theme } from '../../styles/theme';

interface PremiumButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'glass';
  size?: 'small' | 'medium' | 'large';
  icon?: ReactNode;
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  haptic?: boolean;
  glow?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const PremiumButton: React.FC<PremiumButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  icon,
  loading = false,
  disabled = false,
  fullWidth = false,
  haptic = true,
  glow = false,
  className = '',
  style = {},
}) => {
  const [isPressed, setIsPressed] = useState(false);
  const [ripples, setRipples] = useState<{ x: number; y: number; id: number }[]>([]);

  const getVariantStyles = (): React.CSSProperties => {
    const variants = {
      primary: {
        background: theme.colors.gradient.primary,
        color: theme.colors.background.primary,
        border: 'none',
      },
      secondary: {
        background: 'transparent',
        color: theme.colors.primary,
        border: `2px solid ${theme.colors.primary}`,
      },
      success: {
        background: theme.colors.gradient.success,
        color: '#FFFFFF',
        border: 'none',
      },
      danger: {
        background: theme.colors.gradient.danger,
        color: '#FFFFFF',
        border: 'none',
      },
      glass: {
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(10px)',
        color: '#FFFFFF',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      },
    };
    return variants[variant];
  };

  const getSizeStyles = (): React.CSSProperties => {
    const sizes = {
      small: {
        padding: '8px 16px',
        fontSize: '12px',
        borderRadius: '8px',
      },
      medium: {
        padding: '12px 24px',
        fontSize: '14px',
        borderRadius: '12px',
      },
      large: {
        padding: '16px 32px',
        fontSize: '16px',
        borderRadius: '16px',
      },
    };
    return sizes[size];
  };

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled || loading) return;

    // Create ripple effect
    const button = e.currentTarget;
    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const newRipple = { x, y, id: Date.now() };
    
    setRipples(prev => [...prev, newRipple]);
    
    // Remove ripple after animation
    setTimeout(() => {
      setRipples(prev => prev.filter(r => r.id !== newRipple.id));
    }, 600);

    // Haptic feedback simulation
    if (haptic && navigator.vibrate) {
      navigator.vibrate(10);
    }

    // Trigger onClick
    if (onClick) {
      onClick();
    }
  };

  const handleMouseDown = () => {
    setIsPressed(true);
  };

  const handleMouseUp = () => {
    setIsPressed(false);
  };

  const buttonStyles: React.CSSProperties = {
    ...getVariantStyles(),
    ...getSizeStyles(),
    position: 'relative',
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    width: fullWidth ? '100%' : 'auto',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    overflow: 'hidden',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    transform: isPressed ? 'scale(0.98)' : 'scale(1)',
    boxShadow: glow
      ? variant === 'primary'
        ? '0 0 30px rgba(212, 175, 55, 0.4)'
        : variant === 'success'
        ? '0 0 30px rgba(0, 212, 170, 0.4)'
        : variant === 'danger'
        ? '0 0 30px rgba(255, 69, 58, 0.4)'
        : '0 4px 16px rgba(0, 0, 0, 0.2)'
      : '0 4px 16px rgba(0, 0, 0, 0.2)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    ...style,
  };

  return (
    <button
      className={`premium-button ${className}`}
      style={buttonStyles}
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      disabled={disabled || loading}
    >
      {/* Ripple effects */}
      {ripples.map(ripple => (
        <span
          key={ripple.id}
          style={{
            position: 'absolute',
            left: ripple.x,
            top: ripple.y,
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: 'rgba(255, 255, 255, 0.5)',
            transform: 'translate(-50%, -50%)',
            animation: 'ripple 0.6s ease-out',
            pointerEvents: 'none',
          }}
        />
      ))}

      {/* Shimmer effect */}
      <span
        style={{
          position: 'absolute',
          top: 0,
          left: '-100%',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent)',
          transition: 'left 0.5s ease',
          pointerEvents: 'none',
        }}
        className="shimmer"
      />

      {/* Loading spinner */}
      {loading ? (
        <div
          style={{
            width: '16px',
            height: '16px',
            border: '2px solid rgba(255, 255, 255, 0.3)',
            borderTopColor: '#FFFFFF',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
      ) : (
        <>
          {icon && <span style={{ display: 'flex', alignItems: 'center' }}>{icon}</span>}
          <span>{children}</span>
        </>
      )}
    </button>
  );
};

// Floating Action Button Component
export const FloatingActionButton: React.FC<{
  onClick?: () => void;
  icon: ReactNode;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
}> = ({ onClick, icon, position = 'bottom-right' }) => {
  const positionStyles: Record<string, React.CSSProperties> = {
    'bottom-right': { bottom: '24px', right: '24px' },
    'bottom-left': { bottom: '24px', left: '24px' },
    'top-right': { top: '24px', right: '24px' },
    'top-left': { top: '24px', left: '24px' },
  };

  return (
    <button
      onClick={onClick}
      style={{
        position: 'fixed',
        ...positionStyles[position],
        width: '56px',
        height: '56px',
        borderRadius: '50%',
        background: theme.colors.gradient.primary,
        color: theme.colors.background.primary,
        border: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        boxShadow: '0 8px 24px rgba(212, 175, 55, 0.4)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        animation: 'float 3s ease-in-out infinite',
        zIndex: 1000,
      }}
      className="fab"
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.1)';
        e.currentTarget.style.boxShadow = '0 12px 32px rgba(212, 175, 55, 0.6)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.boxShadow = '0 8px 24px rgba(212, 175, 55, 0.4)';
      }}
    >
      {icon}
    </button>
  );
};

export default PremiumButton;