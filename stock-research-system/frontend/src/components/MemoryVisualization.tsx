import React, { useState, useEffect } from 'react';
import {
  Card,
  Typography,
  Row,
  Col,
  Tag,
  Progress,
  List,
  Divider,
  Button,
  Collapse,
  Alert,
  Tabs,
  Badge,
  Tooltip,
  Space,
  Statistic,
} from 'antd';
import {
  DatabaseOutlined,
  BulbOutlined,
  RiseOutlined,
  InfoCircleOutlined,
  DownOutlined,
  UpOutlined,
  FieldTimeOutlined,
  StarOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { designTokens } from '../design-system/tokens';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface MemoryEntry {
  id: string;
  agent: string;
  type: 'working' | 'episodic' | 'shared';
  content: string;
  timestamp: string;
  importance: number;
  accessCount: number;
  context?: any;
}

interface Pattern {
  id: string;
  type: string;
  description: string;
  confidence: number;
  discoveries: number;
  lastSeen: string;
}

interface Insight {
  id: string;
  symbol: string;
  content: string;
  importance: number;
  agent: string;
  timestamp: string;
}

interface MemoryVisualizationProps {
  requestId: string;
  symbols: string[];
}

const MemoryVisualization: React.FC<MemoryVisualizationProps> = ({ requestId, symbols }) => {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [activeTab, setActiveTab] = useState('working');
  const [expandedMemory, setExpandedMemory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalMemories: 0,
    patternsDetected: 0,
    insightsGenerated: 0,
    averageImportance: 0
  });

  useEffect(() => {
    fetchMemoryData();
    const interval = setInterval(fetchMemoryData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [requestId]);

  const fetchMemoryData = async () => {
    try {
      // Fetch memories
      const memoriesRes = await fetch(`/api/memory/entries?request_id=${requestId}`);
      const memoriesData = await memoriesRes.json();
      setMemories(memoriesData.memories || []);

      // Fetch patterns
      const patternsRes = await fetch(`/api/memory/patterns?min_confidence=0.6`);
      const patternsData = await patternsRes.json();
      setPatterns(patternsData.patterns || []);

      // Fetch insights
      const insightsPromises = symbols.map(symbol =>
        fetch(`/api/memory/insights/${symbol}`).then(res => res.json())
      );
      const insightsData = await Promise.all(insightsPromises);
      const allInsights = insightsData.flatMap(d => d.insights || []);
      setInsights(allInsights);

      // Calculate stats
      const avgImportance = memoriesData.memories?.length > 0
        ? memoriesData.memories.reduce((acc: number, m: MemoryEntry) => acc + m.importance, 0) / memoriesData.memories.length
        : 0;

      setStats({
        totalMemories: memoriesData.memories?.length || 0,
        patternsDetected: patternsData.patterns?.length || 0,
        insightsGenerated: allInsights.length,
        averageImportance: avgImportance
      });

      setLoading(false);
    } catch (error) {
      console.error('Error fetching memory data:', error);
      setLoading(false);
    }
  };

  const toggleMemoryExpansion = (memoryId: string) => {
    setExpandedMemory(expandedMemory === memoryId ? null : memoryId);
  };

  const getMemoryTypeIcon = (type: string) => {
    switch (type) {
      case 'working':
        return <DatabaseOutlined style={{ color: designTokens.colors.semantic.info }} />;
      case 'episodic':
        return <FieldTimeOutlined style={{ color: designTokens.colors.semantic.warning }} />;
      case 'shared':
        return <BulbOutlined style={{ color: designTokens.colors.semantic.success }} />;
      default:
        return <InfoCircleOutlined />;
    }
  };

  const getImportanceColor = (importance: number) => {
    if (importance >= 0.8) return 'red';
    if (importance >= 0.6) return 'orange';
    if (importance >= 0.4) return 'blue';
    return 'default';
  };

  const renderMemoryList = (memoryType?: string) => {
    const filteredMemories = memoryType
      ? memories.filter(m => m.type === memoryType)
      : memories;

    return (
      <List
        dataSource={filteredMemories}
        renderItem={(memory, index) => (
          <motion.div
            key={memory.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ delay: index * 0.05 }}
          >
            <List.Item style={{ padding: '12px 0' }}>
              <div style={{ width: '100%' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Space align="center">
                    {getMemoryTypeIcon(memory.type)}
                    <Text strong>{memory.agent}</Text>
                    <Tag color={getImportanceColor(memory.importance)}>
                      {`${(memory.importance * 100).toFixed(0)}%`}
                    </Tag>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {new Date(memory.timestamp).toLocaleTimeString()}
                    </Text>
                  </Space>
                  <Button
                    type="text"
                    size="small"
                    icon={expandedMemory === memory.id ? <UpOutlined /> : <DownOutlined />}
                    onClick={() => toggleMemoryExpansion(memory.id)}
                  />
                </div>
                <Paragraph style={{ marginTop: '8px', marginBottom: 0 }}>
                  {memory.content}
                </Paragraph>
                {expandedMemory === memory.id && (
                  <div style={{
                    marginTop: '12px',
                    padding: '12px',
                    background: designTokens.colors.background.primary,
                    borderRadius: designTokens.borderRadius.md
                  }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      Access Count: {memory.accessCount}
                    </Text>
                    {memory.context && (
                      <pre style={{
                        fontSize: '11px',
                        overflow: 'auto',
                        marginTop: '8px',
                        padding: '8px',
                        background: designTokens.colors.background.secondary,
                        borderRadius: designTokens.borderRadius.sm
                      }}>
                        {JSON.stringify(memory.context, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            </List.Item>
            <Divider style={{ margin: '8px 0' }} />
          </motion.div>
        )}
      />
    );
  };

  const renderPatterns = () => (
    <Row gutter={[16, 16]}>
      <AnimatePresence>
        {patterns.map((pattern, index) => (
          <Col xs={24} md={12} key={pattern.id}>
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card
                style={{
                  background: designTokens.colors.background.card,
                  border: `1px solid ${designTokens.colors.border.default}`
                }}
              >
                <Space align="center" style={{ marginBottom: '8px' }}>
                  <RiseOutlined style={{ color: designTokens.colors.brand.gold, fontSize: '18px' }} />
                  <Text strong style={{ fontSize: '14px' }}>
                    {pattern.type.replace('_', ' ').toUpperCase()}
                  </Text>
                  <Tag color="green">
                    {`${(pattern.confidence * 100).toFixed(0)}% confidence`}
                  </Tag>
                </Space>
                <Paragraph type="secondary" style={{ marginBottom: '12px' }}>
                  {pattern.description}
                </Paragraph>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    Discovered {pattern.discoveries} times
                  </Text>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    Last: {new Date(pattern.lastSeen).toLocaleString()}
                  </Text>
                </div>
              </Card>
            </motion.div>
          </Col>
        ))}
      </AnimatePresence>
    </Row>
  );

  const renderInsights = () => (
    <List
      dataSource={insights}
      renderItem={(insight, index) => (
        <motion.div
          key={insight.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
        >
          <List.Item style={{ padding: '12px 0' }}>
            <div style={{ width: '100%' }}>
              <Space align="center" style={{ marginBottom: '8px' }}>
                <StarOutlined style={{ color: designTokens.colors.brand.gold }} />
                <Tag color="blue">{insight.symbol}</Tag>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  by {insight.agent}
                </Text>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {new Date(insight.timestamp).toLocaleString()}
                </Text>
              </Space>
              <Paragraph style={{ marginBottom: '8px' }}>
                {insight.content}
              </Paragraph>
              <Progress
                percent={insight.importance * 100}
                strokeColor={designTokens.colors.brand.gold}
                showInfo={false}
                size="small"
              />
            </div>
          </List.Item>
          <Divider style={{ margin: '8px 0' }} />
        </motion.div>
      )}
    />
  );

  if (loading) {
    return (
      <Card
        style={{
          background: designTokens.colors.background.card,
          border: `1px solid ${designTokens.colors.border.default}`
        }}
      >
        <Progress percent={30} showInfo={false} />
        <Text type="secondary" style={{ display: 'block', marginTop: '16px', textAlign: 'center' }}>
          Loading memory data...
        </Text>
      </Card>
    );
  }

  const tabItems = [
    {
      key: 'working',
      label: (
        <Badge count={memories.filter(m => m.type === 'working').length} showZero>
          <span>Working Memory</span>
        </Badge>
      ),
      children: renderMemoryList('working')
    },
    {
      key: 'episodic',
      label: (
        <Badge count={memories.filter(m => m.type === 'episodic').length} showZero>
          <span>Episodic Memory</span>
        </Badge>
      ),
      children: renderMemoryList('episodic')
    },
    {
      key: 'patterns',
      label: (
        <Badge count={patterns.length} showZero>
          <span>Patterns</span>
        </Badge>
      ),
      children: renderPatterns()
    },
    {
      key: 'insights',
      label: (
        <Badge count={insights.length} showZero>
          <span>Insights</span>
        </Badge>
      ),
      children: renderInsights()
    }
  ];

  return (
    <Card
      title="Agent Memory System"
      style={{
        background: designTokens.colors.background.card,
        border: `1px solid ${designTokens.colors.border.default}`
      }}
    >
      {/* Stats Overview */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Statistic
            title="Total Memories"
            value={stats.totalMemories}
            valueStyle={{ color: designTokens.colors.brand.gold }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Patterns"
            value={stats.patternsDetected}
            valueStyle={{ color: designTokens.colors.semantic.info }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Insights"
            value={stats.insightsGenerated}
            valueStyle={{ color: designTokens.colors.semantic.warning }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Avg Importance"
            value={`${(stats.averageImportance * 100).toFixed(0)}%`}
            valueStyle={{ color: designTokens.colors.semantic.success }}
          />
        </Col>
      </Row>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        style={{ minHeight: '400px' }}
      />

      {/* Info Alert */}
      {memories.length === 0 && patterns.length === 0 && insights.length === 0 && (
        <Alert
          type="info"
          message="No memory data available yet. Memories will populate as agents process your request."
          style={{ marginTop: '16px' }}
        />
      )}
    </Card>
  );
};

export default MemoryVisualization;