import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Card,
  Button,
  Spin,
  Alert,
  Tabs,
  Row,
  Col,
  Statistic,
  Progress,
  Tag,
  Typography,
  Timeline,
  List,
  Space,
  Badge,
  Tooltip
} from 'antd';
import {
  RocketOutlined,
  ThunderboltOutlined,
  LineChartOutlined,
  HeartOutlined,
  SafetyOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  LoadingOutlined,
  LinkOutlined,
  DashboardOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { theme } from '../styles/theme';
import { useResponsive } from '../hooks/useResponsive';
import ProfessionalTradingChart from './ProfessionalTradingChart';
import CitationPanel, { Citation as CitationData } from './CitationPanel';
import ExecutiveSummary from './ExecutiveSummary';
import '../styles/deep-analysis.css';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

// Semantic color helper for metrics
const getMetricColor = (value: any, type: string): string => {
  // N/A, null, or undefined values always gray
  if (value === 'N/A' || value === null || value === undefined || value === '--') {
    return theme.colors.text.muted; // Gray for missing data
  }

  switch(type) {
    case 'sentiment':
      const sentimentUpper = typeof value === 'string' ? value.toUpperCase() : value;
      if (sentimentUpper === 'BULLISH' || sentimentUpper === 'POSITIVE') return theme.colors.success;
      if (sentimentUpper === 'BEARISH' || sentimentUpper === 'NEGATIVE') return theme.colors.error;
      return theme.colors.text.secondary; // Neutral = gray, not cyan

    case 'recommendation':
      const recUpper = typeof value === 'string' ? value.toUpperCase() : value;
      if (recUpper === 'BUY' || recUpper === 'STRONG BUY') return theme.colors.success;
      if (recUpper === 'SELL' || recUpper === 'STRONG SELL') return theme.colors.error;
      return theme.colors.warning; // HOLD = warning color

    case 'risk':
      const riskUpper = typeof value === 'string' ? value.toUpperCase() : value;
      if (riskUpper === 'LOW') return theme.colors.success;
      if (riskUpper === 'HIGH') return theme.colors.error;
      return theme.colors.warning;

    case 'positive':
      return theme.colors.success;

    case 'negative':
      return theme.colors.error;

    default:
      return theme.colors.text.primary;
  }
};

// Helper to extract numeric value from metadata dict or raw number
const getNumericValue = (val: any): number | null => {
  if (val === null || val === undefined) return null;
  if (typeof val === 'number') return val;
  if (typeof val === 'object') {
    // First try to get val.value if it exists and is not null
    if (val.value !== undefined && val.value !== null) return val.value;
    // Fallback: try to parse formatted string if available
    if (val.formatted && typeof val.formatted === 'string' && val.formatted !== 'N/A') {
      const parsed = parseFloat(val.formatted.replace(/[$,]/g, ''));
      if (!isNaN(parsed)) return parsed;
    }
  }
  return null;
};

// Utility function to extract citations from analysis result
const extractCitations = (result: ResearchResult | null): CitationData[] => {
  if (!result?.analysis) return [];

  const citations: CitationData[] = [];
  const agents = ['sentiment', 'fundamental', 'technical', 'risk', 'peer'];

  agents.forEach((agentId) => {
    const agentData = (result.analysis as any)[agentId];
    if (!agentData) return;

    // Extract from social_data.sources (Sentiment agent)
    if (agentData.social_data?.sources) {
      agentData.social_data.sources.forEach((source: any, index: number) => {
        if (source.url) {
          citations.push({
            id: `${agentId}-${index}`,
            title: source.title || 'Source',
            url: source.url,
            content: source.content || '',
            agent_id: agentId,
            agent_name: agentId.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
            timestamp: new Date().toISOString(),
            relevance_score: source.score || 0.8,
            published_date: source.published_date,
            source: source.source
          });
        }
      });
    }

    // Extract from citations array (if exists)
    if (Array.isArray(agentData.citations)) {
      agentData.citations.forEach((citation: any, index: number) => {
        if (citation.url) {
          citations.push({
            id: `${agentId}-citation-${index}`,
            title: citation.title || citation.citation || 'Citation',
            url: citation.url,
            content: citation.content || citation.citation || '',
            agent_id: agentId,
            agent_name: agentId.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
            timestamp: new Date().toISOString(),
            relevance_score: citation.relevance_score || 0.7,
            source: citation.source
          });
        }
      });
    }
  });

  return citations;
};

// Move agent messages outside component to prevent recreation
const AGENT_MESSAGES: Record<string, string> = {
  'query_parser': '📊 Parsing query and extracting symbols...',
  'market_data': '📈 Fetching real-time market data...',
  'fundamental': '💰 Analyzing fundamental metrics...',
  'sentiment': '🎯 Analyzing market sentiment...',
  'technical': '📉 Running technical analysis...',
  'risk': '⚠️ Assessing risk factors...',
  'peer': '🔍 Comparing with industry peers...',
  'synthesis': '🧠 Synthesizing insights...',
  'critique': '✅ Validating analysis quality...'
};

interface DeepAnalysisProps {
  symbol: string;
  onClose?: () => void;
}

interface ResearchResult {
  // Core fields
  analysis_id: string;
  request_id?: string; // Optional - not always present in API response
  query: string;
  symbols: string[];
  status: string;
  execution_time?: number;
  source?: string;

  // EnhancedStockWorkflow response structure
  executive_summary: string;
  investment_thesis: string;
  confidence_score: number;

  // Analysis data (root level)
  fundamental_analysis: {
    fundamental_data: Record<string, any>;
    key_insights: string[];
    valuation_summary: string;
    risks: string[];
  };

  technical_analysis: {
    technical_data: Record<string, any>;
    trend_analysis: string;
    signals: {
      rsi: any;
      macd: any;
      support_levels: number[];
      resistance_levels: number[];
    };
  };

  risk_analysis: {
    risk_data?: Record<string, any>;
    risk_level: string;
    risk_score: number;
    sharpe_ratio?: number;
    sortino_ratio?: number;
    max_drawdown?: number;
    volatility?: number;
    var_95?: number;
    var_95_pct?: number;
    cvar_95?: number;
    cvar_95_pct?: number;
    beta?: number;
    monte_carlo_projections?: {
      current_price: number;
      expected_value: number;
      pessimistic_5pct: number;
      optimistic_95pct: number;
    };
    risk_insights?: string[];
    mitigation_strategies?: string[];
    downside_analysis?: string[];
    portfolio_impact?: string[];
  };

  sentiment_analysis?: any;
  market_data?: any;
  peer_comparison?: any;

  // Nested analysis object (for backward compatibility)
  analysis?: {
    summary: string;
    fundamental: any;
    technical: any;
    risk: any;
    sentiment: any;
    peer_comparison: any;
    insider_activity: any;
    predictive: any;
    catalysts: any;
    critique: any;
    news: any;
    macro: any;
    chart_analytics?: any;
    market_data?: any;
  };

  agent_results?: any;

  // Recommendations
  recommendations: {
    action: string;
    confidence: number;
    target_price: number;
    stop_loss: number;
    entry_price: number;
    time_horizon: string;
    risk_reward_ratio: number;
    key_catalysts: string[];
    risks: string[];
    strategy: string[];
  };

  // Quality & Synthesis (THE FIX!)
  synthesis?: {
    summary: string;
    action: string;
    confidence: number;
    target_price: number;
    stop_loss: number;
    entry_price: number;
    data_quality?: {
      overall_score: number;
      overall_grade: string;
      agents_validated: number;
      issues: string[];
      validation_details: any[];
    };
  };

  quality_assurance?: {
    critique_passed: boolean;
    critical_issues: string[];
    revision_priority: string;
  };

  // Additional fields
  consensus_breakdown?: any;
  agent_agreement?: string;
  enrichment_status?: any;
  valuation_analysis?: any;
  macro_analysis?: any;
  insider_analysis?: any;
  catalyst_calendar?: any;
  chart_analytics?: any;
  completed_at?: string;

  // Legacy fields for backward compatibility
}

interface AgentProgress {
  agent: string;
  status: string;
  progress: number;
  message: string;
  timestamp: string;
}


const DeepAnalysis: React.FC<DeepAnalysisProps> = ({ symbol, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [agentProgress, setAgentProgress] = useState<AgentProgress[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [citations, setCitations] = useState<CitationData[]>([]);
  const [currentStage, setCurrentStage] = useState<string>('');
  const wsRef = useRef<WebSocket | null>(null);
  const { isMobile, isTablet } = useResponsive();

  // Memoize style objects to prevent re-creation
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const titleStyle = useMemo(() => ({
    color: theme.colors.text.primary,
    marginTop: 16,
    marginBottom: 8
  }), []);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const textSecondaryStyle = useMemo(() => ({
    color: theme.colors.text.secondary,
    fontSize: 14
  }), []);

  // Extract citations from result
  const allCitations = useMemo(() => extractCitations(result), [result]);

  // Update citations state when result changes
  useEffect(() => {
    if (result) {
      setCitations(allCitations);
    }
  }, [result, allCitations]);

  const startDeepAnalysis = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(0);
    setAgentProgress([]);
    setCitations([]);
    setCurrentStage('Initializing...');

    try {
      // Step 1: Call REST API to start analysis
      const apiResponse = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `Analyze ${symbol} stock with detailed research`,
          symbols: [symbol],
          priority: 'high',
          user_id: 'default',
          include_fundamentals: true,
          include_technical: true,
          include_sentiment: true,
          max_revisions: 1
        })
      });

      if (!apiResponse.ok) {
        throw new Error('Failed to start analysis');
      }

      const { analysis_id } = await apiResponse.json();
      console.log('Analysis started:', analysis_id);

      // Step 2: Poll for status with exponential backoff
      let pollInterval = 1000; // Start with 1 second
      const maxPollInterval = 5000; // Max 5 seconds between polls
      let attempts = 0;
      const maxAttempts = 180; // 3 minutes max (with increasing intervals)

      const pollStatus = async (): Promise<void> => {
        if (attempts >= maxAttempts) {
          setError('Analysis timeout - please try again');
          setLoading(false);
          return;
        }

        attempts++;

        try {
          // Check status endpoint
          const statusResponse = await fetch(
            `http://localhost:8000/api/v1/analyze/${analysis_id}/status`
          );

          if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            console.log('📊 Status update:', statusData);
            console.log('🤖 Agent Executions:', statusData.agent_executions);
            console.log('⚡ Active Agents:', statusData.active_agents || statusData.active_agent);

            // Update progress based on status
            // ✅ FIX: Progress is a nested object with percentage property
            const progressPercent = statusData.progress?.percentage || statusData.progress || 0;
            const progressMessage = statusData.progress?.message || 'Processing...';

            // Always update progress percentage
            setProgress(progressPercent);

            // Extract active and completed agents from progress object
            const activeAgentsFromProgress = statusData.progress?.active_agents || [];
            const completedAgentsFromProgress = statusData.progress?.completed_agents || [];
            const agentExecutions = statusData.agent_executions || [];
            const activeAgentsLegacy = statusData.active_agents || (statusData.active_agent ? [statusData.active_agent] : []);

            // Combine active agents from both sources
            const allActiveAgents = Array.from(new Set([...activeAgentsFromProgress, ...activeAgentsLegacy]));

            // Build comprehensive agent progress list
            const allAgents: AgentProgress[] = [];

            // Add completed agents
            completedAgentsFromProgress.forEach((agentName: string) => {
              allAgents.push({
                agent: agentName,
                status: 'completed',
                progress: 100,
                message: AGENT_MESSAGES[agentName] || `${agentName} completed`,
                timestamp: new Date().toISOString()
              });
            });

            // Add active agents
            allActiveAgents.forEach((agentName: string) => {
              if (!completedAgentsFromProgress.includes(agentName)) {
                allAgents.push({
                  agent: agentName,
                  status: 'running',
                  progress: progressPercent,
                  message: AGENT_MESSAGES[agentName] || `Processing ${agentName}...`,
                  timestamp: new Date().toISOString()
                });
              }
            });

            // Process agent executions to add any additional agents
            if (agentExecutions.length > 0) {
              agentExecutions.forEach((exec: any) => {
                const agentName = exec.agent_name || exec.agent;
                if (!allAgents.find(a => a.agent === agentName)) {
                  allAgents.push({
                    agent: agentName,
                    status: exec.status,
                    progress: exec.progress || progressPercent,
                    message: exec.message || AGENT_MESSAGES[agentName] || `Processing ${agentName}...`,
                    timestamp: exec.timestamp || new Date().toISOString()
                  });
                }
              });
            }

            console.log('✅ Setting agent progress:', allAgents);
            setAgentProgress(allAgents);

            // Set current stage from active agents or progress message
            if (allActiveAgents.length > 0) {
              const message = AGENT_MESSAGES[allActiveAgents[0]] || `Processing ${allActiveAgents[0]}...`;
              setCurrentStage(message);
            } else {
              setCurrentStage(progressMessage);
            }

            // Check if completed
            if (statusData.status === 'completed') {
              console.log('Analysis completed! Fetching results...');
              setProgress(100);
              setCurrentStage('Analysis Complete - Fetching results...');

              // Fetch complete results
              const resultResponse = await fetch(
                `http://localhost:8000/api/v1/analyze/${analysis_id}/result`
              );

              if (resultResponse.ok) {
                const resultData = await resultResponse.json();
                console.log('Full result data:', resultData);

                // Map EnhancedStockWorkflow response to ResearchResult interface
                const formattedResult: ResearchResult = {
                  analysis_id: resultData.analysis_id || analysis_id,
                  request_id: analysis_id,
                  query: resultData.query || `Analyze ${symbol}`,
                  symbols: resultData.symbols || [symbol],
                  status: resultData.status || 'completed',
                  source: 'enhanced_workflow',

                  executive_summary: resultData.executive_summary || '',
                  investment_thesis: resultData.investment_thesis || '',
                  confidence_score: resultData.confidence_score || 0,

                  fundamental_analysis: resultData.fundamental_analysis || {
                    fundamental_data: {},
                    key_insights: [],
                    valuation_summary: '',
                    risks: []
                  },

                  technical_analysis: resultData.technical_analysis || {
                    technical_data: {},
                    trend_analysis: '',
                    signals: {
                      rsi: {},
                      macd: {},
                      support_levels: [],
                      resistance_levels: []
                    }
                  },

                  risk_analysis: resultData.risk_analysis || {
                    risk_level: 'MEDIUM',
                    risk_score: 50
                  },

                  sentiment_analysis: resultData.analysis?.sentiment,
                  market_data: resultData.market_data,
                  peer_comparison: resultData.analysis?.peer_comparison,
                  analysis: resultData.analysis,

                  recommendations: resultData.recommendations || {
                    action: 'HOLD',
                    confidence: resultData.synthesis?.confidence || resultData.confidence_score || 0,  // ✅ FIX: Get confidence from synthesis or confidence_score
                    target_price: resultData.synthesis?.target_price || resultData.fundamental?.analyst_target_price || 0,
                    stop_loss: resultData.synthesis?.stop_loss || 0,
                    entry_price: resultData.synthesis?.entry_price || resultData.market_data?.price || 0,
                    time_horizon: 'medium_term',
                    risk_reward_ratio: 1.0,
                    key_catalysts: [],
                    risks: [],
                    strategy: []
                  },

                  // THE CRITICAL FIX - synthesis with data_quality!
                  synthesis: resultData.synthesis,

                  quality_assurance: resultData.quality_assurance,
                  consensus_breakdown: resultData.consensus_breakdown,
                  agent_agreement: resultData.agent_agreement,
                  enrichment_status: resultData.enrichment_status,
                  valuation_analysis: resultData.valuation_analysis,
                  macro_analysis: resultData.macro_analysis,
                  insider_analysis: resultData.insider_analysis,
                  catalyst_calendar: resultData.catalyst_calendar,
                  chart_analytics: resultData.chart_analytics || resultData.analysis?.chart_analytics,
                  completed_at: resultData.completed_at,
                  execution_time: resultData.execution_time  // ✅ FIX: Map execution_time from API
                };

                console.log('Formatted result with synthesis:', formattedResult.synthesis);
                setResult(formattedResult);
                setLoading(false);
              } else {
                setError('Failed to fetch analysis results');
                setLoading(false);
              }
              return; // Stop polling
            } else if (statusData.status === 'failed') {
              setError(statusData.error || 'Analysis failed');
              setLoading(false);
              return; // Stop polling
            } else {
              // Continue polling with exponential backoff
              pollInterval = Math.min(pollInterval * 1.5, maxPollInterval);
              setTimeout(pollStatus, pollInterval);
            }
          } else {
            // Retry with backoff
            pollInterval = Math.min(pollInterval * 1.5, maxPollInterval);
            setTimeout(pollStatus, pollInterval);
          }
        } catch (err) {
          console.error('Polling error:', err);
          // Retry with backoff
          pollInterval = Math.min(pollInterval * 1.5, maxPollInterval);
          setTimeout(pollStatus, pollInterval);
        }
      };

      // Start polling
      setTimeout(pollStatus, pollInterval);

    } catch (err: any) {
      console.error('Error starting analysis:', err);
      setError(err.message || 'Failed to start analysis');
      setLoading(false);
    }
  };

  // Cleanup WebSocket on unmount
  useEffect(() => {
    const ws = wsRef.current;
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const renderOverview = () => {
    if (!result?.analysis) return <Text style={{ color: theme.colors.text.secondary }}>No analysis data available</Text>;

    const { fundamental, technical, risk } = result.analysis;
    const synthesis: any = result.synthesis; // synthesis is at top level, not in analysis

    // Extract risk metrics from nested structure
    let riskMetrics: any = {};
    if (risk?.risk_data) {
      const symbols = Object.keys(risk.risk_data);
      if (symbols.length > 0) {
        const firstSymbol = symbols[0];
        riskMetrics = risk.risk_data[firstSymbol]?.risk_metrics || {};
      }
    } else if (risk?.risk_metrics) {
      // Direct access if risk_metrics is at top level
      riskMetrics = risk.risk_metrics;
    }

    return (
      <div>
        {/* Final Recommendation Banner */}
        {synthesis && (
          <Alert
            type={synthesis.action === 'BUY' ? 'success' : synthesis.action === 'SELL' ? 'error' : 'warning'}
            message={
              <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
                {synthesis.action} | Confidence: {(synthesis.confidence * 100).toFixed(0)}%
              </span>
            }
            description={
              <div>
                <Text style={{ color: theme.colors.text.primary }}>
                  Entry: ${getNumericValue(synthesis.entry_price)?.toFixed(2) || 'N/A'} |
                  Target: ${getNumericValue(synthesis.target_price)?.toFixed(2) || 'N/A'} |
                  Stop Loss: ${getNumericValue(synthesis.stop_loss)?.toFixed(2) || 'N/A'}
                </Text>
                <br />
                {/* @ts-ignore - risk_reward_ratio and time_horizon exist in API response */}
                <Text style={{ color: theme.colors.text.secondary, fontSize: '12px' }}>
                  Risk/Reward: {getNumericValue(synthesis.risk_reward_ratio)?.toFixed(2) || 'N/A'} |
                  Time Horizon: {synthesis.time_horizon}
                </Text>
              </div>
            }
            style={{ marginBottom: 24 }}
          />
        )}

        {/* Key Metrics Grid - 4x3 Layout */}
        <Row gutter={[16, 16]}>
          {/* Row 1: Valuation */}
          <Col xs={12} sm={8} md={6}>
            <Card className="metric-card-core" style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>P/E Ratio</Text>}
                value={fundamental?.pe_ratio?.toFixed(2) || fundamental?.metrics?.pe_ratio?.toFixed(2) || 'N/A'}
                valueStyle={{ color: theme.colors.primary }}
                suffix={
                  (!fundamental?.pe_ratio && !fundamental?.metrics?.pe_ratio) ? (
                    <Tooltip title="P/E Ratio data temporarily unavailable">
                      <InfoCircleOutlined style={{ fontSize: 14, color: theme.colors.text.muted, marginLeft: 4 }} />
                    </Tooltip>
                  ) : undefined
                }
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card className="metric-card-core" style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>EPS</Text>}
                value={fundamental?.eps?.toFixed(2) || fundamental?.metrics?.eps?.toFixed(2) || 'N/A'}
                prefix="$"
                valueStyle={{ color: getMetricColor(fundamental?.eps || fundamental?.metrics?.eps, 'positive') }}
                suffix={
                  (!fundamental?.eps && !fundamental?.metrics?.eps) ? (
                    <Tooltip title="EPS data temporarily unavailable">
                      <InfoCircleOutlined style={{ fontSize: 14, color: theme.colors.text.muted, marginLeft: 4 }} />
                    </Tooltip>
                  ) : undefined
                }
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Beta</Text>}
                value={riskMetrics.beta?.toFixed(2) || 'N/A'}
                valueStyle={{ color: riskMetrics.beta > 1 ? theme.colors.error : theme.colors.success }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Data Quality</Text>}
                value={
                  synthesis?.data_quality?.overall_grade
                    ? `${synthesis.data_quality.overall_grade} ${synthesis.data_quality.overall_score?.toFixed(1)}`
                    : result?.market_data?.data_quality || 'N/A'
                }
                suffix="/100"
                valueStyle={{ color: theme.colors.warning }}
              />
            </Card>
          </Col>

          {/* Row 2: Performance */}
          <Col xs={12} sm={8} md={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Sharpe Ratio</Text>}
                value={riskMetrics.sharpe_ratio?.toFixed(2) || 'N/A'}
                valueStyle={{ color: riskMetrics.sharpe_ratio > 1 ? theme.colors.success : theme.colors.warning }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>VaR (95%)</Text>}
                value={riskMetrics.var?.var ? `$${riskMetrics.var.var.toFixed(2)}` : 'N/A'}
                valueStyle={{ color: theme.colors.error }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>RSI</Text>}
                value={technical?.indicators?.rsi?.value?.toFixed(2) || 'N/A'}
                valueStyle={{
                  color: technical?.indicators?.rsi?.signal === 'overbought' ? theme.colors.error :
                         technical?.indicators?.rsi?.signal === 'oversold' ? theme.colors.success :
                         theme.colors.warning
                }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Sentiment</Text>}
                value={result?.sentiment_analysis?.sentiment || 'NEUTRAL'}
                valueStyle={{ color: getMetricColor(result?.sentiment_analysis?.sentiment, 'sentiment') }}
              />
            </Card>
          </Col>

          {/* Row 3: Financial Health */}
          <Col xs={12} sm={8} md={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Revenue</Text>}
                value={(fundamental?.revenue || fundamental?.metrics?.revenue) ? `$${((fundamental?.revenue || fundamental?.metrics?.revenue) / 1000000000).toFixed(2)}B` : 'N/A'}
                valueStyle={{ color: getMetricColor(fundamental?.revenue || fundamental?.metrics?.revenue, 'positive') }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>FCF</Text>}
                value={(fundamental?.fcf || fundamental?.metrics?.fcf || fundamental?.metrics?.free_cash_flow) ? `$${((fundamental?.fcf || fundamental?.metrics?.fcf || fundamental?.metrics?.free_cash_flow) / 1000000000).toFixed(2)}B` : 'N/A'}
                valueStyle={{ color: getMetricColor(fundamental?.fcf || fundamental?.metrics?.fcf || fundamental?.metrics?.free_cash_flow, 'positive') }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card className="metric-card-core" style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>ROE</Text>}
                value={fundamental?.roe?.toFixed(2) || fundamental?.metrics?.roe?.toFixed(2) || 'N/A'}
                suffix={
                  (!fundamental?.roe && !fundamental?.metrics?.roe) ? (
                    <Tooltip title="ROE data temporarily unavailable">
                      <InfoCircleOutlined style={{ fontSize: 14, color: theme.colors.text.muted, marginLeft: 4 }} />
                    </Tooltip>
                  ) : "%"
                }
                valueStyle={{ color: getMetricColor(fundamental?.roe || fundamental?.metrics?.roe, 'positive') }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              {/* @ts-ignore - risk_reward_ratio exists in API response */}
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Risk/Reward</Text>}
                value={getNumericValue(synthesis?.risk_reward_ratio)?.toFixed(2) || 'N/A'}
                valueStyle={{ color: (getNumericValue(synthesis?.risk_reward_ratio) || 0) > 1.5 ? theme.colors.success : theme.colors.warning }}
              />
            </Card>
          </Col>
        </Row>

        {/* Summary Section */}
        {/* @ts-ignore - rationale and key_catalysts exist in API response */}
        {synthesis?.rationale && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 24 }}>
            <Title level={4} style={{ color: theme.colors.text.primary }}>Analysis Summary</Title>
            <Paragraph style={{ color: theme.colors.text.primary }}>
              {synthesis.rationale}
            </Paragraph>
            {synthesis.key_catalysts && synthesis.key_catalysts.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text style={{ color: theme.colors.text.secondary, fontWeight: 'bold' }}>Key Catalysts:</Text>
                <ul>
                  {synthesis.key_catalysts.map((catalyst: string, index: number) => (
                    <li key={index}>
                      <Text style={{ color: theme.colors.text.primary }}>{catalyst}</Text>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>
        )}
      </div>
    );
  };

  const renderMarketData = () => {
    if (!result?.market_data) return null;

    const data = result.market_data;
    return (
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={8} md={6}>
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
            <Statistic
              title={<Text style={{ color: theme.colors.text.secondary }}>Price</Text>}
              value={data.price || 'N/A'}
              prefix="$"
              valueStyle={{ color: theme.colors.success }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
            <Statistic
              title={<Text style={{ color: theme.colors.text.secondary }}>Change</Text>}
              value={data.change_percent || 0}
              suffix="%"
              valueStyle={{ color: data.change_percent >= 0 ? theme.colors.success : theme.colors.danger }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
            <Statistic
              title={<Text style={{ color: theme.colors.text.secondary }}>Volume</Text>}
              value={data.volume ? (data.volume / 1000000).toFixed(2) : 'N/A'}
              suffix="M"
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6}>
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
            <Statistic
              title={<Text style={{ color: theme.colors.text.secondary }}>Market Cap</Text>}
              value={data.market_cap ? (data.market_cap / 1000000000).toFixed(2) : 'N/A'}
              suffix="B"
            />
          </Card>
        </Col>
      </Row>
    );
  };

  const renderFundamentalAnalysis = () => {
    if (!result?.analysis?.fundamental) return <Text style={{ color: theme.colors.text.secondary }}>No fundamental data available</Text>;

    const fundamental = result.analysis.fundamental;
    const metrics = fundamental.metrics || {};

    return (
      <div>
        {/* Summary Section */}
        {fundamental.insights?.investment_thesis && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 24 }}>
            <Title level={4} style={{ color: theme.colors.text.primary }}>Investment Thesis</Title>
            <Paragraph style={{ color: theme.colors.text.primary }}>
              {fundamental.insights.investment_thesis}
            </Paragraph>
          </Card>
        )}

        {/* 3-Column Layout */}
        <Row gutter={[24, 24]}>
          {/* Column 1: Valuation Metrics */}
          <Col xs={24} md={8}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>Valuation Metrics</Title>
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>P/E Ratio</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.primary, fontSize: 20 }}>
                      {fundamental.pe_ratio?.toFixed(2) || metrics.pe_ratio?.toFixed(2) || 'N/A'}
                    </Text>
                  </div>
                </div>
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>PEG Ratio</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.primary, fontSize: 20 }}>
                      {fundamental.peg_ratio?.toFixed(2) || metrics.peg_ratio?.toFixed(2) || 'N/A'}
                    </Text>
                  </div>
                </div>
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>Price/Book</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.primary, fontSize: 20 }}>
                      {metrics.price_to_book?.toFixed(2) || 'N/A'}
                    </Text>
                  </div>
                </div>
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>Graham Number</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.success, fontSize: 20 }}>
                      ${metrics.graham_number?.fair_value?.toFixed(2) || 'N/A'}
                    </Text>
                  </div>
                </div>
                {metrics.dcf?.intrinsic_value_per_share && (
                  <div>
                    <Text style={{ color: theme.colors.text.secondary }}>DCF Intrinsic Value (Per Share)</Text>
                    <div>
                      <Text strong style={{ color: theme.colors.success, fontSize: 20 }}>
                        ${metrics.dcf.intrinsic_value_per_share.toFixed(2)}
                      </Text>
                    </div>
                  </div>
                )}
              </Space>
            </Card>
          </Col>

          {/* Column 2: Profitability */}
          <Col xs={24} md={8}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>Profitability</Title>
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>ROE</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.success, fontSize: 20 }}>
                      {fundamental.roe?.toFixed(2) || metrics.roe?.toFixed(2) || 'N/A'}%
                    </Text>
                  </div>
                </div>
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>ROA</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.success, fontSize: 20 }}>
                      {fundamental.roa?.toFixed(2) || metrics.roa?.toFixed(2) || 'N/A'}%
                    </Text>
                  </div>
                </div>
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>Net Margin</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.success, fontSize: 20 }}>
                      {fundamental.profit_margin?.toFixed(2) || metrics.net_margin?.toFixed(2) || 'N/A'}%
                    </Text>
                  </div>
                </div>
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>Gross Margin</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.success, fontSize: 20 }}>
                      {metrics.gross_margin?.toFixed(2) || 'N/A'}%
                    </Text>
                  </div>
                </div>
              </Space>
            </Card>
          </Col>

          {/* Column 3: Financial Health */}
          <Col xs={24} md={8}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>Financial Health</Title>
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>Debt/Equity</Text>
                  <div>
                    <Text strong style={{
                      color: (fundamental.debt_to_equity || metrics.debt_to_equity) > 1 ? theme.colors.error : theme.colors.success,
                      fontSize: 20
                    }}>
                      {fundamental.debt_to_equity?.toFixed(2) || metrics.debt_to_equity?.toFixed(2) || 'N/A'}
                    </Text>
                  </div>
                </div>
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>Current Ratio</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.primary, fontSize: 20 }}>
                      {metrics.current_ratio?.toFixed(2) || 'N/A'}
                    </Text>
                  </div>
                </div>
                {metrics.free_cash_flow && (
                  <div>
                    <Text style={{ color: theme.colors.text.secondary }}>Free Cash Flow</Text>
                    <div>
                      <Text strong style={{ color: theme.colors.success, fontSize: 20 }}>
                        ${(metrics.free_cash_flow / 1000000000).toFixed(2)}B
                      </Text>
                    </div>
                  </div>
                )}
                {metrics.revenue && (
                  <div>
                    <Text style={{ color: theme.colors.text.secondary }}>Revenue</Text>
                    <div>
                      <Text strong style={{ color: theme.colors.success, fontSize: 20 }}>
                        ${(metrics.revenue / 1000000000).toFixed(2)}B
                      </Text>
                    </div>
                  </div>
                )}
              </Space>
            </Card>
          </Col>
        </Row>

        {/* DCF Waterfall Chart */}
        {metrics.dcf && metrics.dcf.intrinsic_value && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 24 }}>
            <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>
              💰 DCF Valuation Waterfall
            </Title>

            <Row gutter={[24, 16]}>
              <Col xs={24} lg={16}>
                <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', height: 200 }}>
                  {/* PV Cash Flows */}
                  <div style={{ textAlign: 'center', flex: 1 }}>
                    <div style={{
                      height: 150,
                      background: theme.colors.primary,
                      borderRadius: 8,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexDirection: 'column',
                      color: 'white',
                      margin: '0 8px'
                    }}>
                      <Text strong style={{ color: 'white', fontSize: 20 }}>
                        ${(metrics.dcf.pv_cash_flows / 1000000000).toFixed(1)}B
                      </Text>
                      <Text style={{ color: 'white', fontSize: 12, marginTop: 4 }}>
                        ({((metrics.dcf.pv_cash_flows / metrics.dcf.intrinsic_value) * 100).toFixed(0)}%)
                      </Text>
                    </div>
                    <Text style={{ color: theme.colors.text.secondary, fontSize: 12, marginTop: 8, display: 'block' }}>
                      PV Cash Flows
                    </Text>
                  </div>

                  {/* Plus Sign */}
                  <div style={{ fontSize: 24, color: theme.colors.text.primary, padding: '0 16px', marginBottom: 40 }}>+</div>

                  {/* Terminal Value */}
                  <div style={{ textAlign: 'center', flex: 1 }}>
                    <div style={{
                      height: 180,
                      background: theme.colors.success,
                      borderRadius: 8,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexDirection: 'column',
                      color: 'white',
                      margin: '0 8px'
                    }}>
                      <Text strong style={{ color: 'white', fontSize: 20 }}>
                        ${(metrics.dcf.pv_terminal_value / 1000000000).toFixed(1)}B
                      </Text>
                      <Text style={{ color: 'white', fontSize: 12, marginTop: 4 }}>
                        ({metrics.dcf.terminal_value_pct?.toFixed(1) || ((metrics.dcf.pv_terminal_value / metrics.dcf.intrinsic_value) * 100).toFixed(1)}%)
                      </Text>
                    </div>
                    <Text style={{ color: theme.colors.text.secondary, fontSize: 12, marginTop: 8, display: 'block' }}>
                      Terminal Value
                    </Text>
                  </div>

                  {/* Equals Sign */}
                  <div style={{ fontSize: 24, color: theme.colors.text.primary, padding: '0 16px', marginBottom: 40 }}>=</div>

                  {/* Intrinsic Value */}
                  <div style={{ textAlign: 'center', flex: 1 }}>
                    <div style={{
                      height: 190,
                      background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.success})`,
                      borderRadius: 8,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexDirection: 'column',
                      color: 'white',
                      margin: '0 8px',
                      border: `2px solid ${theme.colors.warning}`
                    }}>
                      <Text strong style={{ color: 'white', fontSize: 22 }}>
                        ${metrics.dcf.intrinsic_value_per_share?.toFixed(2) || 'N/A'}
                      </Text>
                    </div>
                    <Text style={{ color: theme.colors.text.primary, fontSize: 12, marginTop: 8, display: 'block', fontWeight: 'bold' }}>
                      Intrinsic Value (Per Share)
                    </Text>
                  </div>
                </div>

                {metrics.dcf.terminal_value_pct > 65 && (
                  <Alert
                    type="warning"
                    message={`⚠️ WARNING: ${metrics.dcf.terminal_value_pct.toFixed(1)}% of value from terminal assumptions`}
                    description="High terminal value percentage indicates significant valuation uncertainty. Exercise caution."
                    showIcon
                    style={{ marginTop: 16 }}
                  />
                )}
              </Col>

              <Col xs={24} lg={8}>
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <Statistic
                    title="Intrinsic Value per Share"
                    value={metrics.dcf.intrinsic_value_per_share?.toFixed(2) || (metrics.dcf.intrinsic_value / 14850000000).toFixed(2)}
                    prefix="$"
                    valueStyle={{ color: theme.colors.success, fontSize: 24 }}
                  />

                  {result?.analysis?.market_data?.current_price && (
                    <>
                      <Statistic
                        title="Current Price"
                        value={result.analysis.market_data.current_price.toFixed(2)}
                        prefix="$"
                        valueStyle={{ color: theme.colors.primary, fontSize: 24 }}
                      />

                      <div style={{
                        padding: 12,
                        background: result.analysis.market_data.current_price > (metrics.dcf.intrinsic_value_per_share || 75) ?
                          theme.colors.background.primary : theme.colors.background.elevated,
                        borderRadius: 8,
                        borderLeft: `3px solid ${
                          result.analysis.market_data.current_price > (metrics.dcf.intrinsic_value_per_share || 75) ?
                          theme.colors.error : theme.colors.success
                        }`
                      }}>
                        <Text style={{ color: theme.colors.text.primary }}>
                          {result.analysis.market_data.current_price > (metrics.dcf.intrinsic_value_per_share || 75) ?
                            `🔴 Overvalued by ${(((result.analysis.market_data.current_price / (metrics.dcf.intrinsic_value_per_share || 75)) - 1) * 100).toFixed(0)}%` :
                            `🟢 Undervalued by ${((1 - (result.analysis.market_data.current_price / (metrics.dcf.intrinsic_value_per_share || 75))) * 100).toFixed(0)}%`
                          }
                        </Text>
                      </div>
                    </>
                  )}
                </Space>
              </Col>
            </Row>

            {/* 5-Year FCF Projection */}
            {metrics.dcf.projected_fcf && metrics.dcf.projected_fcf.length > 0 && (
              <div style={{ marginTop: 24 }}>
                <Title level={5} style={{ color: theme.colors.text.primary, marginBottom: 12 }}>
                  📈 5-Year FCF Projection
                </Title>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, height: 100 }}>
                  {metrics.dcf.projected_fcf.map((fcf: number, index: number) => (
                    <div key={index} style={{ flex: 1, textAlign: 'center' }}>
                      <div style={{
                        height: `${(fcf / Math.max(...metrics.dcf.projected_fcf)) * 80}px`,
                        background: theme.colors.primary,
                        borderRadius: 4,
                        marginBottom: 4,
                        transition: 'height 0.3s ease'
                      }} />
                      <Text style={{ fontSize: 10, color: theme.colors.text.secondary }}>
                        ${(fcf / 1000000000).toFixed(0)}B
                      </Text>
                      <br />
                      <Text style={{ fontSize: 10, color: theme.colors.text.secondary }}>
                        Y{index + 1}
                      </Text>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        )}

        {/* Health Assessment Dashboard */}
        {metrics.health_assessment && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 24 }}>
            <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>
              🏥 Financial Health Score
            </Title>

            <Row gutter={[24, 16]}>
              <Col xs={24} md={8}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    width: 180,
                    height: 180,
                    margin: '0 auto',
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <div style={{
                      width: '100%',
                      height: '100%',
                      borderRadius: '50%',
                      background: `conic-gradient(
                        ${metrics.health_assessment.score < 40 ? theme.colors.error :
                          metrics.health_assessment.score < 70 ? theme.colors.warning : theme.colors.success}
                        ${metrics.health_assessment.score}%,
                        ${theme.colors.background.primary} 0
                      )`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <div style={{
                        width: '75%',
                        height: '75%',
                        borderRadius: '50%',
                        background: theme.colors.background.elevated,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexDirection: 'column'
                      }}>
                        <Text strong style={{
                          fontSize: 36,
                          color: metrics.health_assessment.score < 40 ? theme.colors.error :
                                 metrics.health_assessment.score < 70 ? theme.colors.warning : theme.colors.success
                        }}>
                          {metrics.health_assessment.score.toFixed(0)}
                        </Text>
                        <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>/ 100</Text>
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: 16 }}>
                    <Tag
                      color={metrics.health_assessment.score < 40 ? 'red' :
                             metrics.health_assessment.score < 70 ? 'orange' : 'green'}
                      style={{ fontSize: 14, padding: '4px 12px' }}
                    >
                      {metrics.health_assessment.rating?.toUpperCase() ||
                       (metrics.health_assessment.score < 40 ? 'POOR' :
                        metrics.health_assessment.score < 70 ? 'FAIR' : 'GOOD')}
                    </Tag>
                  </div>

                  {metrics.health_assessment.recommendation && (
                    <div style={{ marginTop: 12 }}>
                      <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Recommendation</Text>
                      <div>
                        <Tag
                          color={metrics.health_assessment.recommendation.includes('BUY') ? 'green' :
                                 metrics.health_assessment.recommendation.includes('SELL') ? 'red' : 'orange'}
                          style={{ fontSize: 14, marginTop: 4 }}
                        >
                          {metrics.health_assessment.recommendation}
                        </Tag>
                      </div>
                      {metrics.health_assessment.confidence && (
                        <Text style={{ color: theme.colors.text.secondary, fontSize: 11 }}>
                          Confidence: {(metrics.health_assessment.confidence * 100).toFixed(0)}%
                        </Text>
                      )}
                    </div>
                  )}
                </div>
              </Col>

              <Col xs={24} md={16}>
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={12}>
                    <Title level={5} style={{ color: theme.colors.success, marginBottom: 12 }}>
                      ✅ Strengths ({metrics.health_assessment.factors?.filter((f: any) => f.impact === 'positive').length || 0})
                    </Title>
                    <Space direction="vertical" style={{ width: '100%' }} size="small">
                      {metrics.health_assessment.factors?.filter((f: any) => f.impact === 'positive').map((factor: any, index: number) => (
                        <div key={index} style={{
                          padding: 8,
                          background: theme.colors.background.primary,
                          borderRadius: 6,
                          borderLeft: `3px solid ${theme.colors.success}`
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Text style={{ color: theme.colors.text.primary, fontSize: 13 }}>{factor.factor}</Text>
                            <Text strong style={{ color: theme.colors.success, fontSize: 14 }}>✓</Text>
                          </div>
                        </div>
                      ))}
                    </Space>
                  </Col>

                  <Col xs={24} md={12}>
                    <Title level={5} style={{ color: theme.colors.error, marginBottom: 12 }}>
                      ❌ Concerns ({metrics.health_assessment.factors?.filter((f: any) => f.impact === 'negative').length || 0})
                    </Title>
                    <Space direction="vertical" style={{ width: '100%' }} size="small">
                      {metrics.health_assessment.factors?.filter((f: any) => f.impact === 'negative').length > 0 ? (
                        metrics.health_assessment.factors?.filter((f: any) => f.impact === 'negative').map((factor: any, index: number) => (
                          <div key={index} style={{
                            padding: 8,
                            background: theme.colors.background.primary,
                            borderRadius: 6,
                            borderLeft: `3px solid ${theme.colors.error}`
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <Text style={{ color: theme.colors.text.primary, fontSize: 13 }}>{factor.factor}</Text>
                              <Text strong style={{ color: theme.colors.error, fontSize: 14 }}>⚠</Text>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div style={{
                          padding: 16,
                          background: theme.colors.background.primary,
                          borderRadius: 6,
                          textAlign: 'center'
                        }}>
                          <Text style={{ color: theme.colors.text.secondary }}>No concerns identified</Text>
                        </div>
                      )}
                    </Space>
                  </Col>
                </Row>
              </Col>
            </Row>
          </Card>
        )}

        {/* Valuation Spectrum */}
        {(metrics.graham_number?.fair_value || metrics.dcf?.intrinsic_value_per_share) && result?.analysis?.market_data?.current_price && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 24 }}>
            <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>
              📊 Valuation Spectrum
            </Title>

            <Row gutter={[16, 16]}>
              <Col span={24}>
                <div style={{ padding: '24px 0' }}>
                  <div style={{
                    position: 'relative',
                    height: 60,
                    background: `linear-gradient(90deg, ${theme.colors.success} 0%, ${theme.colors.warning} 50%, ${theme.colors.error} 100%)`,
                    borderRadius: 8,
                    display: 'flex',
                    alignItems: 'center'
                  }}>
                    {/* Graham Number Marker */}
                    {metrics.graham_number?.fair_value && (
                      <div style={{
                        position: 'absolute',
                        left: '10%',
                        transform: 'translateX(-50%)',
                        textAlign: 'center'
                      }}>
                        <div style={{
                          width: 4,
                          height: 60,
                          background: 'white',
                          margin: '0 auto'
                        }} />
                        <div style={{
                          marginTop: 8,
                          padding: '4px 8px',
                          background: theme.colors.background.elevated,
                          borderRadius: 4,
                          border: `1px solid ${theme.colors.success}`,
                          whiteSpace: 'nowrap'
                        }}>
                          <Text strong style={{ color: theme.colors.success, fontSize: 12 }}>
                            Graham: ${metrics.graham_number.fair_value.toFixed(2)}
                          </Text>
                        </div>
                      </div>
                    )}

                    {/* DCF Fair Value Marker */}
                    {metrics.dcf?.intrinsic_value_per_share && (
                      <div style={{
                        position: 'absolute',
                        left: '35%',
                        transform: 'translateX(-50%)',
                        textAlign: 'center'
                      }}>
                        <div style={{
                          width: 4,
                          height: 60,
                          background: 'white',
                          margin: '0 auto'
                        }} />
                        <div style={{
                          marginTop: 8,
                          padding: '4px 8px',
                          background: theme.colors.background.elevated,
                          borderRadius: 4,
                          border: `1px solid ${theme.colors.warning}`,
                          whiteSpace: 'nowrap'
                        }}>
                          <Text strong style={{ color: theme.colors.warning, fontSize: 12 }}>
                            DCF: ${metrics.dcf.intrinsic_value_per_share.toFixed(2)}
                          </Text>
                        </div>
                      </div>
                    )}

                    {/* Current Price Marker */}
                    <div style={{
                      position: 'absolute',
                      left: '75%',
                      transform: 'translateX(-50%)',
                      textAlign: 'center'
                    }}>
                      <div style={{
                        width: 6,
                        height: 60,
                        background: theme.colors.primary,
                        margin: '0 auto',
                        border: '2px solid white'
                      }} />
                      <div style={{
                        marginTop: 8,
                        padding: '6px 12px',
                        background: theme.colors.primary,
                        borderRadius: 4,
                        border: `2px solid white`,
                        whiteSpace: 'nowrap'
                      }}>
                        <Text strong style={{ color: 'white', fontSize: 14 }}>
                          Current: ${result.analysis.market_data.current_price.toFixed(2)}
                        </Text>
                      </div>
                    </div>
                  </div>

                  <div style={{
                    marginTop: 48,
                    padding: 12,
                    background: theme.colors.background.primary,
                    borderRadius: 8
                  }}>
                    <Text style={{ color: theme.colors.text.secondary }}>
                      💡 <strong>Interpretation:</strong> {metrics.graham_number?.interpretation ||
                        `Trading at ${(result.analysis.market_data.current_price / metrics.graham_number?.fair_value).toFixed(1)}x Graham Number.
                        ${result.analysis.market_data.current_price > (metrics.dcf?.intrinsic_value_per_share || 0) ?
                          'Currently overvalued by conservative measures.' :
                          'Potentially undervalued opportunity.'}`
                      }
                    </Text>
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        )}

        {/* Competitive Advantages & Risks */}
        {fundamental.insights && (
          <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
            {fundamental.insights.competitive_advantages && fundamental.insights.competitive_advantages.length > 0 && (
              <Col xs={24} md={12}>
                <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
                  <Title level={4} style={{ color: theme.colors.text.primary }}>Competitive Advantages</Title>
                  <ul>
                    {fundamental.insights.competitive_advantages.map((advantage: string, index: number) => (
                      <li key={index}>
                        <Text style={{ color: theme.colors.success }}>{advantage}</Text>
                      </li>
                    ))}
                  </ul>
                </Card>
              </Col>
            )}
            {fundamental.insights.risks && fundamental.insights.risks.length > 0 && (
              <Col xs={24} md={12}>
                <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
                  <Title level={4} style={{ color: theme.colors.text.primary }}>Risks</Title>
                  <ul>
                    {fundamental.insights.risks.map((risk: string, index: number) => (
                      <li key={index}>
                        <Text style={{ color: theme.colors.error }}>{risk}</Text>
                      </li>
                    ))}
                  </ul>
                </Card>
              </Col>
            )}
          </Row>
        )}

        {/* Data Quality & Citations */}
        {renderDataQualityCitations('Fundamental Analysis', result?.analysis?.fundamental)}
      </div>
    );
  };

  const renderTechnicalAnalysis = () => {
    if (!result?.analysis?.technical) return <Text style={{ color: theme.colors.text.secondary }}>No technical data available</Text>;

    const technical = result.analysis.technical;
    const indicators = technical.indicators || {};

    return (
      <div>
        {/* Momentum Indicators */}
        <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>Momentum Indicators</Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>RSI</Text>}
                value={indicators.rsi?.value?.toFixed(2) || 'N/A'}
                valueStyle={{
                  color: indicators.rsi?.signal === 'overbought' ? theme.colors.error :
                         indicators.rsi?.signal === 'oversold' ? theme.colors.success :
                         theme.colors.warning
                }}
              />
              {indicators.rsi?.interpretation && (
                <Text type="secondary" style={{ fontSize: 12 }}>{indicators.rsi.interpretation}</Text>
              )}
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>MACD</Text>}
                value={indicators.macd?.macd?.toFixed(2) || 'N/A'}
                valueStyle={{ color: theme.colors.primary }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                Signal: {indicators.macd?.signal?.toFixed(2) || 'N/A'}
              </Text>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Histogram</Text>}
                value={indicators.macd?.histogram?.toFixed(2) || 'N/A'}
                valueStyle={{
                  color: indicators.macd?.histogram > 0 ? theme.colors.success : theme.colors.error
                }}
              />
              <Tag color={indicators.macd?.trend === 'bullish' ? 'green' : 'red'}>
                {indicators.macd?.trend || 'Neutral'}
              </Tag>
            </Card>
          </Col>
        </Row>

        {/* Volatility Indicators */}
        <Title level={4} style={{ color: theme.colors.text.primary, marginTop: 24, marginBottom: 16 }}>Volatility & Bands</Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={5} style={{ color: theme.colors.text.primary }}>Bollinger Bands</Title>
              <Row gutter={[8, 8]}>
                <Col span={8}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Upper</Text>}
                    value={indicators.bollinger_bands?.upper?.toFixed(2) || 'N/A'}
                    prefix="$"
                    valueStyle={{ fontSize: 16 }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Middle</Text>}
                    value={indicators.bollinger_bands?.middle?.toFixed(2) || 'N/A'}
                    prefix="$"
                    valueStyle={{ fontSize: 16 }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Lower</Text>}
                    value={indicators.bollinger_bands?.lower?.toFixed(2) || 'N/A'}
                    prefix="$"
                    valueStyle={{ fontSize: 16 }}
                  />
                </Col>
              </Row>
              <div style={{ marginTop: 12 }}>
                <Tag color={indicators.bollinger_bands?.signal === 'neutral' ? 'default' : 'processing'}>
                  {indicators.bollinger_bands?.position || 'N/A'}
                </Tag>
              </div>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={5} style={{ color: theme.colors.text.primary }}>Volatility Metrics</Title>
              <Row gutter={[8, 8]}>
                <Col span={12}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.text.secondary }}>ATR</Text>}
                    value={indicators.atr?.toFixed(2) || 'N/A'}
                    valueStyle={{ color: theme.colors.warning }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.text.secondary }}>ADX</Text>}
                    value={indicators.adx || 'N/A'}
                    valueStyle={{ color: theme.colors.warning }}
                  />
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>

        {/* Volume Analysis */}
        {technical.volume_analysis && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 24 }}>
            <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>Volume Analysis</Title>
            <Row gutter={[16, 16]}>
              <Col xs={24} md={8}>
                <div style={{ textAlign: 'center' }}>
                  <Text style={{ color: theme.colors.text.secondary, fontSize: 12, display: 'block', marginBottom: 8 }}>
                    Volume Ratio
                  </Text>
                  <div style={{
                    width: 120,
                    height: 120,
                    margin: '0 auto',
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <div style={{
                      width: '100%',
                      height: '100%',
                      borderRadius: '50%',
                      background: `conic-gradient(
                        ${technical.volume_analysis.volume_ratio < 0.8 ? theme.colors.error :
                          technical.volume_analysis.volume_ratio > 1.2 ? theme.colors.success : theme.colors.warning}
                        ${(technical.volume_analysis.volume_ratio || 0) * 100}%,
                        ${theme.colors.background.primary} 0
                      )`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <div style={{
                        width: '80%',
                        height: '80%',
                        borderRadius: '50%',
                        background: theme.colors.background.elevated,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexDirection: 'column'
                      }}>
                        <Text strong style={{
                          fontSize: 24,
                          color: technical.volume_analysis.volume_ratio < 0.8 ? theme.colors.error :
                                 technical.volume_analysis.volume_ratio > 1.2 ? theme.colors.success : theme.colors.warning
                        }}>
                          {technical.volume_analysis.volume_ratio?.toFixed(2) || 'N/A'}x
                        </Text>
                      </div>
                    </div>
                  </div>
                  <Tag
                    color={technical.volume_analysis.volume_ratio < 0.8 ? 'red' :
                           technical.volume_analysis.volume_ratio > 1.2 ? 'green' : 'orange'}
                    style={{ marginTop: 12 }}
                  >
                    {technical.volume_analysis.volume_ratio < 0.8 ? '▼ Below Average' :
                     technical.volume_analysis.volume_ratio > 1.2 ? '▲ Above Average' : '● Average'}
                  </Tag>
                </div>
              </Col>

              <Col xs={24} md={8}>
                <Statistic
                  title={<Text style={{ color: theme.colors.text.secondary }}>Current Volume</Text>}
                  value={technical.volume_analysis.current_volume ?
                    `${(technical.volume_analysis.current_volume / 1000000).toFixed(1)}M` : 'N/A'}
                  valueStyle={{ color: theme.colors.primary }}
                />
              </Col>

              <Col xs={24} md={8}>
                <Statistic
                  title={<Text style={{ color: theme.colors.text.secondary }}>Average Volume (30d)</Text>}
                  value={technical.volume_analysis.average_volume ?
                    `${(technical.volume_analysis.average_volume / 1000000).toFixed(1)}M` : 'N/A'}
                  valueStyle={{ color: theme.colors.text.secondary }}
                />
              </Col>
            </Row>

            {technical.volume_analysis.interpretation && (
              <div style={{
                marginTop: 16,
                padding: 12,
                background: theme.colors.background.primary,
                borderRadius: 8,
                borderLeft: `3px solid ${
                  technical.volume_analysis.volume_ratio < 0.8 ? theme.colors.error :
                  technical.volume_analysis.volume_ratio > 1.2 ? theme.colors.success : theme.colors.warning
                }`
              }}>
                <Text style={{ color: theme.colors.text.secondary }}>
                  {technical.volume_analysis.interpretation}
                </Text>
              </div>
            )}
          </Card>
        )}

        {/* Chart Patterns */}
        {technical.patterns?.patterns && technical.patterns.patterns.length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Title level={4} style={{ color: theme.colors.text.primary, margin: 0 }}>
                Chart Patterns Detected ({technical.patterns.patterns.length})
              </Title>
            </div>
            <Row gutter={[16, 16]}>
              {technical.patterns.patterns.map((pattern: any, index: number) => {
                const isBullish = pattern.type?.toLowerCase() === 'bullish';
                const isBearish = pattern.type?.toLowerCase() === 'bearish';
                const patternColor = isBullish ? theme.colors.success : isBearish ? theme.colors.error : theme.colors.primary;
                const confidencePercent = pattern.confidence * 100;

                return (
                  <Col xs={24} sm={12} lg={6} key={index}>
                    <Card
                      size="small"
                      style={{
                        background: theme.colors.background.primary,
                        border: `2px solid ${patternColor}`,
                        borderRadius: 8
                      }}
                    >
                      <div style={{ marginBottom: 12 }}>
                        <Text strong style={{ color: theme.colors.text.primary, fontSize: 16 }}>
                          {isBullish && '🔻 '}{isBearish && '🔺 '}{!isBullish && !isBearish && '📈 '}
                          {pattern.pattern}
                        </Text>
                        <div>
                          <Tag color={isBullish ? 'green' : isBearish ? 'red' : 'blue'} style={{ marginTop: 4 }}>
                            {pattern.type?.toUpperCase() || 'CONTINUATION'}
                          </Tag>
                        </div>
                      </div>

                      {/* Confidence Bar */}
                      <div style={{ marginBottom: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                          <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Confidence</Text>
                          <Text strong style={{ color: patternColor, fontSize: 12 }}>{confidencePercent.toFixed(0)}%</Text>
                        </div>
                        <div style={{
                          width: '100%',
                          height: 6,
                          background: theme.colors.background.elevated,
                          borderRadius: 3,
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${confidencePercent}%`,
                            height: '100%',
                            background: patternColor,
                            transition: 'width 0.3s ease'
                          }} />
                        </div>
                      </div>

                      {/* Price Levels */}
                      <Space direction="vertical" size={4} style={{ width: '100%' }}>
                        {pattern.support && (
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Support:</Text>
                            <Text strong style={{ color: theme.colors.success, fontSize: 12 }}>${pattern.support.toFixed(2)}</Text>
                          </div>
                        )}
                        {pattern.resistance && (
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Resistance:</Text>
                            <Text strong style={{ color: theme.colors.error, fontSize: 12 }}>${pattern.resistance.toFixed(2)}</Text>
                          </div>
                        )}
                        {pattern.target && (
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Target:</Text>
                            <Text strong style={{ color: theme.colors.primary, fontSize: 12 }}>${pattern.target.toFixed(2)}</Text>
                          </div>
                        )}
                        {pattern.invalidation_level && (
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Stop Loss:</Text>
                            <Text strong style={{ color: theme.colors.warning, fontSize: 12 }}>${pattern.invalidation_level.toFixed(2)}</Text>
                          </div>
                        )}
                      </Space>

                      {/* Formation Status */}
                      {pattern.formation_complete !== undefined && (
                        <div style={{ marginTop: 12 }}>
                          <Tag color={pattern.formation_complete ? 'success' : 'processing'} style={{ width: '100%', textAlign: 'center' }}>
                            {pattern.formation_complete ? '✓ Complete' : '⏳ Watch'}
                          </Tag>
                        </div>
                      )}

                      {/* Trading Strategy */}
                      {pattern.trading_strategy && (
                        <div style={{
                          marginTop: 12,
                          padding: 8,
                          background: theme.colors.background.elevated,
                          borderRadius: 4,
                          borderLeft: `3px solid ${patternColor}`
                        }}>
                          <Text style={{ color: theme.colors.text.secondary, fontSize: 11, lineHeight: 1.4 }}>
                            {pattern.trading_strategy}
                          </Text>
                        </div>
                      )}
                    </Card>
                  </Col>
                );
              })}
            </Row>
          </Card>
        )}

        {/* Support & Resistance */}
        {indicators.support_resistance && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 24 }}>
            <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>Support & Resistance Levels</Title>
            <Row gutter={[24, 16]}>
              <Col xs={24} md={12}>
                <Title level={5} style={{ color: theme.colors.success }}>Support Levels</Title>
                <Space wrap>
                  {indicators.support_resistance.support?.map((level: number, i: number) => (
                    <Tag key={i} color="green" style={{ fontSize: 14, padding: '4px 8px' }}>
                      ${level.toFixed(2)}
                    </Tag>
                  )) || <Text>No support levels available</Text>}
                </Space>
              </Col>
              <Col xs={24} md={12}>
                <Title level={5} style={{ color: theme.colors.error }}>Resistance Levels</Title>
                <Space wrap>
                  {indicators.support_resistance.resistance?.map((level: number, i: number) => (
                    <Tag key={i} color="red" style={{ fontSize: 14, padding: '4px 8px' }}>
                      ${level.toFixed(2)}
                    </Tag>
                  )) || <Text>No resistance levels available</Text>}
                </Space>
              </Col>
            </Row>
          </Card>
        )}

        {/* Technical Insights */}
        {technical.insights?.technical_summary && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 24 }}>
            <Title level={4} style={{ color: theme.colors.text.primary }}>Technical Summary</Title>
            <Paragraph style={{ color: theme.colors.text.primary }}>
              {technical.insights.technical_summary}
            </Paragraph>
            {technical.insights.recommendation && (
              <div style={{ marginTop: 16 }}>
                <Text strong style={{ color: theme.colors.text.secondary }}>Recommendation: </Text>
                <Tag color={
                  technical.insights.recommendation.includes('BUY') ? 'green' :
                  technical.insights.recommendation.includes('SELL') ? 'red' : 'orange'
                }>
                  {technical.insights.recommendation}
                </Tag>
              </div>
            )}
          </Card>
        )}

        {/* Data Quality & Citations */}
        {renderDataQualityCitations('Technical Analysis', result?.analysis?.technical)}
      </div>
    );
  };

  const renderSentimentAnalysis = () => {
    if (!result?.analysis?.sentiment) return <Text style={{ color: theme.colors.text.secondary }}>No sentiment data available</Text>;

    const sentiment = result.analysis.sentiment;
    const socialData = sentiment.social_data || {};
    const sentimentPulse = sentiment.sentiment_pulse || {};
    const bullArgs = sentiment.bull_arguments || [];
    const bearArgs = sentiment.bear_arguments || [];
    const sources = socialData.sources || [];

    const retailSentiment = sentimentPulse.retail_sentiment || 'neutral';
    const confidenceScore = (sentimentPulse.confidence || 0.5) * 100;
    const volume = sentimentPulse.volume || 'medium';
    const isTrending = sentimentPulse.trending || false;

    // Calculate sentiment distribution from bull/bear arguments
    const positiveCount = bullArgs.length;
    const negativeCount = bearArgs.length;
    const neutralCount = 0; // No neutral arguments in this data structure

    // Vibrant banner colors matching working design
    const bannerColors = {
      'bullish': { bg: '#15803d', text: '#fff' },
      'bearish': { bg: '#991b1b', text: '#fff' },
      'neutral': { bg: '#a16207', text: '#fff' }
    };
    const bannerColor = bannerColors[retailSentiment] || bannerColors['neutral'];

    return (
      <div>
        {/* Sentiment Pulse Banner - Vibrant Design */}
        <Card style={{
          background: bannerColor.bg,
          border: 'none',
          marginBottom: 24,
          padding: '20px 24px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <Title level={4} style={{ color: bannerColor.text, margin: 0, fontSize: '18px', fontWeight: 'bold' }}>
              {retailSentiment.toUpperCase()} Sentiment | Volume: {volume.toUpperCase()} |
              {isTrending && <Tag color="volcano" style={{ marginLeft: 8 }}>TRENDING 🔥</Tag>}
            </Title>
          </div>
          <Text style={{ color: 'rgba(255,255,255,0.9)', display: 'block', marginTop: 8 }}>
            Confidence: {confidenceScore.toFixed(0)}% | Total Mentions: {socialData.total_mentions || 0} |
            Platforms: {(socialData.platforms || []).join(', ')}
          </Text>
        </Card>

        {/* Sentiment Distribution & Key Metrics */}
        <Row gutter={[24, 24]}>
          {/* Sentiment Distribution Pie Chart (Visual Representation) */}
          <Col xs={24} md={12}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>Sentiment Distribution</Title>
              <Row gutter={[8, 8]}>
                <Col span={8}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.success }}>Bullish</Text>}
                    value={positiveCount}
                    suffix={<Text style={{ fontSize: 12, color: theme.colors.text.secondary }}>args</Text>}
                    valueStyle={{ color: theme.colors.success }}
                  />
                  <Progress
                    percent={positiveCount + negativeCount > 0 ? (positiveCount / (positiveCount + negativeCount)) * 100 : 0}
                    strokeColor={theme.colors.success}
                    showInfo={false}
                    size="small"
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.warning }}>Neutral</Text>}
                    value={neutralCount}
                    suffix={<Text style={{ fontSize: 12, color: theme.colors.text.secondary }}>args</Text>}
                    valueStyle={{ color: theme.colors.warning }}
                  />
                  <Progress
                    percent={0}
                    strokeColor={theme.colors.warning}
                    showInfo={false}
                    size="small"
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.error }}>Bearish</Text>}
                    value={negativeCount}
                    suffix={<Text style={{ fontSize: 12, color: theme.colors.text.secondary }}>args</Text>}
                    valueStyle={{ color: theme.colors.error }}
                  />
                  <Progress
                    percent={positiveCount + negativeCount > 0 ? (negativeCount / (positiveCount + negativeCount)) * 100 : 0}
                    strokeColor={theme.colors.error}
                    showInfo={false}
                    size="small"
                  />
                </Col>
              </Row>
            </Card>
          </Col>

          {/* Divergence Score & Confidence */}
          <Col xs={24} md={12}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>Sentiment Reliability</Title>
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>Divergence Score</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.primary, fontSize: 24 }}>
                      {sentiment.divergence_score?.toFixed(2) || '0.00'}
                    </Text>
                    <Text style={{ fontSize: 12, color: theme.colors.text.secondary, marginLeft: 8 }}>
                      (Lower = More Agreement)
                    </Text>
                  </div>
                </div>
                <div>
                  <Text style={{ color: theme.colors.text.secondary }}>Confidence Level</Text>
                  <Progress
                    percent={confidenceScore}
                    strokeColor={confidenceScore > 70 ? theme.colors.success : confidenceScore > 40 ? theme.colors.warning : theme.colors.error}
                    status={confidenceScore > 70 ? 'success' : 'normal'}
                  />
                </div>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* Bull vs Bear Arguments */}
        <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
          <Col xs={24} md={12}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.success, marginBottom: 16 }}>🐂 Bullish Arguments</Title>
              <Timeline>
                {bullArgs.length > 0 ? (
                  bullArgs.map((arg: string, index: number) => (
                    <Timeline.Item key={index} color="green">
                      <Text style={{ color: theme.colors.text.primary }}>{arg}</Text>
                    </Timeline.Item>
                  ))
                ) : (
                  <Text style={{ color: theme.colors.text.secondary }}>No bullish arguments detected</Text>
                )}
              </Timeline>
            </Card>
          </Col>

          <Col xs={24} md={12}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.error, marginBottom: 16 }}>🐻 Bearish Arguments</Title>
              <Timeline>
                {bearArgs.length > 0 ? (
                  bearArgs.map((arg: string, index: number) => (
                    <Timeline.Item key={index} color="red">
                      <Text style={{ color: theme.colors.text.primary }}>{arg}</Text>
                    </Timeline.Item>
                  ))
                ) : (
                  <Text style={{ color: theme.colors.text.secondary }}>No bearish arguments detected</Text>
                )}
              </Timeline>
            </Card>
          </Col>
        </Row>

        {/* Top Social Media Sources */}
        <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 24 }}>
          <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>
            Top Social Media Sources (Sorted by Sentiment Score)
          </Title>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            {sources.slice(0, 5).map((source: any, index: number) => {
              const sentimentColor = source.score > 0.6 ? theme.colors.success : source.score < 0.4 ? theme.colors.error : theme.colors.warning;
              const sentimentLabel = source.score > 0.6 ? 'Bullish' : source.score < 0.4 ? 'Bearish' : 'Neutral';

              return (
                <Card
                  key={index}
                  size="small"
                  style={{
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: `1px solid ${theme.colors.border}`
                  }}
                >
                  <Row justify="space-between" align="middle">
                    <Col span={18}>
                      <div>
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: theme.colors.primary, fontWeight: 500 }}
                        >
                          {source.title}
                        </a>
                      </div>
                      <Text style={{ fontSize: 12, color: theme.colors.text.secondary }}>
                        {source.content?.substring(0, 120)}...
                      </Text>
                    </Col>
                    <Col span={6} style={{ textAlign: 'right' }}>
                      <Tag color={sentimentColor} style={{ fontSize: 12 }}>
                        {sentimentLabel}
                      </Tag>
                      <div>
                        <Text style={{ fontSize: 18, fontWeight: 'bold', color: sentimentColor }}>
                          {(source.score * 100).toFixed(0)}%
                        </Text>
                      </div>
                    </Col>
                  </Row>
                </Card>
              );
            })}
          </Space>
          {sources.length > 5 && (
            <Text style={{ fontSize: 12, color: theme.colors.text.secondary, marginTop: 12, display: 'block' }}>
              Showing top 5 of {sources.length} total sources
            </Text>
          )}
        </Card>

        {/* Timestamp */}
        <Text style={{ fontSize: 12, color: theme.colors.text.secondary, marginTop: 16, display: 'block' }}>
          Last updated: {sentiment.timestamp ? new Date(sentiment.timestamp).toLocaleString() : 'N/A'}
        </Text>
      </div>
    );
  };

  const renderRiskAssessment = () => {
    // ✅ FIX: Check for risk_analysis (not risk_assessment) - matches API response structure
    if (!result?.risk_analysis) return <Text style={{ color: theme.colors.text.secondary }}>No risk data available</Text>;

    const data = result.risk_analysis;
    const riskLevel = data.risk_level || 'medium';
    const riskScore = data.risk_score || 50;

    // ✅ FIX: Extract risk metrics from nested structure (risk_data.SYMBOL.risk_metrics)
    // API returns metrics nested like: risk_data.AAPL.risk_metrics.sharpe_ratio
    let riskMetrics: any = {};
    if (data.risk_data) {
      // Get the first symbol's risk metrics (handles AAPL, TSLA, etc.)
      const symbols = Object.keys(data.risk_data);
      if (symbols.length > 0) {
        const firstSymbol = symbols[0];
        riskMetrics = data.risk_data[firstSymbol]?.risk_metrics || {};
      }
    }

    return (
      <div>
        <Row gutter={[16, 16]}>
          <Col span={8}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.text.primary }}>Risk Level</Title>
              <Tag color={riskLevel.toLowerCase() === 'low' ? 'green' : riskLevel.toLowerCase() === 'high' ? 'red' : 'orange'} style={{ fontSize: 18 }}>
                {riskLevel.toUpperCase()}
              </Tag>
            </Card>
          </Col>
          <Col span={8}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.text.primary }}>Risk Score</Title>
              <Progress
                percent={riskScore}
                strokeColor={theme.colors.warning}
                trailColor={theme.colors.border}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Sharpe Ratio</Text>}
                value={riskMetrics.sharpe_ratio?.toFixed(2) || 'N/A'}
                valueStyle={{ color: riskMetrics.sharpe_ratio && riskMetrics.sharpe_ratio > 1 ? theme.colors.success : theme.colors.warning }}
              />
            </Card>
          </Col>
        </Row>

        {/* Risk Metrics Grid */}
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={12}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Value at Risk (VaR)</Text>}
                value={riskMetrics.var?.var ? `$${riskMetrics.var.var.toFixed(2)}` : 'N/A'}
                suffix={riskMetrics.var?.var_percent ? `(${riskMetrics.var.var_percent.toFixed(2)}%)` : ''}
                valueStyle={{ color: theme.colors.error }}
              />
            </Card>
          </Col>
          <Col span={12}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Conditional VaR (CVaR)</Text>}
                value={riskMetrics.cvar?.cvar ? `$${riskMetrics.cvar.cvar.toFixed(2)}` : 'N/A'}
                suffix={riskMetrics.cvar?.cvar_percent ? `(${riskMetrics.cvar.cvar_percent.toFixed(2)}%)` : ''}
                valueStyle={{ color: theme.colors.error }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Sortino Ratio</Text>}
                value={riskMetrics.sortino_ratio?.toFixed(2) || 'N/A'}
                valueStyle={{ color: theme.colors.text.primary }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Max Drawdown</Text>}
                value={riskMetrics.max_drawdown?.max_drawdown?.toFixed(2) || 'N/A'}
                suffix="%"
                valueStyle={{ color: theme.colors.error }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Volatility</Text>}
                value={riskMetrics.volatility ? `${(riskMetrics.volatility * 100).toFixed(2)}` : 'N/A'}
                suffix="%"
                valueStyle={{ color: theme.colors.warning }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Statistic
                title={<Text style={{ color: theme.colors.text.secondary }}>Beta</Text>}
                value={riskMetrics.beta?.toFixed(2) || 'N/A'}
                valueStyle={{ color: riskMetrics.beta && riskMetrics.beta > 1 ? theme.colors.error : theme.colors.success }}
              />
            </Card>
          </Col>
        </Row>

        {/* Monte Carlo Simulation - Enhanced Visualization */}
        {riskMetrics.monte_carlo && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 24 }}>
            <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>
              Monte Carlo Simulation (1 Year Projection)
            </Title>

            {/* Price Projections Row */}
            <Row gutter={[16, 16]}>
              <Col xs={12} md={6}>
                <Card style={{ background: 'rgba(255, 255, 255, 0.02)', border: `1px solid ${theme.colors.border}` }}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.text.secondary }}>Current Price</Text>}
                    value={riskMetrics.monte_carlo.current_price?.toFixed(2) || 'N/A'}
                    prefix="$"
                    valueStyle={{ color: theme.colors.text.primary, fontSize: 24 }}
                  />
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card style={{ background: 'rgba(66, 135, 245, 0.1)', border: `1px solid ${theme.colors.primary}` }}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.text.secondary }}>Expected Price</Text>}
                    value={riskMetrics.monte_carlo.expected_price?.toFixed(2) || 'N/A'}
                    prefix="$"
                    valueStyle={{ color: theme.colors.primary, fontSize: 24 }}
                  />
                  {riskMetrics.monte_carlo.expected_return && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Return: {riskMetrics.monte_carlo.expected_return.toFixed(2)}%
                    </Text>
                  )}
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card style={{ background: 'rgba(245, 34, 45, 0.1)', border: `1px solid ${theme.colors.error}` }}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.text.secondary }}>Pessimistic (5%)</Text>}
                    value={riskMetrics.monte_carlo.pessimistic?.toFixed(2) || 'N/A'}
                    prefix="$"
                    valueStyle={{ color: theme.colors.error, fontSize: 24 }}
                  />
                  {riskMetrics.monte_carlo.downside_risk && (
                    <Text type="secondary" style={{ fontSize: 12, color: theme.colors.error }}>
                      Downside: {riskMetrics.monte_carlo.downside_risk.toFixed(2)}%
                    </Text>
                  )}
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card style={{ background: 'rgba(82, 196, 26, 0.1)', border: `1px solid ${theme.colors.success}` }}>
                  <Statistic
                    title={<Text style={{ color: theme.colors.text.secondary }}>Optimistic (95%)</Text>}
                    value={riskMetrics.monte_carlo.optimistic?.toFixed(2) || 'N/A'}
                    prefix="$"
                    valueStyle={{ color: theme.colors.success, fontSize: 24 }}
                  />
                  {riskMetrics.monte_carlo.upside_potential && (
                    <Text type="secondary" style={{ fontSize: 12, color: theme.colors.success }}>
                      Upside: {riskMetrics.monte_carlo.upside_potential.toFixed(2)}%
                    </Text>
                  )}
                </Card>
              </Col>
            </Row>

            {/* Price Range Visualization */}
            <div style={{ marginTop: 24, padding: '16px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 8 }}>
              <Text style={{ color: theme.colors.text.secondary, fontSize: 12, display: 'block', marginBottom: 8 }}>
                Price Range Distribution
              </Text>
              <div style={{
                position: 'relative',
                height: 40,
                background: `linear-gradient(90deg, ${theme.colors.error} 0%, ${theme.colors.warning} 25%, ${theme.colors.primary} 50%, ${theme.colors.success} 75%, ${theme.colors.success} 100%)`,
                borderRadius: 8,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 8px'
              }}>
                <Text style={{ color: 'white', fontSize: 10, fontWeight: 'bold' }}>
                  ${riskMetrics.monte_carlo.pessimistic?.toFixed(0)}
                </Text>
                <div style={{
                  position: 'absolute',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: 3,
                  height: '100%',
                  background: 'white',
                  opacity: 0.8
                }}>
                  <div style={{
                    position: 'absolute',
                    top: '-20px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    whiteSpace: 'nowrap',
                    fontSize: 10,
                    color: theme.colors.text.secondary
                  }}>
                    Expected
                  </div>
                </div>
                <Text style={{ color: 'white', fontSize: 10, fontWeight: 'bold' }}>
                  ${riskMetrics.monte_carlo.optimistic?.toFixed(0)}
                </Text>
              </div>
              <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between' }}>
                <Text style={{ fontSize: 10, color: theme.colors.text.secondary }}>Worst Case</Text>
                <Text style={{ fontSize: 10, color: theme.colors.text.secondary }}>Best Case</Text>
              </div>
            </div>

            {/* Risk/Return Summary */}
            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={24}>
                <Alert
                  message="Monte Carlo Analysis Summary"
                  description={
                    <div>
                      <Text style={{ color: theme.colors.text.primary }}>
                        Based on 10,000 simulations, there is a 95% confidence that the stock price will be between{' '}
                        <Text strong style={{ color: theme.colors.error }}>
                          ${riskMetrics.monte_carlo.pessimistic?.toFixed(2)}
                        </Text>
                        {' '}and{' '}
                        <Text strong style={{ color: theme.colors.success }}>
                          ${riskMetrics.monte_carlo.optimistic?.toFixed(2)}
                        </Text>
                        {' '}in one year, with an expected value of{' '}
                        <Text strong style={{ color: theme.colors.primary }}>
                          ${riskMetrics.monte_carlo.expected_price?.toFixed(2)}
                        </Text>
                        .
                      </Text>
                    </div>
                  }
                  type="info"
                  showIcon
                  style={{ background: 'rgba(66, 135, 245, 0.1)', border: `1px solid ${theme.colors.primary}` }}
                />
              </Col>
            </Row>
          </Card>
        )}

        {/* Risk Insights */}
        {data.risk_insights && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 16 }}>
            <Title level={4} style={{ color: theme.colors.text.primary }}>Risk Insights</Title>
            <Timeline>
              {(Array.isArray(data.risk_insights) ? data.risk_insights : [data.risk_insights]).map((insight: string, index: number) => (
                <Timeline.Item key={index} color="orange">
                  <Text style={{ color: theme.colors.text.primary }}>{insight}</Text>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        )}

        {/* Mitigation Strategies */}
        {data.mitigation_strategies && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 16 }}>
            <Title level={4} style={{ color: theme.colors.text.primary }}>Risk Mitigation Strategies</Title>
            <Timeline>
              {(Array.isArray(data.mitigation_strategies) ? data.mitigation_strategies : [data.mitigation_strategies]).map((strategy: string, index: number) => (
                <Timeline.Item key={index} color="green">
                  <Text style={{ color: theme.colors.text.primary }}>{strategy}</Text>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        )}
      </div>
    );
  };

  const renderPeerComparison = () => {
    if (!result?.analysis?.peer_comparison) {
      return <Text style={{ color: theme.colors.text.secondary }}>No peer comparison data available</Text>;
    }

    const peerData = result.analysis.peer_comparison;
    const stocks = peerData.stocks || {};
    const relativePosition = peerData.relative_position || {};
    const competitiveAdvantages = peerData.competitive_advantages || [];
    const competitiveRisks = peerData.competitive_risks || [];

    // Extract stock data
    const stockSymbols = Object.keys(stocks);
    const firstStock = stockSymbols.length > 0 ? stocks[stockSymbols[0]] : null;

    return (
      <div>
        {/* Market Position Summary */}
        <Alert
          type={
            relativePosition.overall === 'strong' ? 'success' :
            relativePosition.overall === 'weak' ? 'error' : 'info'
          }
          message={
            <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
              Market Position: {relativePosition.overall?.toUpperCase() || 'N/A'}
            </span>
          }
          description={
            <div>
              {firstStock && (
                <Text style={{ color: theme.colors.text.primary }}>
                  Valuation: {firstStock.valuation_vs_peers || 'N/A'} |
                  Growth: {firstStock.growth_vs_peers || 'N/A'} |
                  Profitability: {firstStock.profitability_vs_peers || 'N/A'}
                </Text>
              )}
            </div>
          }
          style={{ marginBottom: 24 }}
        />

        {/* Stock Analysis Grid */}
        {stockSymbols.length > 0 && (
          <Row gutter={[24, 24]}>
            {stockSymbols.map((symbol) => {
              const stockInfo = stocks[symbol];
              const peers = stockInfo.identified_peers || [];
              const peerMetrics = stockInfo.peer_metrics || {};
              const keyDifferentiators = stockInfo.key_differentiators || [];

              return (
                <Col xs={24} key={symbol}>
                  <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
                    <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>
                      {symbol} Analysis
                    </Title>

                    {/* Metrics Row */}
                    <Row gutter={[16, 16]}>
                      <Col xs={12} md={6}>
                        <Statistic
                          title={<Text style={{ color: theme.colors.text.secondary }}>Market Position</Text>}
                          value={stockInfo.market_position || 'N/A'}
                          valueStyle={{ color: theme.colors.primary, textTransform: 'capitalize' }}
                        />
                      </Col>
                      <Col xs={12} md={6}>
                        <Statistic
                          title={<Text style={{ color: theme.colors.text.secondary }}>Valuation</Text>}
                          value={stockInfo.valuation_vs_peers || 'N/A'}
                          valueStyle={{ color: theme.colors.primary, textTransform: 'capitalize' }}
                        />
                      </Col>
                      <Col xs={12} md={6}>
                        <Statistic
                          title={<Text style={{ color: theme.colors.text.secondary }}>Growth</Text>}
                          value={stockInfo.growth_vs_peers || 'N/A'}
                          valueStyle={{ color: theme.colors.primary, textTransform: 'capitalize' }}
                        />
                      </Col>
                      <Col xs={12} md={6}>
                        <Statistic
                          title={<Text style={{ color: theme.colors.text.secondary }}>Profitability</Text>}
                          value={stockInfo.profitability_vs_peers || 'N/A'}
                          valueStyle={{ color: theme.colors.primary, textTransform: 'capitalize' }}
                        />
                      </Col>
                    </Row>

                    {/* Identified Peers */}
                    {peers.length > 0 && (
                      <div style={{ marginTop: 16 }}>
                        <Text strong style={{ color: theme.colors.text.primary }}>Identified Peers: </Text>
                        <Space wrap style={{ marginTop: 8 }}>
                          {peers.map((peer: string, idx: number) => (
                            <Tag key={idx} color="blue">{peer}</Tag>
                          ))}
                        </Space>
                      </div>
                    )}

                    {/* Key Differentiators */}
                    {keyDifferentiators.length > 0 && (
                      <div style={{ marginTop: 16 }}>
                        <Text strong style={{ color: theme.colors.text.primary }}>Key Differentiators:</Text>
                        <Timeline style={{ marginTop: 12 }}>
                          {keyDifferentiators.map((diff: string, idx: number) => (
                            <Timeline.Item key={idx} color="blue">
                              <Text style={{ color: theme.colors.text.primary }}>{diff}</Text>
                            </Timeline.Item>
                          ))}
                        </Timeline>
                      </div>
                    )}

                    {/* Peer Metrics (if available) */}
                    {Object.keys(peerMetrics).length > 0 && (
                      <div style={{ marginTop: 16 }}>
                        <Text strong style={{ color: theme.colors.text.primary }}>Peer Metrics:</Text>
                        <Row gutter={[8, 8]} style={{ marginTop: 12 }}>
                          {Object.entries(peerMetrics).map(([key, value]: [string, any]) => (
                            <Col xs={12} md={6} key={key}>
                              <Card size="small" style={{ background: 'rgba(255, 255, 255, 0.02)', border: `1px solid ${theme.colors.border}` }}>
                                <Text style={{ fontSize: 12, color: theme.colors.text.secondary, textTransform: 'capitalize' }}>
                                  {key.replace(/_/g, ' ')}
                                </Text>
                                <div>
                                  <Text strong style={{ color: theme.colors.primary }}>
                                    {typeof value === 'number' ? value.toFixed(2) : value}
                                  </Text>
                                </div>
                              </Card>
                            </Col>
                          ))}
                        </Row>
                      </div>
                    )}
                  </Card>
                </Col>
              );
            })}
          </Row>
        )}

        {/* Competitive Advantages & Risks */}
        <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
          <Col xs={24} md={12}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.success, marginBottom: 16 }}>Competitive Advantages</Title>
              {competitiveAdvantages.length > 0 ? (
                <Timeline>
                  {competitiveAdvantages.map((advantage: string, idx: number) => (
                    <Timeline.Item key={idx} color="green">
                      <Text style={{ color: theme.colors.text.primary }}>{advantage}</Text>
                    </Timeline.Item>
                  ))}
                </Timeline>
              ) : (
                <Text style={{ color: theme.colors.text.secondary }}>No competitive advantages identified</Text>
              )}
            </Card>
          </Col>

          <Col xs={24} md={12}>
            <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
              <Title level={4} style={{ color: theme.colors.error, marginBottom: 16 }}>Competitive Risks</Title>
              {competitiveRisks.length > 0 ? (
                <Timeline>
                  {competitiveRisks.map((risk: string, idx: number) => (
                    <Timeline.Item key={idx} color="red">
                      <Text style={{ color: theme.colors.text.primary }}>{risk}</Text>
                    </Timeline.Item>
                  ))}
                </Timeline>
              ) : (
                <Text style={{ color: theme.colors.text.secondary }}>No competitive risks identified</Text>
              )}
            </Card>
          </Col>
        </Row>

        {/* Timestamp */}
        <Text style={{ fontSize: 12, color: theme.colors.text.secondary, marginTop: 16, display: 'block' }}>
          Last updated: {peerData.timestamp ? new Date(peerData.timestamp).toLocaleString() : 'N/A'}
        </Text>
      </div>
    );
  };

  const renderRecommendations = () => {
    if (!result?.recommendations) return <Text style={{ color: theme.colors.text.secondary }}>No recommendations available</Text>;

    const data = result.recommendations;
    const action = data.action || 'HOLD';
    // ✅ FIX: Convert confidence from 0-1 scale to 0-100 percentage scale
    const confidence = data.confidence ? Math.round(data.confidence * 100) : 50;
    const rationale = result.investment_thesis || result.executive_summary || 'No rationale provided';

    //  Color scheme based on action type
    const actionColors = {
      'BUY': { bg: '#1a4d2e', text: '#4ade80', badge: '#16a34a' },
      'STRONG BUY': { bg: '#1a4d2e', text: '#4ade80', badge: '#16a34a' },
      'SELL': { bg: '#4d1a1a', text: '#f87171', badge: '#dc2626' },
      'STRONG SELL': { bg: '#4d1a1a', text: '#f87171', badge: '#dc2626' },
      'HOLD': { bg: '#4d3319', text: '#fbbf24', badge: '#f59e0b' }
    };
    const colors = actionColors[action] || actionColors['HOLD'];

    return (
      <div>
        {/* Hero Recommendation Card - Matching working design */}
        <Card style={{
          background: colors.bg,
          border: `1px solid ${colors.badge}`,
          marginBottom: 24,
          padding: '24px'
        }}>
          <Title level={2} style={{ color: colors.text, marginBottom: 16, fontSize: '36px', fontWeight: 'bold' }}>
            {action}
          </Title>
          <Tag style={{
            background: colors.badge,
            color: '#fff',
            fontSize: '16px',
            padding: '6px 16px',
            border: 'none',
            fontWeight: 'bold'
          }}>
            Confidence: {Math.round(confidence)}%
          </Tag>
          <Progress
            percent={Math.round(confidence)}
            strokeColor={colors.badge}
            trailColor="rgba(255,255,255,0.1)"
            strokeWidth={12}
            style={{ marginTop: 16 }}
            showInfo={false}
          />
          <Text style={{ color: 'rgba(255,255,255,0.6)', float: 'right', marginTop: 4 }}>{Math.round(confidence)}%</Text>
        </Card>

        <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 16 }}>
          <Title level={5} style={{ color: theme.colors.text.primary }}>Analysis Rationale</Title>
          <Paragraph style={{ color: theme.colors.text.primary }}>
            {rationale}
          </Paragraph>
        </Card>

        {(getNumericValue(data.target_price) || data.stop_loss || data.entry_price) && (
          <Row gutter={[16, 16]}>
            {data.entry_price && (
              <Col span={8}>
                <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
                  <Text style={{ color: theme.colors.text.secondary }}>Entry Price</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.primary, fontSize: 20 }}>${getNumericValue(data.entry_price)?.toFixed(2) || 'N/A'}</Text>
                  </div>
                </Card>
              </Col>
            )}
            {getNumericValue(data.target_price) && (
              <Col span={8}>
                <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
                  <Text style={{ color: theme.colors.text.secondary }}>Target Price</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.success, fontSize: 20 }}>${getNumericValue(data.target_price)?.toFixed(2)}</Text>
                  </div>
                </Card>
              </Col>
            )}
            {data.stop_loss && (
              <Col span={8}>
                <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
                  <Text style={{ color: theme.colors.text.secondary }}>Stop Loss</Text>
                  <div>
                    <Text strong style={{ color: theme.colors.danger, fontSize: 20 }}>${getNumericValue(data.stop_loss)?.toFixed(2) || 'N/A'}</Text>
                  </div>
                </Card>
              </Col>
            )}
          </Row>
        )}

        {data.key_catalysts && data.key_catalysts.length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary }}>Key Catalysts</Title>
            <Timeline>
              {data.key_catalysts.map((catalyst: string, index: number) => (
                <Timeline.Item key={index} color="green">
                  <Text style={{ color: theme.colors.text.primary }}>{catalyst}</Text>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        )}

        {data.risks && data.risks.length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary }}>Risk Factors</Title>
            <Timeline>
              {data.risks.map((risk: string, index: number) => (
                <Timeline.Item key={index} color="red">
                  <Text style={{ color: theme.colors.text.primary }}>{risk}</Text>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        )}

        {data.time_horizon && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 16 }}>
            <Text style={{ color: theme.colors.text.secondary }}>Time Horizon: </Text>
            <Tag color="blue">{data.time_horizon.replace('_', ' ').toUpperCase()}</Tag>
            {data.risk_reward_ratio && (
              <>
                <Text style={{ color: theme.colors.text.secondary, marginLeft: 16 }}>Risk/Reward Ratio: </Text>
                <Text strong style={{ color: theme.colors.primary }}>{getNumericValue(data.risk_reward_ratio)?.toFixed(2) || 'N/A'}</Text>
              </>
            )}
          </Card>
        )}
      </div>
    );
  };

  const renderInsiderAnalysis = () => {
    // Check both insider_analysis and agent_results.insider_activity
    const insiderData = result?.insider_analysis || result?.analysis?.insider_activity || result?.agent_results?.insider_activity;

    if (!insiderData) return <Text style={{ color: theme.colors.text.secondary }}>No insider analysis data available</Text>;

    const smartMoneyAnalysis = insiderData.smart_money_analysis || {};
    const smartMoneyScore = smartMoneyAnalysis.smart_money_score !== undefined ? smartMoneyAnalysis.smart_money_score : null;
    const insiderSentiment = smartMoneyAnalysis.insider_sentiment || insiderData.insider_trading?.insider_sentiment;
    const buySellRatio = smartMoneyAnalysis.insider_buy_sell_ratio !== undefined ? smartMoneyAnalysis.insider_buy_sell_ratio : insiderData.insider_activity?.insider_buy_sell_ratio;

    const institutionalOwnership = smartMoneyAnalysis.institutional_ownership_pct !== undefined ? smartMoneyAnalysis.institutional_ownership_pct : insiderData.institutional_ownership?.institutional_ownership_pct;
    const institutionalSentiment = smartMoneyAnalysis.institutional_sentiment;

    const topHolders = smartMoneyAnalysis.top_institutional_holders || [];
    const analystRatings = insiderData.analyst_ratings || {};

    return (
      <div>
        {/* Smart Money Score Alert */}
        {smartMoneyScore !== null && (
          <Alert
            type={smartMoneyScore < 3 ? 'error' : smartMoneyScore < 6 ? 'warning' : 'success'}
            message={
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 18, fontWeight: 'bold' }}>
                  🚨 SMART MONEY SCORE: {smartMoneyScore}/10
                  {smartMoneyScore < 3 && ' - SEVERE WARNING'}
                  {smartMoneyScore >= 3 && smartMoneyScore < 6 && ' - CAUTION'}
                  {smartMoneyScore >= 6 && ' - POSITIVE'}
                </span>
              </div>
            }
            description={
              <div style={{ marginTop: 8 }}>
                <div style={{
                  width: '100%',
                  height: 12,
                  background: theme.colors.background.elevated,
                  borderRadius: 6,
                  overflow: 'hidden',
                  marginTop: 8
                }}>
                  <div style={{
                    width: `${(smartMoneyScore / 10) * 100}%`,
                    height: '100%',
                    background: smartMoneyScore < 3 ? theme.colors.error : smartMoneyScore < 6 ? theme.colors.warning : theme.colors.success,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
                <Text style={{ color: theme.colors.text.secondary, marginTop: 8, display: 'block' }}>
                  {smartMoneyScore < 3 && '🔴 Insiders selling aggressively - Institutional activity neutral to negative'}
                  {smartMoneyScore >= 3 && smartMoneyScore < 6 && '⚠️ Mixed signals from smart money - Monitor closely'}
                  {smartMoneyScore >= 6 && '✅ Positive smart money activity - Insiders and institutions showing confidence'}
                </Text>
              </div>
            }
            showIcon={false}
            style={{ marginBottom: 24 }}
          />
        )}

        {/* Insider Activity Section */}
        <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 16 }}>
          <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>
            🏦 Insider Activity (Last 6 Months)
          </Title>

          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={24} sm={12}>
              <div style={{
                padding: 16,
                background: theme.colors.background.primary,
                borderRadius: 8,
                border: `1px solid ${buySellRatio === 0 ? theme.colors.error : buySellRatio > 1 ? theme.colors.success : theme.colors.border}`
              }}>
                <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Buy/Sell Ratio</Text>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                  <Text strong style={{
                    fontSize: 24,
                    color: buySellRatio === 0 ? theme.colors.error : buySellRatio > 1 ? theme.colors.success : theme.colors.warning
                  }}>
                    {buySellRatio !== undefined ? buySellRatio.toFixed(1) : 'N/A'}
                  </Text>
                  {buySellRatio === 0 && (
                    <Tag color="red">🔴 ALL SALES, NO BUYS</Tag>
                  )}
                  {buySellRatio > 0 && buySellRatio < 1 && (
                    <Tag color="orange">More Sells</Tag>
                  )}
                  {buySellRatio >= 1 && (
                    <Tag color="green">More Buys</Tag>
                  )}
                </div>
              </div>
            </Col>

            <Col xs={24} sm={12}>
              <div style={{
                padding: 16,
                background: theme.colors.background.primary,
                borderRadius: 8,
                border: `1px solid ${insiderSentiment?.toLowerCase() === 'bearish' ? theme.colors.error : insiderSentiment?.toLowerCase() === 'bullish' ? theme.colors.success : theme.colors.border}`
              }}>
                <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>Insider Sentiment</Text>
                <div style={{ marginTop: 4 }}>
                  <Tag
                    color={insiderSentiment?.toLowerCase() === 'bearish' ? 'red' : insiderSentiment?.toLowerCase() === 'bullish' ? 'green' : 'default'}
                    style={{ fontSize: 16, padding: '4px 12px' }}
                  >
                    {insiderSentiment?.toUpperCase() || 'NEUTRAL'}
                  </Tag>
                </div>
              </div>
            </Col>
          </Row>

          {/* Recent Transactions Summary */}
          {smartMoneyAnalysis.recent_activity && (
            <div style={{
              padding: 12,
              background: theme.colors.background.primary,
              borderRadius: 8,
              marginTop: 12
            }}>
              <Text style={{ color: theme.colors.text.secondary }}>
                Recent Transactions: {smartMoneyAnalysis.recent_activity}
              </Text>
            </div>
          )}
        </Card>

        {/* Institutional Ownership */}
        <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 16 }}>
          <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>
            🏛️ Institutional Ownership
          </Title>

          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Statistic
                title="Ownership Percentage"
                value={institutionalOwnership !== undefined ? institutionalOwnership.toFixed(2) : 'N/A'}
                suffix="%"
                valueStyle={{ color: theme.colors.primary, fontSize: 28 }}
              />
            </Col>
            <Col xs={24} md={12}>
              <div>
                <Text style={{ color: theme.colors.text.secondary, display: 'block', marginBottom: 8 }}>Sentiment</Text>
                <Tag
                  color={institutionalSentiment?.toLowerCase() === 'bearish' ? 'red' : institutionalSentiment?.toLowerCase() === 'bullish' ? 'green' : 'blue'}
                  style={{ fontSize: 16, padding: '4px 12px' }}
                >
                  {institutionalSentiment?.toUpperCase() || 'NEUTRAL'}
                </Tag>
              </div>
            </Col>
          </Row>

          {/* Top Institutional Holders */}
          {topHolders.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <Title level={5} style={{ color: theme.colors.text.primary, marginBottom: 12 }}>Top Holders</Title>
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                {topHolders.slice(0, 5).map((holder: any, index: number) => (
                  <div key={index} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    background: theme.colors.background.primary,
                    borderRadius: 6
                  }}>
                    <div style={{ flex: 1 }}>
                      <Text strong style={{ color: theme.colors.text.primary }}>
                        {index + 1}. {holder.name || holder.holder}
                      </Text>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Text style={{ color: theme.colors.primary, fontSize: 16, fontWeight: 'bold' }}>
                        {holder.percentage !== undefined ? holder.percentage.toFixed(2) : holder.pct?.toFixed(2) || 'N/A'}%
                      </Text>
                      <div style={{
                        width: 100,
                        height: 6,
                        background: theme.colors.background.elevated,
                        borderRadius: 3,
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${holder.percentage || holder.pct || 0}%`,
                          height: '100%',
                          background: theme.colors.primary
                        }} />
                      </div>
                    </div>
                  </div>
                ))}
              </Space>
            </div>
          )}
        </Card>

        {/* Analyst Consensus & Distribution */}
        {analystRatings && Object.keys(analystRatings).length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
            <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>
              📊 Analyst Consensus ({analystRatings.num_analysts || 'N/A'} Analysts)
            </Title>

            <Row gutter={[16, 16]}>
              <Col xs={24} md={8}>
                <Statistic
                  title="Consensus Rating"
                  value={analystRatings.analyst_rating || analystRatings.consensus || 'N/A'}
                  valueStyle={{ color: theme.colors.primary, fontSize: 24 }}
                />
              </Col>
              {analystRatings.consensus_price_target && (
                <Col xs={24} md={8}>
                  <Statistic
                    title="Price Target"
                    prefix="$"
                    value={analystRatings.consensus_price_target.toFixed(2)}
                    valueStyle={{ color: theme.colors.success, fontSize: 24 }}
                  />
                </Col>
              )}
              {analystRatings.num_analysts && (
                <Col xs={24} md={8}>
                  <Statistic
                    title="Total Analysts"
                    value={analystRatings.num_analysts}
                    valueStyle={{ color: theme.colors.text.primary, fontSize: 24 }}
                  />
                </Col>
              )}
            </Row>

            {/* Ratings Distribution Bar */}
            {(analystRatings.strong_buy !== undefined || analystRatings.buy !== undefined ||
              analystRatings.hold !== undefined || analystRatings.sell !== undefined ||
              analystRatings.strong_sell !== undefined) && (
              <div style={{ marginTop: 24 }}>
                <Title level={5} style={{ color: theme.colors.text.primary, marginBottom: 12 }}>
                  Ratings Distribution
                </Title>

                <div style={{ marginBottom: 16 }}>
                  <div style={{
                    display: 'flex',
                    height: 40,
                    borderRadius: 8,
                    overflow: 'hidden',
                    border: `1px solid ${theme.colors.border}`
                  }}>
                    {/* Strong Buy */}
                    {analystRatings.strong_buy > 0 && (
                      <div
                        style={{
                          width: `${(analystRatings.strong_buy / analystRatings.num_analysts) * 100}%`,
                          background: '#52c41a',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          transition: 'width 0.3s ease'
                        }}
                      >
                        <Text strong style={{ color: 'white', fontSize: 12 }}>
                          {analystRatings.strong_buy}
                        </Text>
                      </div>
                    )}

                    {/* Buy */}
                    {analystRatings.buy > 0 && (
                      <div
                        style={{
                          width: `${(analystRatings.buy / analystRatings.num_analysts) * 100}%`,
                          background: '#95de64',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          transition: 'width 0.3s ease'
                        }}
                      >
                        <Text strong style={{ color: 'white', fontSize: 12 }}>
                          {analystRatings.buy}
                        </Text>
                      </div>
                    )}

                    {/* Hold */}
                    {analystRatings.hold > 0 && (
                      <div
                        style={{
                          width: `${(analystRatings.hold / analystRatings.num_analysts) * 100}%`,
                          background: '#faad14',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          transition: 'width 0.3s ease'
                        }}
                      >
                        <Text strong style={{ color: 'white', fontSize: 12 }}>
                          {analystRatings.hold}
                        </Text>
                      </div>
                    )}

                    {/* Sell */}
                    {analystRatings.sell > 0 && (
                      <div
                        style={{
                          width: `${(analystRatings.sell / analystRatings.num_analysts) * 100}%`,
                          background: '#ff7875',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          transition: 'width 0.3s ease'
                        }}
                      >
                        <Text strong style={{ color: 'white', fontSize: 12 }}>
                          {analystRatings.sell}
                        </Text>
                      </div>
                    )}

                    {/* Strong Sell */}
                    {analystRatings.strong_sell > 0 && (
                      <div
                        style={{
                          width: `${(analystRatings.strong_sell / analystRatings.num_analysts) * 100}%`,
                          background: '#f5222d',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          transition: 'width 0.3s ease'
                        }}
                      >
                        <Text strong style={{ color: 'white', fontSize: 12 }}>
                          {analystRatings.strong_sell}
                        </Text>
                      </div>
                    )}
                  </div>
                </div>

                {/* Legend */}
                <Row gutter={[8, 8]} style={{ marginTop: 12 }}>
                  <Col>
                    <Tag color="#52c41a">Strong Buy: {analystRatings.strong_buy || 0}</Tag>
                  </Col>
                  <Col>
                    <Tag color="#95de64">Buy: {analystRatings.buy || 0}</Tag>
                  </Col>
                  <Col>
                    <Tag color="#faad14">Hold: {analystRatings.hold || 0}</Tag>
                  </Col>
                  <Col>
                    <Tag color="#ff7875">Sell: {analystRatings.sell || 0}</Tag>
                  </Col>
                  <Col>
                    <Tag color="#f5222d">Strong Sell: {analystRatings.strong_sell || 0}</Tag>
                  </Col>
                </Row>

                {/* Consensus Interpretation */}
                <div style={{
                  marginTop: 16,
                  padding: 12,
                  background: theme.colors.background.primary,
                  borderRadius: 8,
                  borderLeft: `3px solid ${
                    (analystRatings.hold || 0) > (analystRatings.num_analysts || 1) * 0.4 ? theme.colors.warning :
                    (analystRatings.strong_buy + analystRatings.buy || 0) > (analystRatings.num_analysts || 1) * 0.5 ? theme.colors.success :
                    theme.colors.error
                  }`
                }}>
                  <Text style={{ color: theme.colors.text.secondary }}>
                    <strong>Consensus: </strong>
                    {analystRatings.analyst_rating || analystRatings.consensus || 'HOLD'}
                    {analystRatings.hold && analystRatings.num_analysts &&
                      ` (${((analystRatings.hold / analystRatings.num_analysts) * 100).toFixed(0)}% of analysts)`
                    }
                  </Text>
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    );
  };

  // Data Quality & Citations Footer Component
  const renderDataQualityCitations = (agentName: string, agentData: any) => {
    const dataQuality = agentData?.data_quality;
    const citations = agentData?.citations || [];

    // Don't render if no data quality and no citations
    if (!dataQuality && citations.length === 0) return null;

    return (
      <div style={{ marginTop: 32, paddingTop: 24, borderTop: `1px solid ${theme.colors.border}` }}>
        {/* Data Quality */}
        {dataQuality && dataQuality.overall_score !== undefined && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary, marginBottom: 16 }}>
              ⭐ Data Quality - {agentName}
            </Title>

            <Row gutter={[16, 16]}>
              <Col xs={24} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    width: 100,
                    height: 100,
                    margin: '0 auto',
                    borderRadius: '50%',
                    background: `conic-gradient(
                      ${dataQuality.overall_score >= 80 ? theme.colors.success :
                        dataQuality.overall_score >= 60 ? theme.colors.warning : theme.colors.error}
                      ${dataQuality.overall_score}%,
                      ${theme.colors.background.primary} 0
                    )`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <div style={{
                      width: '75%',
                      height: '75%',
                      borderRadius: '50%',
                      background: theme.colors.background.elevated,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexDirection: 'column'
                    }}>
                      <Text strong style={{
                        fontSize: 20,
                        color: dataQuality.overall_score >= 80 ? theme.colors.success :
                               dataQuality.overall_score >= 60 ? theme.colors.warning : theme.colors.error
                      }}>
                        {dataQuality.overall_score?.toFixed(0)}
                      </Text>
                      <Text style={{ fontSize: 10, color: theme.colors.text.secondary }}>/100</Text>
                    </div>
                  </div>
                  <Tag
                    color={dataQuality.overall_score >= 80 ? 'green' :
                           dataQuality.overall_score >= 60 ? 'orange' : 'red'}
                    style={{ marginTop: 8 }}
                  >
                    {dataQuality.overall_score >= 80 ? 'High Quality' :
                     dataQuality.overall_score >= 60 ? 'Medium Quality' : 'Low Quality'}
                  </Tag>
                </div>
              </Col>

              <Col xs={24} md={18}>
                <Space direction="vertical" style={{ width: '100%' }} size="small">
                  {dataQuality.total_fields !== undefined && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: theme.colors.background.primary, borderRadius: 6 }}>
                      <Text style={{ color: theme.colors.text.secondary }}>Total Fields</Text>
                      <Text strong style={{ color: theme.colors.text.primary }}>{dataQuality.total_fields}</Text>
                    </div>
                  )}
                  {dataQuality.avg_confidence !== undefined && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: theme.colors.background.primary, borderRadius: 6 }}>
                      <Text style={{ color: theme.colors.text.secondary }}>Average Confidence</Text>
                      <Text strong style={{ color: theme.colors.primary }}>{(dataQuality.avg_confidence * 100).toFixed(0)}%</Text>
                    </div>
                  )}
                  {dataQuality.sources_count !== undefined && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: theme.colors.background.primary, borderRadius: 6 }}>
                      <Text style={{ color: theme.colors.text.secondary }}>Data Sources</Text>
                      <Text strong style={{ color: theme.colors.text.primary }}>{dataQuality.sources_count}</Text>
                    </div>
                  )}
                  {dataQuality.cache_hit !== undefined && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: theme.colors.background.primary, borderRadius: 6 }}>
                      <Text style={{ color: theme.colors.text.secondary }}>Cache Status</Text>
                      <Tag color={dataQuality.cache_hit ? 'green' : 'blue'}>
                        {dataQuality.cache_hit ? 'Cached' : 'Fresh'}
                      </Tag>
                    </div>
                  )}
                </Space>
              </Col>
            </Row>
          </Card>
        )}

        {/* Citations */}
        {citations.length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Title level={5} style={{ color: theme.colors.text.primary, margin: 0 }}>
                📚 Data Sources & Citations ({citations.length})
              </Title>
            </div>

            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {citations.map((citation: any, index: number) => (
                <div
                  key={index}
                  style={{
                    padding: 12,
                    background: theme.colors.background.primary,
                    borderRadius: 8,
                    borderLeft: `3px solid ${
                      (citation.relevance_score || citation.relevance) >= 0.8 ? theme.colors.success :
                      (citation.relevance_score || citation.relevance) >= 0.6 ? theme.colors.warning : theme.colors.primary
                    }`
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                    <div style={{ flex: 1 }}>
                      <Text strong style={{ color: theme.colors.text.primary, fontSize: 14 }}>
                        {citation.title || `Source ${index + 1}`}
                      </Text>
                      {citation.url && (
                        <div style={{ marginTop: 4 }}>
                          <a
                            href={citation.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: theme.colors.primary, fontSize: 12 }}
                          >
                            {citation.url.replace(/^https?:\/\//, '').substring(0, 50)}...
                          </a>
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: 8, marginLeft: 16 }}>
                      <Tag color={(citation.relevance_score || citation.relevance) >= 0.8 ? 'green' : (citation.relevance_score || citation.relevance) >= 0.6 ? 'orange' : 'blue'}>
                        Relevance: {(citation.relevance_score || citation.relevance) != null ? ((citation.relevance_score || citation.relevance) * 100).toFixed(0) : 'N/A'}%
                      </Tag>
                      {citation.reliability && (
                        <Tag color={citation.reliability === 'high' ? 'green' : citation.reliability === 'medium' ? 'orange' : 'default'}>
                          {citation.reliability.toUpperCase()}
                        </Tag>
                      )}
                    </div>
                  </div>

                  {citation.content && (
                    <Text style={{ color: theme.colors.text.secondary, fontSize: 12, display: 'block', marginTop: 8 }}>
                      {citation.content.substring(0, 200)}...
                    </Text>
                  )}
                </div>
              ))}
            </Space>
          </Card>
        )}
      </div>
    );
  };

  const renderCatalystCalendar = () => {
    if (!result?.catalyst_calendar) {
      return (
        <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, textAlign: 'center', padding: 48 }}>
          <ClockCircleOutlined style={{ fontSize: 48, color: theme.colors.text.muted, marginBottom: 16 }} />
          <Title level={4} style={{ color: theme.colors.text.primary }}>No Catalyst Calendar Data</Title>
          <Paragraph style={{ color: theme.colors.text.secondary }}>
            Catalyst calendar information is not available for this analysis.
          </Paragraph>
        </Card>
      );
    }

    const catalysts = result.catalyst_calendar;
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const impactColorMap: any = {
      high: theme.colors.danger,
      medium: theme.colors.warning,
      low: theme.colors.text.secondary
    };

    return (
      <div>
        {/* Next Catalyst Highlight */}
        {catalysts.next_catalyst && (
          <Card style={{
            background: `linear-gradient(135deg, ${theme.colors.background.elevated} 0%, ${theme.colors.background.secondary} 100%)`,
            border: `2px solid ${theme.colors.primary}`,
            marginBottom: 24
          }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
              <ThunderboltOutlined style={{ fontSize: 32, color: theme.colors.primary, marginRight: 16 }} />
              <div>
                <Title level={4} style={{ color: theme.colors.text.primary, margin: 0 }}>Next Catalyst</Title>
                <Text style={{ color: theme.colors.text.secondary }}>{catalysts.next_catalyst.days_until} days until</Text>
              </div>
            </div>
            <Title level={5} style={{ color: theme.colors.text.primary }}>{catalysts.next_catalyst.title}</Title>
            <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
              <Tag color={catalysts.next_catalyst.confirmed ? 'success' : 'default'}>
                {catalysts.next_catalyst.confirmed ? 'Confirmed' : 'Unconfirmed'}
              </Tag>
              <Tag color={catalysts.next_catalyst.impact === 'high' ? 'error' : catalysts.next_catalyst.impact === 'medium' ? 'warning' : 'default'}>
                {catalysts.next_catalyst.impact?.toUpperCase()} Impact
              </Tag>
              <Text style={{ color: theme.colors.text.secondary }}>{catalysts.next_catalyst.date}</Text>
            </div>
          </Card>
        )}

        {/* Earnings Info */}
        {catalysts.earnings && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary, display: 'flex', alignItems: 'center', gap: 8 }}>
              <LineChartOutlined /> Earnings
            </Title>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginTop: 16 }}>
              <div>
                <Text style={{ color: theme.colors.text.secondary, display: 'block' }}>Next Earnings Date</Text>
                <Text strong style={{ color: theme.colors.text.primary, fontSize: 18 }}>{catalysts.earnings.next_earnings_date || 'TBD'}</Text>
              </div>
              <div>
                <Text style={{ color: theme.colors.text.secondary, display: 'block' }}>Days Until</Text>
                <Text strong style={{ color: theme.colors.primary, fontSize: 18 }}>{catalysts.earnings.days_until_earnings}</Text>
              </div>
              <div>
                <Text style={{ color: theme.colors.text.secondary, display: 'block' }}>Status</Text>
                <Tag color={catalysts.earnings.earnings_confirmed ? 'success' : 'default'} style={{ marginTop: 4 }}>
                  {catalysts.earnings.earnings_confirmed ? 'Confirmed' : 'Unconfirmed'}
                </Tag>
              </div>
            </div>
          </Card>
        )}

        {/* Prioritized Catalysts */}
        {catalysts.prioritized_catalysts && catalysts.prioritized_catalysts.length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary }}>All Upcoming Catalysts ({catalysts.catalyst_count || catalysts.prioritized_catalysts.length})</Title>
            <Timeline style={{ marginTop: 24 }}>
              {catalysts.prioritized_catalysts.map((event: any, index: number) => (
                <Timeline.Item
                  key={index}
                  color={event.impact === 'high' ? 'red' : event.impact === 'medium' ? 'orange' : 'blue'}
                  dot={event.type === 'earnings' ? <LineChartOutlined /> : event.type === 'product_launch' ? <RocketOutlined /> : <ClockCircleOutlined />}
                >
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <Text strong style={{ color: theme.colors.text.primary, fontSize: 16 }}>{event.title}</Text>
                      <Tag color={event.impact === 'high' ? 'error' : event.impact === 'medium' ? 'warning' : 'default'} style={{ marginLeft: 8 }}>
                        {event.impact?.toUpperCase()}
                      </Tag>
                    </div>
                    <Text style={{ color: theme.colors.text.secondary, display: 'block', marginBottom: 4 }}>
                      {event.date} {event.days_until && `• ${event.days_until} days`}
                    </Text>
                    <Tag color="blue" style={{ marginTop: 4 }}>{event.type?.replace('_', ' ').toUpperCase()}</Tag>
                    {event.source && (
                      <div style={{ marginTop: 8 }}>
                        <a href={event.source} target="_blank" rel="noopener noreferrer" style={{ color: theme.colors.primary, fontSize: 12 }}>
                          <LinkOutlined /> View Source
                        </a>
                      </div>
                    )}
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        )}
      </div>
    );
  };

  const renderMacroAnalysis = () => {
    if (!result?.macro_analysis) {
      return (
        <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, textAlign: 'center', padding: 48 }}>
          <DashboardOutlined style={{ fontSize: 48, color: theme.colors.text.muted, marginBottom: 16 }} />
          <Title level={4} style={{ color: theme.colors.text.primary }}>No Macro Analysis Data</Title>
          <Paragraph style={{ color: theme.colors.text.secondary }}>
            Macroeconomic analysis information is not available for this analysis.
          </Paragraph>
        </Card>
      );
    }

    const macro = result.macro_analysis;
    const regimeColor = macro.market_regime?.regime === 'bull' ? theme.colors.success :
                        macro.market_regime?.regime === 'bear' ? theme.colors.danger :
                        theme.colors.warning;

    return (
      <div>
        {/* Market Regime */}
        {macro.market_regime && (
          <Card style={{
            background: `linear-gradient(135deg, ${theme.colors.background.elevated} 0%, ${theme.colors.background.secondary} 100%)`,
            border: `2px solid ${regimeColor}`,
            marginBottom: 24
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
              <div style={{
                background: regimeColor,
                borderRadius: '50%',
                width: 64,
                height: 64,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {macro.market_regime.regime === 'bull' ? '📈' : macro.market_regime.regime === 'bear' ? '📉' : '➡️'}
              </div>
              <div>
                <Title level={4} style={{ color: theme.colors.text.primary, margin: 0 }}>
                  {macro.market_regime.regime?.toUpperCase()} Market
                </Title>
                <Text style={{ color: theme.colors.text.secondary }}>
                  Fed Policy: {macro.market_regime.fed_policy?.toUpperCase()} • Score: {(macro.market_regime.score * 100).toFixed(0)}%
                </Text>
              </div>
            </div>
          </Card>
        )}

        {/* Sector Analysis */}
        {macro.sector_analysis && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary, display: 'flex', alignItems: 'center', gap: 8 }}>
              <LineChartOutlined /> Sector Analysis
            </Title>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16, marginTop: 16 }}>
              <div>
                <Text style={{ color: theme.colors.text.secondary, display: 'block' }}>Sector Trend</Text>
                <Tag color={macro.sector_analysis.trend === 'outperforming' ? 'success' : 'error'} style={{ marginTop: 4, fontSize: 14 }}>
                  {macro.sector_analysis.trend?.toUpperCase()}
                </Tag>
              </div>
              <div>
                <Text style={{ color: theme.colors.text.secondary, display: 'block' }}>Sector Rotation</Text>
                <Tag color={macro.sector_analysis.rotation ? 'warning' : 'default'} style={{ marginTop: 4, fontSize: 14 }}>
                  {macro.sector_analysis.rotation ? 'ACTIVE' : 'STABLE'}
                </Tag>
              </div>
            </div>
          </Card>
        )}

        {/* Economic Indicators */}
        {macro.economic_indicators && macro.economic_indicators.length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary }}>Economic Indicators</Title>
            <div style={{ marginTop: 16 }}>
              {macro.economic_indicators.map((indicator: string, index: number) => (
                <Tag key={index} color="blue" style={{ margin: 4 }}>
                  {indicator}
                </Tag>
              ))}
            </div>
          </Card>
        )}

        {/* Catalysts */}
        {macro.catalysts && macro.catalysts.length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary, display: 'flex', alignItems: 'center', gap: 8 }}>
              <ThunderboltOutlined /> Macro Catalysts
            </Title>
            <List
              dataSource={macro.catalysts}
              renderItem={(catalyst: string) => (
                <List.Item>
                  <Text style={{ color: theme.colors.text.primary }}>✓ {catalyst}</Text>
                </List.Item>
              )}
            />
          </Card>
        )}

        {/* Headwinds */}
        {macro.headwinds && macro.headwinds.length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary, display: 'flex', alignItems: 'center', gap: 8 }}>
              <SafetyOutlined /> Macro Headwinds
            </Title>
            <Timeline>
              {macro.headwinds.map((headwind: string, index: number) => (
                <Timeline.Item key={index} color="red">
                  <Text style={{ color: theme.colors.text.primary }}>{headwind}</Text>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        )}

        {/* News Sources */}
        {macro.macro_data?.sources && macro.macro_data.sources.length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}` }}>
            <Title level={5} style={{ color: theme.colors.text.primary }}>Recent Macro News ({macro.macro_data.sources.length})</Title>
            {macro.macro_data.search_summary && (
              <Alert
                message={macro.macro_data.search_summary}
                type="info"
                style={{ marginBottom: 16 }}
              />
            )}
            <List
              dataSource={macro.macro_data.sources.slice(0, 5)}
              renderItem={(source: any) => (
                <List.Item>
                  <div style={{ width: '100%' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <Text strong style={{ color: theme.colors.text.primary }}>{source.title}</Text>
                      <Tag color="blue">{(source.score * 100).toFixed(0)}% relevance</Tag>
                    </div>
                    <Text style={{ color: theme.colors.text.secondary, display: 'block', marginBottom: 8 }}>
                      {source.content?.substring(0, 200)}...
                    </Text>
                    <a href={source.url} target="_blank" rel="noopener noreferrer" style={{ color: theme.colors.primary, fontSize: 12 }}>
                      <LinkOutlined /> Read full article
                    </a>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        )}
      </div>
    );
  };

  const renderChartAnalytics = () => {
    // Get chart analytics data from backend - ACTUAL API structure
    const chartData = result?.chart_analytics || result?.analysis?.chart_analytics;
    if (!chartData) {
      return (
        <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, textAlign: 'center', padding: 48 }}>
          <LineChartOutlined style={{ fontSize: 48, color: theme.colors.text.muted, marginBottom: 16 }} />
          <Title level={4} style={{ color: theme.colors.text.primary }}>No Chart Analytics Data</Title>
          <Paragraph style={{ color: theme.colors.text.secondary }}>
            Chart analytics information is not available for this analysis.
          </Paragraph>
        </Card>
      );
    }

    // Extract chart data from backend
    const priceData = chartData?.chart_data?.price_charts?.candlestick?.data;
    const technicalOverlays = chartData?.chart_data?.technical_overlays;
    const indicatorData = {
      rsi: chartData?.chart_data?.indicator_charts?.rsi?.data,
      macd: chartData?.chart_data?.indicator_charts?.macd?.data,
      bollinger_bands: chartData?.chart_data?.indicator_charts?.bollinger_bands?.data
    };
    const supportResistance = chartData?.support_resistance ? {
      support: chartData.support_resistance.support_levels?.map((s: any) => s.level).filter((p: number) => p > 0),
      resistance: chartData.support_resistance.resistance_levels?.map((r: any) => r.level).filter((p: number) => p > 0)
    } : undefined;
    const patterns = chartData?.pattern_analysis?.patterns?.map((p: any) => ({
      date: `${Math.round((p.confidence || 0) * 100)}% confidence`,  // Show confidence instead of N/A date
      type: p.pattern || 'Unknown',
      description: p.implication || 'Pattern detected'  // Use 'implication' instead of 'signal'
    }));

    return (
      <div>
        {/* Professional Trading Chart */}
        {priceData && (
          <ProfessionalTradingChart
            data={priceData}
            symbol={result?.analysis?.market_data?.symbol || 'UNKNOWN'}
            technicalOverlays={technicalOverlays}
            indicatorData={indicatorData}
            supportResistance={supportResistance}
            patterns={patterns}
          />
        )}

        {/* Expert Insights (replaces summary) */}
        {chartData.expert_insights && chartData.expert_insights.length > 0 && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginBottom: 16 }}>
            <Title level={4} style={{ color: theme.colors.text.primary }}>
              <LineChartOutlined style={{ marginRight: 8 }} />
              Chart Insights
            </Title>
            <List
              dataSource={chartData.expert_insights}
              renderItem={(insight: string) => (
                <List.Item>
                  <Text style={{ color: theme.colors.text.primary }}>{insight}</Text>
                </List.Item>
              )}
            />
          </Card>
        )}

        {/* Pattern Analysis */}
        {chartData.pattern_analysis && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary }}>Pattern Analysis</Title>
            <Row gutter={[16, 16]}>
              {chartData.pattern_analysis.patterns && chartData.pattern_analysis.patterns.map((pattern: any, index: number) => (
                <Col key={index} xs={24} sm={12} md={8}>
                  <Card size="small" style={{ background: theme.colors.background.secondary, border: `1px solid ${theme.colors.border}` }}>
                    <Text strong style={{ color: pattern.type === 'bullish' ? theme.colors.success : pattern.type === 'bearish' ? theme.colors.error : theme.colors.text.primary }}>
                      {pattern.pattern}
                    </Text>
                    <br />
                    <Tag color={pattern.type === 'bullish' ? 'green' : pattern.type === 'bearish' ? 'red' : 'default'} style={{ marginTop: 8 }}>
                      {pattern.type?.toUpperCase()}
                    </Tag>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12, marginTop: 8 }}>
                      {pattern.implication} ({Math.round((pattern.confidence || 0) * 100)}% confidence)
                    </Text>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        )}

        {/* Support & Resistance */}
        {chartData.support_resistance && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary }}>Support & Resistance Levels</Title>
            <Row gutter={[16, 16]}>
              {chartData.support_resistance.support_levels && chartData.support_resistance.support_levels.length > 0 && (
                <Col xs={24} md={12}>
                  <Text strong style={{ color: theme.colors.success }}>Support Levels:</Text>
                  <List
                    size="small"
                    dataSource={chartData.support_resistance.support_levels.slice(0, 3)}
                    renderItem={(level: any) => (
                      <List.Item>
                        <Tag color="green">{level.type}</Tag>
                        <Text style={{ color: theme.colors.text.secondary }}>
                          ${level.level?.toFixed(2)}
                        </Text>
                        <Tag color={level.strength === 'strong' ? 'green' : level.strength === 'moderate' ? 'orange' : 'default'} style={{ marginLeft: 8 }}>
                          {level.strength}
                        </Tag>
                      </List.Item>
                    )}
                  />
                </Col>
              )}
              {chartData.support_resistance.resistance_levels && chartData.support_resistance.resistance_levels.length > 0 && (
                <Col xs={24} md={12}>
                  <Text strong style={{ color: theme.colors.error }}>Resistance Levels:</Text>
                  <List
                    size="small"
                    dataSource={chartData.support_resistance.resistance_levels.slice(0, 3)}
                    renderItem={(level: any) => (
                      <List.Item>
                        <Tag color="red">{level.type}</Tag>
                        <Text style={{ color: theme.colors.text.secondary }}>
                          ${level.level?.toFixed(2)}
                        </Text>
                        <Tag color={level.strength === 'strong' ? 'red' : level.strength === 'moderate' ? 'orange' : 'default'} style={{ marginLeft: 8 }}>
                          {level.strength}
                        </Tag>
                      </List.Item>
                    )}
                  />
                </Col>
              )}
            </Row>
          </Card>
        )}

        {/* Multi-Timeframe Analysis */}
        {chartData.multi_timeframe && (
          <Card style={{ background: theme.colors.background.elevated, border: `1px solid ${theme.colors.border}`, marginTop: 16 }}>
            <Title level={5} style={{ color: theme.colors.text.primary }}>Multi-Timeframe Trends</Title>
            <Row gutter={[16, 16]}>
              {Object.entries(chartData.multi_timeframe).map(([timeframe, data]: [string, any]) => (
                <Col key={timeframe} xs={12} sm={8} md={6}>
                  <Card size="small" style={{ background: theme.colors.background.secondary, border: `1px solid ${theme.colors.border}` }}>
                    <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>{timeframe.toUpperCase()}</Text>
                    <br />
                    <Tag color={data.trend === 'bullish' ? 'green' : data.trend === 'bearish' ? 'red' : 'default'}>
                      {data.trend?.toUpperCase()}
                    </Tag>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        )}
      </div>
    );
  };

  return (
    <div style={{
      background: theme.colors.background.primary,
      minHeight: '100%'
    }}>
      {!loading && !result && !error && (
        <div style={{
          padding: isMobile ? '16px' : isTablet ? '24px' : '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 'calc(100vh - 72px)'
        }}>
          <Card style={{
            background: theme.colors.background.elevated,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: 20,
            textAlign: 'center',
            padding: isMobile ? '32px 24px' : isTablet ? '40px 32px' : '48px 40px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
            maxWidth: 1200,
            width: '100%'
          }}>
            {/* Hero Section */}
            <div style={{ marginBottom: isMobile ? 32 : 40 }}>
              <div style={{
                width: isMobile ? 64 : 80,
                height: isMobile ? 64 : 80,
                margin: '0 auto 20px',
                borderRadius: '50%',
                background: `linear-gradient(135deg, ${theme.colors.primary} 0%, ${theme.colors.success} 100%)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: theme.shadows.cyanGlow,
              }}>
                <RocketOutlined style={{ fontSize: isMobile ? 32 : 40, color: '#000' }} />
              </div>

              <Title level={2} style={{
                color: theme.colors.text.primary,
                marginBottom: 12,
                fontSize: isMobile ? 22 : 28,
                fontWeight: 700
              }}>
                AI-Powered Stock Research
              </Title>

              <Text style={{
                color: theme.colors.text.secondary,
                fontSize: isMobile ? 14 : 15,
                display: 'block',
                maxWidth: 500,
                margin: '0 auto',
                lineHeight: 1.5
              }}>
                14 specialized AI agents analyze markets, financials, sentiment, and risks to deliver institutional-grade insights
              </Text>
            </div>

            {/* Feature Cards Grid */}
            <Row gutter={[16, 16]} style={{ marginBottom: isMobile ? 32 : 40 }}>
              <Col xs={12} sm={12} md={6}>
                <Card
                  hoverable
                  style={{
                    background: theme.colors.background.secondary,
                    border: `1px solid ${theme.colors.border}`,
                    borderRadius: 12,
                    height: '100%',
                    transition: 'all 0.3s ease'
                  }}
                  bodyStyle={{ padding: isMobile ? 16 : 20 }}
                >
                  <LineChartOutlined style={{ fontSize: isMobile ? 32 : 36, color: theme.colors.primary, marginBottom: 8 }} />
                  <Title level={5} style={{ color: theme.colors.text.primary, marginBottom: 4, fontSize: isMobile ? 14 : 15 }}>Market Data</Title>
                  <Text style={{ color: theme.colors.text.muted, fontSize: isMobile ? 11 : 12 }}>Real-time prices & trends</Text>
                </Card>
              </Col>
              <Col xs={12} sm={12} md={6}>
                <Card
                  hoverable
                  style={{
                    background: theme.colors.background.secondary,
                    border: `1px solid ${theme.colors.border}`,
                    borderRadius: 12,
                    height: '100%',
                    transition: 'all 0.3s ease'
                  }}
                  bodyStyle={{ padding: isMobile ? 16 : 20 }}
                >
                  <TeamOutlined style={{ fontSize: isMobile ? 32 : 36, color: theme.colors.success, marginBottom: 8 }} />
                  <Title level={5} style={{ color: theme.colors.text.primary, marginBottom: 4, fontSize: isMobile ? 14 : 15 }}>Fundamentals</Title>
                  <Text style={{ color: theme.colors.text.muted, fontSize: isMobile ? 11 : 12 }}>Financial health metrics</Text>
                </Card>
              </Col>
              <Col xs={12} sm={12} md={6}>
                <Card
                  hoverable
                  style={{
                    background: theme.colors.background.secondary,
                    border: `1px solid ${theme.colors.border}`,
                    borderRadius: 12,
                    height: '100%',
                    transition: 'all 0.3s ease'
                  }}
                  bodyStyle={{ padding: isMobile ? 16 : 20 }}
                >
                  <HeartOutlined style={{ fontSize: isMobile ? 32 : 36, color: theme.colors.danger, marginBottom: 8 }} />
                  <Title level={5} style={{ color: theme.colors.text.primary, marginBottom: 4, fontSize: isMobile ? 14 : 15 }}>Sentiment</Title>
                  <Text style={{ color: theme.colors.text.muted, fontSize: isMobile ? 11 : 12 }}>News & social analysis</Text>
                </Card>
              </Col>
              <Col xs={12} sm={12} md={6}>
                <Card
                  hoverable
                  style={{
                    background: theme.colors.background.secondary,
                    border: `1px solid ${theme.colors.border}`,
                    borderRadius: 12,
                    height: '100%',
                    transition: 'all 0.3s ease'
                  }}
                  bodyStyle={{ padding: isMobile ? 16 : 20 }}
                >
                  <SafetyOutlined style={{ fontSize: isMobile ? 32 : 36, color: theme.colors.warning, marginBottom: 8 }} />
                  <Title level={5} style={{ color: theme.colors.text.primary, marginBottom: 4, fontSize: isMobile ? 14 : 15 }}>Risk Analysis</Title>
                  <Text style={{ color: theme.colors.text.muted, fontSize: isMobile ? 11 : 12 }}>Volatility & exposure</Text>
                </Card>
              </Col>
            </Row>

            {/* CTA Section */}
            <div style={{
              padding: isMobile ? '24px 20px' : '28px 24px',
              background: `linear-gradient(135deg, ${theme.colors.background.secondary} 0%, ${theme.colors.background.primary} 100%)`,
              borderRadius: 12,
              border: `1px solid ${theme.colors.border}`
            }}>
              <Button
                type="primary"
                size="large"
                onClick={startDeepAnalysis}
                icon={<ThunderboltOutlined />}
                style={{
                  background: theme.colors.gradient.primary,
                  borderColor: theme.colors.primary,
                  height: isMobile ? 48 : 52,
                  fontSize: isMobile ? 16 : 17,
                  fontWeight: 600,
                  minWidth: isMobile ? 240 : 260,
                  boxShadow: theme.shadows.cyanGlow,
                  borderRadius: 10,
                }}
              >
                Start Deep Analysis
              </Button>
              <div style={{ marginTop: 12 }}>
                <Text style={{ color: theme.colors.text.muted, fontSize: isMobile ? 12 : 13 }}>
                  <ClockCircleOutlined /> Analysis completes in 2-3 minutes
                </Text>
              </div>
            </div>
          </Card>
        </div>
      )}

      {loading && (
        <div style={{
          padding: isMobile ? '16px' : isTablet ? '24px' : '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 'calc(100vh - 72px)'
        }}>
          <Card
            style={{
              background: theme.colors.background.elevated,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: 20,
              padding: isMobile ? '32px 24px' : '48px 40px',
              maxWidth: isMobile ? '100%' : isTablet ? 800 : 1200,
              width: '100%',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
            }}
          >
            {/* Header with spinner and title */}
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <Spin size="large" indicator={<LoadingOutlined style={{ fontSize: 56, color: theme.colors.primary }} spin />} />
              <Title level={2} style={{
                color: theme.colors.text.primary,
                marginTop: 24,
                marginBottom: 8,
                fontSize: isMobile ? 24 : 28
              }}>
                Analyzing {symbol}
              </Title>
              <Text style={{ color: theme.colors.text.secondary, fontSize: 15 }}>
                {currentStage}
              </Text>
            </div>

            {/* Progress Bar */}
            <Progress
              percent={Math.round(progress)}
              status="active"
              strokeColor={{
                '0%': theme.colors.primary,
                '100%': theme.colors.success,
              }}
              strokeWidth={12}
              style={{ marginBottom: 32 }}
            />

            {/* Agent Execution Timeline */}
            <Card
              style={{
                background: theme.colors.background.secondary,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: 12
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
                <RocketOutlined style={{ fontSize: 20, color: theme.colors.primary }} />
                <Text style={{ color: theme.colors.text.primary, fontWeight: 600, fontSize: 16 }}>
                  Agent Execution
                </Text>
              </div>

              <Timeline>
                {(() => {
                  console.log('🔍 Rendering timeline with agentProgress.length:', agentProgress.length, agentProgress);
                  return agentProgress.length === 0 ? (
                    <Timeline.Item color="blue" dot={<LoadingOutlined />}>
                      <Text style={{ color: theme.colors.text.secondary }}>Initializing agents...</Text>
                    </Timeline.Item>
                  ) : (
                    agentProgress.map((agent, index) => (
                    <Timeline.Item
                      key={index}
                      color={agent.status === 'completed' ? 'green' : agent.status === 'running' ? 'blue' : 'gray'}
                      dot={agent.status === 'running' ? <LoadingOutlined /> : agent.status === 'completed' ? <CheckCircleOutlined /> : <ClockCircleOutlined />}
                    >
                      <div>
                        <Text strong style={{ color: theme.colors.text.primary, fontSize: 14 }}>
                          {agent.message}
                        </Text>
                        <br />
                        <Text style={{ color: theme.colors.text.muted, fontSize: 12 }}>
                          {agent.agent} • {agent.status} • {agent.progress}%
                        </Text>
                      </div>
                    </Timeline.Item>
                  ))
                  );
                })()}
              </Timeline>
            </Card>
          </Card>
        </div>
      )}


      {error && (
        <div style={{
          padding: isMobile ? '24px 12px' : isTablet ? '32px 16px' : '48px 24px'
        }}>
          <Alert
            message="Analysis Error"
            description={error}
            type="error"
            showIcon
            closable
            style={{ marginBottom: 24 }}
          />
        </div>
      )}

      {result && (
        <div style={{
          maxWidth: '1400px',
          margin: '0 auto',
          padding: isMobile ? '24px 12px' : isTablet ? '32px 16px' : '48px 24px',
          width: '100%',
          boxSizing: 'border-box'
        }}>
        <>
          {/* Executive Summary Component - Above Fold */}
          <ExecutiveSummary
            analysisData={{
              symbol: result.symbols?.[0] || symbol,
              analysis: {
                market_data: { [result.symbols?.[0] || symbol]: result.market_data || {} },
                key_insights: result.recommendations?.key_catalysts || [],
                risks: result.recommendations?.risks || []
              },
              confidence_scores: {
                overall: result.recommendations?.confidence || 0.7,
                fundamental: 0.75,
                technical: 0.7,
                sentiment: 0.8
              }
            }}
            valuation={{
              price_target: {
                price_target: Number(result.recommendations?.target_price) || (result.market_data?.price * 1.1) || 0,
                upside: result.recommendations?.target_price && result.market_data?.price
                  ? ((Number(result.recommendations.target_price) - result.market_data.price) / result.market_data.price * 100)
                  : 10,
                confidence: Number(result.recommendations?.confidence) || 0.7,
                target_range: {
                  low: result.recommendations?.target_price ? Number(result.recommendations.target_price) * 0.9 : 0,
                  high: result.recommendations?.target_price ? Number(result.recommendations.target_price) * 1.1 : 0
                }
              },
              dcf_valuation: result.fundamental_analysis?.fundamental_data?.valuation?.dcf_valuation || {
                dcf_price: result.market_data?.price || 0,
                wacc: 0.1
              },
              comparative_valuation: result.fundamental_analysis?.fundamental_data?.valuation?.comparative_valuation || {
                comparative_price: result.market_data?.price || 0,
                pe_ratio: result.market_data?.pe_ratio || 'N/A',
                valuation_rating: 'Fairly Valued'
              },
              analyst_targets: result.sentiment_analysis?.analyst_targets || {
                analyst_consensus: result.recommendations?.action || 'Hold',
                target_mean: result.recommendations?.target_price || 0,
                upside_potential: result.recommendations?.target_price && result.market_data?.price
                  ? ((result.recommendations.target_price - result.market_data.price) / result.market_data.price * 100)
                  : 0,
                number_of_analysts: 0
              }
            }}
          />

          {result.executive_summary && (
            <Card
              style={{
                background: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                marginBottom: 24,
                marginTop: 24
              }}
            >
              <Title level={4} style={{ color: theme.colors.text.primary }}>
                <CheckCircleOutlined style={{ color: theme.colors.success, marginRight: 8 }} />
                Analysis Summary
              </Title>
              <Paragraph style={{
                color: theme.colors.text.primary,
                fontSize: 16,
                whiteSpace: 'normal',
                wordWrap: 'break-word',
                overflowWrap: 'break-word',
                maxWidth: '100%'
              }}>
                {result.executive_summary}
              </Paragraph>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Tooltip title={`Analysis completed in ${result.execution_time?.toFixed(2)} seconds`}>
                  <Text style={{ color: theme.colors.text.secondary }}>
                    <ClockCircleOutlined /> Completed in {result.execution_time?.toFixed(2)}s
                  </Text>
                </Tooltip>
                {result.synthesis?.data_quality && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Badge
                      count={result.synthesis.data_quality.overall_grade}
                      style={{
                        backgroundColor:
                          result.synthesis.data_quality.overall_grade === 'A' ? '#52c41a' :
                          result.synthesis.data_quality.overall_grade === 'B' ? '#faad14' :
                          result.synthesis.data_quality.overall_grade === 'C' ? '#ff7a45' :
                          '#f5222d',
                        color: '#fff',
                        fontSize: '14px',
                        padding: '0 8px',
                        height: '24px',
                        lineHeight: '24px'
                      }}
                    />
                    <Text style={{ color: theme.colors.text.secondary, fontSize: '12px' }}>
                      Data Quality: {result.synthesis.data_quality.overall_score.toFixed(1)}/100
                    </Text>
                  </div>
                )}
              </div>
            </Card>
          )}

          <Tabs
            className="high-contrast-tabs"
            defaultActiveKey="overview"
            style={{
              background: theme.colors.background.elevated,
              padding: 16,
              borderRadius: 12
            }}
            tabBarStyle={{
              background: theme.colors.background.elevated,
              marginBottom: 16,
              paddingTop: 0,
              borderBottom: `2px solid ${theme.colors.border}`
            }}
          >
            <TabPane
              tab={
                <span>
                  <DashboardOutlined />
                  Overview
                </span>
              }
              key="overview"
            >
              <div style={{ maxWidth: '100%', overflowX: 'hidden', padding: '0 4px' }}>
                {renderOverview()}
              </div>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <LineChartOutlined />
                  Market Data
                </span>
              }
              key="1"
            >
              {renderMarketData()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <TeamOutlined />
                  Fundamental
                </span>
              }
              key="2"
            >
              {renderFundamentalAnalysis()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <LineChartOutlined />
                  Technical
                </span>
              }
              key="3"
            >
              {renderTechnicalAnalysis()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <HeartOutlined />
                  Sentiment
                </span>
              }
              key="4"
            >
              {renderSentimentAnalysis()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <SafetyOutlined />
                  Risk
                </span>
              }
              key="5"
            >
              {renderRiskAssessment()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <TeamOutlined />
                  Peer Comparison
                </span>
              }
              key="6"
            >
              {renderPeerComparison()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <ThunderboltOutlined />
                  Recommendations
                </span>
              }
              key="7"
            >
              {renderRecommendations()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <TeamOutlined />
                  Insider Analysis
                </span>
              }
              key="8"
            >
              {renderInsiderAnalysis()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <ClockCircleOutlined />
                  Catalyst Calendar
                </span>
              }
              key="9"
            >
              {renderCatalystCalendar()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <DashboardOutlined />
                  Macro Analysis
                </span>
              }
              key="10"
            >
              {renderMacroAnalysis()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <LineChartOutlined />
                  Chart Analytics
                </span>
              }
              key="11"
            >
              {renderChartAnalytics()}
            </TabPane>

            <TabPane
              tab={
                <span>
                  <LinkOutlined />
                  Data Sources
                </span>
              }
              key="12"
            >
              <CitationPanel citations={citations} />
            </TabPane>
          </Tabs>
        </>
        </div>
      )}
    </div>
  );
};

export default DeepAnalysis;
