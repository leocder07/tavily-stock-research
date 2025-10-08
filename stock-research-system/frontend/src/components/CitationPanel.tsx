import React, { useState, useEffect } from 'react';
import {
  Card,
  Timeline,
  Typography,
  Tag,
  Badge,
  Space,
  Button,
  Collapse,
  Empty,
  Tooltip,
  Progress,
  Divider,
  Row,
  Col,
} from 'antd';
import {
  LinkOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  GlobalOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { theme } from '../styles/theme';

const { Text, Paragraph, Title } = Typography;
const { Panel } = Collapse;

export interface Citation {
  id: string;
  title: string;
  url: string;
  content: string;
  agent_id: string;
  agent_name: string;
  timestamp: string;
  relevance_score: number;
  published_date?: string;
  source?: string;
}

interface CitationPanelProps {
  citations: Citation[];
  loading?: boolean;
}

const CitationPanel: React.FC<CitationPanelProps> = ({ citations, loading = false }) => {
  const [groupBy, setGroupBy] = useState<'agent' | 'time'>('agent');
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);

  // Get agent display name and icon
  const getAgentInfo = (agentId: string) => {
    const agentMap: { [key: string]: { name: string; icon: React.ReactNode; color: string } } = {
      market_data: { name: 'Market Data', icon: <DatabaseOutlined />, color: '#1890ff' },
      fundamental: { name: 'Fundamental Analysis', icon: <FileTextOutlined />, color: '#722ed1' },
      sentiment: { name: 'Sentiment Analysis', icon: <GlobalOutlined />, color: '#52c41a' },
      technical: { name: 'Technical Analysis', icon: <TrophyOutlined />, color: '#fa8c16' },
      risk: { name: 'Risk Assessment', icon: <InfoCircleOutlined />, color: '#f5222d' },
      peer: { name: 'Peer Comparison', icon: <CheckCircleOutlined />, color: '#13c2c2' },
    };
    return agentMap[agentId] || { name: agentId, icon: <FileTextOutlined />, color: '#8c8c8c' };
  };

  // Get relevance color
  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return '#52c41a';
    if (score >= 0.6) return '#1890ff';
    if (score >= 0.4) return '#faad14';
    return '#f5222d';
  };

  // Get relevance label
  const getRelevanceLabel = (score: number) => {
    if (score >= 0.8) return 'High Relevance';
    if (score >= 0.6) return 'Moderate';
    if (score >= 0.4) return 'Low';
    return 'Very Low';
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  // Group citations by agent
  const groupedByAgent = citations.reduce((acc, citation) => {
    const agentId = citation.agent_id;
    if (!acc[agentId]) acc[agentId] = [];
    acc[agentId].push(citation);
    return acc;
  }, {} as { [key: string]: Citation[] });

  // Citation statistics
  const totalCitations = citations.length;
  const avgRelevance = citations.length > 0
    ? citations.reduce((sum, c) => sum + c.relevance_score, 0) / citations.length
    : 0;
  const uniqueSources = new Set(citations.map(c => new URL(c.url).hostname)).size;

  if (citations.length === 0 && !loading) {
    return (
      <Card title="Data Sources & Citations" size="small">
        <Empty
          description="No citations yet. Citations will appear as agents gather data."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  return (
    <Card
      title={
        <Space>
          <LinkOutlined />
          <Text strong>Data Sources & Citations</Text>
          <Badge count={totalCitations} showZero style={{ backgroundColor: theme.colors.primary }} />
        </Space>
      }
      size="small"
      extra={
        <Space>
          <Button
            size="small"
            type={groupBy === 'agent' ? 'primary' : 'default'}
            onClick={() => setGroupBy('agent')}
          >
            By Agent
          </Button>
          <Button
            size="small"
            type={groupBy === 'time' ? 'primary' : 'default'}
            onClick={() => setGroupBy('time')}
          >
            By Time
          </Button>
        </Space>
      }
    >
      {/* Citation Statistics */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card size="small" style={{ textAlign: 'center' }}>
            <Text type="secondary">Total Citations</Text>
            <Title level={3} style={{ margin: '8px 0 0 0' }}>{totalCitations}</Title>
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" style={{ textAlign: 'center' }}>
            <Text type="secondary">Avg Relevance</Text>
            <Title level={3} style={{ margin: '8px 0 0 0', color: getRelevanceColor(avgRelevance) }}>
              {(avgRelevance * 100).toFixed(0)}%
            </Title>
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" style={{ textAlign: 'center' }}>
            <Text type="secondary">Unique Sources</Text>
            <Title level={3} style={{ margin: '8px 0 0 0' }}>{uniqueSources}</Title>
          </Card>
        </Col>
      </Row>

      <Divider style={{ margin: '16px 0' }} />

      {/* Citations Display */}
      {groupBy === 'agent' ? (
        // Group by Agent
        <Collapse
          accordion={false}
          defaultActiveKey={Object.keys(groupedByAgent).slice(0, 2)}
          style={{ background: 'transparent', border: 'none' }}
        >
          {Object.entries(groupedByAgent).map(([agentId, agentCitations]) => {
            const agentInfo = getAgentInfo(agentId);
            return (
              <Panel
                key={agentId}
                header={
                  <Space>
                    {agentInfo.icon}
                    <Text strong style={{ color: agentInfo.color }}>{agentInfo.name}</Text>
                    <Badge count={agentCitations.length} style={{ backgroundColor: agentInfo.color }} />
                  </Space>
                }
                style={{
                  marginBottom: 8,
                  background: theme.colors.gradient.glass,
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: theme.borderRadius.md,
                }}
              >
                <Timeline mode="left">
                  {agentCitations.map((citation, index) => (
                    <Timeline.Item
                      key={citation.id}
                      dot={<CheckCircleOutlined style={{ color: getRelevanceColor(citation.relevance_score) }} />}
                    >
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                          <Tooltip title={citation.url}>
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ fontWeight: 500, maxWidth: '400px', display: 'inline-block' }}
                            >
                              {citation.title || new URL(citation.url).hostname}
                            </a>
                          </Tooltip>
                          <Tag color={getRelevanceColor(citation.relevance_score)}>
                            {getRelevanceLabel(citation.relevance_score)}
                          </Tag>
                        </Space>
                        <Progress
                          percent={citation.relevance_score * 100}
                          size="small"
                          showInfo={false}
                          strokeColor={getRelevanceColor(citation.relevance_score)}
                        />
                        {citation.content && (
                          <Paragraph
                            ellipsis={{ rows: 2, expandable: true, symbol: 'more' }}
                            style={{ fontSize: '12px', color: theme.colors.text.secondary, margin: 0 }}
                          >
                            {citation.content}
                          </Paragraph>
                        )}
                        <Space size="small">
                          <ClockCircleOutlined style={{ fontSize: '12px', color: theme.colors.text.secondary }} />
                          <Text type="secondary" style={{ fontSize: '11px' }}>
                            {formatTime(citation.timestamp)}
                          </Text>
                          {citation.published_date && (
                            <>
                              <Divider type="vertical" />
                              <Text type="secondary" style={{ fontSize: '11px' }}>
                                Published: {new Date(citation.published_date).toLocaleDateString()}
                              </Text>
                            </>
                          )}
                        </Space>
                      </Space>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Panel>
            );
          })}
        </Collapse>
      ) : (
        // Group by Time (chronological)
        <Timeline mode="left">
          {citations
            .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
            .map((citation) => {
              const agentInfo = getAgentInfo(citation.agent_id);
              return (
                <Timeline.Item
                  key={citation.id}
                  dot={<CheckCircleOutlined style={{ color: getRelevanceColor(citation.relevance_score) }} />}
                  label={
                    <Text type="secondary" style={{ fontSize: '11px' }}>
                      {formatTime(citation.timestamp)}
                    </Text>
                  }
                >
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <Space>
                      <Badge color={agentInfo.color} text={<Text strong>{agentInfo.name}</Text>} />
                      <Tag color={getRelevanceColor(citation.relevance_score)}>
                        {(citation.relevance_score * 100).toFixed(0)}%
                      </Tag>
                    </Space>
                    <Tooltip title={citation.url}>
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontWeight: 500 }}
                      >
                        {citation.title || new URL(citation.url).hostname}
                      </a>
                    </Tooltip>
                    {citation.content && (
                      <Paragraph
                        ellipsis={{ rows: 2, expandable: true, symbol: 'more' }}
                        style={{ fontSize: '12px', color: theme.colors.text.secondary, margin: 0 }}
                      >
                        {citation.content}
                      </Paragraph>
                    )}
                  </Space>
                </Timeline.Item>
              );
            })}
        </Timeline>
      )}
    </Card>
  );
};

export default CitationPanel;
