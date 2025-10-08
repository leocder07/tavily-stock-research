"""
Hybrid Orchestrator
Combines base expert analysis (70%) with Tavily intelligence (30%)
Implements weighted consensus and graceful degradation
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from langchain_openai import ChatOpenAI

from agents.tavily_agents import (
    TavilyNewsIntelligenceAgent,
    TavilySentimentTrackerAgent,
    MacroContextAgent
)

logger = logging.getLogger(__name__)


class HybridOrchestrator:
    """
    Orchestrates hybrid analysis workflow:
    1. Base analysis runs first (existing 4 expert agents) = 70% weight
    2. Tavily enrichment agents run after = 30% weight
    3. Weighted consensus combines both
    4. Graceful degradation if Tavily fails
    """

    def __init__(self, tavily_api_key: str, llm: ChatOpenAI, database, cache=None, router=None):
        self.llm = llm
        self.database = database

        # Initialize Tavily agents with optional cache
        self.news_agent = TavilyNewsIntelligenceAgent(tavily_api_key, llm, cache=cache, router=router)
        self.sentiment_agent = TavilySentimentTrackerAgent(tavily_api_key, llm, cache=cache)  # No router param
        self.macro_agent = MacroContextAgent(tavily_api_key, llm, cache=cache)  # No router param

        # Weights for consensus
        self.BASE_WEIGHT = 0.7  # 70% weight to base analysis
        self.TAVILY_WEIGHT = 0.3  # 30% weight to Tavily intelligence

    async def enrich_analysis(
        self,
        analysis_id: str,
        symbol: str,
        base_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich base analysis with Tavily intelligence

        Args:
            analysis_id: MongoDB analysis ID
            symbol: Stock symbol
            base_result: Result from base expert agents

        Returns:
            Enriched analysis with weighted recommendation
        """
        logger.info(f"[HybridOrchestrator] Enriching analysis for {symbol}")

        try:
            # Extract base recommendation and confidence
            base_recommendation = base_result.get('recommendation', 'HOLD')
            base_confidence = base_result.get('confidence', 0.5)
            base_reasoning = base_result.get('reasoning', '')

            # Prepare context for Tavily agents
            context = {
                'symbol': symbol,
                'sector': base_result.get('sector', 'General'),
                'market_data': base_result.get('market_data', {}),
                'base_recommendation': base_recommendation
            }

            # Run Tavily agents in parallel (with error handling)
            tavily_results = await self._run_tavily_agents(analysis_id, context)

            # Calculate weighted consensus
            final_result = self._calculate_weighted_consensus(
                base_result=base_result,
                tavily_results=tavily_results,
                base_weight=self.BASE_WEIGHT,
                tavily_weight=self.TAVILY_WEIGHT
            )

            # Save enriched result
            await self._save_enriched_result(analysis_id, final_result)

            logger.info(
                f"[HybridOrchestrator] Enrichment complete: "
                f"Base={base_recommendation} ({base_confidence:.2f}), "
                f"Final={final_result['recommendation']} ({final_result['confidence']:.2f})"
            )

            return final_result

        except Exception as e:
            logger.error(f"[HybridOrchestrator] Enrichment failed: {e}", exc_info=True)
            # Graceful degradation: return base result if enrichment fails
            return {
                **base_result,
                'enrichment_status': 'failed',
                'enrichment_error': str(e),
                'used_base_only': True
            }

    async def _run_tavily_agents(
        self,
        analysis_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run Tavily agents in parallel with error handling"""

        async def safe_agent_run(agent_name: str, agent_method, context: Dict) -> Dict:
            """Wrapper for safe agent execution"""
            try:
                logger.info(f"[{agent_name}] Starting...")
                result = await agent_method(context)
                logger.info(f"[{agent_name}] Completed successfully")
                return {'status': 'success', 'data': result}
            except Exception as e:
                logger.error(f"[{agent_name}] Failed: {e}")
                return {'status': 'failed', 'error': str(e), 'data': {}}

        # Run all Tavily agents in parallel
        results = await asyncio.gather(
            safe_agent_run('NewsIntelligence', self.news_agent.analyze, context),
            safe_agent_run('SentimentTracker', self.sentiment_agent.analyze, context),
            safe_agent_run('MacroContext', self.macro_agent.analyze, context),
            return_exceptions=True
        )

        # Unpack results
        news_result, sentiment_result, macro_result = results

        # Pass news sentiment to sentiment agent for divergence calculation
        if news_result['status'] == 'success' and sentiment_result['status'] == 'success':
            context['news_sentiment'] = news_result['data'].get('sentiment', {})
            # Re-run sentiment agent with news context (async)
            sentiment_result = await safe_agent_run(
                'SentimentTracker',
                self.sentiment_agent.analyze,
                context
            )

        return {
            'news_intelligence': news_result,
            'sentiment_tracker': sentiment_result,
            'macro_context': macro_result
        }

    def _calculate_weighted_consensus(
        self,
        base_result: Dict[str, Any],
        tavily_results: Dict[str, Any],
        base_weight: float,
        tavily_weight: float
    ) -> Dict[str, Any]:
        """
        Calculate weighted consensus between base and Tavily analysis

        Recommendation Score Mapping:
        STRONG_BUY = 1.0
        BUY = 0.5
        HOLD = 0.0
        SELL = -0.5
        STRONG_SELL = -1.0
        """
        # Map recommendations to numeric scores
        rec_to_score = {
            'STRONG_BUY': 1.0,
            'BUY': 0.5,
            'HOLD': 0.0,
            'SELL': -0.5,
            'STRONG_SELL': -1.0
        }
        score_to_rec = {
            (0.75, 1.0): 'STRONG_BUY',
            (0.25, 0.75): 'BUY',
            (-0.25, 0.25): 'HOLD',
            (-0.75, -0.25): 'SELL',
            (-1.0, -0.75): 'STRONG_SELL'
        }

        # Base analysis score
        base_rec = base_result.get('recommendation', 'HOLD')
        base_score = rec_to_score.get(base_rec, 0.0)
        base_confidence = base_result.get('confidence', 0.5)

        # Tavily adjustments
        tavily_adjustment = 0.0
        tavily_confidence = 0.0
        tavily_count = 0

        # News sentiment adjustment
        news_data = tavily_results.get('news_intelligence', {}).get('data', {})
        if news_data and news_data.get('sentiment', {}).get('score') is not None:
            news_sentiment = news_data['sentiment']['score']
            news_conf = news_data['sentiment'].get('confidence', 0.5)
            enrichment_score = news_data.get('enrichment_score', 0.5)

            # Weight news impact by enrichment score
            tavily_adjustment += news_sentiment * enrichment_score
            tavily_confidence += news_conf
            tavily_count += 1

        # Retail sentiment divergence
        sentiment_data = tavily_results.get('sentiment_tracker', {}).get('data', {})
        if sentiment_data and sentiment_data.get('sentiment_pulse', {}).get('score') is not None:
            retail_score = sentiment_data['sentiment_pulse']['score']
            retail_conf = sentiment_data['sentiment_pulse'].get('confidence', 0.5)
            divergence = sentiment_data.get('divergence_score', 0.0)

            # High divergence = use retail sentiment as contrarian signal
            if divergence > 0.5:  # Significant divergence
                tavily_adjustment += retail_score * 0.3  # Lower weight for contrarian signal
            else:
                tavily_adjustment += retail_score * 0.5

            tavily_confidence += retail_conf
            tavily_count += 1

        # Macro context impact
        macro_data = tavily_results.get('macro_context', {}).get('data', {})
        if macro_data and macro_data.get('context_score') is not None:
            macro_score = macro_data['context_score']
            macro_conf = macro_data.get('confidence', 0.5)

            tavily_adjustment += macro_score
            tavily_confidence += macro_conf
            tavily_count += 1

        # Calculate average Tavily adjustment
        if tavily_count > 0:
            tavily_adjustment = tavily_adjustment / tavily_count
            tavily_confidence = tavily_confidence / tavily_count
        else:
            # No Tavily data: use base only
            logger.warning("[HybridOrchestrator] No Tavily data, using base analysis only")
            return {
                **base_result,
                'enrichment_status': 'no_data',
                'used_base_only': True
            }

        # Weighted consensus
        final_score = (base_score * base_weight) + (tavily_adjustment * tavily_weight)
        final_confidence = (base_confidence * base_weight) + (tavily_confidence * tavily_weight)

        # Map score back to recommendation
        final_recommendation = 'HOLD'
        for (low, high), rec in score_to_rec.items():
            if low <= final_score <= high:
                final_recommendation = rec
                break

        # Build enriched result
        enriched_result = {
            **base_result,
            'recommendation': final_recommendation,
            'confidence': round(final_confidence, 3),
            'enrichment_status': 'success',
            'consensus_breakdown': {
                'base_recommendation': base_rec,
                'base_score': base_score,
                'base_confidence': base_confidence,
                'base_weight': base_weight,
                'tavily_adjustment': round(tavily_adjustment, 3),
                'tavily_confidence': round(tavily_confidence, 3),
                'tavily_weight': tavily_weight,
                'final_score': round(final_score, 3),
                'final_confidence': round(final_confidence, 3)
            },
            'tavily_intelligence': {
                'news': news_data,
                'sentiment': sentiment_data,
                'macro': macro_data
            },
            'used_base_only': False
        }

        return enriched_result

    async def _save_enriched_result(self, analysis_id: str, result: Dict[str, Any]):
        """Save enriched result to MongoDB"""
        try:
            # self.database is already a Motor database object with collections
            await self.database['analyses'].update_one(
                {'id': analysis_id},  # Changed from 'analysis_id' to 'id' to match schema
                {
                    '$set': {
                        'enriched_result': result,
                        'enrichment_timestamp': datetime.utcnow().isoformat(),
                        'final_recommendation': result.get('recommendation'),
                        'final_confidence': result.get('confidence')
                    }
                }
            )

            logger.info(f"[HybridOrchestrator] Saved enriched result for {analysis_id}")

        except Exception as e:
            logger.error(f"[HybridOrchestrator] Failed to save enriched result: {e}")
