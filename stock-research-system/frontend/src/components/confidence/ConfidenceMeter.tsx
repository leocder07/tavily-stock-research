import React from 'react';
import styled from 'styled-components';
import { Progress, Tooltip } from 'antd';
import {
  CheckCircleFilled,
  ExclamationCircleFilled,
  WarningFilled,
  ThunderboltFilled,
} from '@ant-design/icons';
import { theme } from '../../styles/theme';

interface ConfidenceMeterProps {
  confidence: number; // 0-1 or 0-100
  label?: string;
  size?: 'small' | 'medium' | 'large';
  showIcon?: boolean;
  showPercentage?: boolean;
  vertical?: boolean;
  animated?: boolean;
}

const MeterContainer = styled.div<{ size: string; vertical: boolean }>`
  display: flex;
  flex-direction: ${props => props.vertical ? 'column' : 'row'};
  align-items: center;
  gap: ${props => props.size === 'small' ? '8px' : props.size === 'medium' ? '12px' : '16px'};
  width: ${props => props.vertical ? 'auto' : '100%'};
`;

const MeterWrapper = styled.div<{ size: string; vertical: boolean }>`
  flex: 1;
  position: relative;
  width: ${props => props.vertical ? '40px' : '100%'};
  height: ${props => props.vertical ? '200px' : props.size === 'small' ? '8px' : props.size === 'medium' ? '12px' : '16px'};
`;

const ConfidenceIcon = styled.div<{ level: string; size: string }>`
  font-size: ${props => props.size === 'small' ? '20px' : props.size === 'medium' ? '28px' : '36px'};
  color: ${props =>
    props.level === 'high' ? theme.colors.success :
    props.level === 'medium' ? theme.colors.warning :
    theme.colors.danger
  };
  display: flex;
  align-items: center;
  justify-content: center;
  filter: ${props => props.level === 'high' ? 'drop-shadow(0 0 8px rgba(0, 212, 170, 0.4))' : 'none'};
  animation: ${props => props.level === 'high' ? 'pulse 2s ease-in-out infinite' : 'none'};

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }
`;

const ConfidenceLabel = styled.div<{ level: string; size: string }>`
  font-size: ${props => props.size === 'small' ? '12px' : props.size === 'medium' ? '14px' : '18px'};
  font-weight: 600;
  color: ${props =>
    props.level === 'high' ? theme.colors.success :
    props.level === 'medium' ? theme.colors.warning :
    theme.colors.danger
  };
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
`;

const PercentageDisplay = styled.div<{ size: string }>`
  font-size: ${props => props.size === 'small' ? '16px' : props.size === 'medium' ? '20px' : '28px'};
  font-weight: 700;
  color: ${theme.colors.text.primary};
  font-family: ${theme.typography.fontFamily.mono};
  min-width: ${props => props.size === 'small' ? '45px' : props.size === 'medium' ? '55px' : '70px'};
  text-align: right;
`;

const ConfidenceInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

const getConfidenceLevel = (confidence: number): { level: string; label: string; color: string; icon: React.ReactNode } => {
  // Normalize to 0-100 if needed
  const normalizedConfidence = confidence <= 1 ? confidence * 100 : confidence;

  if (normalizedConfidence >= 70) {
    return {
      level: 'high',
      label: 'High Confidence',
      color: theme.colors.success,
      icon: <CheckCircleFilled />
    };
  } else if (normalizedConfidence >= 40) {
    return {
      level: 'medium',
      label: 'Medium Confidence',
      color: theme.colors.warning,
      icon: <ExclamationCircleFilled />
    };
  } else {
    return {
      level: 'low',
      label: 'Low Confidence',
      color: theme.colors.danger,
      icon: <WarningFilled />
    };
  }
};

const getConfidenceDescription = (confidence: number): string => {
  const normalizedConfidence = confidence <= 1 ? confidence * 100 : confidence;

  if (normalizedConfidence >= 85) {
    return 'Extremely high confidence - Strong consensus across all agents';
  } else if (normalizedConfidence >= 70) {
    return 'High confidence - Most agents agree on recommendation';
  } else if (normalizedConfidence >= 55) {
    return 'Moderate confidence - Reasonable agent consensus';
  } else if (normalizedConfidence >= 40) {
    return 'Medium confidence - Mixed signals from agents';
  } else if (normalizedConfidence >= 25) {
    return 'Low confidence - Significant disagreement among agents';
  } else {
    return 'Very low confidence - High uncertainty, proceed with caution';
  }
};

const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  confidence,
  label,
  size = 'medium',
  showIcon = true,
  showPercentage = true,
  vertical = false,
  animated = true,
}) => {
  // Normalize confidence to 0-100
  const normalizedConfidence = confidence <= 1 ? confidence * 100 : confidence;
  const confidenceInfo = getConfidenceLevel(confidence);
  const description = getConfidenceDescription(confidence);

  return (
    <Tooltip title={description} placement={vertical ? 'right' : 'top'}>
      <MeterContainer size={size} vertical={vertical}>
        {showIcon && (
          <ConfidenceIcon level={confidenceInfo.level} size={size}>
            {confidenceInfo.level === 'high' && animated ? (
              <ThunderboltFilled />
            ) : (
              confidenceInfo.icon
            )}
          </ConfidenceIcon>
        )}

        <MeterWrapper size={size} vertical={vertical}>
          <Progress
            percent={normalizedConfidence}
            strokeColor={{
              '0%': confidenceInfo.color,
              '100%': confidenceInfo.level === 'high' ? theme.colors.primary : confidenceInfo.color,
            }}
            trailColor={theme.colors.background.elevated}
            strokeWidth={size === 'small' ? 8 : size === 'medium' ? 12 : 16}
            showInfo={false}
            strokeLinecap="round"
            style={{
              filter: confidenceInfo.level === 'high' ? `drop-shadow(0 0 6px ${confidenceInfo.color}40)` : 'none',
            }}
          />
        </MeterWrapper>

        <ConfidenceInfo>
          {showPercentage && (
            <PercentageDisplay size={size}>
              {normalizedConfidence.toFixed(0)}%
            </PercentageDisplay>
          )}
          {label && (
            <ConfidenceLabel level={confidenceInfo.level} size={size}>
              {label}
            </ConfidenceLabel>
          )}
        </ConfidenceInfo>
      </MeterContainer>
    </Tooltip>
  );
};

export default ConfidenceMeter;
