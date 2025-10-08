/**
 * Value Extractor Utilities
 * Safely extracts values from backend metadata format {value, unit, formatted, description}
 * Handles mixed data types (dict/float/string) consistently
 */

export interface MetadataValue {
  value?: any;
  unit?: string;
  formatted?: string;
  description?: string;
}

/**
 * Extract raw value from metadata dict or return direct value
 */
export const extractValue = (data: any, fallback: any = null): any => {
  if (data === null || data === undefined) return fallback;

  // If it's an object with a value property, extract it
  if (typeof data === 'object' && !Array.isArray(data) && 'value' in data) {
    return data.value ?? fallback;
  }

  // Otherwise return as-is
  return data;
};

/**
 * Extract numeric value safely
 */
export const extractNumericValue = (data: any, fallback: number = 0): number => {
  const value = extractValue(data, fallback);

  if (typeof value === 'number') return value;
  if (typeof value === 'string') {
    const parsed = parseFloat(value);
    return isNaN(parsed) ? fallback : parsed;
  }

  return fallback;
};

/**
 * Extract formatted string or format the value
 */
export const extractFormatted = (data: any, fallback: string = 'N/A'): string => {
  if (data === null || data === undefined) return fallback;

  // If it has a formatted field, use it
  if (typeof data === 'object' && 'formatted' in data && data.formatted) {
    return data.formatted;
  }

  // Otherwise extract the raw value and format it
  const value = extractValue(data);

  if (value === null || value === undefined) return fallback;
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return value.toFixed(2);

  return String(value);
};

/**
 * Extract price value with $ formatting
 */
export const extractPrice = (data: any, fallback: string = 'N/A'): string => {
  const value = extractNumericValue(data, null);

  if (value === null) return fallback;

  return `$${value.toFixed(2)}`;
};

/**
 * Extract percentage value with % formatting
 */
export const extractPercentage = (data: any, fallback: string = 'N/A'): string => {
  const value = extractNumericValue(data, null);

  if (value === null) return fallback;

  return `${value.toFixed(2)}%`;
};

/**
 * Extract unit if available
 */
export const extractUnit = (data: any): string => {
  if (typeof data === 'object' && 'unit' in data && data.unit) {
    return data.unit;
  }
  return '';
};

/**
 * Extract description if available
 */
export const extractDescription = (data: any): string => {
  if (typeof data === 'object' && 'description' in data && data.description) {
    return data.description;
  }
  return '';
};

/**
 * Safe access to nested agent results
 */
export const getAgentResult = (results: any, agentName: string): any => {
  if (!results || !results.agent_results) return null;
  return results.agent_results[agentName] || null;
};

/**
 * Extract synthesis data safely
 */
export const extractSynthesisData = (results: any) => {
  const synthesis = getAgentResult(results, 'synthesis');

  if (!synthesis) return null;

  return {
    recommendation: synthesis.recommendation || 'HOLD',
    confidence: extractNumericValue(synthesis.confidence, 50),
    target_price: extractNumericValue(synthesis.target_price),
    stop_loss: extractNumericValue(synthesis.stop_loss),
    entry_price: extractNumericValue(synthesis.entry_price),
    risk_reward_ratio: extractNumericValue(synthesis.risk_reward_ratio),
    rationale: synthesis.rationale || synthesis.reasoning || '',
    timeframe: synthesis.timeframe || '1-3 months',
    key_factors: synthesis.key_factors || []
  };
};

/**
 * Extract fundamental data safely
 */
