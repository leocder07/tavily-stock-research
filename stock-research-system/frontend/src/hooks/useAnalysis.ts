import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export interface AnalysisState {
  isAnalyzing: boolean;
  error: string | null;
  analysisId: string | null;
}

export const useAnalysis = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<AnalysisState>({
    isAnalyzing: false,
    error: null,
    analysisId: null
  });

  // FIX: Track analyzing state per symbol to prevent multi-stock loading issue
  const analyzingSymbols = useRef<Set<string>>(new Set());

  const startAnalysis = useCallback(async (query: string, symbols?: string[]) => {
    const symbol = symbols?.[0] || query.match(/\b[A-Z]{1,5}\b/)?.[0] || 'UNKNOWN';

    // Track this specific symbol as analyzing
    analyzingSymbols.current.add(symbol);
    setState({ isAnalyzing: true, error: null, analysisId: null });

    try {
      // Start the analysis
      const response = await api.startAnalysis({
        query,
        symbols,
        include_technical: true,
        include_sentiment: true,
        include_fundamentals: true
      });

      if (response.analysis_id) {
        setState({
          isAnalyzing: false,
          error: null,
          analysisId: response.analysis_id
        });

        // Navigate to results page
        navigate(`/analysis/${response.analysis_id}`);
      } else {
        throw new Error('No analysis ID returned');
      }
    } catch (error: any) {
      setState({
        isAnalyzing: false,
        error: error.message || 'Failed to start analysis',
        analysisId: null
      });
    } finally {
      // Remove symbol from analyzing set
      analyzingSymbols.current.delete(symbol);
      // Only set analyzing to false if no symbols are being analyzed
      if (analyzingSymbols.current.size === 0) {
        setState(prev => ({ ...prev, isAnalyzing: false }));
      }
    }
  }, [navigate]);

  const viewAnalysis = useCallback((symbol: string) => {
    // Trigger analysis for the specific symbol
    startAnalysis(`analyze ${symbol} stock`, [symbol]);
  }, [startAnalysis]);

  const analyzeFromInput = useCallback((input: string) => {
    // Parse the input to extract symbols if present
    const symbolMatch = input.match(/\b[A-Z]{1,5}\b/g);
    const symbols = symbolMatch ? symbolMatch.filter(s => s.length <= 5) : undefined;

    startAnalysis(input, symbols);
  }, [startAnalysis]);

  // Check if specific symbol is being analyzed
  const isSymbolAnalyzing = useCallback((symbol: string) => {
    return analyzingSymbols.current.has(symbol);
  }, []);

  return {
    ...state,
    startAnalysis,
    viewAnalysis,
    analyzeFromInput,
    isSymbolAnalyzing // NEW: Per-symbol loading state
  };
};