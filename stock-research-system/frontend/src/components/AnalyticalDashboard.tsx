import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Space,
  Tag,
  Typography,
  Select,
  Table,
  Badge,
} from 'antd';
import {
  RiseOutlined,
  FallOutlined,
  FundProjectionScreenOutlined,
  DollarCircleOutlined,
  StockOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { Line, Column, Pie } from '@ant-design/charts';
import { motion } from 'framer-motion';

const { Text } = Typography;
const { Option } = Select;

interface MarketData {
  date: string;
  value: number;
  type: string;
  volume?: number;
}

interface SectorPerformance {
  sector: string;
  performance: number;
  volume: number;
  marketCap: number;
}

interface TechnicalIndicator {
  name: string;
  value: number;
  signal: 'buy' | 'sell' | 'neutral';
  strength: number;
}

interface AnalyticalDashboardProps {
  selectedStock?: string;
  timeRange?: [string, string];
  onRefresh?: () => void;
}

const AnalyticalDashboard: React.FC<AnalyticalDashboardProps> = ({
  selectedStock = 'AAPL',
  timeRange,
  onRefresh
}) => {
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [sectorData, setSectorData] = useState<SectorPerformance[]>([]);
  const [indicators, setIndicators] = useState<TechnicalIndicator[]>([]);

  // Generate sample data
  useEffect(() => {
    const generateMarketData = () => {
      const data: MarketData[] = [];
      const types = ['Price', 'Volume', 'MA50', 'MA200'];
      const baseDate = new Date();

      for (let i = 30; i >= 0; i--) {
        const date = new Date(baseDate);
        date.setDate(date.getDate() - i);

        types.forEach(type => {
          data.push({
            date: date.toISOString().split('T')[0],
            value: type === 'Volume'
              ? Math.random() * 10000000 + 5000000
              : Math.random() * 50 + 150,
            type,
            volume: Math.random() * 10000000 + 5000000
          });
        });
      }

      return data;
    };

    const generateSectorData = (): SectorPerformance[] => [
      { sector: 'Technology', performance: 8.5, volume: 15000000, marketCap: 2500000000 },
      { sector: 'Healthcare', performance: 5.2, volume: 8000000, marketCap: 1800000000 },
      { sector: 'Finance', performance: 3.8, volume: 12000000, marketCap: 2200000000 },
      { sector: 'Energy', performance: -2.1, volume: 9000000, marketCap: 1500000000 },
      { sector: 'Consumer', performance: 4.5, volume: 10000000, marketCap: 1900000000 },
      { sector: 'Industrial', performance: 1.2, volume: 7000000, marketCap: 1200000000 }
    ];

    const generateIndicators = (): TechnicalIndicator[] => [
      { name: 'RSI', value: 65, signal: 'buy', strength: 0.7 },
      { name: 'MACD', value: 2.5, signal: 'buy', strength: 0.8 },
      { name: 'Bollinger Bands', value: 0, signal: 'neutral', strength: 0.5 },
      { name: 'Moving Average', value: 175, signal: 'buy', strength: 0.9 },
      { name: 'Volume Oscillator', value: 15, signal: 'sell', strength: 0.6 },
      { name: 'Stochastic', value: 78, signal: 'sell', strength: 0.65 }
    ];

    setMarketData(generateMarketData());
    setSectorData(generateSectorData());
    setIndicators(generateIndicators());
  }, [selectedStock, timeRange]);

  // Chart configurations
  const priceChartConfig = {
    data: marketData.filter(d => d.type === 'Price' || d.type.startsWith('MA')),
    xField: 'date',
    yField: 'value',
    seriesField: 'type',
    smooth: true,
    animation: {
      appear: {
        animation: 'wave-in',
        duration: 1000,
      },
    },
    color: ['#722ed1', '#52c41a', '#faad14'],
    xAxis: {
      type: 'time',
    },
    tooltip: {
      showMarkers: true,
    },
  };

  const volumeChartConfig = {
    data: marketData.filter(d => d.type === 'Volume'),
    xField: 'date',
    yField: 'value',
    color: '#1890ff',
    columnStyle: {
      radius: [8, 8, 0, 0],
    },
    label: {
      position: 'top',
      style: {
        fill: '#FFFFFF',
        opacity: 0.6,
      },
    },
  };

  const sectorPieConfig = {
    data: sectorData,
    angleField: 'marketCap',
    colorField: 'sector',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
    interactions: [
      {
        type: 'pie-legend-active',
      },
      {
        type: 'element-active',
      },
    ],
  };

  const getSignalColor = (signal: string) => {
    switch(signal) {
      case 'buy': return 'success';
      case 'sell': return 'error';
      default: return 'warning';
    }
  };

  return (
    <div className="analytical-dashboard">
      {/* Header Metrics */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12} lg={6}>
          <Card className="glass-card">
            <Statistic
              title="Current Price"
              value={selectedStock ? 175.82 : 0}
              precision={2}
              valueStyle={{ color: '#52c41a' }}
              prefix={<DollarCircleOutlined />}
              suffix={
                <Space>
                  <Tag color="success">+2.5%</Tag>
                  <RiseOutlined />
                </Space>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="glass-card">
            <Statistic
              title="Market Cap"
              value={2.8}
              suffix="T"
              valueStyle={{ color: '#722ed1' }}
              prefix={<FundProjectionScreenOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="glass-card">
            <Statistic
              title="Volume"
              value={45678900}
              valueStyle={{ color: '#1890ff' }}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="glass-card">
            <Statistic
              title="P/E Ratio"
              value={28.5}
              precision={1}
              valueStyle={{ color: '#faad14' }}
              prefix={<StockOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts Section */}
      <Row gutter={[16, 16]}>
        {/* Price Chart */}
        <Col xs={24} lg={16}>
          <Card
            title="Price Movement & Moving Averages"
            className="glass-card"
            extra={
              <Select defaultValue="1M" style={{ width: 80 }}>
                <Option value="1D">1D</Option>
                <Option value="1W">1W</Option>
                <Option value="1M">1M</Option>
                <Option value="3M">3M</Option>
                <Option value="1Y">1Y</Option>
              </Select>
            }
          >
            <Line {...priceChartConfig} height={300} />
          </Card>
        </Col>

        {/* Technical Indicators */}
        <Col xs={24} lg={8}>
          <Card title="Technical Indicators" className="glass-card">
            <Space direction="vertical" style={{ width: '100%' }}>
              {indicators.map((indicator, index) => (
                <motion.div
                  key={indicator.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Row align="middle" justify="space-between">
                    <Col span={8}>
                      <Text strong>{indicator.name}</Text>
                    </Col>
                    <Col span={8} style={{ textAlign: 'center' }}>
                      <Badge status={getSignalColor(indicator.signal)} text={indicator.signal.toUpperCase()} />
                    </Col>
                    <Col span={8} style={{ textAlign: 'right' }}>
                      <Progress
                        percent={indicator.strength * 100}
                        size="small"
                        strokeColor={indicator.signal === 'buy' ? '#52c41a' : '#ff4d4f'}
                        showInfo={false}
                      />
                    </Col>
                  </Row>
                </motion.div>
              ))}
            </Space>
          </Card>
        </Col>

        {/* Volume Chart */}
        <Col xs={24} lg={12}>
          <Card title="Trading Volume" className="glass-card">
            <Column {...volumeChartConfig} height={250} />
          </Card>
        </Col>

        {/* Sector Performance */}
        <Col xs={24} lg={12}>
          <Card title="Sector Distribution" className="glass-card">
            <Pie {...sectorPieConfig} height={250} />
          </Card>
        </Col>
      </Row>

      {/* Sector Performance Table */}
      <Card title="Sector Performance Analysis" className="glass-card mt-4">
        <Table
          dataSource={sectorData}
          columns={[
            {
              title: 'Sector',
              dataIndex: 'sector',
              key: 'sector',
              render: (text: string) => <Text strong>{text}</Text>,
            },
            {
              title: 'Performance',
              dataIndex: 'performance',
              key: 'performance',
              render: (value: number) => (
                <Tag color={value > 0 ? 'success' : 'error'}>
                  {value > 0 ? <RiseOutlined /> : <FallOutlined />} {Math.abs(value)}%
                </Tag>
              ),
              sorter: (a: SectorPerformance, b: SectorPerformance) => a.performance - b.performance,
            },
            {
              title: 'Volume',
              dataIndex: 'volume',
              key: 'volume',
              render: (value: number) => `${(value / 1000000).toFixed(1)}M`,
              sorter: (a: SectorPerformance, b: SectorPerformance) => a.volume - b.volume,
            },
            {
              title: 'Market Cap',
              dataIndex: 'marketCap',
              key: 'marketCap',
              render: (value: number) => `$${(value / 1000000000).toFixed(1)}B`,
              sorter: (a: SectorPerformance, b: SectorPerformance) => a.marketCap - b.marketCap,
            },
            {
              title: 'Signal',
              key: 'signal',
              render: (_: any, record: SectorPerformance) => {
                const signal = record.performance > 5 ? 'Strong Buy' :
                               record.performance > 0 ? 'Buy' :
                               record.performance > -5 ? 'Hold' : 'Sell';
                const color = signal === 'Strong Buy' ? 'success' :
                              signal === 'Buy' ? 'processing' :
                              signal === 'Hold' ? 'warning' : 'error';
                return <Badge status={color} text={signal} />;
              },
            },
          ]}
          pagination={false}
          size="middle"
        />
      </Card>
    </div>
  );
};

export default AnalyticalDashboard;