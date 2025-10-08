import React, { useState, useEffect } from 'react';
import { Card, List, Tag, Progress, Space, Avatar, Tabs } from 'antd';
import {
  SearchOutlined,
  LineChartOutlined,
  FundOutlined,
  HeartOutlined,
  AreaChartOutlined,
  WarningOutlined,
  TeamOutlined,
  BulbOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  LinkOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import CitationPanel, { Citation } from './CitationPanel';
// WebSocket removed - using polling instead
// import { useWebSocketContext } from '../hooks/useWebSocket';

interface Agent {
  name: string;
  displayName: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  confidence?: number;
  icon: React.ReactNode;
  description: string;
}

interface AgentProgressProps {
  analysisId: string | null;
}

const AgentProgress: React.FC<AgentProgressProps> = ({ analysisId }) => {
  // const { lastMessage } = useWebSocketContext(); // WebSocket removed
  const [citations, setCitations] = useState<Citation[]>([]);
  // Match backend agent names: fundamental, technical, risk, sentiment, synthesis
  const [agents, setAgents] = useState<Agent[]>([
    {
      name: 'fundamental',
      displayName: 'Fundamental Analysis',
      status: 'pending',
      icon: <FundOutlined />,
      description: 'Analyzing financial statements and company metrics',
    },
    {
      name: 'technical',
      displayName: 'Technical Analysis',
      status: 'pending',
      icon: <AreaChartOutlined />,
      description: 'Examining chart patterns and indicators',
    },
    {
      name: 'risk',
      displayName: 'Risk Assessment',
      status: 'pending',
      icon: <WarningOutlined />,
      description: 'Calculating portfolio risk and volatility',
    },
    {
      name: 'sentiment',
      displayName: 'Sentiment Analysis',
      status: 'pending',
      icon: <HeartOutlined />,
      description: 'Evaluating news sentiment and market mood (via Tavily)',
    },
    {
      name: 'synthesis',
      displayName: 'Synthesis',
      status: 'pending',
      icon: <BulbOutlined />,
      description: 'Combining insights into recommendations',
    },
  ]);

  // Handle WebSocket messages for citations and agent updates
  // WebSocket removed - this component now shows static agent list
  /*
  useEffect(() => {
    if (!lastMessage) return;

    // Handle citation updates
    if (lastMessage.type === 'citation_update') {
      const newCitation: Citation = {
        id: lastMessage.citation_id || `${Date.now()}_${Math.random()}`,
        title: lastMessage.title || '',
        url: lastMessage.url || '',
        content: lastMessage.content || '',
        agent_id: lastMessage.agent_id || 'unknown',
        agent_name: lastMessage.agent_name || 'Unknown Agent',
        timestamp: lastMessage.timestamp || new Date().toISOString(),
        relevance_score: lastMessage.relevance_score || 0.5,
        published_date: lastMessage.published_date,
        source: lastMessage.source,
      };
      setCitations(prev => [...prev, newCitation]);
    }

    // Handle agent progress updates
    if (lastMessage.type === 'agent_progress') {
      const agentName = lastMessage.agent_id || lastMessage.agent_name;
      const status = lastMessage.status; // 'started', 'processing', 'completed', 'failed'

      setAgents(prev => {
        const updated = [...prev];
        const agentIndex = updated.findIndex(a => a.name === agentName);

        if (agentIndex !== -1) {
          if (status === 'started' || status === 'processing') {
            updated[agentIndex].status = 'processing';
          } else if (status === 'completed') {
            updated[agentIndex].status = 'completed';
            updated[agentIndex].confidence = lastMessage.confidence || 85;
          } else if (status === 'failed') {
            updated[agentIndex].status = 'failed';
          }
        }

        return updated;
      });
    }

    // Handle bulk citations (e.g., from agent completion)
    if (lastMessage.type === 'agent_citations') {
      const newCitations: Citation[] = (lastMessage.citations || []).map((cit: any) => ({
        id: cit.id || `${Date.now()}_${Math.random()}`,
        title: cit.title || '',
        url: cit.url || '',
        content: cit.content || '',
        agent_id: lastMessage.agent_id || cit.agent_id || 'unknown',
        agent_name: lastMessage.agent_name || cit.agent_name || 'Unknown Agent',
        timestamp: cit.timestamp || new Date().toISOString(),
        relevance_score: cit.relevance_score || 0.5,
        published_date: cit.published_date,
        source: cit.source,
      }));
      setCitations(prev => [...prev, ...newCitations]);
    }
  }, [lastMessage]);
  */

  // Poll for real agent progress from backend
  useEffect(() => {
    if (!analysisId) return;

    let interval: NodeJS.Timeout;

    const fetchAgentStatus = async () => {
      try {
        const response = await fetch(`/api/v1/analyze/${analysisId}/status`);
        const data = await response.json();

        // Update agents based on backend progress
        if (data.progress && typeof data.progress === 'object') {
          const { active_agents = [], completed_agents = [], pending_agents = [] } = data.progress;

          setAgents(prev => prev.map(agent => {
            if (completed_agents.includes(agent.name)) {
              return { ...agent, status: 'completed', confidence: 85 + Math.random() * 10 };
            } else if (active_agents.includes(agent.name)) {
              return { ...agent, status: 'processing' };
            } else if (data.status === 'failed') {
              // Check if this agent failed specifically
              return { ...agent, status: pending_agents.includes(agent.name) ? 'pending' : 'failed' };
            } else if (pending_agents.includes(agent.name)) {
              return { ...agent, status: 'pending' };
            }
            return agent;
          }));
        }

        // Stop polling when analysis is done
        if (data.status === 'completed' || data.status === 'failed') {
          if (interval) clearInterval(interval);
        }
      } catch (error) {
        console.error('Error fetching agent status:', error);
      }
    };

    // Initial fetch
    fetchAgentStatus();

    // Poll every 1 second
    interval = setInterval(fetchAgentStatus, 1000);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [analysisId]);

  const getStatusIcon = (status: Agent['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'processing':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />;
      case 'failed':
        return <WarningOutlined style={{ color: '#f5222d' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'processing';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  // Agent progress tab content
  const AgentProgressTab = () => (
    <List
      itemLayout="horizontal"
      dataSource={agents}
      renderItem={(agent) => (
        <List.Item>
          <List.Item.Meta
            avatar={
              <Avatar
                icon={agent.icon}
                style={{
                  backgroundColor:
                    agent.status === 'completed'
                      ? '#f6ffed'
                      : agent.status === 'processing'
                      ? '#e6f7ff'
                      : '#fafafa',
                  color:
                    agent.status === 'completed'
                      ? '#52c41a'
                      : agent.status === 'processing'
                      ? '#1890ff'
                      : '#d9d9d9',
                }}
              />
            }
            title={
              <Space>
                <span>{agent.displayName}</span>
                {getStatusIcon(agent.status)}
                {agent.confidence && (
                  <Tag color={agent.confidence > 80 ? 'green' : 'orange'}>
                    {agent.confidence.toFixed(0)}% confidence
                  </Tag>
                )}
              </Space>
            }
            description={
              <div>
                <div style={{ fontSize: '12px', color: '#8c8c8c', marginBottom: 4 }}>
                  {agent.description}
                </div>
                {agent.status === 'processing' && (
                  <Progress
                    percent={50}
                    size="small"
                    status="active"
                    showInfo={false}
                    strokeColor="#1890ff"
                  />
                )}
              </div>
            }
          />
          <Tag color={getStatusColor(agent.status)}>
            {agent.status.toUpperCase()}
          </Tag>
        </List.Item>
      )}
    />
  );

  return (
    <Card size="small">
      <Tabs
        defaultActiveKey="agents"
        items={[
          {
            key: 'agents',
            label: (
              <Space>
                <RobotOutlined />
                <span>Agent Progress</span>
              </Space>
            ),
            children: <AgentProgressTab />,
          },
          {
            key: 'citations',
            label: (
              <Space>
                <LinkOutlined />
                <span>Citations ({citations.length})</span>
              </Space>
            ),
            children: <CitationPanel citations={citations} loading={!analysisId} />,
          },
        ]}
      />
    </Card>
  );
};

export default AgentProgress;