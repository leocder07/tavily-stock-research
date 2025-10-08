import React, { useState, useEffect, useCallback } from 'react';
import {
  Row,
  Col,
  Card,
  Tag,
  Space,
  Progress,
  Badge,
  Spin,
  Skeleton,
} from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  FireOutlined,
  GlobalOutlined,
  StockOutlined,
  FundOutlined,
} from '@ant-design/icons';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { theme } from '../styles/theme';


interface MarketOverviewProps {
  watchlist: string[];
}

const MarketOverview: React.FC<MarketOverviewProps> = ({ watchlist }) => {
  const [marketIndices, setMarketIndices] = useState<any[]>([]);
  const [sectorPerformance, setSectorPerformance] = useState<any[]>([]);
  const [aiInsights, setAiInsights] = useState<any[]>([]);
  const [topMovers, setTopMovers] = useState<any>({ gainers: [], losers: [] });
  const [sentimentData, setSentimentData] = useState<any[]>([]);

  // Separate loading states for each section
  const [indicesLoading, setIndicesLoading] = useState(true);
  const [sectorLoading, setSectorLoading] = useState(true);
  const [insightsLoading, setInsightsLoading] = useState(true);
  const [topMoversLoading, setTopMoversLoading] = useState(true);
  const [sentimentLoading, setSentimentLoading] = useState(true);

  useEffect(() => {
    fetchMarketData();
    const interval = setInterval(fetchMarketData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const fetchMarketData = async () => {
    try {
      // Fetch market indices
      setIndicesLoading(true);
      const indicesSymbols = ['SPY', 'QQQ', 'DIA', 'IWM'];
      const indicesPromises = indicesSymbols.map(symbol =>
        fetch(`http://localhost:8000/api/v1/market/price/${symbol}`)
          .then(res => res.json())
          .catch(() => null)
      );

      const indicesData = await Promise.all(indicesPromises);
      const formattedIndices = indicesData
        .filter(data => data && data.price)
        .map((data, idx) => ({
          name: ['S&P 500 (SPY)', 'NASDAQ (QQQ)', 'DOW JONES (DIA)', 'RUSSELL 2000 (IWM)'][idx],
          value: data.price,
          change: data.changePercent || data.change_percent || 0,
          data: generateSparklineData(20, data.price * 0.95, data.price * 1.05)
        }));

      if (formattedIndices.length > 0) {
        setMarketIndices(formattedIndices);
      }
      setIndicesLoading(false);

      // Fetch sector performance
      setSectorLoading(true);
      try {
        const sectorRes = await fetch('http://localhost:8000/api/v1/market/sectors');
        if (sectorRes.ok) {
          const sectorData = await sectorRes.json();
          if (sectorData.sectors) {
            setSectorPerformance(sectorData.sectors);
          }
        }
      } catch {
        // Use default sectors if API fails
        setSectorPerformance([
          { sector: 'Technology', performance: 3.2, volume: 850, sentiment: 85 },
          { sector: 'Healthcare', performance: 2.1, volume: 620, sentiment: 72 },
          { sector: 'Finance', performance: 1.8, volume: 740, sentiment: 68 },
          { sector: 'Energy', performance: -0.5, volume: 410, sentiment: 45 },
          { sector: 'Consumer', performance: 1.2, volume: 560, sentiment: 60 },
          { sector: 'Real Estate', performance: -1.2, volume: 320, sentiment: 38 },
        ]);
      } finally {
        setSectorLoading(false);
      }

      // Fetch market news for insights
      setInsightsLoading(true);
      try {
        const newsRes = await fetch('http://localhost:8000/api/v1/market/news?limit=4');
        if (newsRes.ok) {
          const newsData = await newsRes.json();
          if (newsData.news && newsData.news.length > 0) {
            const insights = newsData.news.map((item: any) => ({
              type: item.sentiment === 'positive' ? 'bullish' : item.sentiment === 'negative' ? 'bearish' : 'warning',
              title: item.title || 'Market Update',
              description: item.summary || item.description || '',
              confidence: item.confidence || 75
            }));
            setAiInsights(insights);
          }
        }
      } catch {
        // Use default insights if API fails
        setAiInsights([
          { type: 'bullish', title: 'Tech Rally Continues', description: 'AI stocks leading gains with +5% avg movement', confidence: 92 },
          { type: 'warning', title: 'Fed Meeting Impact', description: 'Rate decision tomorrow, expect volatility', confidence: 78 },
          { type: 'bearish', title: 'Energy Sector Weakness', description: 'Oil prices declining, sector under pressure', confidence: 85 },
          { type: 'bullish', title: 'Earnings Beat', description: '78% of S&P companies beating estimates', confidence: 88 },
        ]);
      } finally {
        setInsightsLoading(false);
      }

      // Fetch top movers
      try {
        setTopMoversLoading(true);
        const topStocksRes = await fetch('http://localhost:8000/api/v1/analytics/top-stocks');
        if (topStocksRes.ok) {
          const topStocksData = await topStocksRes.json();
          // Map API response to component format
          if (topStocksData.gainers && topStocksData.losers) {
            setTopMovers({
              gainers: topStocksData.gainers.map((stock: any) => ({
                symbol: stock.symbol,
                name: stock.name,
                price: stock.price,
                change: stock.changePercent,
                volume: stock.volume
              })),
              losers: topStocksData.losers.map((stock: any) => ({
                symbol: stock.symbol,
                name: stock.name,
                price: stock.price,
                change: stock.changePercent,
                volume: stock.volume
              }))
            });
          }
        }
      } catch (error) {
        console.error('Error fetching top movers:', error);
      } finally {
        setTopMoversLoading(false);
      }

      // Fetch sentiment heat map data
      setSentimentLoading(true);
      try {
        const sentimentSymbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD'];
        const sentimentPromises = sentimentSymbols.map(symbol =>
          fetch(`http://localhost:8000/api/v1/market/price/${symbol}`)
            .then(res => res.json())
            .catch(() => null)
        );

        const sentimentResults = await Promise.all(sentimentPromises);
        const formattedSentiment = sentimentResults
          .map((data, idx) => ({
            symbol: sentimentSymbols[idx],
            sentiment: data?.changePercent || data?.change_percent || 0,
            volume: data?.volume || 0
          }));

        setSentimentData(formattedSentiment);
      } catch (error) {
        console.error('Error fetching sentiment data:', error);
      } finally {
        setSentimentLoading(false);
      }
    } catch (error) {
      console.error('Error fetching market data:', error);
    }
  };

  const generateSparklineData = useCallback((points: number, min: number, max: number) => {
    // Use a stable seed based on min/max to prevent re-renders
    const seed = Math.round(min + max);
    return Array.from({ length: points }, (_, i) => ({
      x: i,
      y: min + ((seed + i * 123) % 1000) / 1000 * (max - min),
    }));
  }, []);

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'bullish':
        return <ArrowUpOutlined style={{ color: theme.colors.success }} />;
      case 'bearish':
        return <ArrowDownOutlined style={{ color: theme.colors.danger }} />;
      case 'warning':
        return <FireOutlined style={{ color: theme.colors.warning }} />;
      default:
        return <GlobalOutlined style={{ color: theme.colors.primary }} />;
    }
  };

  return (
    <div>
      {/* Market Indices Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {indicesLoading ? (
          // Show skeleton loaders while fetching indices
          [0, 1, 2, 3].map((i) => (
            <Col key={i} xs={24} sm={12} lg={6}>
              <Card
                style={{
                  background: theme.colors.background.secondary,
                  border: `1px solid rgba(255, 255, 255, 0.08)`,
                  borderRadius: theme.borderRadius.lg,
                }}
                styles={{ body: { padding: 20 } }}
              >
                <Skeleton active paragraph={{ rows: 2 }} />
              </Card>
            </Col>
          ))
        ) : (
          marketIndices.map((index) => (
            <Col key={index.name} xs={24} sm={12} lg={6}>
              <Card
                style={{
                  background: theme.colors.background.secondary,
                  border: `1px solid rgba(255, 255, 255, 0.08)`,
                  borderRadius: theme.borderRadius.lg,
                }}
                styles={{ body: { padding: 20 } }}
              >
                <div style={{ marginBottom: 12 }}>
                  <div style={{ color: theme.colors.text.muted, fontSize: 12, fontWeight: 600 }}>
                    {index.name}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', marginBottom: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 700 }}>
                    {index.value.toLocaleString()}
                  </div>
                  <Tag
                    color={index.change > 0 ? 'success' : 'error'}
                    style={{ marginLeft: 12 }}
                    icon={index.change > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  >
                    {Math.abs(index.change)}%
                  </Tag>
                </div>
                <ResponsiveContainer width="100%" height={40}>
                  <AreaChart data={index.data}>
                    <defs>
                      <linearGradient id={`gradient-${index.name}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={index.change > 0 ? theme.colors.success : theme.colors.danger} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={index.change > 0 ? theme.colors.success : theme.colors.danger} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area
                      type="monotone"
                      dataKey="y"
                      stroke={index.change > 0 ? theme.colors.success : theme.colors.danger}
                      fill={`url(#gradient-${index.name})`}
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          ))
        )}
      </Row>

      <Row gutter={[16, 16]}>
        {/* AI Market Insights */}
        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <div style={{
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  background: theme.colors.gradient.primary,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <FireOutlined style={{ color: '#fff', fontSize: 16 }} />
                </div>
                <div style={{ fontSize: 16, fontWeight: 600 }}>AI Market Insights</div>
              </Space>
            }
            style={{
              background: theme.colors.background.secondary,
              border: `1px solid rgba(255, 255, 255, 0.08)`,
              height: '100%',
            }}
            styles={{
              header: {
                borderBottom: `1px solid rgba(255, 255, 255, 0.08)`,
              },
            }}
          >
            {insightsLoading ? (
              <Skeleton active paragraph={{ rows: 4 }} />
            ) : (
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                {aiInsights.map((insight, index) => (
                  <Card
                    key={index}
                    size="small"
                    style={{
                      background: theme.colors.background.elevated,
                      border: `1px solid rgba(255, 255, 255, 0.05)`,
                    }}
                    hoverable
                  >
                    <Space align="start">
                      {getInsightIcon(insight.type)}
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div style={{ fontSize: 14, fontWeight: 600 }}>{insight.title}</div>
                          <Badge
                            count={`${insight.confidence}%`}
                            style={{
                              backgroundColor: insight.confidence > 80 ? theme.colors.success : theme.colors.warning,
                              fontSize: 10,
                            }}
                          />
                        </div>
                        <div style={{ fontSize: 12, color: theme.colors.text.secondary }}>
                          {insight.description}
                        </div>
                      </div>
                    </Space>
                  </Card>
                ))}
              </Space>
            )}
          </Card>
        </Col>

        {/* Sector Performance */}
        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <FundOutlined style={{ color: theme.colors.primary }} />
                <div style={{ fontSize: 16, fontWeight: 600 }}>Sector Performance</div>
              </Space>
            }
            style={{
              background: theme.colors.background.secondary,
              border: `1px solid rgba(255, 255, 255, 0.08)`,
              height: '100%',
            }}
            styles={{
              header: {
                borderBottom: `1px solid rgba(255, 255, 255, 0.08)`,
              },
            }}
          >
            {sectorLoading ? (
              <Skeleton active paragraph={{ rows: 5 }} />
            ) : (
              <Space direction="vertical" style={{ width: '100%' }} size="small">
                {sectorPerformance.map((sector) => (
                  <div key={sector.sector} style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <div style={{ fontSize: 13 }}>{sector.sector}</div>
                      <Tag color={sector.performance > 0 ? 'success' : 'error'}>
                        {sector.performance > 0 ? '+' : ''}{sector.performance}%
                      </Tag>
                    </div>
                    <Progress
                      percent={Math.abs(sector.performance) * 10}
                      strokeColor={sector.performance > 0 ? theme.colors.success : theme.colors.danger}
                      trailColor={theme.colors.background.elevated}
                      showInfo={false}
                      size={['100%', 6]}
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                      <div style={{ fontSize: 11, color: theme.colors.text.muted }}>
                        Vol: {sector.volume}M
                      </div>
                      <div style={{ fontSize: 11, color: theme.colors.text.muted }}>
                        Sentiment: {sector.sentiment}%
                      </div>
                    </div>
                  </div>
                ))}
              </Space>
            )}
          </Card>
        </Col>

        {/* Top Movers */}
        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <StockOutlined style={{ color: theme.colors.primary }} />
                <div style={{ fontSize: 16, fontWeight: 600 }}>Top Movers</div>
              </Space>
            }
            style={{
              background: theme.colors.background.secondary,
              border: `1px solid rgba(255, 255, 255, 0.08)`,
              height: '100%',
            }}
            styles={{
              header: {
                borderBottom: `1px solid rgba(255, 255, 255, 0.08)`,
              },
            }}
          >
            <div>
              <div style={{ color: theme.colors.success, fontSize: 12, fontWeight: 600 }}>
                TOP GAINERS
              </div>
              <Space direction="vertical" style={{ width: '100%', marginTop: 8, marginBottom: 20 }}>
                {topMoversLoading ? (
                  <div style={{ textAlign: 'center', padding: '20px 0', color: theme.colors.text.muted }}>
                    <Spin size="small" />
                    <div style={{ marginTop: 8, fontSize: 12 }}>Loading top gainers...</div>
                  </div>
                ) : topMovers.gainers.length > 0 ? (
                  topMovers.gainers.map((stock: any) => (
                    <div
                      key={stock.symbol}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '8px 12px',
                        background: theme.colors.background.elevated,
                        borderRadius: 8,
                        cursor: 'pointer',
                      }}
                    >
                      <div>
                        <span style={{ fontSize: 14, fontWeight: 600 }}>{stock.symbol}</span>
                        <span style={{ fontSize: 11, color: theme.colors.text.muted, marginLeft: 8 }}>
                          {stock.name}
                        </span>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ color: theme.colors.success, fontWeight: 600 }}>
                          +{stock.change}%
                        </span>
                        <span style={{ fontSize: 11, color: theme.colors.text.muted, marginLeft: 8 }}>
                          ${stock.price}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ textAlign: 'center', padding: '20px 0', color: theme.colors.text.muted, fontSize: 12 }}>
                    No gainers available
                  </div>
                )}
              </Space>

              <div style={{ color: theme.colors.danger, fontSize: 12, fontWeight: 600 }}>
                TOP LOSERS
              </div>
              <Space direction="vertical" style={{ width: '100%', marginTop: 8 }}>
                {topMoversLoading ? (
                  <div style={{ textAlign: 'center', padding: '20px 0', color: theme.colors.text.muted }}>
                    <Spin size="small" />
                    <div style={{ marginTop: 8, fontSize: 12 }}>Loading top losers...</div>
                  </div>
                ) : topMovers.losers.length > 0 ? (
                  topMovers.losers.map((stock: any) => (
                    <div
                      key={stock.symbol}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '8px 12px',
                        background: theme.colors.background.elevated,
                        borderRadius: 8,
                        cursor: 'pointer',
                      }}
                    >
                      <div>
                        <span style={{ fontSize: 14, fontWeight: 600 }}>{stock.symbol}</span>
                        <span style={{ fontSize: 11, color: theme.colors.text.muted, marginLeft: 8 }}>
                          {stock.name}
                        </span>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ color: theme.colors.danger, fontWeight: 600 }}>
                          {stock.change}%
                        </span>
                        <span style={{ fontSize: 11, color: theme.colors.text.muted, marginLeft: 8 }}>
                          ${stock.price}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ textAlign: 'center', padding: '20px 0', color: theme.colors.text.muted, fontSize: 12 }}>
                    No losers available
                  </div>
                )}
              </Space>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Market Heat Map */}
      <Card
        title={
          <Space>
            <GlobalOutlined style={{ color: theme.colors.primary }} />
            <div style={{ fontSize: 16, fontWeight: 600 }}>Market Sentiment Heat Map</div>
          </Space>
        }
        style={{
          background: theme.colors.background.secondary,
          border: `1px solid rgba(255, 255, 255, 0.08)`,
          marginTop: 16,
        }}
        styles={{
          header: {
            borderBottom: `1px solid rgba(255, 255, 255, 0.08)`,
          },
        }}
      >
        {sentimentLoading ? (
          <Skeleton active paragraph={{ rows: 3 }} />
        ) : (
          <Row gutter={[8, 8]}>
            {sentimentData.length > 0 ? sentimentData.map((item) => {
              const sentiment = item.sentiment || 0;
              const volume = item.volume ? Math.min((item.volume / 100000000) * 100, 100) : 0;
              return (
                <Col key={item.symbol} xs={6} sm={4} lg={3}>
                  <div
                    style={{
                      background: sentiment > 0
                        ? `rgba(0, 208, 133, ${Math.min(Math.abs(sentiment) / 5, 0.8)})`
                        : `rgba(255, 71, 87, ${Math.min(Math.abs(sentiment) / 5, 0.8)})`,
                      border: `1px solid rgba(255, 255, 255, 0.1)`,
                      borderRadius: 8,
                      padding: 12,
                      textAlign: 'center',
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                    }}
                  >
                    <div style={{ fontSize: 14, fontWeight: 600 }}>{item.symbol}</div>
                    <div>
                      <div style={{
                        fontSize: 12,
                        color: sentiment > 0 ? theme.colors.success : theme.colors.danger,
                      }}>
                        {sentiment > 0 ? '+' : ''}{sentiment.toFixed(1)}%
                      </div>
                    </div>
                    <Progress
                      percent={volume}
                      showInfo={false}
                      strokeColor={theme.colors.primary}
                      trailColor={theme.colors.background.elevated}
                      size={['100%', 4]}
                      style={{ marginTop: 4 }}
                    />
                  </div>
                </Col>
              );
            }) : (
              <Col span={24}>
                <div style={{ textAlign: 'center', color: theme.colors.text.muted, padding: 20 }}>
                Loading sentiment data...
              </div>
            </Col>
            )}
          </Row>
        )}
      </Card>
    </div>
  );
};

export default MarketOverview;