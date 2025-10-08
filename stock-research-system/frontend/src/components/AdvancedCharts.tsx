import React, { useState, useEffect, useMemo } from 'react';
import ReactApexChart from 'react-apexcharts';
import { ApexOptions } from 'apexcharts';
import { Card, Row, Col, Select, Space, Button, Tabs, Badge, Statistic, Tag, Alert, Spin } from 'antd';
import { ArrowUpOutlined, LineChartOutlined } from '@ant-design/icons';

// Error Boundary for Charts
class ChartErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean}> {
  constructor(props: {children: React.ReactNode}) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.warn('Chart rendering error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Alert
          message="Chart Error"
          description="Unable to render chart. Please refresh the page."
          type="warning"
          showIcon
        />
      );
    }

    return this.props.children;
  }
}

const { Option } = Select;
const { TabPane } = Tabs;

interface AdvancedChartsProps {
  symbol: string;
  marketData: any;
  technicalData?: any;
}

const AdvancedCharts: React.FC<AdvancedChartsProps> = ({ symbol, marketData, technicalData }) => {
  const [timeframe, setTimeframe] = useState('1D');
  const [chartType, setChartType] = useState('candlestick');
  const [isLoading, setIsLoading] = useState(true);
  const [chartError, setChartError] = useState(false);

  useEffect(() => {
    // Simulate chart data loading
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  }, [symbol, timeframe]);

  // Candlestick chart configuration
  const candlestickOptions: ApexOptions = {
    chart: {
      type: 'candlestick',
      height: 500,
      toolbar: {
        tools: {
          download: true,
          selection: true,
          zoom: true,
          zoomin: true,
          zoomout: true,
          pan: true,
          reset: true,
        },
      },
      animations: {
        enabled: true,
        speed: 800,
      },
    },
    title: {
      text: `${symbol} - Price Action`,
      align: 'left',
      style: {
        fontSize: '18px',
        fontWeight: 'bold',
      },
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: '#26a69a',
          downward: '#ef5350',
        },
        wick: {
          useFillColor: true,
        },
      },
    },
    xaxis: {
      type: 'datetime',
      labels: {
        format: 'dd MMM',
      },
    },
    yaxis: {
      title: {
        text: 'Price ($)',
      },
      labels: {
        formatter: (value) => '$' + value.toFixed(2),
      },
    },
    tooltip: {
      enabled: true,
      shared: true,
      intersect: false,
    },
    annotations: {
      xaxis: [],
      yaxis: [
        {
          y: marketData?.current_price || 0,
          borderColor: '#00E396',
          label: {
            borderColor: '#00E396',
            style: {
              color: '#fff',
              background: '#00E396',
            },
            text: 'Current Price',
          },
        },
      ],
      points: [],
    },
    grid: {
      borderColor: '#f1f1f1',
    },
  };

  // Generate candlestick data from real market data or show error
  const generateCandlestickData = useMemo(() => {
    return () => {
      // Debug: Show error if no market data
      if (!marketData || !marketData.historical_data) {
        console.error('[AdvancedCharts] No market data available:', {
          marketData,
          symbol,
          timestamp: new Date().toISOString()
        });
        setChartError(true);
        return [];
      }

      try {
        // Use real historical data if available
        const data = marketData.historical_data.map((item: any) => ({
          x: new Date(item.date).getTime(),
          y: [item.open, item.high, item.low, item.close]
        }));

        if (data.length === 0) {
          console.error('[AdvancedCharts] Historical data is empty');
          setChartError(true);
        }

        return data;
      } catch (error) {
        console.error('[AdvancedCharts] Error processing candlestick data:', error);
        setChartError(true);
        return [];
      }
    };
  }, [marketData, symbol]);

  const candlestickSeries = useMemo(() => {
    if (!symbol || isLoading) return [];
    const data = generateCandlestickData();
    if (data.length === 0) {
      console.warn('[AdvancedCharts] No candlestick data to display');
      return [];
    }
    return [{
      name: 'Price',
      data: data,
    }];
  }, [symbol, generateCandlestickData, isLoading]);

  // Technical Indicators Chart
  const indicatorOptions: ApexOptions = {
    chart: {
      height: 350,
      type: 'line',
      toolbar: {
        show: true,
      },
    },
    stroke: {
      curve: 'smooth',
      width: 2,
    },
    title: {
      text: 'Technical Indicators',
      align: 'left',
    },
    grid: {
      borderColor: '#e7e7e7',
      row: {
        colors: ['#f3f3f3', 'transparent'],
        opacity: 0.5,
      },
    },
    markers: {
      size: 1,
    },
    xaxis: {
      categories: ['Oct 2024', 'Nov 2024', 'Dec 2024', 'Jan 2025', 'Feb 2025', 'Mar 2025', 'Apr 2025', 'May 2025', 'Jun 2025', 'Jul 2025', 'Aug 2025', 'Sep 2025'],
      title: {
        text: 'Month',
      },
    },
    yaxis: [
      {
        title: {
          text: 'RSI',
        },
        min: 0,
        max: 100,
      },
      {
        opposite: true,
        title: {
          text: 'MACD',
        },
      },
    ],
    legend: {
      position: 'top',
      horizontalAlign: 'center',
    },
    annotations: {
      yaxis: [
        {
          y: 70,
          borderColor: '#FF4560',
          label: {
            borderColor: '#FF4560',
            style: {
              color: '#fff',
              background: '#FF4560',
            },
            text: 'Overbought',
          },
        },
        {
          y: 30,
          borderColor: '#00E396',
          label: {
            borderColor: '#00E396',
            style: {
              color: '#fff',
              background: '#00E396',
            },
            text: 'Oversold',
          },
        },
      ],
    },
  };

  // Generate indicator data from technical analysis
  const indicatorSeries = useMemo(() => {
    if (!technicalData) {
      console.error('[AdvancedCharts] No technical data available for indicators');
      return [];
    }

    try {
      return [
        {
          name: 'RSI',
          type: 'line',
          data: technicalData.rsi || [],
        },
        {
          name: 'MACD',
          type: 'line',
          data: technicalData.macd || [],
        },
      ];
    } catch (error) {
      console.error('[AdvancedCharts] Error processing indicator data:', error);
      return [];
    }
  }, [technicalData]);

  // Volume Chart
  const volumeOptions: ApexOptions = {
    chart: {
      height: 200,
      type: 'bar',
      brush: {
        enabled: true,
        target: 'candlestick',
      },
      selection: {
        enabled: true,
      },
    },
    dataLabels: {
      enabled: false,
    },
    plotOptions: {
      bar: {
        columnWidth: '80%',
        colors: {
          ranges: [{
            from: -1000,
            to: 0,
            color: '#ef5350',
          }, {
            from: 1,
            to: 10000000,
            color: '#26a69a',
          }],
        },
      },
    },
    stroke: {
      width: 0,
    },
    xaxis: {
      type: 'datetime',
      axisBorder: {
        offsetX: 13,
      },
    },
    yaxis: {
      labels: {
        formatter: (val) => (val / 1000000).toFixed(0) + 'M',
      },
    },
    title: {
      text: 'Volume',
      align: 'left',
    },
  };

  // Generate volume data from real market data
  const volumeSeries = useMemo(() => {
    if (!symbol || isLoading) return [];

    // Debug: Check for volume data
    if (!marketData || !marketData.historical_data) {
      console.error('[AdvancedCharts] No volume data available');
      return [];
    }

    try {
      const data = marketData.historical_data.map((item: any) => ({
        x: new Date(item.date).getTime(),
        y: item.volume || 0
      }));

      if (data.length === 0) {
        console.warn('[AdvancedCharts] Volume data is empty');
      }

      return [{
        name: 'Volume',
        data: data
      }];
    } catch (error) {
      console.error('[AdvancedCharts] Error generating volume data:', error);
      return [];
    }
  }, [symbol, marketData, isLoading]);

  // Heatmap for correlation
  const correlationOptions: ApexOptions = {
    chart: {
      height: 350,
      type: 'heatmap',
    },
    dataLabels: {
      enabled: true,
    },
    colors: ['#FF4560'],
    title: {
      text: 'Sector Correlation Matrix',
    },
    xaxis: {
      categories: ['Tech', 'Finance', 'Healthcare', 'Energy', 'Consumer'],
    },
  };

  const correlationSeries = useMemo(() => {
    if (!marketData || !marketData.correlations) {
      console.error('[AdvancedCharts] No correlation data available');
      return [];
    }

    try {
      // Use real correlation data if available
      return marketData.correlations || [];
    } catch (error) {
      console.error('[AdvancedCharts] Error processing correlation data:', error);
      return [];
    }
  }, [marketData]);

  if (!symbol) {
    return (
      <Card>
        <Alert
          message="No Symbol Selected"
          description="Please select a stock symbol to view charts."
          type="info"
          showIcon
        />
      </Card>
    );
  }

  if (chartError) {
    return (
      <Card>
        <Alert
          message="Chart Data Error"
          description={
            <div>
              <p>Unable to load chart data. Debug information:</p>
              <ul style={{ fontSize: '12px', marginTop: '8px' }}>
                <li>Symbol: {symbol || 'Not provided'}</li>
                <li>Market Data: {marketData ? 'Available' : 'Missing'}</li>
                <li>Technical Data: {technicalData ? 'Available' : 'Missing'}</li>
                <li>Historical Data: {marketData?.historical_data ? `${marketData.historical_data.length} points` : 'Missing'}</li>
                <li>Timestamp: {new Date().toISOString()}</li>
              </ul>
              <p style={{ marginTop: '8px' }}>Check console for detailed error logs.</p>
            </div>
          }
          type="error"
          showIcon
          action={
            <Space>
              <Button size="small" onClick={() => setChartError(false)}>
                Retry
              </Button>
              <Button size="small" onClick={() => window.location.reload()}>
                Refresh Page
              </Button>
            </Space>
          }
        />
      </Card>
    );
  }

  return (
    <div>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Select value={timeframe} onChange={setTimeframe} style={{ width: 120 }}>
            <Option value="1D">1 Day</Option>
            <Option value="1W">1 Week</Option>
            <Option value="1M">1 Month</Option>
            <Option value="3M">3 Months</Option>
            <Option value="1Y">1 Year</Option>
          </Select>
          <Select value={chartType} onChange={setChartType} style={{ width: 120 }}>
            <Option value="candlestick">Candlestick</Option>
            <Option value="line">Line</Option>
            <Option value="area">Area</Option>
          </Select>
          <Button icon={<LineChartOutlined />}>Add Indicator</Button>
        </Space>

        <Tabs defaultActiveKey="1">
          <TabPane tab="Price Action" key="1">
            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '50px 0' }}>
                <Spin size="large" tip="Loading chart data..." />
              </div>
            ) : (
              <>
                <ChartErrorBoundary>
                  {candlestickSeries.length > 0 ? (
                    <ReactApexChart
                      options={candlestickOptions}
                      series={candlestickSeries}
                      type="candlestick"
                      height={500}
                    />
                  ) : (
                    <Alert
                      message="No Candlestick Data"
                      description={`No historical price data available for ${symbol}. Please check if the market data API is returning historical data.`}
                      type="warning"
                      showIcon
                    />
                  )}
                </ChartErrorBoundary>
                <ChartErrorBoundary>
                  {volumeSeries.length > 0 ? (
                    <ReactApexChart
                      options={volumeOptions}
                      series={volumeSeries}
                      type="bar"
                      height={200}
                    />
                  ) : (
                    <Alert
                      message="No Volume Data"
                      description="Volume data is not available. Check console for details."
                      type="info"
                      showIcon
                    />
                  )}
                </ChartErrorBoundary>
              </>
            )}
          </TabPane>

          <TabPane tab="Technical Indicators" key="2">
            <Row gutter={16}>
              <Col span={16}>
                <ChartErrorBoundary>
                  {!isLoading && indicatorSeries.length > 0 && (
                    <ReactApexChart
                      options={indicatorOptions}
                      series={indicatorSeries}
                      type="line"
                      height={350}
                    />
                  )}
                  {isLoading && (
                    <div style={{ textAlign: 'center', padding: '50px 0' }}>
                      <Spin size="large" tip="Loading indicators..." />
                    </div>
                  )}
                </ChartErrorBoundary>
              </Col>
              <Col span={8}>
                <Card title="Indicator Signals">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Badge status="success" text="RSI: 52 (Neutral)" />
                    </div>
                    <div>
                      <Badge status="processing" text="MACD: Bullish Crossover" />
                    </div>
                    <div>
                      <Badge status="warning" text="Stochastic: 78 (Overbought)" />
                    </div>
                    <div>
                      <Badge status="success" text="Moving Avg: Above 50 MA" />
                    </div>
                    <div>
                      <Badge status="error" text="Volume: Below Average" />
                    </div>
                  </Space>
                </Card>

                <Card title="Pattern Recognition" style={{ marginTop: 16 }}>
                  <Space direction="vertical">
                    <Tag color="green">Ascending Triangle</Tag>
                    <Tag color="blue">Support at $425</Tag>
                    <Tag color="red">Resistance at $450</Tag>
                    <Tag color="purple">Cup & Handle Forming</Tag>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="Market Correlation" key="3">
            <ChartErrorBoundary>
              {!isLoading && correlationSeries.length > 0 && (
                <ReactApexChart
                  options={correlationOptions}
                  series={correlationSeries}
                  type="heatmap"
                  height={350}
                />
              )}
              {isLoading && (
                <div style={{ textAlign: 'center', padding: '50px 0' }}>
                  <Spin size="large" tip="Loading correlation data..." />
                </div>
              )}
            </ChartErrorBoundary>
          </TabPane>

          <TabPane
            tab={
              <span>
                AI Insights
                <Badge count="New" style={{ marginLeft: 8 }} />
              </span>
            }
            key="4"
          >
            <Row gutter={16}>
              <Col span={12}>
                <Card title="Bullish Signals" bordered={false}>
                  <Space direction="vertical">
                    <div>✅ RSI showing positive divergence</div>
                    <div>✅ Volume increasing on up days</div>
                    <div>✅ Breaking above 50-day MA</div>
                    <div>✅ Institutional accumulation detected</div>
                  </Space>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="Bearish Signals" bordered={false}>
                  <Space direction="vertical">
                    <div>❌ Declining momentum indicators</div>
                    <div>❌ Resistance at key level</div>
                    <div>❌ Negative sector rotation</div>
                    <div>❌ High volatility warning</div>
                  </Space>
                </Card>
              </Col>
            </Row>

            <Card title="AI Trading Recommendation" style={{ marginTop: 16 }}>
              <Statistic
                title="Signal Strength"
                value={75}
                suffix="%"
                valueStyle={{ color: '#3f8600' }}
                prefix={<ArrowUpOutlined />}
              />
              <p>
                <strong>Entry Point:</strong> $428.50<br />
                <strong>Stop Loss:</strong> $420.00<br />
                <strong>Target 1:</strong> $445.00<br />
                <strong>Target 2:</strong> $458.00<br />
                <strong>Risk/Reward:</strong> 1:2.5
              </p>
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default AdvancedCharts;