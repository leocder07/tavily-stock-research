import React from 'react';
import styled from 'styled-components';
import { Tooltip, Badge } from 'antd';
import {
  CheckCircleFilled,
  ExclamationCircleFilled,
  WarningFilled,
} from '@ant-design/icons';
import { theme } from '../../styles/theme';

interface ConfidenceBadgeProps {
  confidence: number; // 0-1 or 0-100
  size?: 'small' | 'default' | 'large';
  showIcon?: boolean;
  showLabel?: boolean;
  inline?: boolean;
  pulse?: boolean;
}

const BadgeContainer = styled.span<{ inline: boolean }>`
  display: ${props => props.inline ? 'inline-flex' : 'flex'};
  align-items: center;
  gap: 6px;
`;

const StyledBadge = styled.span<{
  level: string;
  size: string;
  pulse: boolean;
}>`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: ${props =>
    props.size === 'small' ? '2px 8px' :
    props.size === 'large' ? '6px 16px' :
    '4px 12px'
  };
  background: ${props =>
    props.level === 'high' ? `${theme.colors.success}15` :
    props.level === 'medium' ? `${theme.colors.warning}15` :
    `${theme.colors.danger}15`
  };
  border: 1px solid ${props =>
    props.level === 'high' ? `${theme.colors.success}40` :
    props.level === 'medium' ? `${theme.colors.warning}40` :
    `${theme.colors.danger}40`
  };
  border-radius: ${theme.borderRadius.full};
  font-size: ${props =>
    props.size === 'small' ? '11px' :
    props.size === 'large' ? '14px' :
    '12px'
  };
  font-weight: 600;
  color: ${props =>
    props.level === 'high' ? theme.colors.success :
    props.level === 'medium' ? theme.colors.warning :
    theme.colors.danger
  };
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  animation: ${props => props.pulse && props.level === 'high' ? 'badgePulse 2s ease-in-out infinite' : 'none'};
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.05);
    box-shadow: ${props =>
      props.level === 'high' ? `0 0 12px ${theme.colors.success}30` :
      props.level === 'medium' ? `0 0 12px ${theme.colors.warning}30` :
      `0 0 12px ${theme.colors.danger}30`
    };
  }

  @keyframes badgePulse {
    0%, 100% {
      box-shadow: 0 0 0 0 ${theme.colors.success}40;
    }
    50% {
      box-shadow: 0 0 8px 4px ${theme.colors.success}20;
    }
  }
`;

const IconWrapper = styled.span<{ level: string }>`
  font-size: inherit;
  display: flex;
  align-items: center;
  color: ${props =>
    props.level === 'high' ? theme.colors.success :
    props.level === 'medium' ? theme.colors.warning :
    theme.colors.danger
  };
`;

const ConfidenceText = styled.span`
  font-family: ${theme.typography.fontFamily.mono};
  font-weight: 700;
`;

const getConfidenceInfo = (confidence: number): {
  level: string;
  label: string;
  icon: React.ReactNode;
  description: string;
} => {
  const normalizedConfidence = confidence <= 1 ? confidence * 100 : confidence;

  if (normalizedConfidence >= 70) {
    return {
      level: 'high',
      label: 'High',
      icon: <CheckCircleFilled />,
      description: `${normalizedConfidence.toFixed(0)}% confidence - Strong signal`,
    };
  } else if (normalizedConfidence >= 40) {
    return {
      level: 'medium',
      label: 'Med',
      icon: <ExclamationCircleFilled />,
      description: `${normalizedConfidence.toFixed(0)}% confidence - Moderate signal`,
    };
  } else {
    return {
      level: 'low',
      label: 'Low',
      icon: <WarningFilled />,
      description: `${normalizedConfidence.toFixed(0)}% confidence - Weak signal`,
    };
  }
};

const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  confidence,
  size = 'default',
  showIcon = true,
  showLabel = true,
  inline = false,
  pulse = false,
}) => {
  const normalizedConfidence = confidence <= 1 ? confidence * 100 : confidence;
  const confidenceInfo = getConfidenceInfo(confidence);

  const badgeContent = (
    <StyledBadge level={confidenceInfo.level} size={size} pulse={pulse}>
      {showIcon && (
        <IconWrapper level={confidenceInfo.level}>
          {confidenceInfo.icon}
        </IconWrapper>
      )}
      <ConfidenceText>
        {normalizedConfidence.toFixed(0)}%
      </ConfidenceText>
      {showLabel && (
        <span>{confidenceInfo.label}</span>
      )}
    </StyledBadge>
  );

  return (
    <Tooltip title={confidenceInfo.description} placement="top">
      <BadgeContainer inline={inline}>
        {badgeContent}
      </BadgeContainer>
    </Tooltip>
  );
};

export default ConfidenceBadge;
