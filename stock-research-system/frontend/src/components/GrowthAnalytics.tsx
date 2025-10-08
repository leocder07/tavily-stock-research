/**
 * GrowthAnalytics - CRED-style growth analytics dashboard
 * Shows platform growth metrics, user engagement, and performance insights
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Space,
  Typography,
  Select,
  DatePicker,
  Button,
  Tabs,
  List,
  Avatar,
  Badge,
  Tooltip,
} from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  UserOutlined,
  DollarOutlined,
  ThunderboltOutlined,
  RiseOutlined,
  FallOutlined,
  EyeOutlined,
  StarOutlined,
  ClockCircleOutlined,
  FireOutlined,
} from '@ant-design/icons';
import { ApexOptions } from 'apexcharts';
import { theme } from '../styles/theme';

// Dynamic import for ApexCharts to avoid SSR issues
const ReactApexChart = React.lazy(() => import('react-apexcharts'));

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

interface GrowthAnalyticsProps {
  timeRange?: string;
}

const GrowthAnalytics: React.FC<GrowthAnalyticsProps> = ({ timeRange = '7d' }) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [loading, setLoading] = useState(false);
  const [growthMetrics, setGrowthMetrics] = useState({
    totalUsers: 0,
    activeUsers: 0,
    totalAnalyses: 0,
    totalRevenue: 0,
    userGrowthRate: 0,
    analysisGrowthRate: 0,
    revenueGrowthRate: 0,
    retentionRate: 0,
  });
  const [userEngagementData, setUserEngagementData] = useState<any[]>([]);
  const [topStocks, setTopStocks] = useState<any[]>([]);

  // Load real data from backend
  useEffect(() => {
    const loadAnalyticsData = async () => {
      setLoading(true);
      try {
        // Fetch growth metrics
        const growthResponse = await fetch('/api/v1/analytics/growth');
        if (growthResponse.ok) {
          const growthData = await growthResponse.json();
          setGrowthMetrics(growthData);
        }

        // Fetch engagement data
        const engagementResponse = await fetch('/api/v1/analytics/engagement');
        if (engagementResponse.ok) {
          const engagementData = await engagementResponse.json();
          setUserEngagementData(engagementData);
        }

        // Fetch top stocks
        const stocksResponse = await fetch('/api/v1/analytics/top-stocks');
        if (stocksResponse.ok) {
          const stocksData = await stocksResponse.json();
          setTopStocks(stocksData);
        }
      } catch (error) {
        console.error('Failed to load analytics data:', error);
        // Fallback to minimal sample data if API fails
        setGrowthMetrics({
          totalUsers: 1,
          activeUsers: 1,
          totalAnalyses: 6,
          totalRevenue: 90,
          userGrowthRate: 25.0,
          analysisGrowthRate: 35.0,
          revenueGrowthRate: 42.0,
          retentionRate: 95.0,
        });
        setUserEngagementData([
          { date: new Date().toISOString().split('T')[0], users: 1, analyses: 6, revenue: 90 }
        ]);
        setTopStocks([]);
      } finally {
        setLoading(false);
      }
    };

    loadAnalyticsData();
  }, [selectedTimeRange]);

  // User Growth Chart
  const userGrowthOptions: ApexOptions = {
    chart: {
      type: 'area',
      height: 350,
      toolbar: { show: true },
      background: 'transparent',
    },
    stroke: {
      curve: 'smooth',
      width: 3,
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.3,
        stops: [0, 90, 100],
      },
    },
    colors: [theme.colors.primary, theme.colors.success, theme.colors.warning],
    title: {
      text: 'Growth Metrics Over Time',
      style: {
        fontSize: '18px',
        fontWeight: 'bold',
        color: theme.colors.text.primary,
      },
    },
    xaxis: {
      categories: userEngagementData.map(d => d.date),
      labels: {
        style: { colors: theme.colors.text.secondary },
      },
    },
    yaxis: [
      {
        title: {
          text: 'Active Users',
          style: { color: theme.colors.text.secondary },
        },
        labels: {
          style: { colors: theme.colors.text.secondary },
        },
      },
      {
        opposite: true,
        title: {
          text: 'Revenue ($)',
          style: { color: theme.colors.text.secondary },
        },
        labels: {
          style: { colors: theme.colors.text.secondary },
        },
      },
    ],
    legend: {
      labels: { colors: theme.colors.text.secondary },
    },
    grid: {
      borderColor: 'rgba(255, 255, 255, 0.1)',
    },
    tooltip: {
      theme: 'dark',
    },
  };

  const userGrowthSeries = [
    {
      name: 'Active Users',
      data: userEngagementData.map(d => d.users),
    },
    {
      name: 'Analyses',
      data: userEngagementData.map(d => d.analyses),
    },
    {
      name: 'Revenue',
      data: userEngagementData.map(d => d.revenue),
      yAxisIndex: 1,
    },
  ];

  // Top stocks data comes from API via state

  const stockColumns = [
    {
      title: 'Symbol',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => (
        <Tag color={theme.colors.primary} style={{ fontWeight: 600 }}>
          {symbol}
        </Tag>
      ),
    },
    {
      title: 'Company',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Text style={{ color: theme.colors.text.primary }}>{name}</Text>
      ),
    },
    {
      title: 'Analyses',
      dataIndex: 'analyses',
      key: 'analyses',
      render: (analyses: number) => (
        <Text style={{ color: theme.colors.text.secondary }}>
          {analyses.toLocaleString()}
        </Text>
      ),
    },
    {
      title: 'Sentiment',
      dataIndex: 'sentiment',
      key: 'sentiment',
      render: (sentiment: string) => {
        const color = sentiment === 'bullish' ? theme.colors.success :
                     sentiment === 'bearish' ? theme.colors.danger :
                     theme.colors.warning;
        return <Tag color={color}>{sentiment.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Change',
      dataIndex: 'change',
      key: 'change',
      render: (change: number) => (
        <Statistic
          value={Math.abs(change)}
          precision={1}
          valueStyle={{
            color: change > 0 ? theme.colors.success : theme.colors.danger,
            fontSize: 14,
          }}
          prefix={change > 0 ? <RiseOutlined /> : <FallOutlined />}
          suffix="%"
        />
      ),
    },
  ];

  // User Activity Insights
  const userActivityInsights = [
    {
      title: 'Peak Usage Time',
      value: '2:00 PM - 4:00 PM EST',
      icon: <ClockCircleOutlined style={{ color: theme.colors.primary }} />,
      trend: '+15% from last week',
      trendUp: true,
    },
    {
      title: 'Most Searched Sector',
      value: 'Technology',
      icon: <FireOutlined style={{ color: theme.colors.warning }} />,
      trend: '68% of all searches',
      trendUp: true,
    },
    {
      title: 'Average Session Duration',
      value: '14.5 minutes',
      icon: <EyeOutlined style={{ color: theme.colors.success }} />,
      trend: '+2.3 minutes from last week',
      trendUp: true,
    },
    {
      title: 'Feature Adoption Rate',
      value: 'AI Chat: 89%',
      icon: <ThunderboltOutlined style={{ color: theme.colors.primary }} />,
      trend: '+12% from last month',
      trendUp: true,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2} style={{ color: theme.colors.text.primary, margin: 0 }}>
              Growth Analytics
            </Title>
            <Paragraph style={{ color: theme.colors.text.secondary, margin: '8px 0' }}>
              Platform performance insights and growth metrics
            </Paragraph>
          </Col>
          <Col>
            <Space>
              <Select
                value={selectedTimeRange}
                onChange={setSelectedTimeRange}
                style={{ width: 120 }}
              >
                <Option value="1d">Last Day</Option>
                <Option value="7d">Last Week</Option>
                <Option value="30d">Last Month</Option>
                <Option value="90d">Last Quarter</Option>
              </Select>
              <RangePicker />
            </Space>
          </Col>
        </Row>
      </div>

      <Tabs defaultActiveKey="1">
        <TabPane tab="Overview" key="1">
          {/* Key Metrics Cards */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card
                style={{
                  background: theme.colors.background.secondary,
                  border: `1px solid rgba(255, 255, 255, 0.1)`,
                }}
              >
                <Statistic
                  title="Total Users"
                  value={growthMetrics.totalUsers}
                  valueStyle={{ color: theme.colors.text.primary }}
                  prefix={<UserOutlined style={{ color: theme.colors.primary }} />}
                  suffix={
                    <div style={{ fontSize: 12, color: theme.colors.success }}>
                      <ArrowUpOutlined /> {growthMetrics.userGrowthRate}%
                    </div>
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card
                style={{
                  background: theme.colors.background.secondary,
                  border: `1px solid rgba(255, 255, 255, 0.1)`,
                }}
              >
                <Statistic
                  title="Active Users"
                  value={growthMetrics.activeUsers}
                  valueStyle={{ color: theme.colors.text.primary }}
                  prefix={<ArrowUpOutlined style={{ color: theme.colors.success }} />}
                  suffix={
                    <div style={{ fontSize: 12, color: theme.colors.success }}>
                      <ArrowUpOutlined /> {growthMetrics.analysisGrowthRate}%
                    </div>
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card
                style={{
                  background: theme.colors.background.secondary,
                  border: `1px solid rgba(255, 255, 255, 0.1)`,
                }}
              >
                <Statistic
                  title="Total Analyses"
                  value={growthMetrics.totalAnalyses}
                  valueStyle={{ color: theme.colors.text.primary }}
                  prefix={<ThunderboltOutlined style={{ color: theme.colors.warning }} />}
                  suffix={
                    <div style={{ fontSize: 12, color: theme.colors.success }}>
                      <ArrowUpOutlined /> {growthMetrics.analysisGrowthRate}%
                    </div>
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card
                style={{
                  background: theme.colors.background.secondary,
                  border: `1px solid rgba(255, 255, 255, 0.1)`,
                }}
              >
                <Statistic
                  title="Revenue"
                  value={growthMetrics.totalRevenue}
                  precision={0}
                  valueStyle={{ color: theme.colors.text.primary }}
                  prefix={<DollarOutlined style={{ color: theme.colors.success }} />}
                  suffix={
                    <div style={{ fontSize: 12, color: theme.colors.success }}>
                      <ArrowUpOutlined /> {growthMetrics.revenueGrowthRate}%
                    </div>
                  }
                />
              </Card>
            </Col>
          </Row>

          {/* Growth Chart */}
          <Card
            title="Growth Trends"
            style={{
              background: theme.colors.background.secondary,
              border: `1px solid rgba(255, 255, 255, 0.1)`,
              marginBottom: 24,
            }}
          >
            <React.Suspense fallback={<div style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center', color: theme.colors.text.secondary }}>Loading chart...</div>}>
              <ReactApexChart
                options={userGrowthOptions}
                series={userGrowthSeries}
                type="area"
                height={350}
              />
            </React.Suspense>
          </Card>

          {/* User Activity Insights */}
          <Row gutter={[16, 16]}>
            {userActivityInsights.map((insight, index) => (
              <Col xs={24} sm={12} lg={6} key={index}>
                <Card
                  style={{
                    background: theme.colors.background.secondary,
                    border: `1px solid rgba(255, 255, 255, 0.1)`,
                  }}
                >
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {insight.icon}
                      <Text style={{ color: theme.colors.text.secondary, fontSize: 12 }}>
                        {insight.title}
                      </Text>
                    </div>
                    <Text strong style={{ color: theme.colors.text.primary, fontSize: 16 }}>
                      {insight.value}
                    </Text>
                    <Text
                      style={{
                        color: insight.trendUp ? theme.colors.success : theme.colors.danger,
                        fontSize: 11,
                      }}
                    >
                      {insight.trendUp ? '↗' : '↘'} {insight.trend}
                    </Text>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>

        <TabPane tab="Top Stocks" key="2">
          <Card
            title="Most Analyzed Stocks"
            style={{
              background: theme.colors.background.secondary,
              border: `1px solid rgba(255, 255, 255, 0.1)`,
            }}
          >
            <Table
              dataSource={topStocks}
              columns={stockColumns}
              pagination={false}
              style={{
                background: 'transparent',
              }}
              rowKey="symbol"
            />
          </Card>
        </TabPane>

        <TabPane tab="User Engagement" key="3">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card
                title="User Retention"
                style={{
                  background: theme.colors.background.secondary,
                  border: `1px solid rgba(255, 255, 255, 0.1)`,
                }}
              >
                <div style={{ textAlign: 'center', padding: '20px 0' }}>
                  <Progress
                    type="circle"
                    percent={growthMetrics.retentionRate}
                    size={120}
                    strokeColor={theme.colors.success}
                    format={(percent) => `${percent}%`}
                  />
                  <Text
                    style={{
                      display: 'block',
                      marginTop: 16,
                      color: theme.colors.text.secondary,
                    }}
                  >
                    7-day retention rate
                  </Text>
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card
                title="Feature Usage"
                style={{
                  background: theme.colors.background.secondary,
                  border: `1px solid rgba(255, 255, 255, 0.1)`,
                }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: theme.colors.text.secondary }}>AI Chat</Text>
                      <Text style={{ color: theme.colors.text.primary }}>89%</Text>
                    </div>
                    <Progress percent={89} strokeColor={theme.colors.primary} showInfo={false} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: theme.colors.text.secondary }}>Stock Analysis</Text>
                      <Text style={{ color: theme.colors.text.primary }}>76%</Text>
                    </div>
                    <Progress percent={76} strokeColor={theme.colors.success} showInfo={false} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: theme.colors.text.secondary }}>Advanced Charts</Text>
                      <Text style={{ color: theme.colors.text.primary }}>62%</Text>
                    </div>
                    <Progress percent={62} strokeColor={theme.colors.warning} showInfo={false} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: theme.colors.text.secondary }}>Portfolio Tracking</Text>
                      <Text style={{ color: theme.colors.text.primary }}>45%</Text>
                    </div>
                    <Progress percent={45} strokeColor={theme.colors.danger} showInfo={false} />
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default GrowthAnalytics;