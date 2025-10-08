import React, { useEffect, useRef, useState } from 'react';
import { Card, Tag, Tooltip, Space, Badge, Button, Progress, Drawer, Timeline, Statistic, Typography } from 'antd';
import {
  ForkOutlined,
  TeamOutlined,
  SearchOutlined,
  FileTextOutlined,
  RobotOutlined,
  ApiOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  BranchesOutlined,
  NodeExpandOutlined,
  PartitionOutlined,
  EyeOutlined
} from '@ant-design/icons';
import * as d3 from 'd3';
import { motion, AnimatePresence } from 'framer-motion';
import './AgentGraph.css';

interface Agent {
  id: string;
  name: string;
  type: 'orchestrator' | 'worker' | 'tool';
  status: 'idle' | 'running' | 'completed' | 'error';
  model?: string;
  confidence?: number;
  executionTime?: number;
  tokens?: number;
  toolCalls?: ToolCall[];
  dependencies?: string[];
  parallelGroup?: number;
}

interface ToolCall {
  tool: string;
  api?: 'search' | 'extract' | 'crawl' | 'map';
  status: 'pending' | 'calling' | 'success' | 'error';
  latency?: number;
  results?: number;
}

interface Edge {
  source: string;
  target: string;
  type: 'dependency' | 'data_flow' | 'parallel';
  status: 'pending' | 'active' | 'completed';
  dataTransferred?: string;
}

interface AgentGraphProps {
  agents?: Agent[];
  edges?: Edge[];
  onAgentClick?: (agentId: string) => void;
  isLive?: boolean;
}

