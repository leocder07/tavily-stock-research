# SentimentPanel Component Documentation

## Overview
The `SentimentPanel` component provides comprehensive visualization of market sentiment data with a CRED-inspired premium design aesthetic. It maps sentiment scores to intuitive visual indicators and provides multi-source sentiment breakdown.

## Visual Design Approach

### 1. Overall Sentiment Gauge (Left Panel)
**Layout**: Large circular gauge with icon, label, and progress bar

**Visual Elements**:
- **Sentiment Icon**:
  - Bullish (>65): Green arrow up (↑)
  - Neutral (35-65): Yellow horizontal bar (—)
  - Bearish (<35): Red arrow down (↓)

- **Sentiment Label**: Large text (BULLISH/NEUTRAL/BEARISH)
  - Color-coded using CRED tokens:
    - Bullish: `theme.colors.success` (#00D4AA - emerald green)
    - Neutral: `theme.colors.warning` (#FF9F0A - orange)
    - Bearish: `theme.colors.danger` (#FF453A - vibrant red)

- **Score Display**: Numerical score (0-100) beneath label
- **Progress Bar**: Full-width gradient bar showing position on sentiment spectrum
  - Gradient from red (0) → yellow (50) → green (100)

- **Sentiment Summary**: Text box with contextual summary
  - Glass morphism effect background
  - Examples: "Strong positive sentiment across analyzed stocks"

### 2. Source Breakdown (Right Panel)
**Layout**: Vertical list of sentiment sources with individual progress bars

**Sources Visualized**:
1. **News Sentiment** (📈)
   - Score: 0-100
   - Details: "X positive, Y negative mentions"
   - Icon: LineChartOutlined

2. **Analyst Sentiment** (🏆)
   - Score based on consensus (Buy=75, Hold=50, Sell=25)
   - Details: "Consensus: Buy, X buy ratings"
   - Icon: TrophyOutlined

3. **Social Sentiment** (👥)
   - Score based on social media lean
   - Details: "Positive lean, high volume"
   - Icon: TeamOutlined

4. **Insider Activity** (💡)
   - Score based on net buying/selling
   - Details: "Net buying, X buys, Y sells"
   - Icon: BulbOutlined

**Each Source Shows**:
- Name and icon on the left
- Score badge on the right (color-coded)
- Horizontal progress bar (color-coded by score)
- Detailed explanation text below

**Data Points Counter**:
- Shows total data points analyzed
- Source count indicator
- Clock icon for freshness

### 3. Sentiment Drivers (Bottom Panel)
**Layout**: Numbered list of top 5 sentiment drivers

**Visual Elements**:
- Numbered badges (1-5) with CRED gold background
- Driver text descriptions
- Auto-populated from:
  - Key events from news
  - Positive catalysts
  - Risk factors
  - Recent headlines

### 4. Market Context (Optional Bottom Panel)
**Layout**: 4-column grid showing market indicators

**Indicators**:
1. **Fear & Greed Index**: 0-100 score
2. **VIX Level**: Volatility index
3. **Market Trend**: Bullish/Bearish label
4. **Put/Call Ratio** (if available)

## Sentiment Score Mapping

### Input Formats Supported
The component handles multiple sentiment data formats:

1. **Composite Score (0-100)**:
   ```typescript
   {
     composite_score: 75,        // 0-100 scale
     overall_sentiment_score: 75 // Alternative field name
   }
   ```

2. **Sentiment Score (-1.0 to 1.0)**:
   ```typescript
   {
     sentiment_score: 0.5,  // -1.0 (bearish) to 1.0 (bullish)
     sentiment: "bullish"   // Label
   }
   ```

3. **Stock-Specific Breakdown**:
   ```typescript
   {
     stocks: {
       "AAPL": {
         composite_score: 75,
         news_sentiment: { sentiment_score: 65, ... },
         analyst_sentiment: { consensus: "Buy", ... },
         social_sentiment: { sentiment_lean: "positive", ... },
         insider_activity: { net_activity: "buying", ... }
       }
     }
   }
   ```

### Mapping Logic

**Score to Label**:
```
0-34:   BEARISH  (Red)
35-65:  NEUTRAL  (Yellow)
66-100: BULLISH  (Green)
```

**Score to Color** (CRED Design Tokens):
```
Bullish:  #00D4AA (theme.colors.success)
Neutral:  #FF9F0A (theme.colors.warning)
Bearish:  #FF453A (theme.colors.danger)
```

**Score to Icon**:
```
> 65:  ↑ (ArrowUpOutlined)
35-65: — (MinusOutlined)
< 35:  ↓ (ArrowDownOutlined)
```

## Integration with AnalysisResults

### Placement
The SentimentPanel is positioned after the Risk Analysis section and before Predictive Analytics in the analysis flow:

```
Executive Summary
↓
Expert Trading Charts
↓
Confidence Score
↓
Stock Recommendations
↓
Market Data
↓
Fundamental Analysis
↓
Technical Analysis
↓
Risk Analysis
↓
>>> SENTIMENT PANEL <<< (NEW)
↓
Recent News
↓
Predictive Analytics
↓
Peer Comparison
```

### Data Flow
```typescript
// In AnalysisResults.tsx
const sentiment = analysis?.sentiment || {};

// Pass to component
<SentimentPanel
  sentimentData={sentiment}
  symbol={symbols[0]}
/>
```

## CRED Design Tokens Usage

### Colors
- **Primary Gold**: `theme.colors.primary` (#D4AF37)
- **Success Green**: `theme.colors.success` (#00D4AA)
- **Danger Red**: `theme.colors.danger` (#FF453A)
- **Warning Orange**: `theme.colors.warning` (#FF9F0A)
- **Background**: `theme.colors.background.secondary` (#1C1C1E)
- **Elevated**: `theme.colors.background.elevated` (#2C2C2E)
- **Border**: `theme.colors.border` (rgba(255,255,255,0.1))
- **Text Primary**: `theme.colors.text.primary` (#FFFFFF)
- **Text Secondary**: `theme.colors.text.secondary` (#8E8E93)

### Effects
- **Glass Morphism**:
  ```typescript
  background: theme.effects.glassMorphism.background
  backdropFilter: theme.effects.glassMorphism.backdropFilter
  border: theme.effects.glassMorphism.border
  ```

### Typography
- **Title**: Level 4 heading (Stock recommendations level)
- **Subtitle**: Level 3 heading (Section headers)
- **Body Text**: Regular text with type="secondary" for details
- **Font**: Inter font family (theme.typography.fontFamily.primary)

### Spacing
- **Card Gutter**: 24px horizontal, 24px vertical
- **Internal Padding**: 12-16px for content sections
- **Border Radius**: `theme.borderRadius.lg` (16px) for cards
- **Border Radius**: `theme.borderRadius.md` (12px) for inner elements

## Tooltips & Information

### Tooltip Explanations
1. **Overall Sentiment**:
   > "Composite sentiment score aggregated from news, analyst ratings, social media, and insider activity. Weighted by source reliability."

2. **Sentiment by Source**:
   > "Breakdown of sentiment across different data sources. Each source is analyzed independently and weighted by reliability."

3. **Top Sentiment Drivers**:
   > "Key events, catalysts, and risks identified from recent news and market activity. These are the primary factors influencing current sentiment."

### Data Freshness Indicator
Shows time elapsed since data collection:
- "Just now" (< 5 minutes)
- "Xm ago" (< 1 hour)
- "Xh ago" (< 24 hours)
- "Xd ago" (> 24 hours)

Badge displayed in header with clock icon.

## Component Props

```typescript
interface SentimentPanelProps {
  sentimentData: any;  // Sentiment analysis data
  symbol?: string;     // Optional stock symbol for stock-specific view
}
```

## Responsive Design

### Desktop (lg: 1024px+)
- Two-column layout: Gauge on left, Sources on right
- Full-width driver list below
- Market context in 4-column grid

### Tablet (md: 768px - 1024px)
- Maintained two-column layout
- Stacked panels if space constrained

### Mobile (sm: < 768px)
- Single column stacked layout
- Gauge panel full-width
- Sources panel full-width
- Drivers list full-width
- Market context 2x2 grid

## Accessibility Features

- **ARIA Labels**: All interactive elements have proper labels
- **Keyboard Navigation**: Full keyboard support for interactive elements
- **Color Contrast**: WCAG AA compliant contrast ratios
- **Screen Reader Support**: Descriptive text for sentiment indicators
- **Data Test Attributes**: `data-test="sentiment-panel"` for E2E testing

## Testing Selectors

```typescript
// E2E Testing Selectors
'[data-test="sentiment-panel"]'              // Main panel
'[data-test="sentiment-gauge"]'              // Sentiment gauge section
'[data-test="sentiment-source-breakdown"]'   // Source breakdown
'[data-test="sentiment-drivers"]'            // Drivers list
```

## Performance Considerations

1. **Conditional Rendering**: Only renders if sentiment data exists
2. **Memoization**: Consider wrapping in React.memo if parent re-renders frequently
3. **Lazy Loading**: Icons and charts loaded on demand
4. **Data Processing**: Calculations performed once, results cached

## Future Enhancements

### Phase 2 Features
1. **Sentiment Timeline Chart**: Line chart showing sentiment over time
2. **Sentiment Heatmap**: Visual grid of sentiment by sector/industry
3. **Interactive Filters**: Filter by sentiment source
4. **Export Functionality**: Download sentiment report as PDF
5. **Real-time Updates**: WebSocket integration for live sentiment changes
6. **Comparative View**: Compare sentiment across multiple stocks
7. **Historical Sentiment**: View sentiment trends over 30/60/90 days

### Advanced Analytics
1. **Sentiment Momentum**: Rate of change in sentiment
2. **Sentiment Divergence**: Difference between sources (contrarian indicator)
3. **Sentiment Volatility**: Stability of sentiment over time
4. **Predictive Signals**: Sentiment-based trading signals

## Visual Mockup Description

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 Market Sentiment Analysis                    🕐 Updated 5m ago  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐  │
│  │   Overall Sentiment      │  │  Sentiment by Source         │  │
│  │   ───────────────        │  │  ─────────────────           │  │
│  │         ↑                │  │                              │  │
│  │                          │  │  📈 News         [75] ▓▓▓░░  │  │
│  │      BULLISH             │  │  15 positive, 3 negative     │  │
│  │                          │  │                              │  │
│  │      75.0/100            │  │  🏆 Analyst      [80] ▓▓▓▓░  │  │
│  │                          │  │  Consensus: Buy, 12 ratings  │  │
│  │  [▓▓▓▓▓▓▓▓▓▓░░░░]       │  │                              │  │
│  │  Bearish  Neutral Bullish│  │  👥 Social       [70] ▓▓▓░░  │  │
│  │                          │  │  Positive lean, high volume  │  │
│  │  ╔══════════════════╗    │  │                              │  │
│  │  ║ Strong positive  ║    │  │  💡 Insider      [65] ▓▓▓░░  │  │
│  │  ║ sentiment across ║    │  │  Net buying, 5 buys, 1 sell │  │
│  │  ║ analyzed stocks  ║    │  │                              │  │
│  │  ╚══════════════════╝    │  │  ╔════════════════════════╗ │  │
│  │                          │  │  ║ 🕐 Analyzed 247 data   ║ │  │
│  └──────────────────────────┘  │  ║    points from 8 sources║ │  │
│                                 │  ╚════════════════════════╝ │  │
│                                 └──────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Top Sentiment Drivers                                        │ │
│  │  ────────────────────                                         │ │
│  │                                                               │ │
│  │  ① Q4 earnings beat expectations by 15%, revenue up 23% YoY  │ │
│  │  ② Major product launch announced with strong pre-orders     │ │
│  │  ③ CEO purchased 50,000 shares, signaling confidence         │ │
│  │  ④ Analyst upgrades from Goldman Sachs and Morgan Stanley    │ │
│  │  ⑤ Positive regulatory developments in key markets           │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Market Context                                               │ │
│  │  ──────────────                                               │ │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐            │ │
│  │  │ Fear & │  │  VIX   │  │ Market │  │Put/Call│            │ │
│  │  │ Greed  │  │ Level  │  │ Trend  │  │ Ratio  │            │ │
│  │  │   72   │  │  14.5  │  │BULLISH │  │  0.85  │            │ │
│  │  └────────┘  └────────┘  └────────┘  └────────┘            │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Summary

The SentimentPanel provides a comprehensive, visually appealing sentiment visualization that:
1. Maps sentiment scores (-1 to 1, 0 to 100) to intuitive color-coded indicators
2. Breaks down sentiment by source (News, Analyst, Social, Insider)
3. Highlights top sentiment drivers affecting the stock
4. Provides market context with Fear & Greed, VIX, and trend indicators
5. Uses CRED design tokens for premium aesthetic
6. Includes tooltips explaining sentiment calculation methodology
7. Shows data freshness with timestamp indicators
8. Responds beautifully across all screen sizes

The component seamlessly integrates into AnalysisResults and enhances the user's understanding of market sentiment through clear, actionable visualizations.
