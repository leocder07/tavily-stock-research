import React from 'react';
import styled from 'styled-components';
import { Card, Row, Col, Space, Divider, Typography } from 'antd';
import ConfidenceMeter from './ConfidenceMeter';
import AgentConfidenceBreakdown from './AgentConfidenceBreakdown';
import ConfidenceBadge from './ConfidenceBadge';
import ConfidenceWarning from './ConfidenceWarning';
import { theme } from '../../styles/theme';

const { Title, Paragraph } = Typography;

/**
 * ConfidenceShowcase - Demo component showing all confidence visualizations
 *
 * This component demonstrates the complete confidence score visualization system
 * with various confidence levels (high, medium, low) for testing and demonstration.
 */

const ShowcaseContainer = styled.div`
  padding: 24px;
  background: ${theme.colors.background.primary};
  min-height: 100vh;
`;

const Section = styled.div`
  margin-bottom: 48px;
`;

const SectionTitle = styled(Title)`
  color: ${theme.colors.text.primary} !important;
  margin-bottom: 16px !important;
`;

const DemoCard = styled(Card)`
  background: ${theme.effects.glassMorphism.background};
  backdrop-filter: ${theme.effects.glassMorphism.backdropFilter};
  border: ${theme.effects.glassMorphism.border};
  margin-bottom: 16px;
`;

