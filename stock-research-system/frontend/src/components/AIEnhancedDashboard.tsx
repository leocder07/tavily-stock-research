import React, { useState, useEffect } from 'react';
import { Layout, Tabs, Card, Row, Col, Space, Button, Badge, Statistic, Progress, message } from 'antd';
import {
  RobotOutlined,
  BranchesOutlined,
  ExperimentOutlined,
  SearchOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  ApiOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';

// Import our cutting-edge AI components
import AgentGraph from './ai/AgentGraph';
import AITransparencyDashboard from './ai/AITransparencyDashboard';
import SmartQueryBuilder from './SmartQueryBuilder';
import WorkflowVisualizer from './WorkflowVisualizer';

// Import existing components
import StockAnalysisPanel from './StockAnalysisPanel';
import MarketOverview from './MarketOverview';
import AnalyticalDashboard from './AnalyticalDashboard';

import './AIEnhancedDashboard.css';

const { Header, Content } = Layout;

interface SystemMetrics {
  totalQueries: number;
  avgResponseTime: number;
  modelsActive: number;
  parallelTasks: number;
  tokenUsage: number;
  totalCost: number;
  confidenceScore: number;
  cacheHitRate: number;
}

const AIEnhancedDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('ai-chat');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    totalQueries: 42,
    avgResponseTime: 2.3,
    modelsActive: 4,
    parallelTasks: 8,
    tokenUsage: 125000,
    totalCost: 1.85,
    confidenceScore: 0.92,
    cacheHitRate: 0.68
  });

  // Sample data for components
  const [watchlist] = useState(['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']);
  const [selectedStock] = useState({
    symbol: 'AAPL',
    name: 'Apple Inc.',
    price: 175.82,
    change: 4.35,
    changePercent: 2.54,
    volume: 45678900,
    marketCap: 2800000000000
  });

  // Simulate real-time metrics updates
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics(prev => ({
        ...prev,
        tokenUsage: prev.tokenUsage + Math.floor(Math.random() * 100),
        totalCost: prev.totalCost + Math.random() * 0.01,
        parallelTasks: Math.floor(Math.random() * 12),
        confidenceScore: 0.85 + Math.random() * 0.1
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async (query: string, model?: string) => {
    setCurrentQuery(query);
    setIsAnalyzing(true);
    message.info(`Analyzing "${query}" with ${model || 'default model'}...`);

    // Simulate analysis
    setTimeout(() => {
      setIsAnalyzing(false);
      message.success('Analysis complete!');
      setSystemMetrics(prev => ({
        ...prev,
        totalQueries: prev.totalQueries + 1,
        tokenUsage: prev.tokenUsage + Math.floor(Math.random() * 5000),
        totalCost: prev.totalCost + Math.random() * 0.1
      }));
    }, 3000);
  };

  const tabItems = [
    {
      key: 'ai-chat',
      label: (
        <span>
          <RobotOutlined />
          AI Assistant
        </span>
      ),
      children: (
        <Row gutter={[16, 16]}>
          <Col xs={24}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <SmartQueryBuilder onSubmit={handleAnalyze} loading={isAnalyzing} />
              <Card
                className="metrics-card glass-card"
                title="System Performance"
                size="small"
              >
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Statistic
                      title="Response Time"
                      value={systemMetrics.avgResponseTime}
                      suffix="s"
                      prefix={<ClockCircleOutlined />}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Confidence"
                      value={systemMetrics.confidenceScore * 100}
                      suffix="%"
                      prefix={<CheckCircleOutlined />}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Tokens Used"
                      value={systemMetrics.tokenUsage}
                      prefix={<ThunderboltOutlined />}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Total Cost"
                      value={systemMetrics.totalCost}
                      prefix="$"
                      precision={2}
                      valueStyle={{ color: '#faad14' }}
                    />
                  </Col>
                </Row>
              </Card>
            </Space>
          </Col>
        </Row>
      )
    },
    {
      key: 'agent-flow',
      label: (
        <span>
          <BranchesOutlined />
          Agent Workflow
          {systemMetrics.parallelTasks > 0 && (
            <Badge
              count={systemMetrics.parallelTasks}
              style={{ marginLeft: 8, backgroundColor: '#52c41a' }}
            />
          )}
        </span>
      ),
      children: (
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <AgentGraph isLive={isAnalyzing} />
          </Col>
          <Col span={24}>
            <WorkflowVisualizer
              currentAgent={isAnalyzing ? "Analysis Division" : undefined}
              progress={isAnalyzing ? 65 : 0}
              isActive={isAnalyzing}
            />
          </Col>
        </Row>
      )
    },
    {
      key: 'ai-transparency',
      label: (
        <span>
          <EyeOutlined />
          AI Transparency
        </span>
      ),
      children: (
        <AITransparencyDashboard
          queryResult={currentQuery ? { query: currentQuery } : undefined}
          isProcessing={isAnalyzing}
        />
      )
    },
    {
      key: 'market-analysis',
      label: (
        <span>
          <BarChartOutlined />
          Market Analysis
        </span>
      ),
      children: (
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <MarketOverview watchlist={watchlist} />
          </Col>
          <Col span={24}>
            <StockAnalysisPanel stock={selectedStock} />
          </Col>
        </Row>
      )
    },
    {
      key: 'analytics',
      label: (
        <span>
          <ExperimentOutlined />
          Analytics
        </span>
      ),
      children: <AnalyticalDashboard />
    }
  ];

  return (
    <Layout className="ai-enhanced-dashboard">
      <Header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Space size="large">
                <div className="logo">
                  <RocketOutlined style={{ fontSize: 24, color: '#722ed1' }} />
                  <span className="logo-text">TavilyAI Pro</span>
                </div>
                <Badge status="processing" text="AI Systems Active" />
              </Space>
            </motion.div>
          </div>
          <div className="header-right">
            <Space size="middle">
              <Badge count={systemMetrics.modelsActive} style={{ backgroundColor: '#722ed1' }}>
                <ApiOutlined style={{ fontSize: 20, color: '#fff' }} />
              </Badge>
              <Progress
                type="circle"
                percent={systemMetrics.cacheHitRate * 100}
                width={40}
                format={() => `${(systemMetrics.cacheHitRate * 100).toFixed(0)}%`}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
              <Statistic
                value={systemMetrics.totalQueries}
                prefix={<SearchOutlined />}
                valueStyle={{ fontSize: 16, color: '#fff' }}
              />
              <Button type="primary" icon={<RocketOutlined />}>
                Upgrade to Pro
              </Button>
            </Space>
          </div>
        </div>
      </Header>

      <Content className="dashboard-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={tabItems}
              size="large"
              className="dashboard-tabs"
              tabBarStyle={{
                background: 'rgba(10, 14, 27, 0.8)',
                padding: '12px 24px',
                borderRadius: '12px',
                marginBottom: 24
              }}
            />
          </motion.div>
        </AnimatePresence>
      </Content>

      {/* Floating Performance Widget */}
      <motion.div
        className="floating-widget"
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, type: 'spring' }}
        drag
        dragConstraints={{ left: -100, right: 100, top: -100, bottom: 100 }}
      >
        <Card size="small" className="glass-card">
          <Space direction="vertical" align="center">
            <ThunderboltOutlined style={{ fontSize: 24, color: '#722ed1' }} />
            <div style={{ fontSize: 12, color: '#fff' }}>
              {systemMetrics.parallelTasks} Tasks
            </div>
            <Progress
              type="dashboard"
              percent={75}
              width={60}
              strokeColor={{
                '0%': '#722ed1',
                '100%': '#eb2f96',
              }}
            />
          </Space>
        </Card>
      </motion.div>
    </Layout>
  );
};

export default AIEnhancedDashboard;