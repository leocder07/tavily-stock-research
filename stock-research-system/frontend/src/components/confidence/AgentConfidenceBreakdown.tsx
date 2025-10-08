import React from 'react';
import styled from 'styled-components';
import { Card, Progress, Tooltip, Space, Tag } from 'antd';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  RobotOutlined,
  LineChartOutlined,
  DollarOutlined,
  AlertOutlined,
  TrophyOutlined,
  TeamOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { theme } from '../../styles/theme';
import ConfidenceMeter from './ConfidenceMeter';

interface AgentScore {
  name: string;
  confidence: number;
  status?: 'active' | 'warning' | 'error';
  signal?: string;
  weight?: number;
}

interface AgentConfidenceBreakdownProps {
  consensusBreakdown?: {
    weighted_score?: number;
    total_confidence?: number;
    bullish_indicators?: number;
    bearish_indicators?: number;
    neutral_indicators?: number;
  };
  agentAgreement?: string;
  agentScores?: AgentScore[];
  compact?: boolean;
}

const BreakdownCard = styled(Card)`
  background: ${theme.effects.glassMorphism.background};
  backdrop-filter: ${theme.effects.glassMorphism.backdropFilter};
  border: ${theme.effects.glassMorphism.border};
  border-radius: ${theme.borderRadius.lg};

  .ant-card-head {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .ant-card-head-title {
    color: ${theme.colors.text.primary};
    font-weight: 600;
  }
`;

const AgentRow = styled.div<{ confidence: number }>`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: ${theme.colors.background.elevated};
  border-radius: ${theme.borderRadius.md};
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
  opacity: ${props => props.confidence < 0.4 ? 0.6 : 1};

  &:hover {
    background: ${theme.colors.background.secondary};
    border-color: ${theme.colors.primary}40;
    transform: translateX(4px);
  }
`;

const AgentIcon = styled.div<{ confidence: number }>`
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: ${theme.borderRadius.md};
  background: ${props =>
    props.confidence >= 0.7 ? `${theme.colors.success}20` :
    props.confidence >= 0.4 ? `${theme.colors.warning}20` :
    `${theme.colors.danger}20`
  };
  color: ${props =>
    props.confidence >= 0.7 ? theme.colors.success :
    props.confidence >= 0.4 ? theme.colors.warning :
    theme.colors.danger
  };
  font-size: 18px;
`;

const AgentInfo = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

const AgentName = styled.div`
  font-size: 13px;
  font-weight: 600;
  color: ${theme.colors.text.primary};
  display: flex;
  align-items: center;
  gap: 8px;
`;

const AgentMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: ${theme.colors.text.secondary};
`;

const ConfidenceBar = styled.div`
  width: 150px;
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

const ConfidenceValue = styled.div<{ confidence: number }>`
  font-size: 14px;
  font-weight: 700;
  color: ${props =>
    props.confidence >= 0.7 ? theme.colors.success :
    props.confidence >= 0.4 ? theme.colors.warning :
    theme.colors.danger
  };
  text-align: right;
  font-family: ${theme.typography.fontFamily.mono};
`;

const SummaryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
`;

const SummaryItem = styled.div`
  text-align: center;
  padding: 12px;
  background: ${theme.colors.background.elevated};
  border-radius: ${theme.borderRadius.md};
  border: 1px solid rgba(255, 255, 255, 0.05);
`;

const SummaryValue = styled.div<{ color?: string }>`
  font-size: 24px;
  font-weight: 700;
  color: ${props => props.color || theme.colors.primary};
  margin-bottom: 4px;
`;

const SummaryLabel = styled.div`
  font-size: 11px;
  color: ${theme.colors.text.secondary};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const AgreementBadge = styled.div<{ level: string }>`
  padding: 6px 12px;
  background: ${props =>
    props.level === 'high' ? `${theme.colors.success}20` :
    props.level === 'medium' ? `${theme.colors.warning}20` :
    `${theme.colors.danger}20`
  };
  color: ${props =>
    props.level === 'high' ? theme.colors.success :
    props.level === 'medium' ? theme.colors.warning :
    theme.colors.danger
  };
  border-radius: ${theme.borderRadius.md};
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: inline-block;
`;

const getAgentIcon = (name: string) => {
  const lowerName = name.toLowerCase();
  if (lowerName.includes('technical')) return <LineChartOutlined />;
  if (lowerName.includes('fundamental')) return <DollarOutlined />;
  if (lowerName.includes('risk')) return <AlertOutlined />;
  if (lowerName.includes('sentiment')) return <ThunderboltOutlined />;
  if (lowerName.includes('peer')) return <TeamOutlined />;
  if (lowerName.includes('synthesis')) return <TrophyOutlined />;
  return <RobotOutlined />;
};

const getConfidenceIcon = (confidence: number) => {
  if (confidence >= 0.7) return <CheckCircleOutlined style={{ color: theme.colors.success }} />;
  if (confidence >= 0.4) return <ExclamationCircleOutlined style={{ color: theme.colors.warning }} />;
  return <CloseCircleOutlined style={{ color: theme.colors.danger }} />;
};

