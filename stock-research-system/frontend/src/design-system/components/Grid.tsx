import React, { ReactNode, CSSProperties } from 'react';
import { Row, Col } from 'antd';
import { useResponsive } from '../hooks/useResponsive';
import { designTokens } from '../tokens';

interface GridProps {
  children: ReactNode;
  gutter?: number | [number, number];
  align?: 'top' | 'middle' | 'bottom';
  justify?: 'start' | 'end' | 'center' | 'space-around' | 'space-between' | 'space-evenly';
  wrap?: boolean;
  style?: CSSProperties;
  className?: string;
}

export const Grid: React.FC<GridProps> = ({
  children,
  gutter,
  align = 'top',
  justify = 'start',
  wrap = true,
  style,
  className,
}) => {
  const { isMobile, isTablet } = useResponsive();

  // Responsive gutter
  const responsiveGutter = gutter || (
    isMobile ? [12, 12] : isTablet ? [16, 16] : [24, 24]
  );

  return (
    <Row
      gutter={responsiveGutter}
      align={align}
      justify={justify}
      wrap={wrap}
      style={style}
      className={className}
    >
      {children}
    </Row>
  );
};

interface GridItemProps {
  children: ReactNode;
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
  xxl?: number;
  span?: number;
  offset?: number;
  order?: number;
  flex?: string | number;
  style?: CSSProperties;
  className?: string;
}

export const GridItem: React.FC<GridItemProps> = ({
  children,
  xs = 24,
  sm,
  md,
  lg,
  xl,
  xxl,
  span,
  offset = 0,
  order = 0,
  flex,
  style,
  className,
}) => {
  return (
    <Col
      xs={xs}
      sm={sm || xs}
      md={md || sm || xs}
      lg={lg || md || sm || xs}
      xl={xl || lg || md || sm || xs}
      xxl={xxl || xl || lg || md || sm || xs}
      span={span}
      offset={offset}
      order={order}
      flex={flex}
      style={style}
      className={className}
    >
      {children}
    </Col>
  );
};

// Container Component for consistent max-width and padding
interface ContainerProps {
  children: ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  noPadding?: boolean;
  style?: CSSProperties;
  className?: string;
}

export const Container: React.FC<ContainerProps> = ({
  children,
  maxWidth = 'xl',
  noPadding = false,
  style,
  className,
}) => {
  const { isMobile } = useResponsive();

  const maxWidthValues = {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1440px',
    full: '100%',
  };

  const padding = noPadding ? 0 : (
    isMobile
      ? designTokens.layout.containerPaddingMobile
      : designTokens.layout.containerPadding
  );

  return (
    <div
      style={{
        maxWidth: maxWidthValues[maxWidth],
        margin: '0 auto',
        padding,
        width: '100%',
        ...style,
      }}
      className={className}
    >
      {children}
    </div>
  );
};

// Spacer Component for consistent spacing
interface SpacerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl';
  horizontal?: boolean;
}

export const Spacer: React.FC<SpacerProps> = ({ size = 'md', horizontal = false }) => {
  const spacing = {
    xs: designTokens.spacing[2],
    sm: designTokens.spacing[3],
    md: designTokens.spacing[4],
    lg: designTokens.spacing[6],
    xl: designTokens.spacing[8],
    '2xl': designTokens.spacing[12],
    '3xl': designTokens.spacing[16],
  };

  return (
    <div
      style={horizontal
        ? { width: spacing[size], display: 'inline-block' }
        : { height: spacing[size] }
      }
    />
  );
};