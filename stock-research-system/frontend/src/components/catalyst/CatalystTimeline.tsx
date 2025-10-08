import React, { useMemo } from 'react';
import { Card, Timeline, Tag, Space, Typography, Row, Col, Badge, Empty, Divider } from 'antd';
import {
  CalendarOutlined,
  RiseOutlined,
  FallOutlined,
  MinusOutlined,
  TrophyOutlined,
  RocketOutlined,
  SafetyOutlined,
  GlobalOutlined,
} from '@ant-design/icons';
import { theme } from '../../styles/theme';

const { Title, Text, Paragraph } = Typography;

interface Catalyst {
  type: 'earnings' | 'product_launch' | 'regulatory' | 'fed_meeting' | 'economic_data' | string;
  date: string;
  title: string;
  impact: 'high' | 'medium' | 'low';
  confirmed?: boolean;
  days_until?: number;
  source?: string;
  description?: string;
}

interface CatalystData {
  earnings?: {
    next_earnings_date?: string;
    earnings_confirmed?: boolean;
    days_until_earnings?: number;
    estimated_eps?: number;
  };
  product_launches?: Catalyst[];
  regulatory_events?: Catalyst[];
  macro_events?: Catalyst[];
  prioritized_catalysts?: Catalyst[];
  next_catalyst?: Catalyst;
  earnings_history?: {
    beat_rate?: number;
    avg_surprise_pct?: number;
    last_surprise_pct?: number;
  };
}

interface CatalystTimelineProps {
  data: CatalystData;
  symbol?: string;
}

