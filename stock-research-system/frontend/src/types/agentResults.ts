/**
 * Complete TypeScript interfaces for Agent Results
 * Matches backend agent_results structure exactly
 */

export interface MetadataValue<T = any> {
  value: T;
  unit?: string;
  formatted?: string;
  description?: string;
}

// Synthesis Agent Result
export interface SynthesisResult {
  action: string;
  confidence: number | MetadataValue<number>;
  target_price: number | MetadataValue<number>;
  stop_loss: number | MetadataValue<number>;
  entry_price: number | MetadataValue<number>;
  risk_reward_ratio: number | MetadataValue<number>;
  rationale?: string;
  reasoning?: string;
  timeframe?: string;
  key_factors?: string[];
  position_sizing?: PositionSizing;
  data_quality?: DataQuality;
}

export interface PositionSizing {
  account_value: number;
  conservative?: PositionScenario;
  moderate?: PositionScenario;
  aggressive?: PositionScenario;
  recommended?: PositionScenario;
  risk_reward_ratio?: number | MetadataValue<number>;
  guidance?: string;
}

export interface PositionScenario {
  shares: number;
  position_value: number;
  capital_at_risk: number;
  position_pct: number;
  risk_per_trade_pct?: number;
}

export interface DataQuality {
  overall_score: number;
  overall_grade: string;
  agent_reports?: {
    [key: string]: {
      score: number;
      grade: string;
      freshness?: number;
      reliability?: number;
      completeness?: number;
    };
  };
  grade_distribution?: { [key: string]: number };
  issues?: string[];
  warnings?: string[];
  agents_validated?: number;
  validation_timestamp?: string;
}

// Fundamental Agent Result
export interface FundamentalResult {
  valuation_metrics?: ValuationMetrics;
  financial_health?: FinancialHealth;
  growth_metrics?: GrowthMetrics;
  summary?: string;
  analyst_consensus?: string;
  analyst_target_price?: number | MetadataValue<number>;
  analyst_ratings?: AnalystRatings;
}

export interface ValuationMetrics {
  pe_ratio?: number | MetadataValue<number>;
  peg_ratio?: number | MetadataValue<number>;
  pb_ratio?: number | MetadataValue<number>;
  ps_ratio?: number | MetadataValue<number>;
  graham_number?: number | MetadataValue<number>;
  eps?: number | MetadataValue<number>;
}

export interface FinancialHealth {
  roe?: number | MetadataValue<number>;
  roa?: number | MetadataValue<number>;
  debt_to_equity?: number | MetadataValue<number>;
  current_ratio?: number | MetadataValue<number>;
  quick_ratio?: number | MetadataValue<number>;
  profit_margin?: number | MetadataValue<number>;
  operating_margin?: number | MetadataValue<number>;
  gross_margin?: number | MetadataValue<number>;
}

export interface GrowthMetrics {
  revenue_growth?: number | MetadataValue<number>;
  earnings_growth?: number | MetadataValue<number>;
  fcf_growth?: number | MetadataValue<number>;
  book_value_growth?: number | MetadataValue<number>;
}

export interface AnalystRatings {
  strong_buy?: number;
  buy?: number;
  hold?: number;
  sell?: number;
  strong_sell?: number;
  total?: number;
  consensus?: string;
}

// Technical Agent Result
export interface TechnicalResult {
  indicators?: TechnicalIndicators;
  support_levels?: number[];
  resistance_levels?: number[];
  patterns?: ChartPattern[];
  trend?: string;
  confidence?: number;
  summary?: string;
  signal?: string;
  pattern_signals?: string[];
}

export interface TechnicalIndicators {
  rsi?: RSIIndicator | MetadataValue<number>;
  macd?: MACDIndicator | MetadataValue<number>;
  bollinger_bands?: BollingerBands;
  atr?: number | MetadataValue<number>;
  adx?: number | MetadataValue<number>;
  ema_20?: number | MetadataValue<number>;
  ema_50?: number | MetadataValue<number>;
  sma_200?: number | MetadataValue<number>;
}

export interface RSIIndicator {
  value: number;
  signal?: string;
  date?: string;
}

export interface MACDIndicator {
  macd?: number;
  signal?: number;
  histogram?: number;
  trend?: string;
}

export interface BollingerBands {
  upper?: number | MetadataValue<number>;
  middle?: number | MetadataValue<number>;
  lower?: number | MetadataValue<number>;
  bandwidth?: number;
  percent_b?: number;
}

export interface ChartPattern {
  pattern: string;
  type: string;
  confidence: number;
  target?: number | string;
  neckline?: number;
  description: string;
  timeframe?: string;
}

// Risk Agent Result
export interface RiskResult {
  risk_metrics?: RiskMetrics;
  risk_level?: string;
  risk_score?: number;
  risk_factors?: string[];
  mitigation_strategies?: string;
  summary?: string;
}

