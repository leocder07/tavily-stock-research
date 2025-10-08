"""
Expert Synthesis Agent
Combines all expert analyses into final recommendation
Multi-agent consensus with weighted scoring
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from validators.synthesis_validator import SynthesisValidator
from agents.consensus_engine import ConsensusRecommendationEngine

from calculators.position_sizer import PositionSizer, PositionSizeMethod
from calculators.order_builder import OrderBuilder, OrderSide, OrderType
from calculators.data_quality_validator import DataQualityValidator
from agents.mixins.lineage_mixin import LineageMixin
from services.data_lineage_tracker import DataSource, DataReliability
from utils.value_extractors import extract_numeric_value, extract_price_value

logger = logging.getLogger(__name__)


def add_unit_metadata(value: Union[float, int, None], unit: str, description: str = "") -> Dict[str, Any]:
    """
    Add unit and metadata to numeric values for type safety

    Args:
        value: The numeric value
        unit: The unit type (USD, percent, ratio, shares, etc.)
        description: Optional description of what this value represents

    Returns:
        Dict with value, unit, and metadata
    """
    return {
        'value': round(value, 2) if value is not None and isinstance(value, (int, float)) else value,
        'unit': unit,
        'description': description,
        'formatted': f"${value:.2f}" if unit == 'USD' and value is not None else
                     f"{value:.2f}%" if unit == 'percent' and value is not None else
                     f"{value:.2f}" if value is not None else "N/A"
    }


class FinalRecommendation(BaseModel):
    """Structured final recommendation"""
    executive_summary: str = Field(description="High-level investment summary")
    action: str = Field(description="STRONG_BUY, BUY, HOLD, SELL, or STRONG_SELL")
    confidence: float = Field(description="Overall confidence 0-1")
    rationale: str = Field(description="Key reasoning for recommendation")
    target_price: Optional[float] = Field(default=None, description="12-month price target")
    stop_loss: Optional[float] = Field(default=None, description="Recommended stop loss")
    time_horizon: str = Field(description="short_term, medium_term, or long_term")
    risk_reward_ratio: Optional[float] = Field(default=None, description="Risk/reward ratio")
    key_catalysts: List[str] = Field(description="Potential price catalysts")
    risks: List[str] = Field(description="Key risks to watch")


class ExpertSynthesisAgent(LineageMixin):
    """
    Synthesizes all expert agent analyses into final recommendation
    """

    def __init__(self, llm: ChatOpenAI):
        self.name = "ExpertSynthesisAgent"
        self.llm = llm
        self.output_parser = PydanticOutputParser(pydantic_object=FinalRecommendation)
        self.position_sizer = PositionSizer()
        self.order_builder = OrderBuilder()
        self.data_quality_validator = DataQualityValidator()
        self.synthesis_validator = SynthesisValidator()  # Guardrails & sanity checks
        self.consensus_engine = ConsensusRecommendationEngine()  # Multi-agent consensus
        self.init_lineage_tracking()  # Initialize lineage tracking

        # Weighting for different analyses
        self.weights = {
            'fundamental': 0.35,
            'technical': 0.25,
            'risk': 0.20,
            'sentiment': 0.15,
            'market': 0.05
        }

    async def synthesize(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine all agent analyses into final recommendation

        Args:
            analyses: {
                'fundamental': Dict,
                'technical': Dict,
                'risk': Dict,
                'sentiment': Dict,
                'market': Dict,
                'news': Dict,  # News intelligence
                'macro': Dict,  # Macro context
                'peer_comparison': Dict,
                'insider_activity': Dict
            }
        """
        logger.info(f"[{self.name}] Synthesizing {len(analyses)} agent analyses")

        symbol = analyses.get('fundamental', {}).get('symbol', 'UNKNOWN')
        price = analyses.get('market', {}).get('price', 0)

        try:
            # Step 0: Validate data quality
            data_quality = self._validate_data_quality(analyses)

            # Step 1: Calculate consensus scores (legacy weighted)
            consensus = self._calculate_consensus(analyses)

            # Step 1.5: Calculate multi-agent consensus (NEW - uses ConsensusEngine)
            agent_recommendations = self._prepare_agent_recommendations(analyses)
            multi_agent_consensus = self.consensus_engine.calculate_consensus(
                agent_recommendations, symbol
            )
            logger.info(
                f"[{self.name}] Multi-agent consensus: {multi_agent_consensus['consensus_recommendation']} "
                f"({multi_agent_consensus['consensus_strength']:.1f}% strength, "
                f"{multi_agent_consensus['agent_agreement']:.1f}% agreement)"
            )

            # Step 2: Use GPT-4 to synthesize final recommendation (with consensus input)
            recommendation = await self._generate_final_recommendation(
                symbol, price, analyses, consensus, multi_agent_consensus
            )

            # Step 3: Calculate ATR-based stop loss (CRITICAL for risk management)
            technical_data = analyses.get('technical', {})
            atr_data = technical_data.get('indicators', {}).get('atr')
            atr = extract_numeric_value(atr_data, 'value', None) if atr_data else None

            if atr and atr > 0:
                # Use 2x ATR for stop loss (professional standard)
                atr_stop_loss = price - (atr * 2)
                logger.info(f"[{self.name}] ATR-based stop loss for {symbol}: ${atr_stop_loss:.2f} (ATR: ${atr:.2f})")
            else:
                # Fallback: use 2% below current price
                atr_stop_loss = price * 0.98
                logger.warning(f"[{self.name}] No ATR found for {symbol}, using 2% stop loss: ${atr_stop_loss:.2f}")

            # Override LLM stop_loss with ATR-based calculation
            final_stop_loss = atr_stop_loss

            # Step 4: Calculate position sizing (CRITICAL for execution)
            # Extract target price safely (may be dict or float)
            target_price_value = extract_price_value(
                recommendation.get('target_price', price),
                "target_price",
                default=price
            )

            position_sizing = self._calculate_position_sizing(
                price,
                final_stop_loss,
                target_price_value,
                analyses
            )

            # Step 5: Generate strategy with orders (uses position sizing)
            strategy = self._generate_strategy(price, analyses, recommendation, position_sizing)

            # Step 5.5: Track synthesis lineage
            self._track_synthesis_lineage(symbol, price, recommendation, consensus, analyses)

            # Step 6: Build complete synthesis
            result = {
                'agent': self.name,
                'symbol': symbol,
                'summary': recommendation.get('executive_summary', ''),
                'action': recommendation.get('action', 'HOLD'),
                'confidence': recommendation.get('confidence', 0.5),
                'rationale': recommendation.get('rationale', ''),
                'target_price': recommendation.get('target_price', price),
                'stop_loss': final_stop_loss,  # Use ATR-based stop loss
                'entry_price': price,
                'time_horizon': recommendation.get('time_horizon', 'medium_term'),
                'risk_reward_ratio': extract_numeric_value(recommendation.get('risk_reward_ratio', 1.0), 'value', 1.0),
                'key_catalysts': recommendation.get('key_catalysts', []),
                'risks': recommendation.get('risks', []),
                'consensus_breakdown': consensus,
                'multi_agent_consensus': multi_agent_consensus,  # NEW: Advanced consensus engine
                'strategy': strategy,
                'position_sizing': position_sizing,  # NEW: Position sizing guidance
                'agent_agreement': self._calculate_agent_agreement(analyses),
                'data_quality': data_quality,  # NEW: Data quality report
                'timestamp': datetime.utcnow().isoformat()
            }

            # CRITICAL: Validate synthesis for expert-level data integrity
            try:
                logger.info(f"[{self.name}] Running synthesis validation for {symbol} (price: ${price:.2f}, stop: ${result['stop_loss']:.2f})")
                validation_result = self.synthesis_validator.validate(result, price)

                if not validation_result.is_valid:
                    logger.error(f"[{self.name}] Synthesis validation FAILED for {symbol}: {validation_result.errors}")
                    # Apply corrections
                    for key, value in validation_result.corrected_values.items():
                        if key in result:
                            logger.warning(f"[{self.name}] Correcting {key}: {result[key]} -> {value}")
                            result[key] = value
                    # Add validation metadata
                    result['validation_errors'] = validation_result.errors
                    result['validation_warnings'] = validation_result.warnings
                else:
                    if validation_result.warnings:
                        logger.warning(f"[{self.name}] Synthesis warnings for {symbol}: {validation_result.warnings}")
                        result['validation_warnings'] = validation_result.warnings
                    logger.info(f"[{self.name}] Synthesis validation PASSED for {symbol}")
            except Exception as e:
                logger.error(f"[{self.name}] Synthesis validator exception for {symbol}: {e}", exc_info=True)
                result['validation_errors'] = [f"Validator error: {str(e)}"]

            logger.info(f"[{self.name}] Final recommendation: {result['action']} with {result['confidence']*100}% confidence")
            logger.info(f"[{self.name}] Data quality: {data_quality.get('overall_grade', 'N/A')} ({data_quality.get('overall_score', 0):.1f}/100) - {data_quality.get('agents_validated', 0)} agents validated")

            # Add lineage to output
            result = self.add_lineage_to_output(result)
            return result

        except Exception as e:
            logger.error(f"[{self.name}] Error in synthesis: {e}", exc_info=True)
            return self._fallback_synthesis(symbol, price)

    def _prepare_agent_recommendations(self, analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare agent recommendations for consensus engine

        Extracts recommendation, confidence, and reasoning from each agent
        """
        agent_recs = []

        # Fundamental agent
        if 'fundamental' in analyses:
            fund = analyses['fundamental']
            agent_recs.append({
                'agent_name': 'ExpertFundamentalAgent',
                'recommendation': fund.get('recommendation', 'HOLD'),
                'confidence': fund.get('confidence', 0.5) * 100 if fund.get('confidence', 0.5) <= 1 else fund.get('confidence', 50),
                'reasoning': fund.get('summary', 'Fundamental analysis')
            })

        # Technical agent
        if 'technical' in analyses:
            tech = analyses['technical']
            signal = tech.get('signal', 'HOLD').upper()
            # Convert HOLD/BUY/SELL to standard format
            if signal not in ['BUY', 'SELL', 'HOLD']:
                signal = 'HOLD'
            agent_recs.append({
                'agent_name': 'ExpertTechnicalAgent',
                'recommendation': signal,
                'confidence': tech.get('confidence', 0.5) * 100 if tech.get('confidence', 0.5) <= 1 else tech.get('confidence', 50),
                'reasoning': tech.get('summary', 'Technical analysis')
            })

        # Risk agent
        if 'risk' in analyses:
            risk = analyses['risk']
            # Convert risk level to recommendation
            risk_level = risk.get('risk_level', 'medium').upper()
            if risk_level in ['LOW']:
                risk_rec = 'BUY'
            elif risk_level in ['HIGH', 'VERY_HIGH']:
                risk_rec = 'SELL'
            else:
                risk_rec = 'HOLD'

            agent_recs.append({
                'agent_name': 'ExpertRiskAgent',
                'recommendation': risk_rec,
                'confidence': risk.get('confidence', 0.6) * 100 if risk.get('confidence', 0.6) <= 1 else risk.get('confidence', 60),
                'reasoning': f"Risk level: {risk_level}, Sharpe: {risk.get('sharpe_ratio', 'N/A')}"
            })

        # Sentiment agent
        if 'sentiment' in analyses:
            sent = analyses['sentiment']
            sentiment = sent.get('overall_sentiment', 'neutral').lower()
            if sentiment in ['bullish', 'positive']:
                sent_rec = 'BUY'
            elif sentiment in ['bearish', 'negative']:
                sent_rec = 'SELL'
            else:
                sent_rec = 'HOLD'

            agent_recs.append({
                'agent_name': 'SentimentTrackerAgent',
                'recommendation': sent_rec,
                'confidence': sent.get('confidence', 0.4) * 100 if sent.get('confidence', 0.4) <= 1 else sent.get('confidence', 40),
                'reasoning': f"Sentiment: {sentiment}, Score: {sent.get('sentiment_score', 50)}"
            })

        return agent_recs

    def _calculate_consensus(self, analyses: Dict[str, Any]) -> Dict:
        """Calculate weighted consensus from all analyses"""

        scores = []
        weights = []

        # Fundamental score
        if 'fundamental' in analyses:
            fund = analyses['fundamental']
            fund_score = self._recommendation_to_score(fund.get('recommendation', 'HOLD'))
            scores.append(fund_score * self.weights['fundamental'])
            weights.append(self.weights['fundamental'] * fund.get('confidence', 0.5))

        # Technical score
        if 'technical' in analyses:
            tech = analyses['technical']
            tech_score = self._signal_to_score(tech.get('signal', 'HOLD'))
            scores.append(tech_score * self.weights['technical'])
            weights.append(self.weights['technical'] * tech.get('confidence', 0.5))

        # Risk adjustment (inverse)
        if 'risk' in analyses:
            risk = analyses['risk']
            risk_level = risk.get('risk_level', 'medium')
            risk_score = {'low': 1.0, 'medium': 0.5, 'high': 0.0}.get(risk_level, 0.5)
            scores.append(risk_score * self.weights['risk'])
            weights.append(self.weights['risk'] * risk.get('confidence', 0.6))

        # Sentiment score (social media sentiment)
        if 'sentiment' in analyses:
            sent = analyses['sentiment']
            sent_score = self._sentiment_to_score(sent.get('overall_sentiment', 'neutral'))
            scores.append(sent_score * self.weights['sentiment'])
            weights.append(self.weights['sentiment'] * sent.get('confidence', 0.4))

        # CRITICAL FIX: Integrate news sentiment into consensus (was missing!)
        if 'news' in analyses:
            news = analyses['news']
            news_sentiment_data = news.get('sentiment', {})
            if news_sentiment_data:
                # Convert news sentiment score (-1 to 1) to consensus score (0 to 1)
                news_score = (news_sentiment_data.get('score', 0) + 1) / 2  # Map -1..1 to 0..1
                # Weight news sentiment heavily (news is more reliable than social media)
                news_weight = 0.25  # 25% weight for news sentiment
                scores.append(news_score * news_weight)
                weights.append(news_weight * news_sentiment_data.get('confidence', 0.6))
                logger.info(f"[{self.name}] News sentiment integrated: score={news_score:.2f}, confidence={news_sentiment_data.get('confidence', 0.6):.2f}")

        # Calculate weighted average
        total_weight = sum(weights) if weights else 1
        weighted_score = sum(scores) / total_weight if total_weight > 0 else 0.5

        return {
            'weighted_score': round(weighted_score, 2),
            'total_confidence': round(sum(weights), 2),
            'bullish_indicators': sum(1 for s in scores if s > 0.6),
            'bearish_indicators': sum(1 for s in scores if s < 0.4),
            'neutral_indicators': sum(1 for s in scores if 0.4 <= s <= 0.6)
        }

    def _recommendation_to_score(self, rec: str) -> float:
        """Convert recommendation to numeric score 0-1"""
        mapping = {
            'STRONG_BUY': 1.0,
            'BUY': 0.75,
            'HOLD': 0.5,
            'SELL': 0.25,
            'STRONG_SELL': 0.0
        }
        return mapping.get(rec, 0.5)

    def _signal_to_score(self, signal: str) -> float:
        """Convert signal to numeric score 0-1"""
        mapping = {
            'BUY': 0.8,
            'HOLD': 0.5,
            'SELL': 0.2,
            'neutral': 0.5
        }
        return mapping.get(signal, 0.5)

    def _sentiment_to_score(self, sentiment: str) -> float:
        """Convert sentiment to numeric score 0-1"""
        mapping = {
            'bullish': 0.8,
            'positive': 0.7,
            'neutral': 0.5,
            'negative': 0.3,
            'bearish': 0.2
        }
        return mapping.get(sentiment.lower(), 0.5)

    async def _generate_final_recommendation(self,
                                            symbol: str,
                                            price: float,
                                            analyses: Dict,
                                            consensus: Dict,
                                            multi_agent_consensus: Dict = None) -> Dict:
        """Use GPT-4 to synthesize final recommendation"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior portfolio manager synthesizing research from expert analysts.
Combine fundamental, technical, risk, sentiment, news, and macro analyses into a clear investment recommendation.

EXECUTIVE SUMMARY REQUIREMENTS:
- Start with recent news context and market events (from news analysis)
- Mention specific news sources, analyst ratings changes, or major events
- Include macro economic context (Fed policy, sector trends)
- Reference key financial metrics (P/E, growth rate, profit margins)
- State clear recommendation with confidence level
- Cite specific data points and sources

CRITICAL RISK/REWARD VALIDATION RULES:
1. **Sharpe Ratio < 0.5 + HIGH/VERY_HIGH risk = DO NOT recommend BUY**
   - Even with strong fundamentals, downgrade to HOLD or SELL
   - Explicitly state: "Strong signals but unfavorable risk/reward (Sharpe {{value}})"
2. **Risk/Reward Ratio < 1.0 = DO NOT recommend BUY**
   - Target upside must exceed downside risk
3. **ATR-Based Stop Loss Required**:
   - Calculate stop_loss as: entry_price - (ATR * 2) for long positions
   - Use ATR * 2 as standard volatility-adjusted stop distance
   - NEVER use VaR or dollar amounts as stop_loss (stop_loss must be a PRICE)
   - For shorts: entry_price + (ATR * 2)
4. **Logical Consistency Required**:
   - If risk_level is HIGH and max_drawdown > 30%, be extremely cautious
   - If multiple bearish indicators (RSI overbought, high P/E, negative momentum), do not contradict with BUY
5. **Confidence Adjustment**:
   - High risk + bullish signals = Lower confidence (max 60%)
   - Strong risk-adjusted returns + bullish signals = Higher confidence (70-90%)

Consider:
1. Multi-factor agreement/disagreement
2. Risk-adjusted return potential (ALWAYS check Sharpe ratio)
3. Time horizon appropriateness
4. Catalyst identification (news events, earnings, product launches)
5. Risk management (OVERRIDE bullish signals if risk metrics are unfavorable)

Provide decisive, actionable recommendations that NEVER contradict risk metrics."""),
            ("human", """Synthesize analysis for {symbol} at ${price}:

FUNDAMENTAL ANALYSIS:
- Recommendation: {fund_rec}
- Confidence: {fund_conf}%
- Key Metrics: P/E {pe}, ROE {roe}%
- Analyst Target: ${target}

TECHNICAL ANALYSIS:
- Signal: {tech_signal}
- Confidence: {tech_conf}%
- Trend: {trend}
- RSI: {rsi}
- ATR (14-day): ${atr}

RISK ASSESSMENT:
- Risk Level: {risk_level}
- Sharpe Ratio: {sharpe}
- Max Drawdown: {max_dd}%
- VaR (95%): ${var}

SENTIMENT:
- Social Media Sentiment: {sentiment} ({sent_score}/100)
- News Sentiment: {news_sentiment} ({news_sent_score}/100)

NEWS INTELLIGENCE:
- Recent Events: {news_events}
- Analyst Actions: {analyst_actions}
- Key Catalysts: {news_catalysts}
- Risks from News: {news_risks}

MACRO CONTEXT:
- Market Regime: {macro_regime}
- Fed Policy: {fed_policy}
- Sector Trend: {sector_trend}
- Economic Indicators: {economic_indicators}

CONSENSUS:
- Weighted Score: {consensus_score}
- Bullish Indicators: {bullish_count}
- Bearish Indicators: {bearish_count}

MULTI-AGENT CONSENSUS (NEW):
- Final Recommendation: {mac_rec}
- Consensus Strength: {mac_strength}%
- Agent Agreement: {mac_agreement}%
- Dissenting Agents: {mac_dissent}

{format_instructions}

IMPORTANT: Create executive_summary that:
1. Starts with recent news context and specific events
2. Cites analyst rating changes or news sources
3. Mentions macro environment (Fed policy, sector trends)
4. References key fundamental metrics
5. States clear directional view with confidence
6. Example: "Following recent analyst downgrades citing AI monetization concerns (Seeking Alpha, Sept 29), AAPL faces headwinds despite strong fundamentals (P/E 39.2, ROE 4.3%). The Fed's neutral policy stance and sector rotation provide mixed signals. Technical indicators show overbought conditions (RSI 71.05). Recommend HOLD with 60% confidence pending clarity on tariff policies and AI revenue trajectory."

Provide your final investment recommendation.""")
        ])

        try:
            fund = analyses.get('fundamental', {})
            tech = analyses.get('technical', {})
            risk = analyses.get('risk', {})
            sent = analyses.get('sentiment', {})
            news = analyses.get('news', {})
            macro = analyses.get('macro', {})

            # Extract news context
            news_events = ', '.join(news.get('key_events', [])) if news.get('key_events') else 'No recent events'
            analyst_actions = ', '.join(news.get('analyst_actions', [])) if news.get('analyst_actions') else 'No analyst actions'
            news_catalysts = ', '.join(news.get('catalysts', [])) if news.get('catalysts') else 'No catalysts identified'
            news_risks = ', '.join(news.get('risks', [])) if news.get('risks') else 'No risks identified'

            # Extract macro context
            macro_data = macro.get('market_regime', {})
            macro_regime = macro_data.get('regime', 'neutral') if isinstance(macro_data, dict) else 'neutral'
            fed_policy = macro_data.get('fed_policy', 'neutral') if isinstance(macro_data, dict) else 'neutral'

            sector_data = macro.get('sector_analysis', {})
            sector_trend = sector_data.get('trend', 'neutral') if isinstance(sector_data, dict) else 'neutral'

            economic_indicators = ', '.join(macro.get('economic_indicators', [])) if macro.get('economic_indicators') else 'None'

            # Extract multi-agent consensus data
            mac_rec = 'N/A'
            mac_strength = 0
            mac_agreement = 0
            mac_dissent = 'None'

            if multi_agent_consensus:
                mac_rec = multi_agent_consensus.get('consensus_recommendation', 'N/A')
                mac_strength = multi_agent_consensus.get('consensus_strength', 0)
                mac_agreement = multi_agent_consensus.get('agent_agreement', 0)
                dissenting = multi_agent_consensus.get('dissenting_agents', [])
                if dissenting:
                    mac_dissent = ', '.join([f"{d['agent']}: {d['recommendation']}" for d in dissenting[:3]])
                else:
                    mac_dissent = 'None'

            formatted_prompt = prompt.format_messages(
                symbol=symbol,
                price=price,
                fund_rec=fund.get('recommendation', 'N/A'),
                fund_conf=round(fund.get('confidence', 0.5) * 100),
                pe=fund.get('pe_ratio', 'N/A'),
                roe=fund.get('roe', 'N/A'),
                target=fund.get('analyst_target_price', price),
                tech_signal=tech.get('signal', 'N/A'),
                tech_conf=round(tech.get('confidence', 0.5) * 100),
                trend=tech.get('trend', 'neutral'),
                rsi=tech.get('rsi', {}).get('value', 'N/A') if isinstance(tech.get('rsi'), dict) else str(tech.get('rsi', 'N/A')),
                atr=tech.get('atr', 'N/A'),
                risk_level=risk.get('risk_level', 'medium').upper(),
                sharpe=risk.get('sharpe_ratio', 'N/A'),
                max_dd=risk.get('max_drawdown', 'N/A'),
                var=risk.get('var_95', 'N/A'),
                sentiment=sent.get('overall_sentiment', 'neutral'),
                sent_score=sent.get('sentiment_score', 50),
                news_sentiment=news.get('sentiment', {}).get('overall', 'neutral'),
                news_sent_score=round((news.get('sentiment', {}).get('score', 0) + 1) * 50),  # Map -1..1 to 0..100
                news_events=news_events,
                analyst_actions=analyst_actions,
                news_catalysts=news_catalysts,
                news_risks=news_risks,
                macro_regime=macro_regime,
                fed_policy=fed_policy,
                sector_trend=sector_trend,
                economic_indicators=economic_indicators,
                consensus_score=consensus.get('weighted_score', 0.5),
                bullish_count=consensus.get('bullish_indicators', 0),
                bearish_count=consensus.get('bearish_indicators', 0),
                mac_rec=mac_rec,
                mac_strength=mac_strength,
                mac_agreement=mac_agreement,
                mac_dissent=mac_dissent,
                format_instructions=self.output_parser.get_format_instructions()
            )

            response = await self.llm.ainvoke(formatted_prompt)
            parsed = self.output_parser.parse(response.content)

            return {
                'executive_summary': parsed.executive_summary,
                'action': parsed.action,
                'confidence': parsed.confidence,
                'rationale': parsed.rationale,
                'target_price': add_unit_metadata(parsed.target_price, 'USD', '12-month price target'),
                'stop_loss': add_unit_metadata(parsed.stop_loss, 'USD', 'Risk management stop-loss price'),
                'entry_price': add_unit_metadata(price, 'USD', 'Current market price for entry'),
                'time_horizon': parsed.time_horizon,
                'risk_reward_ratio': add_unit_metadata(parsed.risk_reward_ratio, 'ratio', 'Potential reward / risk ratio'),
                'key_catalysts': parsed.key_catalysts,
                'risks': parsed.risks
            }

        except Exception as e:
            logger.error(f"[{self.name}] LLM synthesis failed: {e}", exc_info=True)
            tech = analyses.get('technical', {})
            logger.error(f"[{self.name}] Technical data: rsi={tech.get('rsi')}, type={type(tech.get('rsi'))}")
            return self._rule_based_synthesis(price, consensus, analyses)

    def _rule_based_synthesis(self, price: float, consensus: Dict, analyses: Dict = None) -> Dict:
        """Fallback rule-based synthesis with risk-adjusted recommendations"""

        score = consensus.get('weighted_score', 0.5)

        # Extract risk metrics for risk-adjusted decisions
        risk_data = analyses.get('risk', {}) if analyses else {}
        sharpe_ratio = risk_data.get('sharpe_ratio', 0.5)
        risk_level = risk_data.get('risk_level', 'medium').upper()

        # Extract ATR from technical analysis for stop-loss calculation
        tech_data = analyses.get('technical', {}) if analyses else {}

        # ATR can be a dict with 'value' key or a direct number
        atr_raw = tech_data.get('atr')
        if isinstance(atr_raw, dict):
            atr = atr_raw.get('value', price * 0.02)
        elif isinstance(atr_raw, (int, float)):
            atr = atr_raw
        else:
            atr = price * 0.02  # Fallback to 2% of price if ATR not available

        # Ensure ATR is numeric
        if not isinstance(atr, (int, float)):
            atr = price * 0.02

        # ATR multiplier for stop-loss (2x ATR is standard for aggressive, 1.5x for conservative)
        atr_multiplier = 2.0

        # CRITICAL FIX: Risk-reward validation
        # A Sharpe ratio < 0.5 indicates poor risk-adjusted returns
        # Should not recommend BUY regardless of other signals

        if score > 0.7:
            # Check if risk metrics support bullish view
            if sharpe_ratio < 0.5 and risk_level in ['HIGH', 'VERY_HIGH']:
                # DOWNGRADE: Strong signals but poor risk/reward
                action = 'HOLD'
                target = price * 1.05
                stop = price - (atr * atr_multiplier)  # ATR-based stop (2x ATR)
                rationale = f'Strong fundamentals/technicals (score {score:.2f}) but unfavorable risk/reward (Sharpe {sharpe_ratio:.2f}, {risk_level} risk). Downgraded to HOLD pending risk improvement.'
            else:
                action = 'BUY'
                target = price * 1.15
                stop = price - (atr * atr_multiplier)  # ATR-based stop (2x ATR)
                rationale = f'Multi-factor bullish consensus (score {score:.2f}) with acceptable risk profile (Sharpe {sharpe_ratio:.2f}).'
        elif score > 0.55:
            action = 'HOLD'
            target = price * 1.05
            stop = price - (atr * 1.5 * atr_multiplier)  # More conservative stop for HOLD (3x ATR)
            rationale = f'Neutral consensus (score {score:.2f}). Monitor for clearer signals.'
        elif score < 0.3:
            # Enhanced SELL logic with risk confirmation
            if risk_level in ['HIGH', 'VERY_HIGH']:
                action = 'STRONG_SELL'
                target = price * 0.80
                stop = min(price + (atr * atr_multiplier), price * 1.03)  # ATR-based stop for shorts
                rationale = f'Bearish signals (score {score:.2f}) confirmed by {risk_level} risk level. Strong sell recommended.'
            else:
                action = 'SELL'
                target = price * 0.85
                stop = min(price + (atr * atr_multiplier), price * 1.05)  # ATR-based stop for shorts
                rationale = f'Bearish consensus (score {score:.2f}). Consider reducing exposure.'
        else:
            action = 'HOLD'
            target = price
            stop = price - (atr * atr_multiplier)  # ATR-based stop (2x ATR)
            rationale = f'Mixed signals (score {score:.2f}). Await clearer trend.'

        rr_ratio = abs(target - price) / abs(price - stop) if stop != price else 1.0

        # Final validation: Ensure risk/reward ratio is reasonable
        if rr_ratio < 1.0 and action in ['BUY', 'STRONG_BUY']:
            action = 'HOLD'
            rationale += ' Risk/reward ratio below 1.0 - downgraded to HOLD.'

        return {
            'executive_summary': f'Consensus analysis: {action} | Score: {score*100:.0f}% | Sharpe: {sharpe_ratio:.2f} | Risk: {risk_level} | R/R: {rr_ratio:.2f}',
            'action': action,
            'confidence': min(consensus.get('total_confidence', 0.5), 1.0),
            'rationale': rationale,
            'target_price': add_unit_metadata(target, 'USD', '12-month price target'),
            'stop_loss': add_unit_metadata(stop, 'USD', 'Risk management stop-loss price'),
            'entry_price': add_unit_metadata(price, 'USD', 'Current market price for entry'),
            'time_horizon': 'medium_term',
            'risk_reward_ratio': add_unit_metadata(rr_ratio, 'ratio', 'Potential reward / risk ratio'),
            'key_catalysts': ['Market conditions', 'Earnings reports', 'Risk regime change'],
            'risks': ['Market volatility', 'Sector rotation', 'Poor risk-adjusted returns'] if sharpe_ratio < 0.5 else ['Market volatility', 'Sector rotation']
        }

    def _generate_strategy(self, price: float, analyses: Dict, recommendation: Dict, position_sizing: Dict) -> Dict[str, Any]:
        """
        Generate comprehensive trading strategy with conditional orders

        CRITICAL: Provides complete execution framework for traders
        """

        action = recommendation.get('action', 'HOLD')
        target = recommendation.get('target_price', price)
        stop = recommendation.get('stop_loss', price * 0.9)
        symbol = analyses.get('fundamental', {}).get('symbol', 'UNKNOWN')

        # Get position sizing for order quantity
        recommended_size = position_sizing.get('recommended', {})
        quantity = recommended_size.get('shares', 100)

        strategy = {
            'action': action,
            'symbol': symbol,
            'entry_price': price,
            'target_price': target,
            'stop_loss': stop,
            'orders': [],
            'execution_plan': '',
            'risk_management': {}
        }

        if action in ['BUY', 'STRONG_BUY']:
            try:
                # Build bracket order (entry + profit + stop)
                bracket_order = self.order_builder.build_bracket_order(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    entry_price=price,
                    profit_target=target,
                    stop_loss=stop,
                    trailing_stop_pct=None  # Can add trailing stop if desired
                )

                strategy['orders'].append(bracket_order)
                strategy['execution_plan'] = bracket_order.get('instructions', '')

                # Add scaling strategy if R/R is good
                rr_ratio = recommendation.get('risk_reward_ratio', 0)
                if rr_ratio >= 2.0:
                    # Scale in at better prices
                    scale_levels = [
                        price,  # Initial entry
                        price * 0.985,  # 1.5% lower
                        price * 0.97    # 3% lower
                    ]

                    scaling_order = self.order_builder.build_scaling_strategy(
                        symbol=symbol,
                        side=OrderSide.BUY,
                        total_quantity=quantity,
                        entry_price=price,
                        scale_levels=[
                            {'price': scale_levels[0], 'pct': 0.4},
                            {'price': scale_levels[1], 'pct': 0.3},
                            {'price': scale_levels[2], 'pct': 0.3}
                        ],
                        profit_target=target,
                        stop_loss=stop
                    )

                    strategy['orders'].append(scaling_order)
                    strategy['execution_plan'] += f"\n\nSCALING STRATEGY:\n{scaling_order.get('instructions', '')}"

                # Risk management rules
                strategy['risk_management'] = {
                    'max_loss': round(abs(price - stop) * quantity, 2),
                    'max_gain': round(abs(target - price) * quantity, 2),
                    'risk_reward_ratio': rr_ratio,
                    'stop_adjustment_rules': [
                        f"If price reaches ${price * 1.05:.2f} (+5%), move stop to break-even (${price:.2f})",
                        f"If price reaches ${price * 1.10:.2f} (+10%), trail stop 5% below price",
                        f"On earnings announcement, consider tightening stop to ${price * 0.97:.2f} (-3%)"
                    ],
                    'exit_triggers': [
                        f"Take profit at ${target:.2f} (primary target)",
                        f"Stop loss at ${stop:.2f} (risk management)",
                        f"Exit if RSI > 80 (extreme overbought)",
                        f"Exit if volume drops 70% below average (liquidity concern)"
                    ]
                }

            except Exception as e:
                logger.error(f"[{self.name}] Order building failed: {e}")
                strategy['execution_plan'] = f"Manual execution required: {action} {quantity} shares at ${price:.2f}"

        elif action in ['SELL', 'STRONG_SELL']:
            # For SELL recommendations (short or exit long)
            strategy['execution_plan'] = f"""
SELL STRATEGY FOR {symbol}:

1. EXIT EXISTING LONG POSITION (if held):
   - Sell at market or limit ${price:.2f}
   - Expected proceeds: ${price * quantity:,.2f}

2. CONSIDER SHORT POSITION (advanced traders only):
   - Short entry: ${price:.2f}
   - Cover target: ${target:.2f}
   - Stop loss: ${stop:.2f}
   - Risk: ${abs(price - stop) * quantity:,.2f}

3. RISK MANAGEMENT:
   - Use tight stops for short positions
   - Monitor short squeeze risk
   - Check borrow availability
            """.strip()

        else:  # HOLD
            strategy['execution_plan'] = f"""
HOLD STRATEGY FOR {symbol}:

1. NO ACTION REQUIRED
   - Current recommendation: HOLD
   - Monitor for entry opportunity

2. WATCH LEVELS:
   - Consider buying below ${price * 0.95:.2f} (-5%)
   - Consider selling above ${price * 1.05:.2f} (+5%)

3. WAIT FOR:
   - Clearer technical signals
   - Earnings catalyst
   - Risk/reward improvement
            """.strip()

        return strategy

    def _calculate_agent_agreement(self, analyses: Dict) -> str:
        """Calculate how many agents agree on direction"""

        bullish_count = 0
        bearish_count = 0
        total = 0

        for key, analysis in analyses.items():
            if key == 'fundamental':
                rec = analysis.get('recommendation', 'HOLD')
                if 'BUY' in rec:
                    bullish_count += 1
                elif 'SELL' in rec:
                    bearish_count += 1
                total += 1

            elif key == 'technical':
                signal = analysis.get('signal', 'HOLD')
                if signal == 'BUY':
                    bullish_count += 1
                elif signal == 'SELL':
                    bearish_count += 1
                total += 1

            elif key == 'sentiment':
                sent = analysis.get('overall_sentiment', 'neutral').lower()
                if sent in ['bullish', 'positive']:
                    bullish_count += 1
                elif sent in ['bearish', 'negative']:
                    bearish_count += 1
                total += 1

        if bullish_count > bearish_count:
            return f"{bullish_count}/{total} agents bullish"
        elif bearish_count > bullish_count:
            return f"{bearish_count}/{total} agents bearish"
        else:
            return f"{total} agents neutral/mixed"

    def _calculate_position_sizing(
        self,
        entry_price: float,
        stop_loss: float,
        target_price: float,
        analyses: Dict[str, Any],
        account_value: float = 100000  # Default $100k account
    ) -> Dict[str, Any]:
        """
        Calculate position sizing scenarios for the recommendation

        CRITICAL: Tells traders HOW MANY shares to buy, not just BUY/SELL
        """

        # Extract volatility from technical analysis
        tech_data = analyses.get('technical', {})
        volatility = tech_data.get('volatility', 0.20)  # Default 20%

        # Extract risk metrics
        risk_data = analyses.get('risk', {})
        win_rate = risk_data.get('win_rate', 0.50)  # Default 50%

        try:
            # Calculate multiple position sizing scenarios
            scenarios = self.position_sizer.calculate_multiple_scenarios(
                account_value=account_value,
                entry_price=entry_price,
                stop_loss_price=stop_loss,
                target_price=target_price,
                volatility=volatility,
                win_rate=win_rate
            )

            return {
                'account_value': account_value,
                'conservative': scenarios['conservative'],  # 1% risk
                'moderate': scenarios['moderate'],          # 2% risk
                'aggressive': scenarios['aggressive'],       # Kelly criterion
                'volatility_adjusted': scenarios['volatility_adjusted'],
                'recommended': scenarios['recommended'],     # Best choice
                'risk_reward_ratio': scenarios['risk_reward_ratio'],
                'guidance': self._get_position_sizing_guidance(scenarios)
            }

        except Exception as e:
            logger.error(f"[{self.name}] Position sizing failed: {e}")
            return {
                'error': str(e),
                'guidance': 'Position sizing unavailable. Consult with financial advisor.'
            }

    def _get_position_sizing_guidance(self, scenarios: Dict) -> str:
        """Generate human-readable position sizing guidance"""

        recommended = scenarios.get('recommended', {})
        rr_ratio = scenarios.get('risk_reward_ratio', 0)

        shares = recommended.get('shares', 0)
        position_value = recommended.get('position_value', 0)
        capital_at_risk = recommended.get('capital_at_risk', 0)
        position_pct = recommended.get('position_pct', 0)

        if shares == 0:
            return "Position size too small for this account. Consider larger capital or better entry/stop."

        guidance = f"Recommended: {shares} shares (${position_value:,.0f} position, {position_pct:.1f}% of account). "
        guidance += f"Capital at risk: ${capital_at_risk:,.0f}. "

        if rr_ratio >= 3.0:
            guidance += f"Excellent risk/reward ({rr_ratio:.1f}:1) supports moderate position sizing."
        elif rr_ratio >= 2.0:
            guidance += f"Good risk/reward ({rr_ratio:.1f}:1) - conservative sizing recommended."
        elif rr_ratio >= 1.5:
            guidance += f"Acceptable risk/reward ({rr_ratio:.1f}:1) - use conservative sizing."
        else:
            guidance += f"Poor risk/reward ({rr_ratio:.1f}:1) - consider reducing position or avoiding trade."

        return guidance

    def _fallback_synthesis(self, symbol: str, price: float) -> Dict:
        """Fallback synthesis if everything fails"""

        return {
            'agent': self.name,
            'symbol': symbol,
            'summary': 'Analysis synthesis unavailable',
            'action': 'HOLD',
            'confidence': 0.3,
            'target_price': add_unit_metadata(price, 'USD', '12-month price target (fallback)'),
            'stop_loss': add_unit_metadata(price * 0.9, 'USD', 'Risk management stop-loss price (fallback)'),
            'entry_price': add_unit_metadata(price, 'USD', 'Current market price for entry'),
            'time_horizon': 'medium_term',
            'consensus_breakdown': {},
            'strategy': [],
            'data_source': 'fallback',
            'timestamp': datetime.utcnow().isoformat()
        }

    def _validate_data_quality(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data quality across all agent outputs

        Args:
            analyses: All agent analyses

        Returns:
            Data quality report with scores and issues
        """
        logger.info(f"[{self.name}] Validating data quality across {len(analyses)} agents")

        quality_reports = {}
        overall_issues = []
        overall_warnings = []

        # Validate each agent's data
        for agent_name, agent_data in analyses.items():
            if not agent_data or isinstance(agent_data, str):
                continue

            # Add source metadata
            if 'source' not in agent_data:
                agent_data['source'] = 'internal_calculation'
            if 'timestamp' not in agent_data:
                agent_data['timestamp'] = datetime.utcnow().isoformat()

            # Validate based on agent type
            data_type = 'general'
            expected_freshness = 'daily'

            if agent_name == 'market':
                data_type = 'price'
                expected_freshness = 'intraday'
            elif agent_name == 'fundamental':
                data_type = 'fundamental'
                expected_freshness = 'weekly'
            elif agent_name == 'news':
                data_type = 'news'
                expected_freshness = 'intraday'
            elif agent_name == 'technical':
                data_type = 'technical'
                expected_freshness = 'daily'

            # Run validation
            report = self.data_quality_validator.validate_data_quality(
                data=agent_data,
                data_type=data_type,
                expected_freshness=expected_freshness
            )

            quality_reports[agent_name] = {
                'score': report.overall_score,
                'grade': report.quality_grade,
                'freshness': report.freshness_score,
                'reliability': report.reliability_score,
                'completeness': report.completeness_score,
                'anomaly_score': report.anomaly_score
            }

            # Collect issues
            if report.issues:
                overall_issues.extend([f"{agent_name}: {issue}" for issue in report.issues])
            if report.warnings:
                overall_warnings.extend([f"{agent_name}: {warning}" for warning in report.warnings])

        # Calculate aggregate quality score
        if quality_reports:
            avg_score = sum(r['score'] for r in quality_reports.values()) / len(quality_reports)
            avg_grade = self._calculate_quality_grade(avg_score)

            # Count by grade
            grade_counts = {}
            for report in quality_reports.values():
                grade = report['grade']
                grade_counts[grade] = grade_counts.get(grade, 0) + 1

        else:
            avg_score = 50
            avg_grade = 'C'
            grade_counts = {}

        logger.info(
            f"[{self.name}] Data quality: {avg_grade} ({avg_score:.1f}/100), "
            f"{len(overall_issues)} issues, {len(overall_warnings)} warnings"
        )

        return {
            'overall_score': avg_score,
            'overall_grade': avg_grade,
            'agent_reports': quality_reports,
            'grade_distribution': grade_counts,
            'issues': overall_issues[:10],  # Top 10 issues
            'warnings': overall_warnings[:10],  # Top 10 warnings
            'agents_validated': len(quality_reports),
            'validation_timestamp': datetime.utcnow().isoformat()
        }

    def _calculate_quality_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _track_synthesis_lineage(self, symbol: str, price: float, recommendation: Dict, consensus: Dict, analyses: Dict):
        """Track data lineage for synthesis recommendations"""

        # Track final recommendation (LLM-generated synthesis)
        action = recommendation.get('action', 'HOLD')
        self.track_llm_output(
            field_name='final_recommendation',
            value=action,
            model='gpt-4',
            prompt_context='Multi-agent portfolio manager synthesis',
            confidence=recommendation.get('confidence', 0.5),
            sources_cited=[
                'fundamental_analysis',
                'technical_analysis',
                'risk_assessment',
                'sentiment_analysis',
                'news_intelligence'
            ]
        )

        # Track target price
        target_price = recommendation.get('target_price')
        if target_price and isinstance(target_price, dict):
            target_price_value = target_price.get('value')
        else:
            target_price_value = target_price

        if target_price_value:
            self.track_calculated(
                field_name='target_price',
                value=target_price_value,
                formula='Weighted synthesis of fundamental DCF, technical patterns, and risk-adjusted expectations',
                input_fields=['dcf_intrinsic_value', 'technical_targets', 'analyst_consensus'],
                confidence=recommendation.get('confidence', 0.5)
            )

        # Track stop loss
        stop_loss = recommendation.get('stop_loss')
        if stop_loss and isinstance(stop_loss, dict):
            stop_loss_value = stop_loss.get('value')
        else:
            stop_loss_value = stop_loss

        if stop_loss_value:
            self.track_calculated(
                field_name='stop_loss',
                value=stop_loss_value,
                formula='ATR-based stop loss: Entry Price - (2 × ATR)',
                input_fields=['price', 'atr'],
                confidence=0.95
            )

        # Track consensus score
        consensus_score = consensus.get('weighted_score', 0.5)
        self.track_calculated(
            field_name='consensus_score',
            value=consensus_score,
            formula='Weighted average: Fundamental(35%) + Technical(25%) + Risk(20%) + Sentiment(15%) + Market(5%)',
            input_fields=[
                'fundamental_recommendation',
                'technical_signal',
                'risk_level',
                'sentiment_score',
                'market_conditions'
            ],
            confidence=0.88
        )

        # Track risk/reward ratio
        rr_ratio = recommendation.get('risk_reward_ratio')
        if rr_ratio and isinstance(rr_ratio, dict):
            rr_ratio_value = rr_ratio.get('value')
        else:
            rr_ratio_value = rr_ratio

        if rr_ratio_value:
            self.track_calculated(
                field_name='risk_reward_ratio',
                value=rr_ratio_value,
                formula='(Target Price - Entry Price) / (Entry Price - Stop Loss)',
                input_fields=['target_price', 'entry_price', 'stop_loss'],
                confidence=0.90
            )

        # Track agent agreement
        bullish_count = consensus.get('bullish_indicators', 0)
        bearish_count = consensus.get('bearish_indicators', 0)
        total_agents = bullish_count + bearish_count + consensus.get('neutral_indicators', 0)

        if total_agents > 0:
            agreement_pct = max(bullish_count, bearish_count) / total_agents
            self.track_data(
                field_name='agent_agreement',
                value=agreement_pct,
                source=DataSource.INTERNAL,
                reliability=DataReliability.HIGH,
                confidence=0.85,
                citation=f"{bullish_count} bullish, {bearish_count} bearish out of {total_agents} agents"
            )

        # Track data quality from all agents
        fundamental_lineage = analyses.get('fundamental', {}).get('lineage', {})
        technical_lineage = analyses.get('technical', {}).get('lineage', {})
        risk_lineage = analyses.get('risk', {}).get('lineage', {})

        if fundamental_lineage or technical_lineage or risk_lineage:
            self.track_data(
                field_name='upstream_data_quality',
                value={
                    'fundamental_quality': fundamental_lineage.get('data_quality', {}).get('overall_score', 0),
                    'technical_quality': technical_lineage.get('data_quality', {}).get('overall_score', 0),
                    'risk_quality': risk_lineage.get('data_quality', {}).get('overall_score', 0)
                },
                source=DataSource.INTERNAL,
                reliability=DataReliability.HIGH,
                confidence=0.92,
                citation='Aggregated data quality from upstream expert agents'
            )

        logger.info(f"[{self.name}] Tracked lineage for {len(self.lineage_tracker.records)} synthesis data points")
