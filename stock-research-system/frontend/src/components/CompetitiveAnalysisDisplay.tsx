import React from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Space,
  Tag,
  Alert,
  Progress,
  Table,
  Badge,
  Statistic,
  List,
  Tooltip,
  Avatar
} from 'antd';
import {
  TrophyOutlined,
  TeamOutlined,
  RocketOutlined,
  CrownOutlined,
  SafetyCertificateOutlined,
  FireOutlined,
  BarChartOutlined,
  PieChartOutlined,
  RiseOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts';

const { Title, Text, Paragraph } = Typography;

interface CompetitiveAnalysisDisplayProps {
  competitive: any;
  symbol: string;
}

const CompetitiveAnalysisDisplay: React.FC<CompetitiveAnalysisDisplayProps> = ({ competitive, symbol }) => {
  if (!competitive) {
    return (
      <Card>
        <Alert message="No competitive analysis data available" type="info" showIcon />
      </Card>
    );
  }

  const marketShare = competitive?.market_analysis?.market_share || {};
  const marketPosition = competitive?.market_analysis?.market_position || {};
  const competitiveAdvantages = competitive?.competitive_assessment?.competitive_advantages || [];
  const competitiveRisks = competitive?.competitive_assessment?.competitive_risks || [];
  const moatAnalysis = competitive?.competitive_assessment?.moat_analysis || {};
  const strategicPosition = competitive?.competitive_assessment?.strategic_position || 'Unknown';
  const comparativeMetrics = competitive?.comparative_metrics || {};
  const compositeScore = comparativeMetrics?.composite_score || {};

  const getMoatColor = (moat: string) => {
    if (moat === 'WIDE MOAT') return '#52c41a';
    if (moat === 'NARROW MOAT') return '#1890ff';
    return '#f5222d';
  };

  const getPositionIcon = (position: string) => {
    if (position.includes('LEADER')) return <CrownOutlined />;
    if (position.includes('DISRUPTOR')) return <RocketOutlined />;
    if (position.includes('FOLLOWER')) return <TeamOutlined />;
    return <BarChartOutlined />;
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return '#52c41a';
    if (score >= 50) return '#1890ff';
    if (score >= 30) return '#faad14';
    return '#f5222d';
  };

  // Prepare market share pie chart data
  const marketShareData = [
    { name: symbol, value: marketShare.revenue_share || 0, color: '#1890ff' },
    { name: 'Others', value: 100 - (marketShare.revenue_share || 0), color: '#f0f0f0' }
  ];

  // Prepare peer comparison data
  const peerComparisonData = [
    { metric: 'P/E Ratio', value: comparativeMetrics?.valuation_vs_peers?.pe_vs_peers?.percentile_rank || 0 },
    { metric: 'Gross Margin', value: comparativeMetrics?.operational_efficiency?.gross_margin_vs_peers?.percentile_rank || 0 },
    { metric: 'ROE', value: comparativeMetrics?.operational_efficiency?.roe_vs_peers?.percentile_rank || 0 },
    { metric: 'Revenue Growth', value: comparativeMetrics?.growth_comparison?.revenue_growth_vs_peers?.percentile_rank || 0 },
  ];

  return (
    <div className="competitive-analysis-display">
      {/* Strategic Position Header */}
      <Card
        style={{ marginBottom: 16, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
        bodyStyle={{ color: 'white' }}
      >
        <Row align="middle" justify="space-between">
          <Col>
            <Space align="center">
              {getPositionIcon(strategicPosition)}
              <div>
                <Text style={{ color: 'rgba(255,255,255,0.8)' }}>Strategic Position</Text>
                <Title level={3} style={{ margin: 0, color: 'white' }}>
                  {strategicPosition}
                </Title>
              </div>
            </Space>
          </Col>
          <Col>
            <Statistic
              title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>Competitive Score</Text>}
              value={compositeScore?.overall_score || 0}
              suffix="/100"
              valueStyle={{ color: 'white' }}
            />
          </Col>
        </Row>
      </Card>

      {/* Market Position Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="Market Share"
              value={marketShare.revenue_share || 0}
              suffix="%"
              prefix={<PieChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="Revenue Rank"
              value={marketPosition.revenue_rank || 'N/A'}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: marketPosition.revenue_rank?.startsWith('1') ? '#faad14' : '#595959' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="Growth Rank"
              value={marketPosition.growth_rank || 'N/A'}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <SafetyCertificateOutlined style={{ fontSize: 24, color: getMoatColor(moatAnalysis.moat_rating) }} />
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">Economic Moat</Text>
                <div>
                  <Tag color={getMoatColor(moatAnalysis.moat_rating)} style={{ margin: '4px 0' }}>
                    {moatAnalysis.moat_rating || 'NO MOAT'}
                  </Tag>
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Market Share Visualization */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <PieChartOutlined />
                <Text strong>Market Share</Text>
              </Space>
            }
            size="small"
          >
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={marketShareData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {marketShareData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div style={{ textAlign: 'center', marginTop: -100 }}>
              <Title level={2} style={{ margin: 0 }}>{marketShare.revenue_share?.toFixed(1)}%</Title>
              <Text type="secondary">Market Share</Text>
            </div>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <BarChartOutlined />
                <Text strong>Peer Comparison (Percentile Rank)</Text>
              </Space>
            }
            size="small"
          >
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={peerComparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="metric" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="value" fill="#1890ff" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Competitive Advantages & Risks */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <FireOutlined style={{ color: '#52c41a' }} />
                <Text strong>Competitive Advantages</Text>
              </Space>
            }
            size="small"
          >
            {competitiveAdvantages.length > 0 ? (
              <List
                size="small"
                dataSource={competitiveAdvantages}
                renderItem={(advantage: string) => (
                  <List.Item>
                    <Space>
                      <Badge status="success" />
                      <Text>{advantage}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            ) : (
              <Text type="secondary">No significant advantages identified</Text>
            )}

            {moatAnalysis.moat_factors && moatAnalysis.moat_factors.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text type="secondary">Moat Factors:</Text>
                <div style={{ marginTop: 8 }}>
                  {moatAnalysis.moat_factors.map((factor: string, index: number) => (
                    <Tag key={index} color="blue" style={{ marginBottom: 4 }}>
                      {factor}
                    </Tag>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <ExclamationCircleOutlined style={{ color: '#f5222d' }} />
                <Text strong>Competitive Risks</Text>
              </Space>
            }
            size="small"
          >
            {competitiveRisks.length > 0 ? (
              <List
                size="small"
                dataSource={competitiveRisks}
                renderItem={(risk: string) => (
                  <List.Item>
                    <Space>
                      <Badge status="error" />
                      <Text>{risk}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            ) : (
              <Text type="secondary">No significant risks identified</Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* Peer Metrics Table */}
      {comparativeMetrics?.valuation_vs_peers && (
        <Card
          title={
            <Space>
              <TeamOutlined />
              <Text strong>Detailed Peer Comparison</Text>
            </Space>
          }
          size="small"
          style={{ marginTop: 16 }}
        >
          <Table
            size="small"
            pagination={false}
            columns={[
              {
                title: 'Metric',
                dataIndex: 'metric',
                key: 'metric',
              },
              {
                title: 'Company Value',
                dataIndex: 'company_value',
                key: 'company_value',
                render: (value) => <Text strong>{value}</Text>
              },
              {
                title: 'Peer Average',
                dataIndex: 'peer_average',
                key: 'peer_average',
              },
              {
                title: 'Relative',
                dataIndex: 'relative',
                key: 'relative',
                render: (value) => (
                  <Tag color={value?.includes('+') ? 'green' : 'red'}>
                    {value}
                  </Tag>
                )
              },
              {
                title: 'Percentile',
                dataIndex: 'percentile',
                key: 'percentile',
                render: (value) => (
                  <Progress
                    percent={value}
                    size="small"
                    strokeColor={getScoreColor(value)}
                    format={percent => `${percent}%`}
                  />
                )
              }
            ]}
            dataSource={[
              {
                metric: 'P/E Ratio',
                company_value: comparativeMetrics.valuation_vs_peers?.pe_vs_peers?.company_value,
                peer_average: comparativeMetrics.valuation_vs_peers?.pe_vs_peers?.peer_average,
                relative: comparativeMetrics.valuation_vs_peers?.pe_vs_peers?.relative_to_avg,
                percentile: comparativeMetrics.valuation_vs_peers?.pe_vs_peers?.percentile_rank
              },
              {
                metric: 'Gross Margin',
                company_value: comparativeMetrics.operational_efficiency?.gross_margin_vs_peers?.company_value,
                peer_average: comparativeMetrics.operational_efficiency?.gross_margin_vs_peers?.peer_average,
                relative: comparativeMetrics.operational_efficiency?.gross_margin_vs_peers?.relative_to_avg,
                percentile: comparativeMetrics.operational_efficiency?.gross_margin_vs_peers?.percentile_rank
              },
              {
                metric: 'ROE',
                company_value: comparativeMetrics.operational_efficiency?.roe_vs_peers?.company_value,
                peer_average: comparativeMetrics.operational_efficiency?.roe_vs_peers?.peer_average,
                relative: comparativeMetrics.operational_efficiency?.roe_vs_peers?.relative_to_avg,
                percentile: comparativeMetrics.operational_efficiency?.roe_vs_peers?.percentile_rank
              }
            ].filter(item => item.company_value)}
          />
        </Card>
      )}

      {/* Competitive Summary */}
      <Alert
        message="Competitive Position Summary"
        description={
          <Space direction="vertical">
            <Paragraph>
              {symbol} holds a <strong>{strategicPosition}</strong> with a{' '}
              <strong>{marketShare.revenue_share?.toFixed(1)}%</strong> market share.
            </Paragraph>
            <Paragraph>
              The company has a <strong>{moatAnalysis.moat_rating}</strong> with a competitive score of{' '}
              <strong>{compositeScore.overall_score?.toFixed(0)}/100</strong>.
            </Paragraph>
            {competitive?.insights && competitive.insights.length > 0 && (
              <div>
                <Text strong>Key Insights:</Text>
                <ul style={{ marginTop: 8, marginBottom: 0 }}>
                  {competitive.insights.slice(0, 3).map((insight: string, index: number) => (
                    <li key={index}>{insight}</li>
                  ))}
                </ul>
              </div>
            )}
          </Space>
        }
        type="info"
        showIcon
        icon={<TrophyOutlined />}
        style={{ marginTop: 16 }}
      />
    </div>
  );
};

export default CompetitiveAnalysisDisplay;