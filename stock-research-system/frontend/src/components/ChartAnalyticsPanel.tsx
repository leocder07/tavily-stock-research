import React, { useState, useEffect } from 'react';
import ReactApexChart from 'react-apexcharts';
import { ApexOptions } from 'apexcharts';
import { Card, Row, Col, Tabs, Spin, Alert, Statistic, Tag, Space, Typography } from 'antd';
import {
  LineChartOutlined,
  RiseOutlined,
  FallOutlined,
  ThunderboltOutlined,
  AlertOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface ChartAnalyticsProps {
  symbol: string;
}

interface ChartData {
  symbol: string;
  timestamp: string;
  chart_data: {
    price_charts: any;
    indicator_charts: any;
    technical_overlays: any;
  };
  pattern_analysis: {
    patterns: any[];
    current_trend: string;
    trend_strength: number;
    reversal_probability: number;
  };
  support_resistance: {
    pivot_point: number;
    support_levels: number[];
    resistance_levels: number[];
    fibonacci_retracements: any;
    current_price: number;
    nearest_support: number;
    nearest_resistance: number;
  };
  volume_profile: any;
  multi_timeframe: any;
  expert_insights: any;
}

const ChartAnalyticsPanel: React.FC<ChartAnalyticsProps> = ({ symbol }) => {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchChartData();
  }, [symbol]);

  const fetchChartData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`http://localhost:8000/api/v1/charts/${symbol}`);
      setChartData(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch chart data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <p style={{ marginTop: 16 }}>Loading chart analytics...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert
        message="Chart Analytics Error"
        description={error}
        type="error"
        showIcon
      />
    );
  }

  if (!chartData) return null;

  // Candlestick chart configuration
  const candlestickOptions: ApexOptions = {
    chart: {
      type: 'candlestick',
      height: 450,
      toolbar: {
        show: true,
        tools: {
          download: true,
          zoom: true,
          zoomin: true,
          zoomout: true,
          pan: true,
          reset: true,
        },
      },
    },
    title: {
      text: `${symbol} - Expert Trading Chart`,
      align: 'left',
      style: {
        fontSize: '16px',
        fontWeight: '600',
      },
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: '#00D084',
          downward: '#FF4560',
        },
      },
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeUTC: false,
      },
    },
    yaxis: {
      tooltip: {
        enabled: true,
      },
      labels: {
        formatter: (value: number) => `$${value.toFixed(2)}`,
      },
    },
    annotations: {
      yaxis: [
        ...(chartData.support_resistance.support_levels || []).map((level: number) => ({
          y: level,
          borderColor: '#00D084',
          label: {
            text: `Support: $${level.toFixed(2)}`,
            style: {
              color: '#fff',
              background: '#00D084',
            },
          },
        })),
        ...(chartData.support_resistance.resistance_levels || []).map((level: number) => ({
          y: level,
          borderColor: '#FF4560',
          label: {
            text: `Resistance: $${level.toFixed(2)}`,
            style: {
              color: '#fff',
              background: '#FF4560',
            },
          },
        })),
      ],
    },
  };

  const candlestickSeries = [{
    name: 'Price',
    data: (chartData.chart_data.price_charts?.candlestick?.data?.dates || []).map((date: string, i: number) => ({
      x: new Date(date).getTime(),
      y: [
        chartData.chart_data.price_charts.candlestick.data.open[i],
        chartData.chart_data.price_charts.candlestick.data.high[i],
        chartData.chart_data.price_charts.candlestick.data.low[i],
        chartData.chart_data.price_charts.candlestick.data.close[i],
      ],
    })),
  }];

  // RSI Chart
  const rsiOptions: ApexOptions = {
    chart: {
      type: 'line',
      height: 200,
      toolbar: { show: false },
    },
    title: {
      text: 'RSI (14)',
      align: 'left',
      style: { fontSize: '14px' },
    },
    stroke: {
      width: 2,
      colors: ['#775DD0'],
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeUTC: false,
      },
    },
    yaxis: {
      min: 0,
      max: 100,
      labels: {
        formatter: (value: number) => value.toFixed(0),
      },
    },
    annotations: {
      yaxis: [
        { y: 70, borderColor: '#FF4560', strokeDashArray: 4, label: { text: 'Overbought' } },
        { y: 30, borderColor: '#00D084', strokeDashArray: 4, label: { text: 'Oversold' } },
      ],
    },
  };

  const rsiSeries = [{
    name: 'RSI',
    data: (chartData.chart_data.indicator_charts?.rsi?.dates || []).map((date: string, i: number) => ({
      x: new Date(date).getTime(),
      y: chartData.chart_data.indicator_charts.rsi.values[i],
    })),
  }];

  // MACD Chart
  const macdOptions: ApexOptions = {
    chart: {
      type: 'line',
      height: 200,
      toolbar: { show: false },
    },
    title: {
      text: 'MACD',
      align: 'left',
      style: { fontSize: '14px' },
    },
    stroke: {
      width: [2, 2, 1],
      dashArray: [0, 0, 4],
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeUTC: false,
      },
    },
    colors: ['#008FFB', '#FF4560', '#FEB019'],
  };

  const macdSeries = [
    {
      name: 'MACD',
      type: 'line',
      data: (chartData.chart_data.indicator_charts?.macd?.dates || []).map((date: string, i: number) => ({
        x: new Date(date).getTime(),
        y: chartData.chart_data.indicator_charts.macd.macd[i],
      })),
    },
    {
      name: 'Signal',
      type: 'line',
      data: (chartData.chart_data.indicator_charts?.macd?.dates || []).map((date: string, i: number) => ({
        x: new Date(date).getTime(),
        y: chartData.chart_data.indicator_charts.macd.signal[i],
      })),
    },
    {
      name: 'Histogram',
      type: 'column',
      data: (chartData.chart_data.indicator_charts?.macd?.dates || []).map((date: string, i: number) => ({
        x: new Date(date).getTime(),
        y: chartData.chart_data.indicator_charts.macd.histogram[i],
      })),
    },
  ];

  return (
    <div style={{ padding: '0' }}>
      <Tabs defaultActiveKey="1" type="card">
        <TabPane
          tab={
            <span>
              <LineChartOutlined />
              Price Chart
            </span>
          }
          key="1"
        >
          <Card>
            {/* Main Candlestick Chart */}
            <ReactApexChart
              options={candlestickOptions}
              series={candlestickSeries}
              type="candlestick"
              height={450}
            />

            {/* Pattern Analysis */}
            <Card
              title="Pattern Analysis"
              size="small"
              style={{ marginTop: 16 }}
            >
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="Current Trend"
                    value={chartData.pattern_analysis?.current_trend || 'N/A'}
                    prefix={
                      chartData.pattern_analysis?.current_trend === 'bullish' ?
                      <RiseOutlined style={{ color: '#00D084' }} /> :
                      <FallOutlined style={{ color: '#FF4560' }} />
                    }
                    valueStyle={{
                      color: chartData.pattern_analysis?.current_trend === 'bullish' ? '#00D084' : '#FF4560'
                    }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Trend Strength"
                    value={(chartData.pattern_analysis?.trend_strength || 0) * 100}
                    suffix="%"
                    precision={1}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Reversal Probability"
                    value={(chartData.pattern_analysis?.reversal_probability || 0) * 100}
                    suffix="%"
                    precision={1}
                    prefix={<AlertOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>Detected Patterns</Text>
                    <div style={{ marginTop: 8 }}>
                      {(chartData.pattern_analysis?.patterns || []).slice(0, 3).map((pattern: any, i: number) => (
                        <Tag key={i} color={pattern.type === 'bullish' ? 'green' : 'red'}>
                          {pattern.name}
                        </Tag>
                      ))}
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>

            {/* Support & Resistance */}
            <Card
              title="Support & Resistance Levels"
              size="small"
              style={{ marginTop: 16 }}
            >
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="Current Price"
                    value={chartData.support_resistance?.current_price || 0}
                    prefix="$"
                    precision={2}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Nearest Support"
                    value={chartData.support_resistance?.nearest_support || 0}
                    prefix="$"
                    precision={2}
                    valueStyle={{ color: '#00D084' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Nearest Resistance"
                    value={chartData.support_resistance?.nearest_resistance || 0}
                    prefix="$"
                    precision={2}
                    valueStyle={{ color: '#FF4560' }}
                  />
                </Col>
              </Row>
            </Card>
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <ThunderboltOutlined />
              Technical Indicators
            </span>
          }
          key="2"
        >
          <Card>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* RSI */}
              <div>
                <ReactApexChart
                  options={rsiOptions}
                  series={rsiSeries}
                  type="line"
                  height={200}
                />
              </div>

              {/* MACD */}
              <div>
                <ReactApexChart
                  options={macdOptions}
                  series={macdSeries}
                  type="line"
                  height={200}
                />
              </div>

              {/* Volume */}
              {chartData.chart_data.indicator_charts?.volume && (
                <div>
                  <ReactApexChart
                    options={{
                      chart: {
                        type: 'bar',
                        height: 150,
                        toolbar: { show: false },
                      },
                      title: {
                        text: 'Volume',
                        align: 'left',
                        style: { fontSize: '14px' },
                      },
                      xaxis: {
                        type: 'datetime',
                        labels: {
                          datetimeUTC: false,
                        },
                      },
                      colors: ['#008FFB'],
                    }}
                    series={[{
                      name: 'Volume',
                      data: (chartData.chart_data.indicator_charts.volume.dates || []).map((date: string, i: number) => ({
                        x: new Date(date).getTime(),
                        y: chartData.chart_data.indicator_charts.volume.values[i],
                      })),
                    }]}
                    type="bar"
                    height={150}
                  />
                </div>
              )}
            </Space>
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <AlertOutlined />
              Expert Insights
            </span>
          }
          key="3"
        >
          <Card>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* Multi-Timeframe Analysis */}
              {chartData.multi_timeframe && (
                <Card title="Multi-Timeframe Analysis" size="small">
                  <Row gutter={16}>
                    {Object.entries(chartData.multi_timeframe).map(([timeframe, data]: [string, any]) => (
                      <Col span={6} key={timeframe}>
                        <Statistic
                          title={timeframe.toUpperCase()}
                          value={data?.trend || 'N/A'}
                          valueStyle={{
                            color: data?.trend === 'bullish' ? '#00D084' :
                                   data?.trend === 'bearish' ? '#FF4560' : '#666',
                          }}
                        />
                      </Col>
                    ))}
                  </Row>
                </Card>
              )}

              {/* Expert Insights */}
              {chartData.expert_insights && (
                <Card title="Trading Insights" size="small">
                  <Paragraph>
                    <Text strong>Summary: </Text>
                    {chartData.expert_insights.summary || 'No insights available'}
                  </Paragraph>
                  {chartData.expert_insights.key_levels && (
                    <>
                      <Title level={5}>Key Levels to Watch</Title>
                      <ul>
                        {chartData.expert_insights.key_levels.map((level: string, i: number) => (
                          <li key={i}>{level}</li>
                        ))}
                      </ul>
                    </>
                  )}
                  {chartData.expert_insights.trading_strategy && (
                    <>
                      <Title level={5}>Trading Strategy</Title>
                      <Paragraph>{chartData.expert_insights.trading_strategy}</Paragraph>
                    </>
                  )}
                </Card>
              )}
            </Space>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default ChartAnalyticsPanel;