const ConfidenceShowcase: React.FC = () => {
  // Sample data for different confidence levels
  const highConfidenceData = {
    confidence: 0.85,
    consensusBreakdown: {
      weighted_score: 0.85,
      total_confidence: 0.80,
      bullish_indicators: 4,
      bearish_indicators: 0,
      neutral_indicators: 1,
    },
    agentAgreement: 'Strong agreement across all agents',
    agentScores: [
      { name: 'Fundamental Agent', confidence: 0.88, signal: 'BUY', weight: 0.35 },
      { name: 'Technical Agent', confidence: 0.82, signal: 'BUY', weight: 0.25 },
      { name: 'Risk Agent', confidence: 0.85, signal: 'HOLD', weight: 0.20 },
      { name: 'Sentiment Agent', confidence: 0.78, signal: 'BUY', weight: 0.15 },
      { name: 'Peer Comparison', confidence: 0.90, signal: 'BUY', weight: 0.05 },
    ],
  };

  const mediumConfidenceData = {
    confidence: 0.55,
    consensusBreakdown: {
      weighted_score: 0.55,
      total_confidence: 0.50,
      bullish_indicators: 2,
      bearish_indicators: 1,
      neutral_indicators: 2,
    },
    agentAgreement: 'Moderate agreement with some conflicting signals',
    agentScores: [
      { name: 'Fundamental Agent', confidence: 0.65, signal: 'BUY', weight: 0.35 },
      { name: 'Technical Agent', confidence: 0.48, signal: 'HOLD', weight: 0.25 },
      { name: 'Risk Agent', confidence: 0.55, signal: 'HOLD', weight: 0.20 },
      { name: 'Sentiment Agent', confidence: 0.52, signal: 'HOLD', weight: 0.15 },
      { name: 'Peer Comparison', confidence: 0.60, signal: 'BUY', weight: 0.05 },
    ],
  };

  const lowConfidenceData = {
    confidence: 0.32,
    consensusBreakdown: {
      weighted_score: 0.32,
      total_confidence: 0.28,
      bullish_indicators: 1,
      bearish_indicators: 3,
      neutral_indicators: 1,
    },
    agentAgreement: 'Low agreement with significant conflicts',
    agentScores: [
      { name: 'Fundamental Agent', confidence: 0.35, signal: 'SELL', weight: 0.35 },
      { name: 'Technical Agent', confidence: 0.28, signal: 'SELL', weight: 0.25 },
      { name: 'Risk Agent', confidence: 0.42, signal: 'HOLD', weight: 0.20 },
      { name: 'Sentiment Agent', confidence: 0.25, signal: 'SELL', weight: 0.15 },
      { name: 'Peer Comparison', confidence: 0.38, signal: 'HOLD', weight: 0.05 },
    ],
  };

  return (
    <ShowcaseContainer>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Title level={2} style={{ color: theme.colors.primary }}>
            Confidence Score Visualization System
          </Title>
          <Paragraph style={{ color: theme.colors.text.secondary, fontSize: 16 }}>
            A comprehensive system for displaying AI analysis confidence scores with visual cues,
            agent breakdowns, and intelligent warnings.
          </Paragraph>
        </div>

        {/* Confidence Meters */}
        <Section>
          <SectionTitle level={3}>1. Confidence Meters</SectionTitle>
          <Paragraph style={{ color: theme.colors.text.secondary }}>
            Primary confidence visualization with color-coded progress bars and icons.
          </Paragraph>

          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <DemoCard title="High Confidence (85%)">
                <ConfidenceMeter
                  confidence={0.85}
                  label="Strong Signal"
                  size="large"
                  showIcon={true}
                  showPercentage={true}
                  animated={true}
                />
              </DemoCard>
            </Col>
            <Col xs={24} md={8}>
              <DemoCard title="Medium Confidence (55%)">
                <ConfidenceMeter
                  confidence={0.55}
                  label="Moderate Signal"
                  size="large"
                  showIcon={true}
                  showPercentage={true}
                />
              </DemoCard>
            </Col>
            <Col xs={24} md={8}>
              <DemoCard title="Low Confidence (32%)">
                <ConfidenceMeter
                  confidence={0.32}
                  label="Weak Signal"
                  size="large"
                  showIcon={true}
                  showPercentage={true}
                />
              </DemoCard>
            </Col>
          </Row>
        </Section>

        {/* Confidence Badges */}
        <Section>
          <SectionTitle level={3}>2. Confidence Badges</SectionTitle>
          <Paragraph style={{ color: theme.colors.text.secondary }}>
            Inline badges for compact displays in recommendation cards and lists.
          </Paragraph>

          <DemoCard>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Space size="large" wrap>
                <ConfidenceBadge confidence={0.85} size="small" showIcon={true} showLabel={true} pulse={true} />
                <ConfidenceBadge confidence={0.85} size="default" showIcon={true} showLabel={true} />
                <ConfidenceBadge confidence={0.85} size="large" showIcon={true} showLabel={true} />
              </Space>

              <Divider />

              <Space size="large" wrap>
                <ConfidenceBadge confidence={0.55} size="small" showIcon={true} showLabel={true} />
                <ConfidenceBadge confidence={0.55} size="default" showIcon={true} showLabel={true} />
                <ConfidenceBadge confidence={0.55} size="large" showIcon={true} showLabel={true} />
              </Space>

              <Divider />

              <Space size="large" wrap>
                <ConfidenceBadge confidence={0.32} size="small" showIcon={true} showLabel={true} />
                <ConfidenceBadge confidence={0.32} size="default" showIcon={true} showLabel={true} />
                <ConfidenceBadge confidence={0.32} size="large" showIcon={true} showLabel={true} />
              </Space>
            </Space>
          </DemoCard>
        </Section>

        {/* Agent Breakdown */}
        <Section>
          <SectionTitle level={3}>3. Agent Confidence Breakdown</SectionTitle>
          <Paragraph style={{ color: theme.colors.text.secondary }}>
            Detailed breakdown showing confidence scores for each analysis agent.
          </Paragraph>

          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <AgentConfidenceBreakdown
                consensusBreakdown={highConfidenceData.consensusBreakdown}
                agentAgreement={highConfidenceData.agentAgreement}
                agentScores={highConfidenceData.agentScores}
              />
            </Col>
            <Col xs={24} lg={12}>
              <AgentConfidenceBreakdown
                consensusBreakdown={lowConfidenceData.consensusBreakdown}
                agentAgreement={lowConfidenceData.agentAgreement}
                agentScores={lowConfidenceData.agentScores}
              />
            </Col>
          </Row>
        </Section>

        {/* Confidence Warnings */}
        <Section>
          <SectionTitle level={3}>4. Confidence Warnings</SectionTitle>
          <Paragraph style={{ color: theme.colors.text.secondary }}>
            Contextual warnings that appear based on confidence levels to alert users.
          </Paragraph>

          <DemoCard title="High Confidence Warning">
            <ConfidenceWarning confidence={0.85} showAlways={true} />
          </DemoCard>

          <DemoCard title="Medium Confidence Warning">
            <ConfidenceWarning confidence={0.55} />
          </DemoCard>

          <DemoCard title="Low Confidence Warning">
            <ConfidenceWarning
              confidence={0.32}
              customMessage="Critical: Multiple agents show conflicting signals."
              reasons={[
                'Significant disagreement between fundamental and technical analysis',
                'Limited historical data available for this security',
                'Unusual market volatility detected',
                'News sentiment conflicts with technical indicators',
              ]}
            />
          </DemoCard>
        </Section>

        {/* Full Integration Example */}
        <Section>
          <SectionTitle level={3}>5. Full Integration Example</SectionTitle>
          <Paragraph style={{ color: theme.colors.text.secondary }}>
            Complete confidence visualization as it appears in analysis results.
          </Paragraph>

          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card
                title="Analysis Confidence Score"
                style={{
                  background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.05) 0%, rgba(0, 0, 0, 0.1) 100%)',
                  border: '1px solid rgba(212, 175, 55, 0.2)',
                }}
              >
                <ConfidenceMeter
                  confidence={highConfidenceData.confidence}
                  label="AI Confidence"
                  size="large"
                  showIcon={true}
                  showPercentage={true}
                  animated={true}
                />
                <ConfidenceWarning
                  confidence={highConfidenceData.confidence}
                  showAlways={true}
                />
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <AgentConfidenceBreakdown
                consensusBreakdown={highConfidenceData.consensusBreakdown}
                agentAgreement={highConfidenceData.agentAgreement}
                agentScores={highConfidenceData.agentScores}
              />
            </Col>
          </Row>
        </Section>
      </Space>
    </ShowcaseContainer>
  );
};

export default ConfidenceShowcase;
