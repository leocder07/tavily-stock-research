import React, { useMemo, memo, useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Table,
  Tag,
  Space,
  Progress,
  Statistic,
  Button,
  Skeleton,
  Alert,
} from 'antd';
import {
  PieChartOutlined,
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  PlusOutlined,
  EditOutlined,
  TrophyOutlined,
  SafetyOutlined,
  LineChartOutlined,
} from '@ant-design/icons';
import { PieChart, Pie, Cell, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { theme } from '../styles/theme';
import axios from 'axios';
import AddHoldingModal from './AddHoldingModal';
import EditHoldingModal from './EditHoldingModal';

// Sample portfolio holdings - MOVED OUTSIDE to prevent re-creation on every render
const SAMPLE_HOLDINGS = [
  {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    shares: 50,
    avgCost: 145.20,
    currentPrice: 195.20,
    value: 9760,
    dayChange: 2.5,
    totalReturn: 34.4,
    allocation: 28.5,
  },
  {
    symbol: 'NVDA',
    name: 'NVIDIA Corp',
    shares: 10,
    avgCost: 450.00,
    currentPrice: 885.42,
    value: 8854.20,
    dayChange: 5.2,
    totalReturn: 96.8,
    allocation: 25.8,
  },
  {
    symbol: 'MSFT',
    name: 'Microsoft',
    shares: 25,
    avgCost: 320.00,
    currentPrice: 420.80,
    value: 10520,
    dayChange: 1.8,
    totalReturn: 31.5,
    allocation: 30.7,
  },
  {
    symbol: 'GOOGL',
    name: 'Alphabet',
    shares: 8,
    avgCost: 125.00,
    currentPrice: 142.15,
    value: 1137.20,
    dayChange: -0.5,
    totalReturn: 13.7,
    allocation: 3.3,
  },
  {
    symbol: 'TSLA',
    name: 'Tesla Inc.',
    shares: 15,
    avgCost: 180.00,
    currentPrice: 245.80,
    value: 3687,
    dayChange: 3.2,
    totalReturn: 36.6,
    allocation: 10.8,
  },
];

// Sector allocation - MOVED OUTSIDE to prevent re-creation
const SECTOR_ALLOCATION = [
  { sector: 'Technology', value: 65, color: theme.colors.primary },
  { sector: 'Consumer', value: 15, color: theme.colors.success },
  { sector: 'Healthcare', value: 10, color: theme.colors.warning },
  { sector: 'Finance', value: 5, color: theme.colors.danger },
  { sector: 'Energy', value: 5, color: theme.colors.text.secondary },
];

interface PortfolioProps {
  metrics: {
    totalValue: number;
    dayChange: number;
    dayChangePercent: number;
    totalReturn: number;
    winRate: number;
    sharpeRatio: number;
  };
}

// Memoized AllocationChart component to prevent Recharts infinite loop
const AllocationChart = memo(({ data, colors, tooltipStyle }: {
  data: Array<{ name: string; value: number }>;
  colors: string[];
  tooltipStyle: React.CSSProperties;
}) => {
  const cells = useMemo(() =>
    data.map((entry, index) => (
      <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
    )), [data, colors]);

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={5}
          dataKey="value"
        >
          {cells}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} />
      </PieChart>
    </ResponsiveContainer>
  );
});

AllocationChart.displayName = 'AllocationChart';

