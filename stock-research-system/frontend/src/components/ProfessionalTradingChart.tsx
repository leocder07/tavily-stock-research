import React, { useMemo } from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area
} from 'recharts';
import { Card, Tag } from 'antd';
import theme from '../styles/theme';

interface TradingChartProps {
  data: {
    dates: string[];
    open: number[];
    high: number[];
    low: number[];
    close: number[];
    volume?: number[];
  };
  symbol: string;
  technicalOverlays?: {
    sma_20?: number[];
    sma_50?: number[];
    sma_200?: number[];
    ema_12?: number[];
    ema_26?: number[];
    vwap?: number[];
  };
  indicatorData?: {
    rsi?: { dates: string[]; values: number[] };  // Backend uses "values" not "rsi"
    macd?: { dates: string[]; macd: number[]; signal: number[]; histogram: number[] };  // Backend uses these keys
    bollinger_bands?: { dates: string[]; upper: number[]; middle: number[]; lower: number[] };
  };
  supportResistance?: {
    support: number[];
    resistance: number[];
  };
  patterns?: Array<{
    date: string;
    type: string;
    description: string;
  }>;
}

const ProfessionalTradingChart: React.FC<TradingChartProps> = ({
  data,
  symbol,
  technicalOverlays,
  indicatorData,
  supportResistance,
  patterns
}) => {
  // Transform data for candlestick rendering
  const priceData = useMemo(() => {
    // Validate data structure
    if (!data || !data.dates || !Array.isArray(data.dates) || data.dates.length === 0) {
      return [];
    }
    if (!data.open || !data.close || !data.high || !data.low) {
      return [];
    }

    return data.dates.map((date, idx) => {
      const open = data.open[idx];
      const close = data.close[idx];
      const high = data.high[idx];
      const low = data.low[idx];

      // Skip invalid data points
      if (open == null || close == null || high == null || low == null) {
        return null;
      }

      const isGreen = close >= open;

      return {
        date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        fullDate: date,
        open,
        high,
        low,
        close,
        volume: data.volume?.[idx],
        // For candlestick wicks (thin lines from low to high)
        wickLow: low,
        wickHigh: high,
        // For candlestick bodies (thick bars from open to close)
        candleOpen: open,
        candleClose: close,
        candleMin: Math.min(open, close),
        candleMax: Math.max(open, close),
        isGreen,
        // Technical overlays
        sma20: technicalOverlays?.sma_20?.[idx],
        sma50: technicalOverlays?.sma_50?.[idx],
        sma200: technicalOverlays?.sma_200?.[idx],
        ema12: technicalOverlays?.ema_12?.[idx],
        ema26: technicalOverlays?.ema_26?.[idx],
        vwap: technicalOverlays?.vwap?.[idx]
      };
    }).filter(Boolean); // Remove null entries
  }, [data, technicalOverlays]);

  // RSI Data
  const rsiData = useMemo(() => {
    if (!indicatorData?.rsi || !indicatorData.rsi.dates || !indicatorData.rsi.values) return [];
    if (!Array.isArray(indicatorData.rsi.dates) || !Array.isArray(indicatorData.rsi.values)) return [];

    return indicatorData.rsi.dates.map((date, idx) => ({
      date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      rsi: indicatorData.rsi.values[idx]
    })).filter(d => d.rsi != null); // Filter out null/undefined RSI values
  }, [indicatorData?.rsi]);

  // MACD Data (not currently displayed but available for future use)
  // const macdData = useMemo(() => {
  //   if (!indicatorData?.macd) return [];
  //   return indicatorData.macd.dates.map((date, idx) => ({
  //     date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  //     macd: indicatorData.macd.macd_line[idx],
  //     signal: indicatorData.macd.signal_line[idx],
  //     histogram: indicatorData.macd.histogram[idx]
  //   }));
  // }, [indicatorData?.macd]);

  // Custom Candlestick Shape
  const renderCandlestick = (props: any) => {
    const { x, y, width, height, payload } = props;
    if (!payload) return null;

    const { open, close, high, low, isGreen } = payload;
    const color = isGreen ? theme.colors.success : theme.colors.error;
    const candleWidth = 6;
    const wickX = x + width / 2;

    // Calculate y positions
    const openY = y + ((payload.candleMax - open) / (high - low)) * height;
    const closeY = y + ((payload.candleMax - close) / (high - low)) * height;
    const highY = y;
    const lowY = y + height;
    const bodyTop = Math.min(openY, closeY);
    const bodyHeight = Math.abs(closeY - openY);

    return (
      <g>
        {/* Wick (thin line from low to high) */}
        <line
          x1={wickX}
          y1={highY}
          x2={wickX}
          y2={lowY}
          stroke={color}
          strokeWidth={1}
        />
        {/* Body (rectangle from open to close) */}
        <rect
          x={wickX - candleWidth / 2}
          y={bodyTop}
          width={candleWidth}
          height={Math.max(bodyHeight, 1)} // Min height 1px for doji
          fill={color}
          fillOpacity={isGreen ? 0.8 : 1}
          stroke={color}
          strokeWidth={1}
        />
      </g>
    );
  };

  // Support and resistance levels
  const supportLevel = supportResistance?.support?.[0];
  const resistanceLevel = supportResistance?.resistance?.[0];

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const point = payload[0].payload;
    const priceChange = point.close - point.open;
    const priceChangePercent = ((priceChange / point.open) * 100).toFixed(2);

    return (
      <div
        style={{
          background: theme.colors.background.elevated,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: 8,
          padding: 12,
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          fontSize: 12
        }}
      >
        <div style={{ color: theme.colors.text.primary, fontWeight: 'bold', marginBottom: 8 }}>
          {point.date}
        </div>
        <div style={{ color: theme.colors.text.secondary }}>
          <div><strong>O:</strong> ${point.open.toFixed(2)} <strong>H:</strong> ${point.high.toFixed(2)}</div>
          <div><strong>L:</strong> ${point.low.toFixed(2)} <strong>C:</strong> ${point.close.toFixed(2)}</div>
          <div
            style={{
              color: point.isGreen ? theme.colors.success : theme.colors.error,
              fontWeight: 'bold',
              marginTop: 4
            }}
          >
            {priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)} ({priceChangePercent}%)
          </div>
          {point.volume && (
            <div style={{ marginTop: 4 }}>Vol: {(point.volume / 1000000).toFixed(2)}M</div>
          )}
        </div>
      </div>
    );
  };

  if (priceData.length === 0) {
    return (
      <Card
        style={{
          background: theme.colors.background.elevated,
          border: `1px solid ${theme.colors.border}`,
          padding: 24,
          textAlign: 'center'
        }}
      >
        <div style={{ color: theme.colors.text.secondary }}>No chart data available</div>
      </Card>
    );
  }

  return (
    <div style={{ marginBottom: 24 }}>
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: theme.colors.text.primary, fontSize: 18, fontWeight: 600 }}>
              {symbol} - Professional Trading Chart
            </span>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {technicalOverlays?.sma_20 && <Tag color="magenta">SMA 20</Tag>}
              {technicalOverlays?.sma_50 && <Tag color="blue">SMA 50</Tag>}
              {technicalOverlays?.ema_12 && <Tag color="cyan">EMA 12</Tag>}
              {technicalOverlays?.ema_26 && <Tag color="geekblue">EMA 26</Tag>}
              {supportLevel && <Tag color="green">Support</Tag>}
              {resistanceLevel && <Tag color="red">Resistance</Tag>}
            </div>
          </div>
        }
        style={{
          background: theme.colors.background.elevated,
          border: `1px solid ${theme.colors.border}`
        }}
        bodyStyle={{ padding: 16 }}
      >
        {/* Main Price Chart with Candlesticks */}
        <ResponsiveContainer width="100%" height={450}>
          <ComposedChart data={priceData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} opacity={0.3} />

            <XAxis
              dataKey="date"
              stroke={theme.colors.text.secondary}
              tick={{ fill: theme.colors.text.secondary, fontSize: 11 }}
              interval="preserveStartEnd"
            />

            <YAxis
              stroke={theme.colors.text.secondary}
              tick={{ fill: theme.colors.text.secondary, fontSize: 11 }}
              domain={['dataMin - 5', 'dataMax + 5']}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />

            <Tooltip content={<CustomTooltip />} />

            {/* Support Line */}
            {supportLevel && (
              <ReferenceLine
                y={supportLevel}
                stroke={theme.colors.success}
                strokeDasharray="5 5"
                strokeWidth={2}
                label={{
                  value: `Support: $${supportLevel.toFixed(2)}`,
                  position: 'right',
                  fill: theme.colors.success,
                  fontSize: 11
                }}
              />
            )}

            {/* Resistance Line */}
            {resistanceLevel && (
              <ReferenceLine
                y={resistanceLevel}
                stroke={theme.colors.error}
                strokeDasharray="5 5"
                strokeWidth={2}
                label={{
                  value: `Resistance: $${resistanceLevel.toFixed(2)}`,
                  position: 'right',
                  fill: theme.colors.error,
                  fontSize: 11
                }}
              />
            )}

            {/* Bollinger Bands */}
            {indicatorData?.bollinger_bands && (
              <>
                <Line
                  type="monotone"
                  dataKey="bbUpper"
                  stroke="#9C27B0"
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="3 3"
                />
                <Line
                  type="monotone"
                  dataKey="bbMiddle"
                  stroke="#9C27B0"
                  strokeWidth={1}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="bbLower"
                  stroke="#9C27B0"
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="3 3"
                />
              </>
            )}

            {/* Moving Averages */}
            {technicalOverlays?.sma_20 && (
              <Line
                type="monotone"
                dataKey="sma20"
                stroke="#FF6B6B"
                strokeWidth={2}
                dot={false}
                name="SMA 20"
              />
            )}

            {technicalOverlays?.sma_50 && (
              <Line
                type="monotone"
                dataKey="sma50"
                stroke="#4ECDC4"
                strokeWidth={2}
                dot={false}
                name="SMA 50"
              />
            )}

            {technicalOverlays?.ema_12 && (
              <Line
                type="monotone"
                dataKey="ema12"
                stroke="#45B7D1"
                strokeWidth={2}
                dot={false}
                strokeDasharray="5 5"
                name="EMA 12"
              />
            )}

            {technicalOverlays?.ema_26 && (
              <Line
                type="monotone"
                dataKey="ema26"
                stroke="#FFA07A"
                strokeWidth={2}
                dot={false}
                strokeDasharray="5 5"
                name="EMA 26"
              />
            )}

            {/* Candlesticks rendered as custom shapes */}
            <Bar
              dataKey="high"
              shape={renderCandlestick}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>

        {/* Volume Chart */}
        {data.volume && data.volume.length > 0 && (
          <>
            <div style={{ height: 1, background: theme.colors.border, margin: '16px 0', opacity: 0.5 }} />
            <ResponsiveContainer width="100%" height={120}>
              <ComposedChart data={priceData} margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} opacity={0.3} />
                <XAxis
                  dataKey="date"
                  stroke={theme.colors.text.secondary}
                  tick={{ fill: theme.colors.text.secondary, fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke={theme.colors.text.secondary}
                  tick={{ fill: theme.colors.text.secondary, fontSize: 10 }}
                  tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`}
                  width={50}
                />
                <Tooltip
                  content={({ active, payload }: any) => {
                    if (!active || !payload || payload.length === 0) return null;
                    const point = payload[0].payload;
                    return (
                      <div
                        style={{
                          background: theme.colors.background.elevated,
                          border: `1px solid ${theme.colors.border}`,
                          borderRadius: 8,
                          padding: 8,
                          fontSize: 12
                        }}
                      >
                        <div style={{ color: theme.colors.text.primary }}>{point.date}</div>
                        <div style={{ color: theme.colors.text.secondary }}>
                          Volume: {(point.volume / 1000000).toFixed(2)}M
                        </div>
                      </div>
                    );
                  }}
                />
                <Bar dataKey="volume" radius={[4, 4, 0, 0]}>
                  {priceData.map((entry, index) => (
                    <rect
                      key={`vol-${index}`}
                      fill={entry.isGreen ? theme.colors.success : theme.colors.error}
                      fillOpacity={0.5}
                    />
                  ))}
                </Bar>
              </ComposedChart>
            </ResponsiveContainer>
          </>
        )}

        {/* RSI Indicator */}
        {rsiData && rsiData.length > 0 && (
          <>
            <div style={{ height: 1, background: theme.colors.border, margin: '16px 0', opacity: 0.5 }} />
            <div style={{ color: theme.colors.text.primary, fontWeight: 600, marginBottom: 8 }}>
              RSI (14)
            </div>
            <ResponsiveContainer width="100%" height={120}>
              <ComposedChart data={rsiData} margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} opacity={0.3} />
                <XAxis
                  dataKey="date"
                  stroke={theme.colors.text.secondary}
                  tick={{ fill: theme.colors.text.secondary, fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke={theme.colors.text.secondary}
                  tick={{ fill: theme.colors.text.secondary, fontSize: 10 }}
                  domain={[0, 100]}
                  width={40}
                />
                <ReferenceLine y={70} stroke={theme.colors.error} strokeDasharray="3 3" />
                <ReferenceLine y={30} stroke={theme.colors.success} strokeDasharray="3 3" />
                <Area
                  type="monotone"
                  dataKey="rsi"
                  stroke="#9C27B0"
                  fill="#9C27B0"
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </>
        )}

        {/* Pattern Markers */}
        {patterns && patterns.length > 0 && (
          <div style={{ marginTop: 16, padding: 12, background: theme.colors.background.elevated, borderRadius: 8 }}>
            <div style={{ color: theme.colors.text.primary, fontWeight: 600, marginBottom: 8 }}>
              📊 Detected Patterns
            </div>
            {patterns.map((pattern, idx) => (
              <div
                key={idx}
                style={{
                  color: theme.colors.text.secondary,
                  fontSize: 12,
                  marginBottom: 4,
                  paddingLeft: 12
                }}
              >
                • <strong>{pattern.type}</strong> on {pattern.date}: {pattern.description}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default ProfessionalTradingChart;