export interface RiskMetrics {
  var_95?: number | MetadataValue<number>;
  cvar_95?: number | MetadataValue<number>;
  sharpe_ratio?: number | MetadataValue<number>;
  sortino_ratio?: number | MetadataValue<number>;
  beta?: number | MetadataValue<number>;
  volatility?: number | MetadataValue<number>;
  max_drawdown?: number | MetadataValue<number>;
  correlation?: number | MetadataValue<number>;
}

// Market Data Agent Result
export interface MarketDataResult {
  current_price?: number | MetadataValue<number>;
  previous_close?: number | MetadataValue<number>;
  change?: number | MetadataValue<number>;
  change_percent?: number | MetadataValue<number>;
  volume?: number | MetadataValue<number>;
  avg_volume?: number | MetadataValue<number>;
  market_cap?: number | MetadataValue<number>;
  day_high?: number | MetadataValue<number>;
  day_low?: number | MetadataValue<number>;
  '52_week_high'?: number | MetadataValue<number>;
  '52_week_low'?: number | MetadataValue<number>;
  week_52_high?: number | MetadataValue<number>;
  week_52_low?: number | MetadataValue<number>;
}

// Sentiment Agent Result
export interface SentimentResult {
  overall_sentiment?: string;
  sentiment_score?: number;
  confidence?: number;
  news_sentiment?: NewsSentiment;
  social_sentiment?: SocialSentiment;
  sources?: SentimentSource[];
  citations?: Citation[];
  summary?: string;
}

export interface NewsSentiment {
  score?: number;
  sentiment?: string;
  article_count?: number;
  sources?: SentimentSource[];
}

export interface SocialSentiment {
  score?: number;
  sentiment?: string;
  volume?: number;
  trending?: boolean;
}

export interface SentimentSource {
  title: string;
  url: string;
  source: string;
  content?: string;
  summary?: string;
  sentiment?: string;
  score?: number;
  published_date?: string;
}

export interface Citation {
  source: string;
  url: string;
  content?: string;
  reliability?: string;
  timestamp?: string;
}

// Peer Comparison Agent Result
export interface PeerComparisonResult {
  peers?: PeerData[];
  summary?: string;
  relative_position?: string;
}

export interface PeerData {
  symbol: string;
  name?: string;
  pe_ratio?: number;
  market_cap?: number;
  relative_performance?: number;
  sector?: string;
}

// Predictive Agent Result
export interface PredictiveResult {
  price_forecast?: PriceForecast;
  trend_prediction?: TrendPrediction;
  model_confidence?: number;
  recommendations?: PredictiveRecommendation;
  backtest_results?: BacktestResults;
  summary?: string;
}

export interface PriceForecast {
  short_term?: number;
  medium_term?: number;
  long_term?: number;
  '1_day'?: { expected_return: number; confidence: number };
  '30_day'?: { expected_return: number; confidence: number };
  '90_day'?: { expected_return: number; confidence: number };
}

export interface TrendPrediction {
  current_trend?: string;
  reversal_probability?: number;
  reversal_signals?: string[];
}

export interface PredictiveRecommendation {
  action?: string;
  confidence?: number;
  rationale?: string[];
  timeframe?: string;
}

export interface BacktestResults {
  accuracy?: string;
  win_rate?: string;
  sharpe_ratio?: string;
  performance_grade?: string;
  out_of_sample?: {
    train_accuracy?: string;
    test_accuracy?: string;
    overfitting_gap?: string;
  };
}

// Complete Agent Results Interface
export interface AgentResults {
  synthesis?: SynthesisResult;
  fundamental?: FundamentalResult;
  technical?: TechnicalResult;
  risk?: RiskResult;
  market_data?: MarketDataResult;
  sentiment?: SentimentResult;
  peer_comparison?: PeerComparisonResult;
  predictive?: PredictiveResult;
  insider_activity?: any;
  catalyst_tracker?: any;
  chart_analytics?: any;
}

// Complete Analysis Response
export interface AnalysisResponse {
  analysis_id: string;
  status: string;
  query: string;
  symbols: string[];
  agent_results?: AgentResults;

  // Legacy fields (for backward compatibility)
  synthesis?: SynthesisResult;
  risk_analysis?: RiskResult;
  analysis?: {
    summary?: string;
    market_data?: MarketDataResult;
    fundamental?: FundamentalResult;
    technical?: TechnicalResult;
    sentiment?: SentimentResult;
    predictive?: PredictiveResult;
    peer_comparison?: PeerComparisonResult;
    news?: any;
  };

  // Metadata
  execution_time?: number;
  timestamp?: string;
  request_id?: string;
  recommendations?: { [symbol: string]: any };
  executive_summary?: string;
  investment_thesis?: string;
  confidence_score?: number;
}
