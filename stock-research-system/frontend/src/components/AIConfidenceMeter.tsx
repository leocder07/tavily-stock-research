import React from 'react';
import { Card, Progress, Typography, Space, Tag, Row, Col } from 'antd';
import {
  ThunderboltOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { theme } from '../styles/theme';

const { Text, Title } = Typography;

interface AIConfidenceMeterProps {
  confidence: number;
  factors: {
    technical: number;
    fundamental: number;
    sentiment: number;
    macro: number;
  };
  recommendation: 'buy' | 'sell' | 'hold';
  riskLevel: 'low' | 'medium' | 'high';
}

const AIConfidenceMeter: React.FC<AIConfidenceMeterProps> = ({
  confidence,
  factors,
  recommendation,
  riskLevel,
}) => {
  const getConfidenceColor = (score: number) => {
    if (score >= 80) return theme.colors.success;
    if (score >= 60) return theme.colors.warning;
    return theme.colors.danger;
  };

  const getConfidenceIcon = (score: number) => {
    if (score >= 80) return <CheckCircleOutlined />;
    if (score >= 60) return <ExclamationCircleOutlined />;
    return <CloseCircleOutlined />;
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return theme.colors.success;
      case 'medium': return theme.colors.warning;
      case 'high': return theme.colors.danger;
      default: return theme.colors.neutral;
    }
  };

  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'buy': return theme.colors.success;
      case 'sell': return theme.colors.danger;
      case 'hold': return theme.colors.warning;
      default: return theme.colors.neutral;
    }
  };

  return (
    <Card
      style={{
        background: theme.effects.glassMorphism.background,
        backdropFilter: theme.effects.glassMorphism.backdropFilter,
        border: theme.effects.glassMorphism.border,
        borderRadius: theme.borderRadius.lg,
        boxShadow: theme.shadows.glass,
      }}
    >
      {/* Main Confidence Display */}
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <div style={{
          position: 'relative',
          display: 'inline-block',
          marginBottom: 16,
        }}>
          <Progress
            type="circle"
            percent={confidence}
            size={120}
            strokeColor={{
              '0%': getConfidenceColor(confidence),
              '100%': theme.colors.primary,
            }}
            trailColor={theme.colors.background.elevated}
            strokeWidth={8}
            format={() => (
              <div style={{ textAlign: 'center' }}>
                <div style={{
                  fontSize: 28,
                  fontWeight: 700,
                  color: theme.colors.primary,
                  lineHeight: 1,
                }}>
                  {confidence}%
                </div>
                <div style={{
                  fontSize: 12,
                  color: theme.colors.text.secondary,
                  marginTop: 4,
                }}>
                  AI Confidence
                </div>
              </div>
            )}
          />
          <div style={{
            position: 'absolute',
            top: -8,
            right: -8,
            background: theme.colors.gradient.cyan,
            borderRadius: '50%',
            width: 32,
            height: 32,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: theme.shadows.cyanGlow,
          }}>
            <ThunderboltOutlined style={{ color: '#fff', fontSize: 16 }} />
          </div>
        </div>

        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Tag
            color={getRecommendationColor(recommendation)}
            style={{
              fontSize: 14,
              fontWeight: 600,
              padding: '4px 12px',
              textTransform: 'uppercase',
              letterSpacing: 1,
            }}
          >
            {recommendation}
          </Tag>
          <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>
            Risk Level: <span style={{ color: getRiskColor(riskLevel), fontWeight: 600 }}>
              {riskLevel.toUpperCase()}
            </span>
          </Text>
        </Space>
      </div>

      {/* Factor Breakdown */}
      <div>
        <Title level={5} style={{
          color: theme.colors.text.primary,
          marginBottom: 16,
          textAlign: 'center',
        }}>
          Analysis Factors
        </Title>

        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {Object.entries(factors).map(([factor, score]) => (
            <div key={factor}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 8,
              }}>
                <Space>
                  {getConfidenceIcon(score)}
                  <Text style={{
                    color: theme.colors.text.primary,
                    textTransform: 'capitalize',
                    fontSize: 13,
                    fontWeight: 500,
                  }}>
                    {factor}
                  </Text>
                </Space>
                <Text style={{
                  color: getConfidenceColor(score),
                  fontSize: 13,
                  fontWeight: 600,
                }}>
                  {score}%
                </Text>
              </div>
              <Progress
                percent={score}
                strokeColor={getConfidenceColor(score)}
                trailColor={theme.colors.background.elevated}
                strokeWidth={6}
                showInfo={false}
                style={{ marginBottom: 4 }}
              />
            </div>
          ))}
        </Space>
      </div>

      {/* Confidence Indicators */}
      <div style={{
        marginTop: 20,
        padding: 16,
        background: theme.colors.background.elevated,
        borderRadius: theme.borderRadius.md,
        border: `1px solid rgba(255, 255, 255, 0.05)`,
      }}>
        <Row gutter={[8, 8]}>
          <Col span={12}>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                fontSize: 18,
                fontWeight: 700,
                color: theme.colors.success,
              }}>
                {Object.values(factors).filter(f => f >= 70).length}
              </div>
              <Text style={{
                fontSize: 11,
                color: theme.colors.text.secondary,
              }}>
                Strong Signals
              </Text>
            </div>
          </Col>
          <Col span={12}>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                fontSize: 18,
                fontWeight: 700,
                color: theme.colors.warning,
              }}>
                {Object.values(factors).filter(f => f < 50).length}
              </div>
              <Text style={{
                fontSize: 11,
                color: theme.colors.text.secondary,
              }}>
                Weak Signals
              </Text>
            </div>
          </Col>
        </Row>
      </div>
    </Card>
  );
};

export default AIConfidenceMeter;