export const extractFundamentalData = (results: any) => {
  const fundamental = getAgentResult(results, 'fundamental');

  if (!fundamental) return null;

  const valuation = fundamental.valuation_metrics || {};
  const financial = fundamental.financial_health || {};
  const growth = fundamental.growth_metrics || {};

  return {
    pe_ratio: extractNumericValue(valuation.pe_ratio),
    peg_ratio: extractNumericValue(valuation.peg_ratio),
    pb_ratio: extractNumericValue(valuation.pb_ratio),
    graham_number: extractNumericValue(valuation.graham_number),
    roe: extractNumericValue(financial.roe),
    roa: extractNumericValue(financial.roa),
    debt_to_equity: extractNumericValue(financial.debt_to_equity),
    current_ratio: extractNumericValue(financial.current_ratio),
    profit_margin: extractNumericValue(financial.profit_margin),
    revenue_growth: extractNumericValue(growth.revenue_growth),
    earnings_growth: extractNumericValue(growth.earnings_growth),
    fcf_growth: extractNumericValue(growth.fcf_growth)
  };
};

/**
 * Extract technical data safely
 */
export const extractTechnicalData = (results: any) => {
  const technical = getAgentResult(results, 'technical');

  if (!technical) return null;

  const indicators = technical.indicators || {};
  const patterns = technical.patterns || {};

  return {
    rsi: extractNumericValue(indicators.rsi),
    macd: extractNumericValue(indicators.macd),
    macd_signal: extractNumericValue(indicators.macd_signal),
    macd_histogram: extractNumericValue(indicators.macd_histogram),
    bb_upper: extractNumericValue(indicators.bb_upper),
    bb_middle: extractNumericValue(indicators.bb_middle),
    bb_lower: extractNumericValue(indicators.bb_lower),
    atr: extractNumericValue(indicators.atr),
    adx: extractNumericValue(indicators.adx),
    support_levels: indicators.support_levels || [],
    resistance_levels: indicators.resistance_levels || [],
    patterns_detected: patterns.detected || [],
    trend: technical.trend || 'NEUTRAL'
  };
};

/**
 * Extract risk data safely
 */
export const extractRiskData = (results: any) => {
  const risk = getAgentResult(results, 'risk');

  if (!risk) return null;

  const metrics = risk.risk_metrics || {};

  return {
    var_95: extractNumericValue(metrics.var_95),
    cvar_95: extractNumericValue(metrics.cvar_95),
    sharpe_ratio: extractNumericValue(metrics.sharpe_ratio),
    sortino_ratio: extractNumericValue(metrics.sortino_ratio),
    max_drawdown: extractNumericValue(metrics.max_drawdown),
    volatility: extractNumericValue(metrics.volatility),
    beta: extractNumericValue(metrics.beta),
    risk_level: risk.risk_level || 'MEDIUM',
    risk_factors: risk.risk_factors || []
  };
};

/**
 * Extract market data safely
 */
export const extractMarketData = (results: any) => {
  const marketData = getAgentResult(results, 'market_data');

  if (!marketData) return null;

  return {
    current_price: extractNumericValue(marketData.current_price),
    previous_close: extractNumericValue(marketData.previous_close),
    change: extractNumericValue(marketData.change),
    change_percent: extractNumericValue(marketData.change_percent),
    volume: extractNumericValue(marketData.volume),
    avg_volume: extractNumericValue(marketData.avg_volume),
    market_cap: extractNumericValue(marketData.market_cap),
    day_high: extractNumericValue(marketData.day_high),
    day_low: extractNumericValue(marketData.day_low),
    week_52_high: extractNumericValue(marketData['52_week_high'] || marketData.week_52_high),
    week_52_low: extractNumericValue(marketData['52_week_low'] || marketData.week_52_low)
  };
};

/**
 * Extract data quality metrics
 */
export const extractDataQuality = (results: any) => {
  const dataQuality = results?.data_quality || results?.metadata?.data_quality;

  if (!dataQuality) return null;

  return {
    overall_score: extractNumericValue(dataQuality.overall_score, 0),
    grade: dataQuality.grade || 'N/A',
    reliability_score: extractNumericValue(dataQuality.reliability_score, 0),
    freshness_score: extractNumericValue(dataQuality.freshness_score, 0),
    completeness_score: extractNumericValue(dataQuality.completeness_score, 0)
  };
};
