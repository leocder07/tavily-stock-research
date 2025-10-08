import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Typography,
  Row,
  Col,
  Tag,
  Progress,
  Avatar,
  List,
  Divider,
  Alert,
  Badge,
  Tooltip,
  Space,
  Collapse,
} from 'antd';
import {
  BranchesOutlined,
  UserOutlined,
  SendOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  StarOutlined,
  SearchOutlined,
  BarChartOutlined,
  RiseOutlined,
  BulbOutlined,
  LinkOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ReactFlow,
  Node,
  Edge,
  ConnectionMode,
  useNodesState,
  useEdgesState,
  ReactFlowProvider
} from 'reactflow';
import 'reactflow/dist/style.css';
import { designTokens } from '../design-system/tokens';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface AgentStatus {
  name: string;
  status: 'idle' | 'active' | 'thinking' | 'searching' | 'analyzing' | 'completed' | 'error';
  currentTask: string;
  duration: number;
  citations: number;
  confidence?: number;
}

interface ProgressEvent {
  type: string;
  agent: string;
  message: string;
  timestamp: string;
  metadata?: any;
}

interface DelegationFlow {
  from: string;
  to: string;
  task: string;
  timestamp: string;
}

interface AgentVisualizationProps {
  requestId: string;
  wsUrl?: string;
}