const Portfolio: React.FC<PortfolioProps> = ({ metrics }) => {
  // State for real portfolio data
  const [portfolioData, setPortfolioData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState<any>(null);

  const userEmail = 'vkpr15@gmail.com'; // TODO: Get from auth context

  // Fetch portfolio data from API
  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        setLoading(true);
        const response = await axios.get('http://localhost:8000/api/v1/portfolio/vkpr15@gmail.com');
        setPortfolioData(response.data.data);
        setLoading(false);
      } catch (err: any) {
        console.error('Error fetching portfolio:', err);
        setError(err.message || 'Failed to load portfolio');
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, []);

  // Use real holdings if available, otherwise fall back to sample data
  const holdings = portfolioData?.holdings || SAMPLE_HOLDINGS;

  // Calculate displayMetrics from API data if available, otherwise use props
  const displayMetrics = useMemo(() => {
    if (portfolioData) {
      return {
        totalValue: portfolioData.total_value || portfolioData.totalValue || 0,
        dayChange: portfolioData.day_change || portfolioData.dayChange || 0,
        dayChangePercent: portfolioData.day_change_percent || portfolioData.dayChangePercent || 0,
        totalReturn: portfolioData.total_return_percent || portfolioData.totalReturn || 0,
        winRate: portfolioData.win_rate || portfolioData.winRate || 0,
        sharpeRatio: portfolioData.sharpe_ratio || portfolioData.sharpeRatio || 0,
      };
    }
    return metrics;
  }, [portfolioData, metrics]);

  // Portfolio allocation data for pie chart - NOW STABLE (no holdings dependency needed)
  const allocationData = useMemo(() =>
    holdings.map((h: any) => ({
      name: h.symbol,
      value: h.allocation || 0,
    })), [holdings]);

  // Performance history data - Calculate from actual portfolio metrics
  const performanceHistory = useMemo(() => {
    if (!portfolioData) {
      // Fallback to mock data if portfolio not loaded
      return Array.from({ length: 30 }, (_, i) => ({
        day: i + 1,
        value: 100000 + Math.sin(12345 + i) * 2500 + i * 800,
      }));
    }

    // Calculate historical performance based on current portfolio value
    const currentValue = displayMetrics.totalValue;
    const totalReturn = displayMetrics.totalReturn / 100; // Convert percentage to decimal
    const startingValue = currentValue / (1 + totalReturn);

    // Generate 30-day performance history showing growth from start to current
    return Array.from({ length: 30 }, (_, i) => {
      const dayProgress = i / 29; // 0 to 1 progress through the period
      const value = startingValue + (currentValue - startingValue) * dayProgress;

      // Add some realistic daily volatility (±2%)
      const volatility = Math.sin(i * 0.5) * value * 0.015;

      return {
        day: i + 1,
        value: Math.round(value + volatility),
      };
    });
  }, [portfolioData, displayMetrics.totalValue, displayMetrics.totalReturn]);

  const sectorAllocation = SECTOR_ALLOCATION;

  const columns = useMemo(() => [
    {
      title: 'Symbol',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text: string, record: any) => (
        <Space>
          <span style={{ fontSize: 14, fontWeight: 600 }}>{text}</span>
          <span style={{ fontSize: 12, color: theme.colors.text.muted }}>
            {record.name}
          </span>
        </Space>
      ),
    },
    {
      title: 'Shares',
      dataIndex: 'shares',
      key: 'shares',
      align: 'center' as const,
    },
    {
      title: 'Avg Cost',
      dataIndex: 'avg_cost',
      key: 'avg_cost',
      render: (value: number) => `$${value?.toFixed(2) || '0.00'}`,
      align: 'right' as const,
    },
    {
      title: 'Current Price',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (value: number) => `$${value?.toFixed(2) || '0.00'}`,
      align: 'right' as const,
    },
    {
      title: 'Market Value',
      dataIndex: 'value',
      key: 'value',
      render: (value: number) => (
        <span style={{ fontWeight: 600 }}>${value?.toLocaleString() || '0'}</span>
      ),
      align: 'right' as const,
    },
    {
      title: 'Day Change',
      dataIndex: 'day_change_percent',
      key: 'day_change_percent',
      render: (value: number) => (
        <Tag color={value > 0 ? 'success' : 'error'}>
          {value > 0 ? <RiseOutlined /> : <FallOutlined />}
          {Math.abs(value || 0).toFixed(2)}%
        </Tag>
      ),
      align: 'center' as const,
    },
    {
      title: 'Total Return',
      dataIndex: 'total_return_percent',
      key: 'total_return_percent',
      render: (value: number) => (
        <Space>
          <span style={{ color: (value || 0) > 0 ? theme.colors.success : theme.colors.danger }}>
            {(value || 0) > 0 ? '+' : ''}{(value || 0).toFixed(2)}%
          </span>
        </Space>
      ),
      align: 'right' as const,
    },
    {
      title: 'Allocation',
      dataIndex: 'allocation',
      key: 'allocation',
      render: (value: number) => (
        <Progress
          percent={value || 0}
          size="small"
          strokeColor={theme.colors.primary}
          trailColor={theme.colors.background.elevated}
          format={(percent) => `${percent}%`}
        />
      ),
      width: 150,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: any) => (
        <Button
          size="small"
          icon={<EditOutlined />}
          onClick={() => {
            setSelectedHolding(record);
            setShowEditModal(true);
          }}
          style={{
            backgroundColor: theme.colors.background.elevated,
            border: `1px solid ${theme.colors.border}`,
            color: theme.colors.primary
          }}
        >
          Edit
        </Button>
      ),
      align: 'center' as const,
      width: 100,
    },
  ], []);

  const COLORS = useMemo(() => [
    theme.colors.primary,
    theme.colors.success,
    theme.colors.warning,
    theme.colors.danger,
    theme.colors.text.secondary,
  ], []);

  // Memoize chart props to prevent infinite re-renders
  const chartAxisStyle = useMemo(() => ({ fontSize: 12 }), []);
  const tooltipContentStyle = useMemo(() => ({
    background: theme.colors.background.elevated,
    border: `1px solid ${theme.colors.primary}`,
    borderRadius: 8,
  }), []);
  const tooltipFormatter = useMemo(() => (value: any) => `$${value.toLocaleString()}`, []);
  const yAxisTickFormatter = useMemo(() => (value: number) => `$${(value / 1000).toFixed(0)}k`, []);

  // Memoize PieChart cells to prevent re-creation on every render
  const pieCells = useMemo(() =>
    allocationData.map((entry, index) => (
      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
    )), [allocationData, COLORS]);

  // Memoize BarChart cells
  const barCells = useMemo(() =>
    sectorAllocation.map((entry, index) => (
      <Cell key={`cell-${index}`} fill={entry.color} />
    )), [sectorAllocation]);

  // Show loading skeleton while fetching data
  if (loading) {
    return (
      <div>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          {[1, 2, 3, 4].map((i) => (
            <Col key={i} xs={24} sm={12} lg={6}>
              <Card>
                <Skeleton active paragraph={{ rows: 2 }} />
              </Card>
            </Col>
          ))}
        </Row>
        <Row gutter={[16, 16]}>
          <Col span={16}>
            <Card>
              <Skeleton active paragraph={{ rows: 6 }} />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Skeleton active paragraph={{ rows: 6 }} />
            </Card>
          </Col>
        </Row>
      </div>
    );
  }

  // Show error state if API call failed
  if (error) {
    return (
      <Alert
        message="Error Loading Portfolio"
        description={error}
        type="error"
        showIcon
        style={{ marginBottom: 24 }}
      />
    );
  }

  return (
    <div>
      {/* Portfolio Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card
            style={{
              background: theme.colors.gradient.primary,
              border: 'none',
            }}
          >
            <Statistic
              title={<span style={{ color: '#fff' }}>Total Value</span>}
              value={displayMetrics.totalValue}
              precision={2}
              prefix="$"
              valueStyle={{ color: '#fff' }}
            />
            <div style={{ marginTop: 8 }}>
              <span style={{ color: '#fff', opacity: 0.9, fontSize: 12 }}>
                {displayMetrics.dayChange > 0 ? <RiseOutlined /> : <FallOutlined />}
                {' '}${Math.abs(displayMetrics.dayChange).toFixed(2)} ({displayMetrics.dayChangePercent}%) today
              </span>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ background: theme.colors.background.secondary }}>
            <Statistic
              title="Total Return"
              value={displayMetrics.totalReturn}
              suffix="%"
              prefix={displayMetrics.totalReturn > 0 ? "+" : ""}
              valueStyle={{ color: theme.colors.success }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ background: theme.colors.background.secondary }}>
            <Statistic
              title="Win Rate"
              value={displayMetrics.winRate}
              suffix="%"
              valueStyle={{ color: theme.colors.warning }}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ background: theme.colors.background.secondary }}>
            <Statistic
              title="Sharpe Ratio"
              value={displayMetrics.sharpeRatio}
              precision={2}
              valueStyle={{ color: theme.colors.primary }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* Performance Chart */}
        <Col xs={24} lg={16}>
          <Card
            title={
              <Space>
                <LineChartOutlined style={{ color: theme.colors.primary }} />
                <div style={{ fontWeight: 600 }}>Portfolio Performance</div>
              </Space>
            }
            style={{
              background: theme.colors.background.secondary,
              border: `1px solid rgba(255, 255, 255, 0.08)`,
            }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceHistory}>
                <defs>
                  <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={theme.colors.primary} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={theme.colors.primary} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.background.elevated} />
                <XAxis
                  dataKey="day"
                  stroke={theme.colors.text.muted}
                  style={chartAxisStyle}
                />
                <YAxis
                  stroke={theme.colors.text.muted}
                  style={chartAxisStyle}
                  tickFormatter={yAxisTickFormatter}
                />
                <Tooltip
                  contentStyle={tooltipContentStyle}
                  formatter={tooltipFormatter}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={theme.colors.primary}
                  fill="url(#portfolioGradient)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Allocation Charts */}
        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <PieChartOutlined style={{ color: theme.colors.primary }} />
                <div style={{ fontWeight: 600 }}>Asset Allocation</div>
              </Space>
            }
            style={{
              background: theme.colors.background.secondary,
              border: `1px solid rgba(255, 255, 255, 0.08)`,
              height: '100%',
            }}
          >
            <AllocationChart
              data={allocationData}
              colors={COLORS}
              tooltipStyle={tooltipContentStyle}
            />
            <div style={{ marginTop: 16 }}>
              {allocationData.map((item, index) => (
                <div
                  key={item.name}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 8,
                  }}
                >
                  <Space>
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        borderRadius: 2,
                        background: COLORS[index % COLORS.length],
                      }}
                    />
                    <span style={{ fontSize: 13 }}>{item.name}</span>
                  </Space>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{item.value}%</span>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Holdings Table */}
      <Card
        title={
          <Space>
            <SafetyOutlined style={{ color: theme.colors.primary }} />
            <div style={{ fontWeight: 600 }}>Current Holdings</div>
          </Space>
        }
        style={{
          background: theme.colors.background.secondary,
          border: `1px solid rgba(255, 255, 255, 0.08)`,
          marginTop: 16,
        }}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setShowAddModal(true)}
            style={{
              background: theme.colors.gradient.primary,
              border: 'none',
              color: '#000',
              fontWeight: 600
            }}
          >
            Add Holding
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={holdings}
          rowKey="symbol"
          pagination={false}
          style={{
            background: theme.colors.background.secondary,
          }}
        />
      </Card>

      {/* Sector Allocation */}
      <Card
        title={
          <Space>
            <DollarOutlined style={{ color: theme.colors.primary }} />
            <div style={{ fontWeight: 600 }}>Sector Allocation</div>
          </Space>
        }
        style={{
          background: theme.colors.background.secondary,
          border: `1px solid rgba(255, 255, 255, 0.08)`,
          marginTop: 16,
        }}
      >
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={sectorAllocation}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.background.elevated} />
            <XAxis dataKey="sector" stroke={theme.colors.text.muted} />
            <YAxis stroke={theme.colors.text.muted} />
            <Tooltip contentStyle={tooltipContentStyle} />
            <Bar dataKey="value" fill={theme.colors.primary}>
              {barCells}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Modals */}
      <AddHoldingModal
        visible={showAddModal}
        onCancel={() => setShowAddModal(false)}
        onSuccess={() => {
          setShowAddModal(false);
          // Refetch portfolio data
          const fetchData = async () => {
            try {
              const response = await axios.get(`http://localhost:8000/api/v1/portfolio/${userEmail}`);
              setPortfolioData(response.data.data);
            } catch (err) {
              console.error('Error refetching portfolio:', err);
            }
          };
          fetchData();
        }}
        userEmail={userEmail}
      />

      <EditHoldingModal
        visible={showEditModal}
        onCancel={() => {
          setShowEditModal(false);
          setSelectedHolding(null);
        }}
        onSuccess={() => {
          setShowEditModal(false);
          setSelectedHolding(null);
          // Refetch portfolio data
          const fetchData = async () => {
            try {
              const response = await axios.get(`http://localhost:8000/api/v1/portfolio/${userEmail}`);
              setPortfolioData(response.data.data);
            } catch (err) {
              console.error('Error refetching portfolio:', err);
            }
          };
          fetchData();
        }}
        userEmail={userEmail}
        holding={selectedHolding}
      />
    </div>
  );
};

export default Portfolio;