const getAgreementLevel = (agreement: string): string => {
  const lower = agreement.toLowerCase();
  if (lower.includes('strong') || lower.includes('high')) return 'high';
  if (lower.includes('moderate') || lower.includes('medium')) return 'medium';
  return 'low';
};

const AgentConfidenceBreakdown: React.FC<AgentConfidenceBreakdownProps> = ({
  consensusBreakdown,
  agentAgreement,
  agentScores,
  compact = false,
}) => {
  // Default agent scores if not provided
  const defaultAgents: AgentScore[] = agentScores || [
    { name: 'Fundamental Agent', confidence: 0.75 },
    { name: 'Technical Agent', confidence: 0.68 },
    { name: 'Risk Agent', confidence: 0.82 },
    { name: 'Sentiment Agent', confidence: 0.55 },
    { name: 'Peer Comparison', confidence: 0.70 },
  ];

  const normalizeConfidence = (conf: number) => conf <= 1 ? conf * 100 : conf;

  return (
    <BreakdownCard
      title={
        <Space>
          <RobotOutlined style={{ color: theme.colors.primary }} />
          Agent Confidence Breakdown
        </Space>
      }
      size={compact ? 'small' : 'default'}
    >
      {/* Summary Statistics */}
      {consensusBreakdown && (
        <SummaryGrid>
          {consensusBreakdown.weighted_score !== undefined && (
            <SummaryItem>
              <SummaryValue color={theme.colors.primary}>
                {(normalizeConfidence(consensusBreakdown.weighted_score)).toFixed(0)}%
              </SummaryValue>
              <SummaryLabel>Weighted Score</SummaryLabel>
            </SummaryItem>
          )}
          {consensusBreakdown.bullish_indicators !== undefined && (
            <SummaryItem>
              <SummaryValue color={theme.colors.success}>
                {consensusBreakdown.bullish_indicators}
              </SummaryValue>
              <SummaryLabel>Bullish</SummaryLabel>
            </SummaryItem>
          )}
          {consensusBreakdown.neutral_indicators !== undefined && (
            <SummaryItem>
              <SummaryValue color={theme.colors.warning}>
                {consensusBreakdown.neutral_indicators}
              </SummaryValue>
              <SummaryLabel>Neutral</SummaryLabel>
            </SummaryItem>
          )}
          {consensusBreakdown.bearish_indicators !== undefined && (
            <SummaryItem>
              <SummaryValue color={theme.colors.danger}>
                {consensusBreakdown.bearish_indicators}
              </SummaryValue>
              <SummaryLabel>Bearish</SummaryLabel>
            </SummaryItem>
          )}
        </SummaryGrid>
      )}

      {/* Agent Agreement */}
      {agentAgreement && (
        <div style={{ marginBottom: 20, textAlign: 'center' }}>
          <AgreementBadge level={getAgreementLevel(agentAgreement)}>
            {agentAgreement}
          </AgreementBadge>
        </div>
      )}

      {/* Individual Agent Scores */}
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {defaultAgents.map((agent, index) => {
          const normalizedConf = agent.confidence <= 1 ? agent.confidence : agent.confidence / 100;
          const displayConf = normalizeConfidence(agent.confidence);

          return (
            <AgentRow key={index} confidence={normalizedConf}>
              <AgentIcon confidence={normalizedConf}>
                {getAgentIcon(agent.name)}
              </AgentIcon>

              <AgentInfo>
                <AgentName>
                  {agent.name}
                  {agent.signal && (
                    <Tag
                      color={
                        agent.signal.toUpperCase() === 'BUY' ? 'success' :
                        agent.signal.toUpperCase() === 'SELL' ? 'error' :
                        'warning'
                      }
                      style={{ fontSize: 10, padding: '0 6px', marginLeft: 4 }}
                    >
                      {agent.signal}
                    </Tag>
                  )}
                </AgentName>
                <AgentMeta>
                  {getConfidenceIcon(normalizedConf)}
                  {agent.weight && (
                    <span>Weight: {(agent.weight * 100).toFixed(0)}%</span>
                  )}
                </AgentMeta>
              </AgentInfo>

              <ConfidenceBar>
                <Tooltip title={`${agent.name}: ${displayConf.toFixed(0)}% confidence`}>
                  <Progress
                    percent={displayConf}
                    strokeColor={
                      normalizedConf >= 0.7 ? theme.colors.success :
                      normalizedConf >= 0.4 ? theme.colors.warning :
                      theme.colors.danger
                    }
                    trailColor={theme.colors.background.primary}
                    strokeWidth={6}
                    showInfo={false}
                  />
                </Tooltip>
                <ConfidenceValue confidence={normalizedConf}>
                  {displayConf.toFixed(0)}%
                </ConfidenceValue>
              </ConfidenceBar>
            </AgentRow>
          );
        })}
      </Space>

      {/* Low Confidence Warning */}
      {defaultAgents.some(a => (a.confidence <= 1 ? a.confidence : a.confidence / 100) < 0.4) && (
        <div style={{ marginTop: 16 }}>
          <Tag color="warning" icon={<ExclamationCircleOutlined />} style={{ width: '100%', padding: '8px 12px' }}>
            Some agents show low confidence. Consider additional research before making decisions.
          </Tag>
        </div>
      )}
    </BreakdownCard>
  );
};

export default AgentConfidenceBreakdown;