const AgentVisualization: React.FC<AgentVisualizationProps> = ({
  requestId,
  wsUrl = 'ws://localhost:8000/ws'
}) => {
  const [agents, setAgents] = useState<Map<string, AgentStatus>>(new Map());
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [delegations, setDelegations] = useState<DelegationFlow[]>([]);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [connected, setConnected] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<'active' | 'completed' | 'error'>('active');
  const wsRef = useRef<WebSocket | null>(null);
  const eventListRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestId]);

  useEffect(() => {
    updateFlowChart();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agents, delegations]);

  useEffect(() => {
    // Auto-scroll event list
    if (eventListRef.current) {
      eventListRef.current.scrollTop = eventListRef.current.scrollHeight;
    }
  }, [events]);

  const connectWebSocket = () => {
    const ws = new WebSocket(`${wsUrl}/${requestId}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000);
    };

    wsRef.current = ws;
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'agent_status':
        updateAgentStatus(data);
        break;
      case 'delegation':
        addDelegation(data);
        break;
      case 'citation_added':
      case 'memory_recalled':
      case 'pattern_detected':
      case 'insight_generated':
      case 'tool_call':
      case 'decision_made':
        addEvent(data);
        break;
      case 'error':
        handleError(data);
        break;
      case 'state_sync':
        handleStateSync(data);
        break;
      case 'agents_update':
        handleAgentsUpdate(data);
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const updateAgentStatus = (data: any) => {
    setAgents(prev => {
      const newAgents = new Map(prev);
      const existing = newAgents.get(data.agent) || {
        name: data.agent,
        status: 'idle',
        currentTask: '',
        duration: 0,
        citations: 0
      };

      newAgents.set(data.agent, {
        ...existing,
        status: data.metadata?.status || 'active',
        currentTask: data.message,
        duration: existing.duration + 1,
        confidence: data.metadata?.confidence
      });

      if (data.message.includes('completed')) {
        existing.status = 'completed';
      }

      return newAgents;
    });

    addEvent(data);
  };

  const addDelegation = (data: any) => {
    const delegation: DelegationFlow = {
      from: data.metadata.from,
      to: data.metadata.to,
      task: data.metadata.task,
      timestamp: data.timestamp
    };

    setDelegations(prev => [...prev, delegation]);
    addEvent(data);
  };

  const addEvent = (data: any) => {
    const event: ProgressEvent = {
      type: data.type,
      agent: data.agent,
      message: data.message,
      timestamp: data.timestamp,
      metadata: data.metadata
    };

    setEvents(prev => [...prev.slice(-50), event]); // Keep last 50 events
  };

  const handleError = (data: any) => {
    setAnalysisStatus('error');
    addEvent(data);
  };

  const handleStateSync = (data: any) => {
    if (data.analysis) {
      setAnalysisStatus(data.analysis.status);
    }
  };

  const handleAgentsUpdate = (data: any) => {
    if (data.agents) {
      const newAgents = new Map<string, AgentStatus>();
      data.agents.forEach((agent: any) => {
        newAgents.set(agent.agent, {
          name: agent.agent,
          status: agent.status,
          currentTask: agent.task,
          duration: 0,
          citations: agent.citations || 0
        });
      });
      setAgents(newAgents);
    }
  };

  const updateFlowChart = () => {
    // Create nodes for agents
    const agentNodes: Node[] = [];
    const agentEdges: Edge[] = [];

    // CEO node (root)
    agentNodes.push({
      id: 'CEO',
      data: {
        label: (
          <div style={{ textAlign: 'center' }}>
            <Avatar
              style={{
                backgroundColor: designTokens.colors.brand.gold,
                margin: '0 auto 8px'
              }}
              size={40}
              icon={<BranchesOutlined />}
            />
            <Text style={{ fontSize: '12px' }}>CEO</Text>
          </div>
        )
      },
      position: { x: 400, y: 50 },
      type: 'default',
      style: {
        background: agents.get('CEO')?.status === 'active'
          ? designTokens.colors.background.glass
          : designTokens.colors.background.card,
        border: `2px solid ${designTokens.colors.brand.gold}`,
        borderRadius: designTokens.borderRadius.md,
        padding: '10px'
      }
    });

    // Division Leaders
    const divisions = ['Research_Leader', 'Analysis_Leader', 'Strategy_Leader'];
    divisions.forEach((division, index) => {
      const agent = agents.get(division);
      agentNodes.push({
        id: division,
        data: {
          label: (
            <div style={{ textAlign: 'center' }}>
              <Avatar
                style={{
                  backgroundColor: getAgentColor(division),
                  margin: '0 auto 4px'
                }}
                size={35}
              >
                {getAgentIcon(division)}
              </Avatar>
              <Text style={{ fontSize: '11px', display: 'block' }}>
                {division.replace('_', ' ')}
              </Text>
              {agent && (
                <Tag
                  color={getStatusColor(agent.status)}
                  style={{ marginTop: '4px', fontSize: '10px' }}
                >
                  {agent.status}
                </Tag>
              )}
            </div>
          )
        },
        position: { x: 200 + index * 200, y: 200 },
        type: 'default',
        style: {
          background: agent?.status === 'active'
            ? designTokens.colors.background.glass
            : designTokens.colors.background.card,
          border: `2px solid ${getAgentColor(division)}`,
          borderRadius: designTokens.borderRadius.md,
          padding: '10px'
        }
      });

      // Connect CEO to divisions
      agentEdges.push({
        id: `CEO-${division}`,
        source: 'CEO',
        target: division,
        type: 'smoothstep',
        animated: agent?.status === 'active',
        style: { stroke: getAgentColor(division) }
      });
    });

    // Add worker agents
    agents.forEach((agent, name) => {
      if (!['CEO', ...divisions].includes(name)) {
        const parentDivision = getParentDivision(name);
        const parentNode = agentNodes.find(n => n.id === parentDivision);
        if (parentNode) {
          const workerIndex = Array.from(agents.keys()).filter(
            a => !['CEO', ...divisions].includes(a) && getParentDivision(a) === parentDivision
          ).indexOf(name);

          agentNodes.push({
            id: name,
            data: {
              label: (
                <div style={{ textAlign: 'center' }}>
                  <Avatar
                    style={{
                      backgroundColor: designTokens.colors.text.secondary
                    }}
                    size={30}
                  >
                    <UserOutlined style={{ fontSize: '14px' }} />
                  </Avatar>
                  <Text style={{ fontSize: '9px', display: 'block' }}>
                    {name.replace(/_/g, ' ')}
                  </Text>
                </div>
              )
            },
            position: {
              x: parentNode.position.x - 50 + workerIndex * 30,
              y: parentNode.position.y + 120
            },
            type: 'default',
            style: {
              background: agent.status === 'active'
                ? designTokens.colors.background.glass
                : designTokens.colors.background.card,
              border: `1px solid ${designTokens.colors.border.medium}`,
              borderRadius: designTokens.borderRadius.sm,
              padding: '8px'
            }
          });

          agentEdges.push({
            id: `${parentDivision}-${name}`,
            source: parentDivision,
            target: name,
            type: 'straight',
            animated: agent.status === 'active',
            style: { stroke: designTokens.colors.text.tertiary }
          });
        }
      }
    });

    setNodes(agentNodes);
    setEdges(agentEdges);
  };

  const getAgentColor = (agent: string): string => {
    if (agent.includes('Research')) return designTokens.colors.semantic.info;
    if (agent.includes('Analysis')) return designTokens.colors.semantic.warning;
    if (agent.includes('Strategy')) return designTokens.colors.semantic.success;
    return designTokens.colors.brand.gold;
  };

  const getAgentIcon = (agent: string) => {
    if (agent.includes('Research')) return <SearchOutlined />;
    if (agent.includes('Analysis')) return <BarChartOutlined />;
    if (agent.includes('Strategy')) return <RiseOutlined />;
    return <UserOutlined />;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'active': return 'blue';
      case 'thinking': return 'cyan';
      case 'searching': return 'purple';
      case 'analyzing': return 'orange';
      case 'completed': return 'green';
      case 'error': return 'red';
      default: return 'default';
    }
  };

  const getParentDivision = (agentName: string): string => {
    if (agentName.toLowerCase().includes('research')) return 'Research_Leader';
    if (agentName.toLowerCase().includes('analysis') || agentName.toLowerCase().includes('technical')) return 'Analysis_Leader';
    if (agentName.toLowerCase().includes('strategy') || agentName.toLowerCase().includes('portfolio')) return 'Strategy_Leader';
    return 'CEO';
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'delegation': return <SendOutlined style={{ fontSize: '14px' }} />;
      case 'citation_added': return <LinkOutlined style={{ fontSize: '14px' }} />;
      case 'insight_generated': return <StarOutlined style={{ fontSize: '14px' }} />;
      case 'pattern_detected': return <BulbOutlined style={{ fontSize: '14px' }} />;
      case 'decision_made': return <CheckCircleOutlined style={{ fontSize: '14px' }} />;
      case 'error': return <ExclamationCircleOutlined style={{ fontSize: '14px', color: designTokens.colors.semantic.danger }} />;
      default: return <UserOutlined style={{ fontSize: '14px' }} />;
    }
  };

  return (
    <Row gutter={[16, 16]}>
      {/* Connection Status */}
      <Col span={24}>
        <Alert
          type={connected ? 'success' : 'warning'}
          icon={connected ? <CheckCircleOutlined /> : <WarningOutlined />}
          message={connected ? 'Real-time updates connected' : 'Connecting to real-time updates...'}
          showIcon
        />
      </Col>

      {/* Agent Flow Chart */}
      <Col xs={24} lg={16}>
        <Card
          title="Agent Collaboration Flow"
          style={{
            background: designTokens.colors.background.card,
            border: `1px solid ${designTokens.colors.border.default}`
          }}
        >
          <div style={{ height: '500px', background: designTokens.colors.background.primary }}>
            <ReactFlowProvider>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                connectionMode={ConnectionMode.Loose}
                fitView
              />
            </ReactFlowProvider>
          </div>
        </Card>
      </Col>

      {/* Active Agents & Stats */}
      <Col xs={24} lg={8}>
        <Card
          title="Active Agents"
          style={{
            background: designTokens.colors.background.card,
            border: `1px solid ${designTokens.colors.border.default}`,
            height: '100%'
          }}
        >
          <List
            dataSource={Array.from(agents.values())}
            renderItem={(agent, index) => (
              <motion.div
                key={agent.name}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: index * 0.05 }}
              >
                <List.Item style={{ padding: '12px 0' }}>
                  <Space style={{ width: '100%' }} direction="vertical" size="small">
                    <Space align="center">
                      <Badge count={agent.citations} showZero={false}>
                        <Avatar
                          style={{ backgroundColor: getAgentColor(agent.name) }}
                          size={30}
                        >
                          {getAgentIcon(agent.name)}
                        </Avatar>
                      </Badge>
                      <div style={{ flex: 1 }}>
                        <Text strong style={{ display: 'block' }}>
                          {agent.name.replace(/_/g, ' ')}
                        </Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {agent.currentTask}
                        </Text>
                      </div>
                      <Tag color={getStatusColor(agent.status)}>
                        {agent.status}
                      </Tag>
                    </Space>
                    {agent.status === 'active' && (
                      <Progress
                        percent={agent.confidence ? agent.confidence * 100 : undefined}
                        strokeColor={designTokens.colors.brand.gold}
                        showInfo={false}
                        size="small"
                      />
                    )}
                  </Space>
                </List.Item>
              </motion.div>
            )}
          />
        </Card>
      </Col>

      {/* Event Stream */}
      <Col span={24}>
        <Card
          title="Real-time Event Stream"
          style={{
            background: designTokens.colors.background.card,
            border: `1px solid ${designTokens.colors.border.default}`
          }}
        >
          <div
            ref={eventListRef}
            style={{
              maxHeight: '300px',
              overflow: 'auto',
              background: designTokens.colors.background.primary,
              padding: '12px',
              borderRadius: designTokens.borderRadius.md
            }}
          >
            <AnimatePresence>
              {events.map((event, index) => (
                <motion.div
                  key={`${event.timestamp}-${index}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  style={{ marginBottom: '8px' }}
                >
                  <Space align="center" style={{ width: '100%' }}>
                    {getEventIcon(event.type)}
                    <Text type="secondary" style={{ fontSize: '12px', minWidth: '60px' }}>
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </Text>
                    <Tag style={{ minWidth: '100px' }}>{event.agent}</Tag>
                    <Text style={{ flex: 1 }}>{event.message}</Text>
                  </Space>
                  <Divider style={{ margin: '8px 0' }} />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </Card>
      </Col>
    </Row>
  );
};

export default AgentVisualization;