const AgentGraph: React.FC<AgentGraphProps> = ({
  agents: propsAgents,
  edges: propsEdges,
  onAgentClick,
  isLive = false
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [graphStats, setGraphStats] = useState({
    totalAgents: 0,
    runningAgents: 0,
    completedAgents: 0,
    parallelGroups: 0,
    estimatedTime: 0
  });

  // Default agents for demonstration
  const defaultAgents: Agent[] = [
    {
      id: 'ceo',
      name: 'CEO Orchestrator',
      type: 'orchestrator',
      status: 'completed',
      model: 'claude-3-opus',
      confidence: 0.95,
      executionTime: 1.2,
      tokens: 1500,
      dependencies: []
    },
    {
      id: 'research-lead',
      name: 'Research Lead',
      type: 'orchestrator',
      status: 'running',
      model: 'gpt-4-turbo',
      confidence: 0.88,
      executionTime: 0.8,
      dependencies: ['ceo'],
      parallelGroup: 1
    },
    {
      id: 'analysis-lead',
      name: 'Analysis Lead',
      type: 'orchestrator',
      status: 'running',
      model: 'gpt-4-turbo',
      confidence: 0.91,
      executionTime: 0.9,
      dependencies: ['ceo'],
      parallelGroup: 1
    },
    {
      id: 'researcher-1',
      name: 'Market Researcher',
      type: 'worker',
      status: 'completed',
      model: 'claude-3-sonnet',
      executionTime: 0.5,
      dependencies: ['research-lead'],
      toolCalls: [
        { tool: 'tavily', api: 'search', status: 'success', latency: 0.3, results: 25 },
        { tool: 'tavily', api: 'extract', status: 'success', latency: 0.2, results: 10 }
      ],
      parallelGroup: 2
    },
    {
      id: 'researcher-2',
      name: 'News Analyst',
      type: 'worker',
      status: 'running',
      model: 'gpt-3.5-turbo',
      executionTime: 0.4,
      dependencies: ['research-lead'],
      toolCalls: [
        { tool: 'tavily', api: 'crawl', status: 'calling', latency: 0.1 }
      ],
      parallelGroup: 2
    },
    {
      id: 'analyst-1',
      name: 'Technical Analyst',
      type: 'worker',
      status: 'idle',
      model: 'gpt-4-turbo',
      dependencies: ['analysis-lead', 'researcher-1'],
      parallelGroup: 3
    },
    {
      id: 'analyst-2',
      name: 'Fundamental Analyst',
      type: 'worker',
      status: 'idle',
      model: 'claude-3-sonnet',
      dependencies: ['analysis-lead', 'researcher-2'],
      parallelGroup: 3
    },
    {
      id: 'strategy',
      name: 'Strategy Synthesizer',
      type: 'orchestrator',
      status: 'idle',
      model: 'claude-3-opus',
      dependencies: ['analyst-1', 'analyst-2'],
      toolCalls: [
        { tool: 'tavily', api: 'map', status: 'pending' }
      ]
    }
  ];

  const defaultEdges: Edge[] = [
    { source: 'ceo', target: 'research-lead', type: 'dependency', status: 'completed' },
    { source: 'ceo', target: 'analysis-lead', type: 'dependency', status: 'completed' },
    { source: 'research-lead', target: 'researcher-1', type: 'data_flow', status: 'active' },
    { source: 'research-lead', target: 'researcher-2', type: 'data_flow', status: 'active' },
    { source: 'researcher-1', target: 'analyst-1', type: 'data_flow', status: 'pending' },
    { source: 'researcher-2', target: 'analyst-2', type: 'data_flow', status: 'pending' },
    { source: 'analysis-lead', target: 'analyst-1', type: 'dependency', status: 'pending' },
    { source: 'analysis-lead', target: 'analyst-2', type: 'dependency', status: 'pending' },
    { source: 'analyst-1', target: 'strategy', type: 'data_flow', status: 'pending' },
    { source: 'analyst-2', target: 'strategy', type: 'data_flow', status: 'pending' }
  ];

  const agents = propsAgents || defaultAgents;
  const edges = propsEdges || defaultEdges;

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = 500;
    const margin = { top: 40, right: 40, bottom: 40, left: 40 };

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Create container group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Define arrow markers
    const defs = svg.append('defs');

    ['pending', 'active', 'completed'].forEach(status => {
      defs.append('marker')
        .attr('id', `arrow-${status}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', status === 'active' ? '#1890ff' : status === 'completed' ? '#52c41a' : '#8c8c8c');
    });

    // Create force simulation
    const simulation = d3.forceSimulation(agents as any)
      .force('link', d3.forceLink(edges)
        .id((d: any) => d.id)
        .distance(120))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(width / 2 - margin.left, height / 2 - margin.top))
      .force('collision', d3.forceCollide().radius(40));

    // Create links
    const link = g.selectAll('.link')
      .data(edges)
      .enter().append('line')
      .attr('class', d => `link link-${d.status}`)
      .attr('stroke', d => d.status === 'active' ? '#1890ff' : d.status === 'completed' ? '#52c41a' : '#8c8c8c')
      .attr('stroke-width', d => d.status === 'active' ? 3 : 2)
      .attr('stroke-dasharray', d => d.status === 'pending' ? '5,5' : 'none')
      .attr('marker-end', d => `url(#arrow-${d.status})`);

    // Create node groups
    const node = g.selectAll('.node')
      .data(agents)
      .enter().append('g')
      .attr('class', 'node')
      .on('click', (event, d) => {
        setSelectedAgent(d as Agent);
        setDrawerVisible(true);
        if (onAgentClick) onAgentClick(d.id);
      })
      .call(d3.drag<any, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any);

    // Add circles for nodes
    node.append('circle')
      .attr('r', d => d.type === 'orchestrator' ? 25 : 20)
      .attr('fill', d => {
        if (d.status === 'completed') return '#52c41a';
        if (d.status === 'running') return '#1890ff';
        if (d.status === 'error') return '#ff4d4f';
        return '#8c8c8c';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    // Add icons
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '16px')
      .text(d => {
        if (d.type === 'orchestrator') return '👔';
        if (d.type === 'worker') return '🤖';
        return '🔧';
      });

    // Add labels
    node.append('text')
      .attr('x', 0)
      .attr('y', 35)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .attr('font-size', '11px')
      .text(d => d.name);

    // Add status indicator
    node.append('circle')
      .attr('class', 'status-indicator')
      .attr('cx', 15)
      .attr('cy', -15)
      .attr('r', 5)
      .attr('fill', d => {
        if (d.status === 'running') return '#52c41a';
        if (d.status === 'completed') return '#1890ff';
        return 'transparent';
      })
      .attr('stroke', d => d.status === 'running' ? '#52c41a' : 'transparent')
      .attr('stroke-width', 2)
      .style('animation', d => d.status === 'running' ? 'pulse 2s infinite' : 'none');

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Calculate statistics
    const stats = {
      totalAgents: agents.length,
      runningAgents: agents.filter(a => a.status === 'running').length,
      completedAgents: agents.filter(a => a.status === 'completed').length,
      parallelGroups: new Set(agents.map(a => a.parallelGroup).filter(Boolean)).size,
      estimatedTime: Math.max(...agents.map(a => a.executionTime || 0))
    };
    setGraphStats(stats);

  }, [agents, edges, onAgentClick]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'running': return 'blue';
      case 'error': return 'red';
      default: return 'default';
    }
  };

  const getModelBadgeColor = (model?: string) => {
    if (!model) return 'default';
    if (model.includes('claude')) return 'purple';
    if (model.includes('gpt-4')) return 'blue';
    if (model.includes('gpt-3.5')) return 'cyan';
    return 'default';
  };

  return (
    <Card
      className="agent-graph-container glass-card"
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <BranchesOutlined style={{ fontSize: 20, color: '#722ed1' }} />
            <span>Agent Execution Graph</span>
            {isLive && (
              <Badge status="processing" text="Live" />
            )}
          </Space>
          <Space>
            <Tag color="blue">
              <SyncOutlined spin={graphStats.runningAgents > 0} />
              {graphStats.runningAgents} Running
            </Tag>
            <Tag color="green">
              <CheckCircleOutlined />
              {graphStats.completedAgents} Completed
            </Tag>
            <Tag color="purple">
              <PartitionOutlined />
              {graphStats.parallelGroups} Parallel Groups
            </Tag>
          </Space>
        </div>
      }
      extra={
        <Button
          icon={<EyeOutlined />}
          onClick={() => setDrawerVisible(true)}
        >
          View Details
        </Button>
      }
    >
      <div ref={containerRef} className="graph-container">
        <svg ref={svgRef} className="agent-graph"></svg>
      </div>

      <div className="graph-legend">
        <Space>
          <Tag color="green">Completed</Tag>
          <Tag color="blue">Running</Tag>
          <Tag color="default">Idle</Tag>
          <Tag color="red">Error</Tag>
        </Space>
      </div>

      <Drawer
        title={selectedAgent ? `Agent: ${selectedAgent.name}` : 'Agent Details'}
        placement="right"
        width={400}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedAgent && (
          <div className="agent-details">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <h4>Status</h4>
                <Tag color={getStatusColor(selectedAgent.status)}>
                  {selectedAgent.status.toUpperCase()}
                </Tag>
              </div>

              {selectedAgent.model && (
                <div>
                  <h4>Model</h4>
                  <Tag color={getModelBadgeColor(selectedAgent.model)}>
                    {selectedAgent.model}
                  </Tag>
                </div>
              )}

              {selectedAgent.confidence !== undefined && (
                <div>
                  <h4>Confidence</h4>
                  <Progress
                    percent={selectedAgent.confidence * 100}
                    strokeColor={{
                      '0%': '#108ee9',
                      '100%': '#87d068',
                    }}
                  />
                </div>
              )}

              {selectedAgent.executionTime !== undefined && (
                <div>
                  <h4>Execution Time</h4>
                  <Statistic
                    value={selectedAgent.executionTime}
                    suffix="seconds"
                    prefix={<ClockCircleOutlined />}
                  />
                </div>
              )}

              {selectedAgent.tokens !== undefined && (
                <div>
                  <h4>Tokens Used</h4>
                  <Statistic
                    value={selectedAgent.tokens}
                    prefix={<ThunderboltOutlined />}
                  />
                </div>
              )}

              {selectedAgent.toolCalls && selectedAgent.toolCalls.length > 0 && (
                <div>
                  <h4>Tool Calls</h4>
                  <Timeline>
                    {selectedAgent.toolCalls.map((call, idx) => (
                      <Timeline.Item
                        key={idx}
                        color={call.status === 'success' ? 'green' : call.status === 'calling' ? 'blue' : 'gray'}
                        dot={<ApiOutlined />}
                      >
                        <div>
                          <strong>{call.tool}</strong>
                          {call.api && ` - ${call.api}`}
                        </div>
                        {call.latency && (
                          <span style={{ fontSize: 12, color: 'rgba(0, 0, 0, 0.45)' }}>
                            {call.latency}s
                          </span>
                        )}
                        {call.results && (
                          <Tag color="blue" style={{ marginLeft: 8 }}>
                            {call.results} results
                          </Tag>
                        )}
                      </Timeline.Item>
                    ))}
                  </Timeline>
                </div>
              )}

              {selectedAgent.dependencies && selectedAgent.dependencies.length > 0 && (
                <div>
                  <h4>Dependencies</h4>
                  <Space wrap>
                    {selectedAgent.dependencies.map(dep => (
                      <Tag key={dep}>{dep}</Tag>
                    ))}
                  </Space>
                </div>
              )}

              {selectedAgent.parallelGroup !== undefined && (
                <div>
                  <h4>Parallel Group</h4>
                  <Tag color="purple">Group {selectedAgent.parallelGroup}</Tag>
                </div>
              )}
            </Space>
          </div>
        )}
      </Drawer>
    </Card>
  );
};

export default AgentGraph;