const CatalystTimeline: React.FC<CatalystTimelineProps> = ({ data, symbol }) => {
  // Get prioritized catalysts or build from individual arrays
  const catalysts = useMemo(() => {
    if (data.prioritized_catalysts && data.prioritized_catalysts.length > 0) {
      return data.prioritized_catalysts;
    }

    // Build from individual sources
    const allCatalysts: Catalyst[] = [];

    // Add earnings
    if (data.earnings?.next_earnings_date) {
      allCatalysts.push({
        type: 'earnings',
        date: data.earnings.next_earnings_date,
        title: 'Earnings Release',
        impact: 'high',
        confirmed: data.earnings.earnings_confirmed,
        days_until: data.earnings.days_until_earnings,
      });
    }

    // Add other catalysts
    if (data.product_launches) allCatalysts.push(...data.product_launches);
    if (data.regulatory_events) allCatalysts.push(...data.regulatory_events);
    if (data.macro_events) allCatalysts.push(...data.macro_events);

    // Sort by days_until or date
    return allCatalysts
      .filter(c => c.date && c.date !== 'TBD')
      .sort((a, b) => {
        if (a.days_until !== undefined && b.days_until !== undefined) {
          return a.days_until - b.days_until;
        }
        return new Date(a.date).getTime() - new Date(b.date).getTime();
      })
      .slice(0, 10); // Show top 10
  }, [data]);

  // Format date for display
  const formatDate = (dateStr: string): string => {
    try {
      const date = new Date(dateStr);
      const options: Intl.DateTimeFormatOptions = {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      };
      return date.toLocaleDateString('en-US', options);
    } catch {
      return dateStr;
    }
  };

  // Calculate countdown
  const getCountdown = (dateStr: string, daysUntil?: number): string => {
    if (daysUntil !== undefined) {
      if (daysUntil === 0) return 'Today';
      if (daysUntil === 1) return 'Tomorrow';
      if (daysUntil < 0) return 'Past';
      if (daysUntil < 7) return `${daysUntil} days`;
      if (daysUntil < 30) return `${Math.floor(daysUntil / 7)} weeks`;
      if (daysUntil < 365) return `${Math.floor(daysUntil / 30)} months`;
      return `${Math.floor(daysUntil / 365)} years`;
    }

    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = date.getTime() - now.getTime();
      const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

      if (days === 0) return 'Today';
      if (days === 1) return 'Tomorrow';
      if (days < 0) return 'Past';
      if (days < 7) return `${days} days`;
      if (days < 30) return `${Math.floor(days / 7)} weeks`;
      if (days < 365) return `${Math.floor(days / 30)} months`;
      return `${Math.floor(days / 365)} years`;
    } catch {
      return '';
    }
  };

  // Get catalyst type icon
  const getCatalystIcon = (type: string) => {
    const iconStyle = { fontSize: '18px' };
    switch (type) {
      case 'earnings':
        return <TrophyOutlined style={{ ...iconStyle, color: theme.colors.warning }} />;
      case 'product_launch':
        return <RocketOutlined style={{ ...iconStyle, color: theme.colors.primary }} />;
      case 'regulatory':
        return <SafetyOutlined style={{ ...iconStyle, color: theme.colors.danger }} />;
      case 'fed_meeting':
      case 'economic_data':
        return <GlobalOutlined style={{ ...iconStyle, color: theme.colors.accent }} />;
      default:
        return <CalendarOutlined style={{ ...iconStyle, color: theme.colors.neutral }} />;
    }
  };

  // Get impact color
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return theme.colors.danger;
      case 'medium':
        return theme.colors.warning;
      case 'low':
        return theme.colors.neutral;
      default:
        return theme.colors.neutral;
    }
  };

  // Get impact badge
  const getImpactBadge = (impact: string) => {
    const color = impact === 'high' ? 'red' : impact === 'medium' ? 'orange' : 'default';
    return <Tag color={color}>{impact.toUpperCase()}</Tag>;
  };

  // Get urgency style based on days until
  const getUrgencyStyle = (daysUntil?: number) => {
    if (daysUntil === undefined) return {};
    if (daysUntil <= 7) return { borderLeft: `3px solid ${theme.colors.danger}` };
    if (daysUntil <= 30) return { borderLeft: `3px solid ${theme.colors.warning}` };
    return { borderLeft: `3px solid ${theme.colors.success}` };
  };

  // Calculate next catalyst urgency
  const nextCatalyst = catalysts[0] || data.next_catalyst;
  const isUrgent = nextCatalyst && (nextCatalyst.days_until ?? 999) <= 7;

  if (!catalysts || catalysts.length === 0) {
    return (
      <Card
        title={
          <Space>
            <CalendarOutlined style={{ color: theme.colors.primary }} />
            <Text strong style={{ color: theme.colors.text.primary }}>
              Catalyst Calendar
            </Text>
          </Space>
        }
        style={{
          background: theme.colors.background.secondary,
          borderRadius: theme.borderRadius.lg,
          border: `1px solid ${theme.colors.border}`,
        }}
        data-test="catalyst-timeline-empty"
      >
        <Empty
          description={
            <Text style={{ color: theme.colors.text.secondary }}>
              No upcoming catalysts found
            </Text>
          }
        />
      </Card>
    );
  }

  return (
    <Card
      title={
        <Space>
          <CalendarOutlined style={{ color: theme.colors.primary }} />
          <Text strong style={{ color: theme.colors.text.primary }}>
            Catalyst Calendar {symbol && `- ${symbol}`}
          </Text>
        </Space>
      }
      style={{
        background: theme.colors.background.secondary,
        borderRadius: theme.borderRadius.lg,
        border: `1px solid ${theme.colors.border}`,
      }}
      data-test="catalyst-timeline"
    >
      {/* Next Catalyst Highlight */}
      {nextCatalyst && (
        <div
          style={{
            background: isUrgent
              ? 'rgba(255, 69, 58, 0.1)'
              : 'rgba(212, 175, 55, 0.1)',
            padding: theme.spacing.md,
            borderRadius: theme.borderRadius.md,
            marginBottom: theme.spacing.lg,
            border: `1px solid ${isUrgent ? theme.colors.danger : theme.colors.primary}`,
          }}
          data-test="next-catalyst-highlight"
        >
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} md={6}>
              <div style={{ textAlign: 'center' }}>
                <Text
                  style={{
                    fontSize: theme.typography.fontSize['3xl'],
                    fontWeight: theme.typography.fontWeight.bold,
                    color: theme.colors.primary,
                    display: 'block',
                  }}
                  data-test="next-catalyst-countdown"
                >
                  {getCountdown(nextCatalyst.date, nextCatalyst.days_until)}
                </Text>
                <Text style={{ color: theme.colors.text.secondary, fontSize: theme.typography.fontSize.sm }}>
                  Next Catalyst
                </Text>
              </div>
            </Col>
            <Col xs={24} md={18}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Space>
                  {getCatalystIcon(nextCatalyst.type)}
                  <Text
                    strong
                    style={{
                      fontSize: theme.typography.fontSize.lg,
                      color: theme.colors.text.primary,
                    }}
                  >
                    {nextCatalyst.title}
                  </Text>
                  {getImpactBadge(nextCatalyst.impact)}
                  {nextCatalyst.confirmed && (
                    <Badge status="success" text="Confirmed" />
                  )}
                </Space>
                <Text
                  style={{
                    fontSize: theme.typography.fontSize.xl,
                    color: theme.colors.primary,
                    fontWeight: theme.typography.fontWeight.semibold,
                  }}
                  data-test="next-catalyst-date"
                >
                  {formatDate(nextCatalyst.date)}
                </Text>
                {nextCatalyst.description && (
                  <Text style={{ color: theme.colors.text.secondary }}>
                    {nextCatalyst.description}
                  </Text>
                )}
              </Space>
            </Col>
          </Row>
        </div>
      )}

      {/* Earnings History Badge (if available) */}
      {data.earnings_history && data.earnings_history.beat_rate !== undefined && (
        <div
          style={{
            background: 'rgba(0, 212, 170, 0.1)',
            padding: theme.spacing.sm,
            borderRadius: theme.borderRadius.md,
            marginBottom: theme.spacing.md,
          }}
        >
          <Row gutter={16}>
            <Col span={8}>
              <Text style={{ color: theme.colors.text.secondary }}>Beat Rate: </Text>
              <Text strong style={{ color: theme.colors.success }}>
                {data.earnings_history.beat_rate.toFixed(0)}%
              </Text>
            </Col>
            <Col span={8}>
              <Text style={{ color: theme.colors.text.secondary }}>Avg Surprise: </Text>
              <Text strong style={{ color: theme.colors.primary }}>
                {data.earnings_history.avg_surprise_pct?.toFixed(1)}%
              </Text>
            </Col>
            <Col span={8}>
              <Text style={{ color: theme.colors.text.secondary }}>Last: </Text>
              <Text
                strong
                style={{
                  color: (data.earnings_history.last_surprise_pct ?? 0) > 0
                    ? theme.colors.success
                    : theme.colors.danger,
                }}
              >
                {data.earnings_history.last_surprise_pct?.toFixed(1)}%
              </Text>
            </Col>
          </Row>
        </div>
      )}

      <Divider style={{ borderColor: theme.colors.border, margin: `${theme.spacing.lg} 0` }} />

      {/* Timeline of Catalysts */}
      <Timeline
        mode="left"
        style={{ marginTop: theme.spacing.md }}
        data-test="catalyst-timeline-list"
      >
        {catalysts.map((catalyst, index) => (
          <Timeline.Item
            key={`${catalyst.type}-${catalyst.date}-${index}`}
            dot={getCatalystIcon(catalyst.type)}
            color={getImpactColor(catalyst.impact)}
            data-test={`catalyst-item-${index}`}
          >
            <div
              style={{
                background: theme.colors.background.elevated,
                padding: theme.spacing.md,
                borderRadius: theme.borderRadius.md,
                ...getUrgencyStyle(catalyst.days_until),
              }}
            >
              <Row gutter={[16, 8]} align="middle">
                <Col xs={24} md={6}>
                  <div>
                    <Text
                      strong
                      style={{
                        fontSize: theme.typography.fontSize.lg,
                        color: theme.colors.primary,
                        display: 'block',
                      }}
                      data-test={`catalyst-date-${index}`}
                    >
                      {formatDate(catalyst.date)}
                    </Text>
                    <Text
                      style={{
                        fontSize: theme.typography.fontSize.sm,
                        color: theme.colors.text.secondary,
                      }}
                    >
                      {getCountdown(catalyst.date, catalyst.days_until)}
                    </Text>
                  </div>
                </Col>
                <Col xs={24} md={18}>
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <Space wrap>
                      <Text
                        strong
                        style={{
                          color: theme.colors.text.primary,
                          fontSize: theme.typography.fontSize.base,
                        }}
                      >
                        {catalyst.title}
                      </Text>
                      {getImpactBadge(catalyst.impact)}
                      {catalyst.confirmed && (
                        <Badge status="success" text="Confirmed" />
                      )}
                      <Tag color="blue" style={{ textTransform: 'capitalize' }}>
                        {catalyst.type.replace('_', ' ')}
                      </Tag>
                    </Space>
                    {catalyst.description && (
                      <Paragraph
                        ellipsis={{ rows: 2, expandable: true }}
                        style={{
                          color: theme.colors.text.secondary,
                          margin: 0,
                          fontSize: theme.typography.fontSize.sm,
                        }}
                      >
                        {catalyst.description}
                      </Paragraph>
                    )}
                    {catalyst.source && (
                      <a
                        href={catalyst.source}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: theme.typography.fontSize.xs }}
                      >
                        View Source →
                      </a>
                    )}
                  </Space>
                </Col>
              </Row>
            </div>
          </Timeline.Item>
        ))}
      </Timeline>

      {/* Catalyst Type Legend */}
      <Divider style={{ borderColor: theme.colors.border, margin: `${theme.spacing.lg} 0` }} />
      <div style={{ textAlign: 'center' }}>
        <Text style={{ color: theme.colors.text.secondary, fontSize: theme.typography.fontSize.sm }}>
          Catalyst Types:
        </Text>
        <Space wrap style={{ marginTop: theme.spacing.sm, justifyContent: 'center' }}>
          <Space size="small">
            <TrophyOutlined style={{ color: theme.colors.warning }} />
            <Text style={{ color: theme.colors.text.secondary, fontSize: theme.typography.fontSize.xs }}>
              Earnings
            </Text>
          </Space>
          <Space size="small">
            <RocketOutlined style={{ color: theme.colors.primary }} />
            <Text style={{ color: theme.colors.text.secondary, fontSize: theme.typography.fontSize.xs }}>
              Product Launch
            </Text>
          </Space>
          <Space size="small">
            <SafetyOutlined style={{ color: theme.colors.danger }} />
            <Text style={{ color: theme.colors.text.secondary, fontSize: theme.typography.fontSize.xs }}>
              Regulatory
            </Text>
          </Space>
          <Space size="small">
            <GlobalOutlined style={{ color: theme.colors.accent }} />
            <Text style={{ color: theme.colors.text.secondary, fontSize: theme.typography.fontSize.xs }}>
              Macro Events
            </Text>
          </Space>
        </Space>
      </div>
    </Card>
  );
};

export default CatalystTimeline;
