"""
Enhanced Stock Analysis Workflow
Uses expert AI agents with local calculations - no external API dependencies
Implements DAG-based parallel execution with progress tracking
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import asyncio
from dataclasses import is_dataclass, asdict

from langchain_openai import ChatOpenAI

from agents.expert_agents.expert_fundamental_agent import ExpertFundamentalAgent
from agents.expert_agents.expert_technical_agent import ExpertTechnicalAgent
from agents.expert_agents.expert_risk_agent import ExpertRiskAgent
from agents.expert_agents.expert_synthesis_agent import ExpertSynthesisAgent
from agents.workers.peer_comparison_agent import PeerComparisonAgent
from agents.workers.critique_agent import CritiqueAgent
from agents.workers.insider_activity_agent import InsiderActivityAgent
from agents.workers.predictive_agent import PredictiveAnalyticsAgent

logger = logging.getLogger(__name__)


def convert_to_serializable(obj):
    """Convert dataclasses and other non-serializable objects to dicts for MongoDB."""
    if is_dataclass(obj):
        return asdict(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj


class EnhancedStockWorkflow:
    """
    Orchestrates expert AI agents for comprehensive stock analysis
    """

    def __init__(self, llm: ChatOpenAI, database, tavily_api_key: str = None, redis_url: str = None):
        self.llm = llm
        self.database = database

        # Initialize expert agents
        self.fundamental_agent = ExpertFundamentalAgent(llm)
        self.technical_agent = ExpertTechnicalAgent(llm)
        self.risk_agent = ExpertRiskAgent(llm)
        self.synthesis_agent = ExpertSynthesisAgent(llm)

        # Initialize Tavily cache (optional)
        self.tavily_cache = None
        if redis_url:
            try:
                from services.tavily_cache import get_tavily_cache
                self.tavily_cache = get_tavily_cache(redis_url)
                logger.info("[EnhancedWorkflow] Tavily cache enabled")
            except Exception as e:
                logger.warning(f"[EnhancedWorkflow] Tavily cache disabled: {e}")

        # Initialize SmartModelRouter (optional)
        self.smart_router = None
        try:
            from services.smart_model_router import get_smart_router
            import os
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.smart_router = get_smart_router(openai_key)
                logger.info("[EnhancedWorkflow] SmartModelRouter enabled")
        except Exception as e:
            logger.warning(f"[EnhancedWorkflow] SmartModelRouter disabled: {e}")

        # Initialize Tavily enrichment (optional)
        self.hybrid_orchestrator = None
        if tavily_api_key:
            try:
                from workflow.hybrid_orchestrator import HybridOrchestrator
                self.hybrid_orchestrator = HybridOrchestrator(
                    tavily_api_key, llm, database,
                    cache=self.tavily_cache,
                    router=self.smart_router
                )
                logger.info("[EnhancedWorkflow] Tavily enrichment enabled (cache: %s, router: %s)",
                           "yes" if self.tavily_cache else "no",
                           "yes" if self.smart_router else "no")
            except Exception as e:
                logger.warning(f"[EnhancedWorkflow] Tavily enrichment disabled: {e}")

        # Initialize Tavily-based sentiment agent (if available)
        self.sentiment_agent = None
        if tavily_api_key:
            try:
                from agents.tavily_agents import TavilySentimentTrackerAgent
                self.sentiment_agent = TavilySentimentTrackerAgent(tavily_api_key, llm, cache=self.tavily_cache)
                logger.info("[EnhancedWorkflow] Sentiment agent enabled")
            except Exception as e:
                logger.warning(f"[EnhancedWorkflow] Sentiment agent disabled: {e}")

        # Initialize additional analysis agents (Phase 3)
        self.peer_comparison_agent = None
        self.insider_activity_agent = None
        self.predictive_agent = None
        self.critique_agent = None
        self.catalyst_tracker_agent = None
        self.chart_analytics_agent = None

        if tavily_api_key:
            try:
                from services.tavily_service import TavilyMarketService
                tavily_client = TavilyMarketService(api_key=tavily_api_key)
                self.peer_comparison_agent = PeerComparisonAgent("peer_comparison", "peer_comparison", tavily_client=tavily_client)
                self.insider_activity_agent = InsiderActivityAgent(tavily_client=tavily_client)

                # Add Catalyst Tracker
                from agents.workers.catalyst_tracker_agent import CatalystTrackerAgent
                self.catalyst_tracker_agent = CatalystTrackerAgent(tavily_client=tavily_client)

                logger.info("[EnhancedWorkflow] Peer Comparison, Insider Activity & Catalyst Tracker agents enabled")
            except Exception as e:
                logger.warning(f"[EnhancedWorkflow] Tavily-based agents disabled: {e}")

        # Predictive agent (no Tavily required)
        try:
            self.predictive_agent = PredictiveAnalyticsAgent()
            logger.info("[EnhancedWorkflow] Predictive Analytics agent enabled")
        except Exception as e:
            logger.warning(f"[EnhancedWorkflow] Predictive agent disabled: {e}")

        # Critique agent (LLM-based)
        try:
            self.critique_agent = CritiqueAgent("critique", "critique", tavily_client=None, llm=llm)
            logger.info("[EnhancedWorkflow] Critique agent enabled")
        except Exception as e:
            logger.warning(f"[EnhancedWorkflow] Critique agent disabled: {e}")

        # Chart Analytics agent (yfinance-based, no API key required)
        try:
            from agents.workers.chart_analytics_agent import ChartAnalyticsAgent
            self.chart_analytics_agent = ChartAnalyticsAgent(name="ChartAnalyticsAgent", llm=llm, database=database)
            logger.info("[EnhancedWorkflow] Chart Analytics agent enabled")
        except Exception as e:
            logger.warning(f"[EnhancedWorkflow] Chart Analytics agent disabled: {e}")

        # Track total agents for progress calculation
        active_agents = 4  # Base: Fundamental, Technical, Risk, Synthesis
        if self.sentiment_agent: active_agents += 1
        if self.peer_comparison_agent: active_agents += 1
        if self.insider_activity_agent: active_agents += 1
        if self.predictive_agent: active_agents += 1
        if self.critique_agent: active_agents += 1
        if self.catalyst_tracker_agent: active_agents += 1
        if self.chart_analytics_agent: active_agents += 1
        self.total_agents = active_agents
        logger.info(f"[EnhancedWorkflow] Total active agents: {self.total_agents}")

    async def execute(self, analysis_id: str, query: str, symbols: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute complete analysis workflow with parallel agent execution

        Args:
            analysis_id: MongoDB document ID for tracking
            query: User's analysis query
            symbols: List of stock symbols to analyze
            context: Additional context (market data, historical prices, etc.)

        Returns:
            Complete analysis with recommendations
        """
        logger.info(f"[EnhancedWorkflow] Starting analysis for {symbols} (ID: {analysis_id})")

        try:
            # Initialize progress tracking
            await self._update_progress(analysis_id, 0, "Starting analysis...")

            # Step 1: Parse query and prepare context
            symbol = symbols[0] if symbols else 'UNKNOWN'
            if context is None:
                context = await self._prepare_context(symbol)

            # Step 2: Execute core analysis agents in parallel (Fundamental, Technical, Risk)
            await self._update_progress(analysis_id, 10, "Running core analysis agents...")

            # Build list of agents to run
            agent_tasks = [
                self._run_agent_with_tracking(analysis_id, 'ExpertFundamentalAgent', self.fundamental_agent, context),
                self._run_agent_with_tracking(analysis_id, 'ExpertTechnicalAgent', self.technical_agent, context),
                self._run_agent_with_tracking(analysis_id, 'ExpertRiskAgent', self.risk_agent, context),
            ]

            # Add sentiment agent if available
            if self.sentiment_agent:
                sentiment_context = {'symbol': symbol, 'sector': context.get('sector', 'Technology')}
                agent_tasks.append(
                    self._run_agent_with_tracking(analysis_id, 'TavilySentimentAgent', self.sentiment_agent, sentiment_context, method='track')
                )

            # Add peer comparison agent if available
            if self.peer_comparison_agent:
                peer_context = {'stock_symbols': [symbol], 'markets': ['US']}
                agent_tasks.append(
                    self._run_agent_with_tracking(analysis_id, 'PeerComparisonAgent', self.peer_comparison_agent, peer_context, method='execute')
                )

            # Add insider activity agent if available
            if self.insider_activity_agent:
                insider_context = {'symbol': symbol, 'symbols': [symbol]}
                agent_tasks.append(
                    self._run_agent_with_tracking(analysis_id, 'InsiderActivityAgent', self.insider_activity_agent, insider_context, method='execute')
                )

            # Add predictive agent if available
            if self.predictive_agent:
                # Predictive agent needs symbol and optional sentiment data
                agent_tasks.append(
                    self._run_agent_with_tracking(analysis_id, 'PredictiveAgent', self.predictive_agent, {'symbol': symbol}, method='execute')
                )

            # Add catalyst tracker agent if available
            if self.catalyst_tracker_agent:
                agent_tasks.append(
                    self._run_agent_with_tracking(analysis_id, 'CatalystTrackerAgent', self.catalyst_tracker_agent, symbol, method='execute')
                )

            # Add chart analytics agent if available
            if self.chart_analytics_agent:
                chart_context = {'symbol': symbol}
                agent_tasks.append(
                    self._run_agent_with_tracking(analysis_id, 'ChartAnalyticsAgent', self.chart_analytics_agent, chart_context, method='execute')
                )

            parallel_results = await asyncio.gather(*agent_tasks, return_exceptions=True)

            # Unpack results safely
            fundamental_result = parallel_results[0] if not isinstance(parallel_results[0], Exception) else {}
            technical_result = parallel_results[1] if not isinstance(parallel_results[1], Exception) else {}
            risk_result = parallel_results[2] if not isinstance(parallel_results[2], Exception) else {}

            # Dynamic unpacking based on active agents
            result_idx = 3
            sentiment_result = {}
            peer_comparison_result = {}
            insider_activity_result = {}
            predictive_result = {}
            catalyst_result = {}
            chart_analytics_result = {}

            if self.sentiment_agent and result_idx < len(parallel_results):
                sentiment_result = parallel_results[result_idx] if not isinstance(parallel_results[result_idx], Exception) else {}
                result_idx += 1

            if self.peer_comparison_agent and result_idx < len(parallel_results):
                peer_comparison_result = parallel_results[result_idx] if not isinstance(parallel_results[result_idx], Exception) else {}
                result_idx += 1

            if self.insider_activity_agent and result_idx < len(parallel_results):
                insider_activity_result = parallel_results[result_idx] if not isinstance(parallel_results[result_idx], Exception) else {}
                result_idx += 1

            if self.predictive_agent and result_idx < len(parallel_results):
                predictive_result = parallel_results[result_idx] if not isinstance(parallel_results[result_idx], Exception) else {}
                result_idx += 1

            if self.catalyst_tracker_agent and result_idx < len(parallel_results):
                catalyst_result = parallel_results[result_idx] if not isinstance(parallel_results[result_idx], Exception) else {}
                result_idx += 1

            if self.chart_analytics_agent and result_idx < len(parallel_results):
                chart_analytics_result = parallel_results[result_idx] if not isinstance(parallel_results[result_idx], Exception) else {}
                result_idx += 1

            await self._update_progress(analysis_id, 70, "Synthesizing recommendations...")

            # Step 3: Synthesis agent combines all analyses
            analyses = {
                'fundamental': fundamental_result,
                'technical': technical_result,
                'risk': risk_result,
                'sentiment': sentiment_result,
                'peer_comparison': peer_comparison_result,
                'insider_activity': insider_activity_result,
                'predictive': predictive_result,
                'catalysts': catalyst_result,
                'chart_analytics': chart_analytics_result,
                'market': context.get('market_data', {})
            }

            synthesis_result = await self._run_agent_with_tracking(
                analysis_id,
                'ExpertSynthesisAgent',
                self.synthesis_agent,
                analyses,
                method='synthesize'
            )

            # Step 3.5: Critique agent validates synthesis (if available)
            critique_result = {}
            if self.critique_agent:
                await self._update_progress(analysis_id, 75, "Validating synthesis quality...")
                try:
                    critique_context = {
                        'synthesis': synthesis_result,
                        'confidence_score': synthesis_result.get('confidence', 0.5),
                        'agent_results': analyses
                    }
                    critique_result = await self._run_agent_with_tracking(
                        analysis_id,
                        'CritiqueAgent',
                        self.critique_agent,
                        critique_context,
                        method='execute'
                    )

                    # Adjust confidence based on critique
                    if critique_result and 'confidence_adjustment' in critique_result:
                        original_confidence = synthesis_result.get('confidence', 0.5)
                        adjusted_confidence = max(0.0, min(1.0, original_confidence + critique_result['confidence_adjustment']))
                        synthesis_result['confidence'] = adjusted_confidence
                        logger.info(f"[EnhancedWorkflow] Critique adjusted confidence: {original_confidence:.2f} → {adjusted_confidence:.2f}")

                except Exception as e:
                    logger.warning(f"[EnhancedWorkflow] Critique agent failed: {e}")
                    critique_result = {}

            # Step 4: Optional Tavily enrichment (if enabled)
            base_result = {
                'recommendation': synthesis_result.get('action', 'HOLD'),
                'confidence': synthesis_result.get('confidence', 0.5),
                'sector': context.get('sector', 'General'),
                'market_data': context.get('market_data', {}),
                'reasoning': synthesis_result.get('summary', '')
            }

            # Enrich with Tavily intelligence if available
            if self.hybrid_orchestrator:
                await self._update_progress(analysis_id, 85, "Enriching with real-time intelligence...")
                try:
                    enriched = await self.hybrid_orchestrator.enrich_analysis(
                        analysis_id, symbol, base_result
                    )
                    # Use enriched recommendation if available
                    final_recommendation = enriched.get('recommendation', base_result['recommendation'])
                    final_confidence = enriched.get('confidence', base_result['confidence'])
                    enrichment_data = enriched.get('tavily_intelligence', {})
                    enrichment_status = enriched.get('enrichment_status', 'success')
                except Exception as e:
                    logger.warning(f"[EnhancedWorkflow] Tavily enrichment failed, using base: {e}")
                    final_recommendation = base_result['recommendation']
                    final_confidence = base_result['confidence']
                    enrichment_data = {}
                    enrichment_status = 'failed'
            else:
                final_recommendation = base_result['recommendation']
                final_confidence = base_result['confidence']
                enrichment_data = {}
                enrichment_status = 'disabled'

            await self._update_progress(analysis_id, 100, "Analysis complete")

            # Step 5: Build final response
            final_result = {
                'analysis_id': analysis_id,
                'query': query,
                'symbols': symbols,
                'status': 'completed',
                # CRITICAL: agent_results needed for frontend synthesis data access
                'agent_results': analyses,
                # Frontend compatibility - add fields at root level
                'executive_summary': synthesis_result.get('summary', ''),
                'investment_thesis': fundamental_result.get('insights', {}).get('investment_thesis', '') if fundamental_result else '',
                'confidence_score': final_confidence,
                # Frontend expects these at root level
                'fundamental_analysis': {
                    'fundamental_data': {symbols[0]: fundamental_result} if fundamental_result and symbols else {},
                    'key_insights': fundamental_result.get('insights', {}).get('competitive_advantages', []) if fundamental_result else [],
                    'valuation_summary': fundamental_result.get('insights', {}).get('valuation_assessment', '') if fundamental_result else '',
                    'risks': fundamental_result.get('insights', {}).get('risks', []) if fundamental_result else []
                },
                'technical_analysis': {
                    'technical_data': {symbols[0]: technical_result} if technical_result and symbols else {},
                    'trend_analysis': technical_result.get('insights', {}).get('trend_analysis', '') if technical_result else '',
                    'signals': {
                        'rsi': technical_result.get('rsi', {}) if technical_result else {},
                        'macd': technical_result.get('macd', {}) if technical_result else {},
                        'support_levels': technical_result.get('support_levels', []) if technical_result else [],
                        'resistance_levels': technical_result.get('resistance_levels', []) if technical_result else []
                    }
                },
                'risk_analysis': {
                    'risk_data': {symbols[0]: risk_result} if risk_result and symbols else {},
                    'risk_level': risk_result.get('risk_level', 'MEDIUM') if risk_result else 'MEDIUM',
                    'risk_score': risk_result.get('risk_score', 50) if risk_result else 50,
                    'mitigation_strategies': risk_result.get('insights', {}).get('risk_mitigation', '') if risk_result else ''
                },
                'market_data': context.get('market_data', {}),
                'valuation_analysis': {
                    'intrinsic_value': fundamental_result.get('intrinsic_value') if fundamental_result else None,
                    'fair_value': fundamental_result.get('metrics', {}).get('graham_number', {}).get('fair_value') if fundamental_result else None,
                    'price_to_fair_value': None  # Calculate if needed
                },
                'macro_analysis': enrichment_data.get('macro', {}),
                'insider_analysis': insider_activity_result or {},
                'catalyst_calendar': catalyst_result or {},
                'chart_analytics': chart_analytics_result or {},  # Expert trader charts
                # Original nested structure for backward compatibility
                'analysis': {
                    'summary': synthesis_result.get('summary', ''),
                    'market_data': context.get('market_data', {}),
                    'fundamental': fundamental_result,
                    'technical': technical_result,
                    'risk': risk_result,
                    'sentiment': sentiment_result or enrichment_data.get('sentiment', {}),  # From direct sentiment agent or Tavily
                    'peer_comparison': peer_comparison_result,  # Phase 3 agents
                    'insider_activity': insider_activity_result,
                    'predictive': predictive_result,
                    'catalysts': catalyst_result,  # Catalyst calendar
                    'chart_analytics': chart_analytics_result,  # Expert trading charts
                    'critique': critique_result,
                    'news': enrichment_data.get('news', {}),  # From Tavily
                    'macro': enrichment_data.get('macro', {})  # From Tavily
                },
                'recommendations': {
                    'action': final_recommendation,  # Enriched or base
                    'confidence': final_confidence,  # Enriched or base (potentially adjusted by critique)
                    'target_price': synthesis_result.get('target_price', 0),
                    'stop_loss': synthesis_result.get('stop_loss', 0),
                    'entry_price': synthesis_result.get('entry_price', 0),
                    'time_horizon': synthesis_result.get('time_horizon', 'medium_term'),
                    'risk_reward_ratio': synthesis_result.get('risk_reward_ratio', 1.0),
                    'key_catalysts': synthesis_result.get('key_catalysts', []),
                    'risks': synthesis_result.get('risks', []),
                    'strategy': synthesis_result.get('strategy', [])
                },
                'consensus_breakdown': synthesis_result.get('consensus_breakdown', {}),
                'agent_agreement': synthesis_result.get('agent_agreement', ''),
                'enrichment_status': enrichment_status,
                'synthesis': synthesis_result,  # CRITICAL FIX: Include full synthesis object for frontend data_quality badge
                'quality_assurance': {
                    'critique_passed': critique_result.get('quality_pass', True) if critique_result else True,
                    'critical_issues': critique_result.get('critical_issues', []) if critique_result else [],
                    'revision_priority': critique_result.get('revision_priority', 'NONE') if critique_result else 'NONE'
                },
                'completed_at': datetime.utcnow().isoformat()
            }

            # Save to database
            await self._save_results(analysis_id, final_result)

            logger.info(f"[EnhancedWorkflow] Analysis complete: {synthesis_result.get('action', 'HOLD')} with {synthesis_result.get('confidence', 0)*100}% confidence")

            return final_result

        except Exception as e:
            logger.error(f"[EnhancedWorkflow] Fatal error: {e}", exc_info=True)
            await self._mark_failed(analysis_id, str(e))
            raise

    async def _run_agent_with_tracking(self, analysis_id: str, agent_name: str, agent: Any, context: Dict, method: str = 'analyze') -> Dict:
        """
        Run an agent and track execution in MongoDB

        Args:
            analysis_id: Analysis document ID
            agent_name: Name of the agent for tracking
            agent: Agent instance
            context: Context to pass to agent
            method: Method to call on agent (analyze or synthesize)
        """
        logger.info(f"[EnhancedWorkflow] Starting {agent_name}")

        # Track agent start
        agent_execution = {
            'agent': agent_name,
            'status': 'RUNNING',
            'start_time': datetime.utcnow(),
            'end_time': None,
            'error': None
        }

        await self.database['analyses'].update_one(
            {"id": analysis_id},
            {
                "$push": {"agent_executions": agent_execution},
                "$set": {"active_agent": agent_name}
            }
        )

        # Send WebSocket update for agent start
        await self._send_websocket_update(analysis_id, {
            "type": "agent_started",
            "agent": agent_name,
            "status": "RUNNING",
            "message": f"{agent_name} is now running",
            "timestamp": datetime.utcnow().isoformat()
        })

        try:
            # Execute agent with appropriate method
            if method == 'synthesize':
                result = await agent.synthesize(context)
            elif method == 'execute':
                result = await agent.execute(context)
            elif method == 'track':
                result = await agent.track(context)
            else:
                result = await agent.analyze(context)

            # Convert AgentState to dict if needed
            if hasattr(result, 'output_data'):
                # AgentState object - extract output_data
                result = result.output_data if result.output_data else {}
            elif not isinstance(result, dict):
                # Unknown type - convert to empty dict
                logger.warning(f"[EnhancedWorkflow] {agent_name} returned non-dict result: {type(result)}")
                result = {}

            # Mark agent as completed
            await self.database['analyses'].update_one(
                {"id": analysis_id, "agent_executions.agent": agent_name},
                {
                    "$set": {
                        "agent_executions.$.status": "COMPLETED",
                        "agent_executions.$.end_time": datetime.utcnow(),
                        "active_agent": None  # Clear active agent when completed
                    }
                }
            )

            # Update progress
            completed_count = await self._get_completed_count(analysis_id)
            progress_percent = int((completed_count / self.total_agents) * 100)
            await self._update_progress(analysis_id, progress_percent, f"{agent_name} completed")

            # Send WebSocket update for agent completion
            await self._send_websocket_update(analysis_id, {
                "type": "agent_completed",
                "agent": agent_name,
                "status": "COMPLETED",
                "message": f"{agent_name} completed successfully",
                "progress": progress_percent,
                "timestamp": datetime.utcnow().isoformat()
            })

            logger.info(f"[EnhancedWorkflow] {agent_name} completed successfully")
            return result

        except Exception as e:
            logger.error(f"[EnhancedWorkflow] {agent_name} failed: {e}", exc_info=True)

            # Mark agent as failed
            await self.database['analyses'].update_one(
                {"id": analysis_id, "agent_executions.agent": agent_name},
                {
                    "$set": {
                        "agent_executions.$.status": "FAILED",
                        "agent_executions.$.end_time": datetime.utcnow(),
                        "agent_executions.$.error": str(e)
                    }
                }
            )

            # Return empty result so workflow continues
            return {
                'agent': agent_name,
                'status': 'failed',
                'error': str(e)
            }

    async def _prepare_context(self, symbol: str) -> Dict[str, Any]:
        """
        Prepare context for agents - fetch REAL market data, historical prices from FinancialDataService

        Args:
            symbol: Stock symbol

        Returns:
            Context dictionary with REAL market data and historical prices
        """
        try:
            from services.financial_data_service import FinancialDataService
            service = FinancialDataService()

            logger.info(f"[EnhancedWorkflow] Fetching real data for {symbol}")

            # Get real-time quote
            quote = await service.get_stock_quote(symbol)

            # Get 1 year of historical data (returns List[Dict] with OHLCV)
            historical_data = await service.get_historical_data(symbol, period="1y", interval="1d")

            # Get fundamental data
            fundamentals = await service.get_fundamental_data(symbol)

            # Extract price arrays from historical data
            closes = [d['close'] for d in historical_data]
            volumes = [d['volume'] for d in historical_data]
            highs = [d['high'] for d in historical_data]
            lows = [d['low'] for d in historical_data]

            # Prepare context with REAL data
            context = {
                'symbol': symbol,
                'prices': closes,  # Real historical closes (252 days)
                'volumes': volumes,
                'highs': highs,
                'lows': lows,
                'market_data': quote,  # Real-time quote data
                'fundamentals': fundamentals,  # Real P/E, EPS, etc.
                'sector': fundamentals.get('sector', 'Technology'),
                'historical_prices': closes[-30:] if len(closes) >= 30 else closes,  # Last 30 days
                'balance_sheet': fundamentals.get('balance_sheet', {}),
                'income_statement': fundamentals.get('income_statement', {}),
                'cash_flow': fundamentals.get('cash_flow', {})
            }

            logger.info(f"[EnhancedWorkflow] Fetched {len(closes)} days of price data for {symbol}")
            return context

        except Exception as e:
            logger.error(f"[EnhancedWorkflow] Failed to fetch real data for {symbol}: {e}", exc_info=True)

            # Fallback to minimal context
            return {
                'symbol': symbol,
                'prices': [],
                'volumes': [],
                'highs': [],
                'lows': [],
                'market_data': {
                    'symbol': symbol,
                    'price': 0,
                    'change': 0,
                    'volume': 0,
                    'error': f"Data fetch failed: {str(e)}"
                },
                'sector': 'Unknown',
                'historical_prices': [],
                'balance_sheet': {},
                'income_statement': {},
                'cash_flow': {}
            }

    async def _get_completed_count(self, analysis_id: str) -> int:
        """Count completed agents"""
        analysis = await self.database['analyses'].find_one({"id": analysis_id})
        if analysis and 'agent_executions' in analysis:
            return len([e for e in analysis['agent_executions'] if e.get('status') == 'COMPLETED'])
        return 0

    async def _update_progress(self, analysis_id: str, percentage: int, message: str, active_agents: List[str] = None, completed_agents: List[str] = None):
        """Update progress tracking with agent-level detail"""
        # Get current agent status from database
        analysis = await self.database['analyses'].find_one({"id": analysis_id})
        agent_execs = analysis.get('agent_executions', []) if analysis else []

        # Determine active and completed agents from execution records
        if active_agents is None:
            active_agents = [e['agent'] for e in agent_execs if e.get('status') == 'RUNNING']
        if completed_agents is None:
            completed_agents = [e['agent'] for e in agent_execs if e.get('status') == 'COMPLETED']

        # Build dynamic list of all possible agents based on what's actually initialized
        all_agents = []
        if self.fundamental_agent: all_agents.append('ExpertFundamentalAgent')
        if self.technical_agent: all_agents.append('ExpertTechnicalAgent')
        if self.risk_agent: all_agents.append('ExpertRiskAgent')
        if self.sentiment_agent: all_agents.append('TavilySentimentAgent')
        if self.peer_comparison_agent: all_agents.append('PeerComparisonAgent')
        if self.insider_activity_agent: all_agents.append('InsiderActivityAgent')
        if self.predictive_agent: all_agents.append('PredictiveAgent')
        if self.catalyst_tracker_agent: all_agents.append('CatalystTrackerAgent')
        if self.chart_analytics_agent: all_agents.append('ChartAnalyticsAgent')
        if self.synthesis_agent: all_agents.append('ExpertSynthesisAgent')
        if self.critique_agent: all_agents.append('CritiqueAgent')

        # Calculate pending agents (not completed and not running)
        pending_agents = [a for a in all_agents if a not in completed_agents and a not in active_agents]

        progress_data = {
            "percentage": percentage,
            "message": message,
            "active_agents": active_agents,
            "completed_agents": completed_agents,
            "pending_agents": pending_agents,
            "updated_at": datetime.utcnow().isoformat()
        }

        await self.database['analyses'].update_one(
            {"id": analysis_id},
            {"$set": {"progress": progress_data}}
        )

        # Send WebSocket broadcast for progress update
        await self._send_websocket_update(analysis_id, {
            "type": "progress_update",
            "progress": progress_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def _save_results(self, analysis_id: str, result: Dict):
        """Save final results to analysis_results collection"""
        try:
            logger.info(f"[EnhancedWorkflow] Saving results for {analysis_id} to database")

            # Convert dataclasses (like Citation) to dicts for MongoDB serialization
            serializable_result = convert_to_serializable(result)

            logger.info(f"[EnhancedWorkflow] Serialized result has {len(serializable_result)} top-level keys")

            # Save to analysis_results collection
            # Add analysis_id to the result for proper querying
            serializable_result['analysis_id'] = analysis_id

            update_result = await self.database['analysis_results'].update_one(
                {"analysis_id": analysis_id},
                {"$set": serializable_result},
                upsert=True
            )

            logger.info(f"[EnhancedWorkflow] Saved to analysis_results: matched={update_result.matched_count}, modified={update_result.modified_count}, upserted={update_result.upserted_id}")

            # Update main analysis document
            await self.database['analyses'].update_one(
                {"id": analysis_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "active_agent": None
                    }
                }
            )

            logger.info(f"[EnhancedWorkflow] Successfully saved results for {analysis_id}")

        except Exception as e:
            logger.error(f"[EnhancedWorkflow] Failed to save results for {analysis_id}: {e}", exc_info=True)

    async def _mark_failed(self, analysis_id: str, error: str):
        """Mark analysis as failed"""
        await self.database['analyses'].update_one(
            {"id": analysis_id},
            {
                "$set": {
                    "status": "failed",
                    "error": error,
                    "completed_at": datetime.utcnow(),
                    "active_agent": None
                }
            }
        )

    async def _send_websocket_update(self, analysis_id: str, message: Dict[str, Any]):
        """
        Send real-time WebSocket update for progress tracking

        Args:
            analysis_id: Analysis ID to send update to
            message: Message payload to send
        """
        try:
            # Import manager from main to send WebSocket updates
            from main import manager
            await manager.send_message(message, analysis_id)
            logger.debug(f"[EnhancedWorkflow] Sent WebSocket update: {message.get('type')}")
        except Exception as e:
            # Non-critical - don't fail workflow if WebSocket fails
            logger.warning(f"[EnhancedWorkflow] WebSocket update failed: {e}")
