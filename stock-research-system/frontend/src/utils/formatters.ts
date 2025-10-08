/**
 * Utility functions for formatting numbers and financial data
 */

/**
 * Format large numbers with K/M/B/T suffixes
 * @param num - The number to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted string (e.g., "1.5M", "2.3B")
 */
export const formatLargeNumber = (num: number | null | undefined, decimals: number = 2): string => {
  if (num === null || num === undefined || isNaN(num)) {
    return 'N/A';
  }

  const absNum = Math.abs(num);

  if (absNum >= 1e12) {
    return (num / 1e12).toFixed(decimals) + 'T';
  } else if (absNum >= 1e9) {
    return (num / 1e9).toFixed(decimals) + 'B';
  } else if (absNum >= 1e6) {
    return (num / 1e6).toFixed(decimals) + 'M';
  } else if (absNum >= 1e3) {
    return (num / 1e3).toFixed(decimals) + 'K';
  }

  return num.toFixed(decimals);
};

/**
 * Format currency values with $ symbol
 * @param value - The value to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted currency string (e.g., "$123.45")
 */
export const formatCurrency = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }

  return '$' + value.toFixed(decimals);
};

/**
 * Format percentage values with % symbol
 * @param value - The value to format (as a percentage, e.g., 5.25 for 5.25%)
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted percentage string (e.g., "5.25%")
 */
export const formatPercentage = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }

  return value.toFixed(decimals) + '%';
};

/**
 * Format market cap with proper suffix
 * @param marketCap - Market cap value
 * @returns Formatted string (e.g., "$500.2B")
 */
export const formatMarketCap = (marketCap: number | null | undefined): string => {
  if (marketCap === null || marketCap === undefined || isNaN(marketCap)) {
    return 'N/A';
  }

  return '$' + formatLargeNumber(marketCap, 2);
};

/**
 * Format volume with appropriate suffix
 * @param volume - Volume value
 * @returns Formatted string (e.g., "15.3M")
 */
export const formatVolume = (volume: number | null | undefined): string => {
  if (volume === null || volume === undefined || isNaN(volume)) {
    return 'N/A';
  }

  return formatLargeNumber(volume, 2);
};

/**
 * Determine market cap tier based on value
 * @param marketCap - Market cap value
 * @returns Tier description (e.g., "Large Cap", "Mid Cap", "Small Cap", "Micro Cap")
 */
export const getMarketCapTier = (marketCap: number | null | undefined): string => {
  if (marketCap === null || marketCap === undefined || isNaN(marketCap)) {
    return 'Unknown';
  }

  if (marketCap >= 200e9) {
    return 'Mega Cap';
  } else if (marketCap >= 10e9) {
    return 'Large Cap';
  } else if (marketCap >= 2e9) {
    return 'Mid Cap';
  } else if (marketCap >= 300e6) {
    return 'Small Cap';
  } else if (marketCap >= 50e6) {
    return 'Micro Cap';
  } else {
    return 'Nano Cap';
  }
};

/**
 * Format ratio values (like P/E ratio, beta)
 * @param value - The ratio value
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted string
 */
export const formatRatio = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }

  return value.toFixed(decimals);
};

/**
 * Get color for percentage change (positive/negative)
 * @param value - The percentage value
 * @returns Color code for Ant Design
 */
export const getChangeColor = (value: number | null | undefined): string => {
  if (value === null || value === undefined || isNaN(value)) {
    return '#000000';
  }

  if (value > 0) {
    return '#3f8600'; // green
  } else if (value < 0) {
    return '#cf1322'; // red
  }

  return '#000000'; // black for zero
};

/**
 * Get beta risk description
 * @param beta - Beta value
 * @returns Risk description
 */
export const getBetaDescription = (beta: number | null | undefined): string => {
  if (beta === null || beta === undefined || isNaN(beta)) {
    return 'Unknown';
  }

  if (beta > 1.5) {
    return 'High Volatility';
  } else if (beta > 1.0) {
    return 'Moderate-High';
  } else if (beta >= 0.8) {
    return 'Market Average';
  } else if (beta >= 0.5) {
    return 'Low-Moderate';
  } else {
    return 'Low Volatility';
  }
};
