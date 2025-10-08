import React, { useState, useEffect } from 'react';
import { Card, Progress, Tag, Badge, Space, Row, Col, Timeline, Alert, Tooltip } from 'antd';
import {
  RobotOutlined,
  TeamOutlined,
  SearchOutlined,
  FileTextOutlined,
  GlobalOutlined,
  ForkOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  ApiOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import './GlassCard.css';

interface AgentStatus {
  name: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  message?: string;
  progress?: number;
  icon?: React.ReactNode;
  tavilyAPIs?: TavilyAPICall[];
}

interface TavilyAPICall {
  api: 'search' | 'extract' | 'crawl' | 'map';
  status: 'pending' | 'calling' | 'success' | 'error';
  count: number;
  results?: number;
  latency?: number;
}

interface WorkflowVisualizerProps {
  currentAgent?: string;
  progress?: number;
  agents?: AgentStatus[];
  isActive?: boolean;
}

const WorkflowVisualizer: React.FC<WorkflowVisualizerProps> = ({
  currentAgent,
  progress = 0,
  agents: propsAgents,
  isActive = false,
}) => {
  const [agents, setAgents] = useState<AgentStatus[]>([
    {
      name: 'CEO Orchestrator',
      status: 'pending',
      message: 'Strategic planning',
      icon: <TeamOutlined />,
      tavilyAPIs: [],
    },
    {
      name: 'Research Division',
      status: 'pending',
      message: 'Market data gathering',
      icon: <SearchOutlined />,
      tavilyAPIs: [
        { api: 'search', status: 'pending', count: 0 },
        { api: 'extract', status: 'pending', count: 0 },
      ],
    },
    {
      name: 'Analysis Division',
      status: 'pending',
      message: 'Technical & fundamental analysis',
      icon: <FileTextOutlined />,
      tavilyAPIs: [
        { api: 'crawl', status: 'pending', count: 0 },
      ],
    },
    {
      name: 'Strategy Division',
      status: 'pending',
      message: 'Investment recommendations',
      icon: <ForkOutlined />,
      tavilyAPIs: [
        { api: 'map', status: 'pending', count: 0 },
      ],
    },
  ]);

  useEffect(() => {
    if (propsAgents) {
      setAgents(propsAgents);
    }
  }, [propsAgents]);

  // Simulate agent progression (for demo)
  useEffect(() => {
    if (!isActive) return;

    const simulateProgress = () => {
      setAgents((prevAgents) => {
        const updatedAgents = [...prevAgents];

        // Find first pending agent and activate it
        const pendingIndex = updatedAgents.findIndex((a) => a.status === 'pending');
        if (pendingIndex !== -1) {
          updatedAgents[pendingIndex].status = 'active';

          // Simulate Tavily API calls
          if (updatedAgents[pendingIndex].tavilyAPIs) {
            updatedAgents[pendingIndex].tavilyAPIs = updatedAgents[pendingIndex].tavilyAPIs!.map(
              (api) => ({
                ...api,
                status: 'calling',
                count: Math.floor(Math.random() * 5) + 1,
              })
            );
          }
        }

        // Find active agent and complete it
        const activeIndex = updatedAgents.findIndex((a) => a.status === 'active');
        if (activeIndex !== -1 && Math.random() > 0.5) {
          updatedAgents[activeIndex].status = 'completed';
          updatedAgents[activeIndex].progress = 100;

          // Complete Tavily API calls
          if (updatedAgents[activeIndex].tavilyAPIs) {
            updatedAgents[activeIndex].tavilyAPIs = updatedAgents[activeIndex].tavilyAPIs!.map(
              (api) => ({
                ...api,
                status: 'success',
                results: Math.floor(Math.random() * 100) + 10,
                latency: Math.floor(Math.random() * 2000) + 500,
              })
            );
          }
        }

        return updatedAgents;
      });
    };

    const interval = setInterval(simulateProgress, 2000);
    return () => clearInterval(interval);
  }, [isActive]);

  const getAgentColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'processing';
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getTavilyAPIIcon = (api: string) => {
    switch (api) {
      case 'search':
        return <SearchOutlined />;
      case 'extract':
        return <FileTextOutlined />;
      case 'crawl':
        return <GlobalOutlined />;
      case 'map':
        return <ForkOutlined />;
      default:
        return <ApiOutlined />;
    }
  };

  const getTavilyAPIColor = (api: string) => {
    switch (api) {
      case 'search':
        return '#1890ff'; // Blue
      case 'extract':
        return '#52c41a'; // Green
      case 'crawl':
        return '#faad14'; // Orange
      case 'map':
        return '#722ed1'; // Purple
      default:
        return '#666';
    }
  };

  const renderTavilyAPIs = (apis?: TavilyAPICall[]) => {
    if (!apis || apis.length === 0) return null;

    return (
      <Space wrap style={{ marginTop: 8 }}>
        {apis.map((api, idx) => (
          <Tooltip
            key={idx}
            title={
              <div>
                <div>Status: {api.status}</div>
                {api.count > 0 && <div>Calls: {api.count}</div>}
                {api.results && <div>Results: {api.results}</div>}
                {api.latency && <div>Latency: {api.latency}ms</div>}
              </div>
            }
          >
            <Badge
              count={api.count || 0}
              style={{ backgroundColor: getTavilyAPIColor(api.api) }}
            >
              <Tag
                icon={getTavilyAPIIcon(api.api)}
                color={api.status === 'success' ? 'success' : api.status === 'calling' ? 'processing' : 'default'}
              >
                {api.api.toUpperCase()}
              </Tag>
            </Badge>
          </Tooltip>
        ))}
      </Space>
    );
  };

  const renderAgentNode = (agent: AgentStatus, index: number) => {
    const isActive = agent.status === 'active';
    const isCompleted = agent.status === 'completed';

    return (
      <motion.div
        key={agent.name}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.1 }}
        style={{ marginBottom: 16 }}
      >
        <Card
          className={`glass-card ${isActive ? 'agent-active' : ''}`}
          style={{
            borderLeft: `4px solid ${
              isCompleted ? '#52c41a' : isActive ? '#1890ff' : '#666'
            }`,
          }}
        >
          <Row align="middle" gutter={16}>
            <Col span={1}>
              <div style={{ fontSize: 24 }}>{agent.icon}</div>
            </Col>
            <Col span={15}>
              <div>
                <Space>
                  <strong>{agent.name}</strong>
                  <Badge status={getAgentColor(agent.status)} />
                </Space>
              </div>
              <div style={{ color: '#888', fontSize: 12, marginTop: 4 }}>
                {agent.message}
              </div>
              {renderTavilyAPIs(agent.tavilyAPIs)}
            </Col>
            <Col span={8}>
              {isActive && (
                <Progress
                  percent={agent.progress || 50}
                  status="active"
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
              )}
              {isCompleted && (
                <Tag color="success" icon={<CheckCircleOutlined />}>
                  Completed
                </Tag>
              )}
              {agent.status === 'pending' && (
                <Tag icon={<ClockCircleOutlined />}>Pending</Tag>
              )}
            </Col>
          </Row>
        </Card>
      </motion.div>
    );
  };

  const renderWorkflowDiagram = () => {
    return (
      <div style={{ padding: '20px 0' }}>
        <Timeline mode="left">
          {agents.map((agent, idx) => (
            <Timeline.Item
              key={idx}
              color={
                agent.status === 'completed'
                  ? 'green'
                  : agent.status === 'active'
                  ? 'blue'
                  : 'gray'
              }
              dot={
                agent.status === 'active' ? (
                  <SyncOutlined spin style={{ fontSize: 16 }} />
                ) : (
                  agent.icon
                )
              }
            >
              <div>
                <strong>{agent.name}</strong>
                {agent.status === 'active' && (
                  <Tag color="processing" style={{ marginLeft: 8 }}>
                    Processing
                  </Tag>
                )}
              </div>
              <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>
                {agent.message}
              </div>
              {agent.tavilyAPIs && agent.tavilyAPIs.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <Space size={4}>
                    {agent.tavilyAPIs.map((api, apiIdx) => (
                      <Badge
                        key={apiIdx}
                        status={
                          api.status === 'success'
                            ? 'success'
                            : api.status === 'calling'
                            ? 'processing'
                            : 'default'
                        }
                        text={api.api}
                      />
                    ))}
                  </Space>
                </div>
              )}
            </Timeline.Item>
          ))}
        </Timeline>
      </div>
    );
  };

  const totalTavilyAPICalls = agents.reduce((total, agent) => {
    if (!agent.tavilyAPIs) return total;
    return total + agent.tavilyAPIs.reduce((sum, api) => sum + (api.count || 0), 0);
  }, 0);

  const completedAgents = agents.filter((a) => a.status === 'completed').length;

  return (
    <Card
      className="glass-card"
      title={
        <Space>
          <RobotOutlined />
          <span>AI Agent Workflow</span>
          {isActive && <Badge status="processing" text="Active" />}
        </Space>
      }
      extra={
        <Space>
          <Tag icon={<ApiOutlined />} color="blue">
            Tavily Calls: {totalTavilyAPICalls}
          </Tag>
          <Tag icon={<ThunderboltOutlined />} color="green">
            {completedAgents}/{agents.length} Complete
          </Tag>
        </Space>
      }
    >
      {isActive && (
        <Alert
          message="Analysis in Progress"
          description="AI agents are working together to analyze your query using multiple Tavily APIs"
          type="info"
          showIcon
          icon={<SyncOutlined spin />}
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={[16, 16]}>
        <Col span={14}>
          <div style={{ padding: '0 16px' }}>
            {agents.map((agent, idx) => renderAgentNode(agent, idx))}
          </div>
        </Col>
        <Col span={10}>
          <Card
            className="glass-card"
            size="small"
            title="Workflow Timeline"
            style={{ height: '100%' }}
          >
            {renderWorkflowDiagram()}
          </Card>
        </Col>
      </Row>

      {progress > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 8 }}>
            <span style={{ color: '#888' }}>Overall Progress</span>
          </div>
          <Progress
            percent={progress}
            status="active"
            strokeColor={{
              '0%': '#FFD700',
              '100%': '#52c41a',
            }}
          />
        </div>
      )}
    </Card>
  );
};

export default WorkflowVisualizer;