import React from 'react';
import styled from 'styled-components';
import { Alert, Space } from 'antd';
import {
  ExclamationCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { theme } from '../../styles/theme';

interface ConfidenceWarningProps {
  confidence: number; // 0-1 or 0-100
  showAlways?: boolean; // Show even for high confidence
  customMessage?: string;
  reasons?: string[];
}

const WarningContainer = styled.div`
  margin: 16px 0;
`;

const StyledAlert = styled(Alert)<{ confidenceLevel: string }>`
  background: ${props =>
    props.confidenceLevel === 'low' ? `${theme.colors.danger}15` :
    props.confidenceLevel === 'medium' ? `${theme.colors.warning}15` :
    `${theme.colors.success}15`
  };
  border: 1px solid ${props =>
    props.confidenceLevel === 'low' ? `${theme.colors.danger}40` :
    props.confidenceLevel === 'medium' ? `${theme.colors.warning}40` :
    `${theme.colors.success}40`
  };
  border-radius: ${theme.borderRadius.md};

  .ant-alert-message {
    color: ${theme.colors.text.primary};
    font-weight: 600;
  }

  .ant-alert-description {
    color: ${theme.colors.text.secondary};
  }
`;

const ReasonsList = styled.ul`
  margin: 8px 0 0 0;
  padding-left: 20px;

  li {
    color: ${theme.colors.text.secondary};
    font-size: 13px;
    margin: 4px 0;
  }
`;

const ConfidenceWarning: React.FC<ConfidenceWarningProps> = ({
  confidence,
  showAlways = false,
  customMessage,
  reasons = [],
}) => {
  const normalizedConfidence = confidence <= 1 ? confidence * 100 : confidence;

  const getWarningConfig = () => {
    if (normalizedConfidence >= 70) {
      return {
        show: showAlways,
        type: 'success' as const,
        level: 'high',
        icon: <InfoCircleOutlined />,
        message: 'High Confidence Analysis',
        description: customMessage || 'This recommendation is backed by strong consensus across multiple agents and data sources.',
      };
    } else if (normalizedConfidence >= 40) {
      return {
        show: true,
        type: 'warning' as const,
        level: 'medium',
        icon: <ExclamationCircleOutlined />,
        message: 'Moderate Confidence - Exercise Caution',
        description: customMessage || 'Some uncertainty exists in this analysis. Consider additional research and risk management.',
      };
    } else {
      return {
        show: true,
        type: 'error' as const,
        level: 'low',
        icon: <WarningOutlined />,
        message: 'Low Confidence - High Uncertainty',
        description: customMessage || 'Significant uncertainty detected. This recommendation should be treated with extreme caution. Agents show conflicting signals.',
      };
    }
  };

  const config = getWarningConfig();

  if (!config.show) {
    return null;
  }

  const defaultReasons = reasons.length > 0 ? reasons : (() => {
    if (normalizedConfidence >= 70) {
      return [
        'Strong agreement across multiple analysis agents',
        'High-quality data with minimal gaps',
        'Clear technical and fundamental signals',
      ];
    } else if (normalizedConfidence >= 40) {
      return [
        'Mixed signals from different analysis methods',
        'Some data quality concerns or gaps',
        'Market conditions may be uncertain',
      ];
    } else {
      return [
        'Significant disagreement between agents',
        'Limited or low-quality data available',
        'Conflicting technical and fundamental signals',
        'High market volatility or unusual conditions',
      ];
    }
  })();

  return (
    <WarningContainer>
      <StyledAlert
        type={config.type}
        confidenceLevel={config.level}
        icon={config.icon}
        message={
          <Space>
            {config.message}
            <span style={{
              fontFamily: theme.typography.fontFamily.mono,
              fontSize: '12px',
              opacity: 0.8,
            }}>
              ({normalizedConfidence.toFixed(0)}%)
            </span>
          </Space>
        }
        description={
          <>
            {config.description}
            {defaultReasons.length > 0 && (
              <ReasonsList>
                {defaultReasons.map((reason, index) => (
                  <li key={index}>{reason}</li>
                ))}
              </ReasonsList>
            )}
          </>
        }
        showIcon
      />
    </WarningContainer>
  );
};

export default ConfidenceWarning;
