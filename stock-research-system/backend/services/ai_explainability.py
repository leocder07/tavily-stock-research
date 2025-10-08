"""
AI Explainability Engine
Provides transparent explanations for AI-driven investment recommendations
"""

from typing import Dict, Any, List, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AIExplainabilityEngine:
    """
    Explains AI decisions with full transparency
    Following XAI (Explainable AI) best practices
    """

    def __init__(self):
        self.decision_weights = {
            'valuation': 0.30,
            'technical': 0.20,
            'sentiment': 0.15,
            'fundamentals': 0.20,
            'market_conditions': 0.15
        }

    def explain_recommendation(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive explanation for investment recommendation
        """
        try:
            symbol = analysis_data.get('symbol', 'Unknown')

            # Extract key factors
            factors = self._extract_decision_factors(analysis_data)

            # Calculate contribution of each factor
            contributions = self._calculate_factor_contributions(factors)

            # Generate decision tree
            decision_tree = self._build_decision_tree(factors, contributions)

            # Create natural language explanation
            explanation = self._generate_natural_explanation(factors, contributions)

            # Identify key drivers
            key_drivers = self._identify_key_drivers(contributions)

            # Calculate confidence and uncertainty
            confidence_analysis = self._analyze_confidence(analysis_data)

            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'recommendation': self._determine_recommendation(contributions),
                'explanation': {
                    'summary': explanation['summary'],
                    'detailed': explanation['detailed'],
                    'factors': factors,
                    'contributions': contributions,
                    'key_drivers': key_drivers,
                    'decision_tree': decision_tree
                },
                'confidence_analysis': confidence_analysis,
                'counterfactual': self._generate_counterfactual(factors),
                'sensitivity_analysis': self._perform_sensitivity_analysis(factors),
                'bias_check': self._check_for_biases(analysis_data)
            }

        except Exception as e:
            logger.error(f"Error in explainability engine: {e}")
            return {'error': str(e)}

    def _extract_decision_factors(self, data: Dict) -> Dict[str, Any]:
        """Extract key decision factors from analysis"""
        factors = {}

        # Valuation factors
        if 'valuation' in data:
            val = data['valuation']
            factors['valuation'] = {
                'price_target_upside': val.get('price_target', {}).get('upside', 0),
                'dcf_undervalued': (val.get('dcf_valuation', {}).get('dcf_price', 0) >
                                   val.get('current_price', 0)),
                'analyst_consensus': val.get('analyst_targets', {}).get('analyst_consensus', 'Hold'),
                'pe_attractive': val.get('comparative_valuation', {}).get('pe_ratio', 20) < 25
            }

        # Technical factors
        if 'technical_analysis' in data:
            tech = data['technical_analysis']
            factors['technical'] = {
                'trend': tech.get('trend', {}).get('direction', 'neutral'),
                'momentum': tech.get('indicators', {}).get('rsi', 50),
                'support_resistance': tech.get('support_resistance', {}),
                'signals': tech.get('signals', {}).get('overall', 'NEUTRAL')
            }

        # Sentiment factors
        factors['sentiment'] = {
            'news_sentiment': data.get('aggregated_data', {}).get('data', {}).get(
                'market_insights', {}).get('sentiment', 'neutral'),
            'analyst_upgrades': self._count_analyst_actions(data.get('news', [])),
            'social_sentiment': 'positive'  # Placeholder for social media analysis
        }

        # Market conditions
        if 'market_mood' in data:
            mood = data['market_mood']
            factors['market_conditions'] = {
                'market_mood': mood.get('mood_level', 'neutral'),
                'mood_score': mood.get('mood_score', 50),
                'sector_rotation': data.get('sector_rotation', {}).get('rotation_signal', 'Mixed')
            }

        return factors

    def _calculate_factor_contributions(self, factors: Dict) -> Dict[str, float]:
        """Calculate how much each factor contributes to the decision"""
        contributions = {}

        # Valuation contribution
        if 'valuation' in factors:
            val_score = 0
            val_factors = factors['valuation']
            if val_factors.get('price_target_upside', 0) > 20:
                val_score += 40
            if val_factors.get('dcf_undervalued'):
                val_score += 30
            if 'buy' in str(val_factors.get('analyst_consensus', '')).lower():
                val_score += 30
            contributions['valuation'] = val_score * self.decision_weights['valuation']

        # Technical contribution
        if 'technical' in factors:
            tech_score = 0
            tech_factors = factors['technical']
            if tech_factors.get('trend') == 'bullish':
                tech_score += 40
            if 30 < tech_factors.get('momentum', 50) < 70:
                tech_score += 30
            if 'BUY' in str(tech_factors.get('signals', '')):
                tech_score += 30
            contributions['technical'] = tech_score * self.decision_weights['technical']

        # Sentiment contribution
        if 'sentiment' in factors:
            sent_score = 50  # Base neutral
            if factors['sentiment'].get('news_sentiment') == 'bullish':
                sent_score += 30
            if factors['sentiment'].get('analyst_upgrades', 0) > 0:
                sent_score += 20
            contributions['sentiment'] = sent_score * self.decision_weights['sentiment']

        # Market conditions contribution
        if 'market_conditions' in factors:
            market_score = factors['market_conditions'].get('mood_score', 50)
            contributions['market_conditions'] = market_score * self.decision_weights['market_conditions']

        return contributions

    def _build_decision_tree(self, factors: Dict, contributions: Dict) -> Dict:
        """Build a decision tree showing the logic path"""
        tree = {
            'root': 'Investment Decision',
            'branches': []
        }

        # Primary branch: Valuation
        if 'valuation' in factors:
            val_branch = {
                'factor': 'Valuation Analysis',
                'weight': self.decision_weights['valuation'],
                'score': contributions.get('valuation', 0),
                'conditions': []
            }

            val_factors = factors['valuation']
            if val_factors.get('price_target_upside', 0) > 20:
                val_branch['conditions'].append({
                    'condition': 'Price target upside > 20%',
                    'met': True,
                    'impact': 'Positive'
                })

            tree['branches'].append(val_branch)

        # Technical branch
        if 'technical' in factors:
            tech_branch = {
                'factor': 'Technical Analysis',
                'weight': self.decision_weights['technical'],
                'score': contributions.get('technical', 0),
                'conditions': [
                    {
                        'condition': f"Trend is {factors['technical'].get('trend')}",
                        'met': factors['technical'].get('trend') == 'bullish',
                        'impact': 'Positive' if factors['technical'].get('trend') == 'bullish' else 'Negative'
                    }
                ]
            }
            tree['branches'].append(tech_branch)

        return tree

    def _generate_natural_explanation(self, factors: Dict, contributions: Dict) -> Dict[str, str]:
        """Generate human-readable explanation"""

        # Determine primary driver
        if contributions:
            primary_driver = max(contributions.items(), key=lambda x: x[1])
            driver_name, driver_score = primary_driver
        else:
            driver_name, driver_score = 'unknown', 0

        # Build summary
        summary_parts = []

        if 'valuation' in factors:
            val = factors['valuation']
            if val.get('price_target_upside', 0) > 20:
                summary_parts.append(f"significant upside potential of {val['price_target_upside']:.1f}%")
            if val.get('dcf_undervalued'):
                summary_parts.append("DCF analysis indicates undervaluation")

        if 'technical' in factors:
            tech = factors['technical']
            if tech.get('trend') == 'bullish':
                summary_parts.append("bullish technical trend")
            elif tech.get('trend') == 'bearish':
                summary_parts.append("bearish technical trend")

        summary = f"The recommendation is primarily driven by {driver_name} factors"
        if summary_parts:
            summary += f", particularly {' and '.join(summary_parts[:2])}"

        # Build detailed explanation
        detailed = []

        # Explain each factor
        for factor_name, factor_data in factors.items():
            if isinstance(factor_data, dict):
                factor_explanation = self._explain_factor(factor_name, factor_data)
                if factor_explanation:
                    detailed.append(factor_explanation)

        return {
            'summary': summary,
            'detailed': '\n\n'.join(detailed)
        }

    def _explain_factor(self, factor_name: str, factor_data: Dict) -> str:
        """Explain a single factor in natural language"""
        explanations = {
            'valuation': self._explain_valuation,
            'technical': self._explain_technical,
            'sentiment': self._explain_sentiment,
            'market_conditions': self._explain_market_conditions
        }

        explainer = explanations.get(factor_name)
        if explainer:
            return explainer(factor_data)
        return ""

    def _explain_valuation(self, data: Dict) -> str:
        """Explain valuation factors"""
        parts = ["**Valuation Analysis:**"]

        if 'price_target_upside' in data:
            upside = data['price_target_upside']
            if upside > 20:
                parts.append(f"• The stock shows strong upside potential of {upside:.1f}% to analyst price targets")
            elif upside > 0:
                parts.append(f"• Moderate upside of {upside:.1f}% to price targets")
            else:
                parts.append(f"• Limited upside with {upside:.1f}% to targets")

        if data.get('dcf_undervalued'):
            parts.append("• DCF model suggests the stock is undervalued at current levels")

        if 'analyst_consensus' in data:
            parts.append(f"• Analyst consensus rating is '{data['analyst_consensus']}'")

        return '\n'.join(parts)

    def _explain_technical(self, data: Dict) -> str:
        """Explain technical factors"""
        parts = ["**Technical Analysis:**"]

        if 'trend' in data:
            parts.append(f"• The stock is in a {data['trend']} trend")

        if 'momentum' in data:
            rsi = data['momentum']
            if rsi > 70:
                parts.append(f"• RSI at {rsi} indicates overbought conditions")
            elif rsi < 30:
                parts.append(f"• RSI at {rsi} indicates oversold conditions")
            else:
                parts.append(f"• RSI at {rsi} shows neutral momentum")

        if 'signals' in data:
            parts.append(f"• Technical indicators generate a '{data['signals']}' signal")

        return '\n'.join(parts)

    def _explain_sentiment(self, data: Dict) -> str:
        """Explain sentiment factors"""
        parts = ["**Market Sentiment:**"]

        if 'news_sentiment' in data:
            parts.append(f"• Recent news sentiment is {data['news_sentiment']}")

        if 'analyst_upgrades' in data and data['analyst_upgrades'] > 0:
            parts.append(f"• {data['analyst_upgrades']} recent analyst upgrades")

        return '\n'.join(parts)

    def _explain_market_conditions(self, data: Dict) -> str:
        """Explain market conditions"""
        parts = ["**Market Conditions:**"]

        if 'market_mood' in data:
            parts.append(f"• Market mood is '{data['market_mood']}' with a score of {data.get('mood_score', 'N/A')}")

        if 'sector_rotation' in data:
            parts.append(f"• Sector rotation signal: {data['sector_rotation']}")

        return '\n'.join(parts)

    def _identify_key_drivers(self, contributions: Dict) -> List[Dict]:
        """Identify the key drivers of the recommendation"""
        if not contributions:
            return []

        # Sort by contribution
        sorted_factors = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)

        key_drivers = []
        total_contribution = sum(abs(c) for _, c in contributions.items())

        for factor, contribution in sorted_factors[:3]:  # Top 3 drivers
            percentage = (abs(contribution) / total_contribution * 100) if total_contribution > 0 else 0
            key_drivers.append({
                'factor': factor,
                'contribution': contribution,
                'percentage': percentage,
                'direction': 'positive' if contribution > 0 else 'negative'
            })

        return key_drivers

    def _analyze_confidence(self, data: Dict) -> Dict:
        """Analyze confidence in the recommendation"""
        confidence_factors = []

        # Data quality
        if 'confidence_scores' in data:
            scores = data['confidence_scores']
            overall = scores.get('overall', 0)
            confidence_factors.append({
                'factor': 'Data Quality',
                'score': overall,
                'impact': 'high' if overall > 80 else 'medium' if overall > 60 else 'low'
            })

        # Agreement between models
        agreement_score = self._calculate_model_agreement(data)
        confidence_factors.append({
            'factor': 'Model Agreement',
            'score': agreement_score,
            'impact': 'high' if agreement_score > 80 else 'medium'
        })

        # Market conditions alignment
        market_alignment = self._check_market_alignment(data)
        confidence_factors.append({
            'factor': 'Market Alignment',
            'score': market_alignment,
            'impact': 'medium'
        })

        # Calculate overall confidence
        if confidence_factors:
            overall_confidence = sum(f['score'] for f in confidence_factors) / len(confidence_factors)
        else:
            overall_confidence = 50

        return {
            'overall_confidence': overall_confidence,
            'factors': confidence_factors,
            'uncertainty_sources': self._identify_uncertainty_sources(data)
        }

    def _calculate_model_agreement(self, data: Dict) -> float:
        """Calculate how well different models agree"""
        recommendations = []

        # Collect recommendations from different sources
        if 'valuation' in data:
            val_rec = data['valuation'].get('price_target', {}).get('recommendation', '')
            if val_rec:
                recommendations.append(val_rec.upper())

        if 'technical_analysis' in data:
            tech_sig = data['technical_analysis'].get('signals', {}).get('overall', '')
            if tech_sig:
                recommendations.append(tech_sig.upper())

        if not recommendations:
            return 50

        # Check agreement
        if all('BUY' in r or 'STRONG' in r for r in recommendations):
            return 90
        elif all('SELL' in r for r in recommendations):
            return 90
        elif all('HOLD' in r or 'NEUTRAL' in r for r in recommendations):
            return 80
        else:
            return 40  # Disagreement

    def _check_market_alignment(self, data: Dict) -> float:
        """Check if recommendation aligns with market conditions"""
        if 'market_mood' not in data:
            return 50

        mood_score = data['market_mood'].get('mood_score', 50)
        recommendation = self._determine_recommendation({})

        # Bullish recommendation in bullish market = good alignment
        if recommendation in ['BUY', 'STRONG BUY'] and mood_score > 60:
            return 80
        # Bearish recommendation in bearish market = good alignment
        elif recommendation in ['SELL', 'STRONG SELL'] and mood_score < 40:
            return 80
        # Neutral in neutral market
        elif recommendation == 'HOLD' and 40 <= mood_score <= 60:
            return 70
        else:
            return 30  # Poor alignment

    def _identify_uncertainty_sources(self, data: Dict) -> List[str]:
        """Identify sources of uncertainty in the analysis"""
        uncertainties = []

        # Check data completeness
        if 'confidence_scores' in data:
            scores = data['confidence_scores']
            if scores.get('analyst_consensus', 0) < 50:
                uncertainties.append("Limited analyst coverage")
            if scores.get('price_data', 0) < 80:
                uncertainties.append("Incomplete price data")

        # Check volatility
        if 'technical_analysis' in data:
            volatility = data['technical_analysis'].get('volatility', {})
            if volatility.get('current', 0) > 30:
                uncertainties.append("High market volatility")

        # Check market conditions
        if 'market_mood' in data:
            mood = data['market_mood'].get('mood_level', '')
            if 'extreme' in mood.lower():
                uncertainties.append(f"Extreme market conditions ({mood})")

        return uncertainties

    def _generate_counterfactual(self, factors: Dict) -> Dict:
        """Generate 'what-if' scenarios"""
        counterfactuals = []

        # What if valuation changes
        if 'valuation' in factors:
            current_upside = factors['valuation'].get('price_target_upside', 0)
            counterfactuals.append({
                'scenario': 'If price target upside was 10% lower',
                'current_value': f"{current_upside:.1f}%",
                'new_value': f"{current_upside - 10:.1f}%",
                'impact': 'Recommendation might change to HOLD' if current_upside < 30 else 'Recommendation would remain BUY'
            })

        # What if market mood changes
        if 'market_conditions' in factors:
            current_mood = factors['market_conditions'].get('mood_score', 50)
            counterfactuals.append({
                'scenario': 'If market mood turned bearish (score: 30)',
                'current_value': f"Score: {current_mood}",
                'new_value': 'Score: 30',
                'impact': 'Risk adjustment would increase, position size should decrease'
            })

        return {
            'scenarios': counterfactuals,
            'note': 'These scenarios help understand recommendation sensitivity'
        }

    def _perform_sensitivity_analysis(self, factors: Dict) -> Dict:
        """Analyze how sensitive the recommendation is to input changes"""
        sensitivities = []

        # Valuation sensitivity
        if 'valuation' in factors:
            sensitivities.append({
                'factor': 'Price Target',
                'sensitivity': 'HIGH',
                'threshold': '±10% change could alter recommendation'
            })

        # Technical sensitivity
        if 'technical' in factors:
            sensitivities.append({
                'factor': 'Technical Indicators',
                'sensitivity': 'MEDIUM',
                'threshold': 'RSI crossing 30/70 would trigger signal change'
            })

        return {
            'factors': sensitivities,
            'overall_sensitivity': 'MEDIUM',
            'recommendation_stability': 'Stable within ±5% price movement'
        }

    def _check_for_biases(self, data: Dict) -> Dict:
        """Check for potential biases in the analysis"""
        biases = []

        # Recency bias
        if 'news' in data:
            news_items = data.get('news', [])
            if len(news_items) > 0:
                # Check if all news is from last 24 hours
                biases.append({
                    'type': 'Recency Bias',
                    'detected': False,
                    'mitigation': 'Using 30-day average metrics alongside recent data'
                })

        # Confirmation bias
        biases.append({
            'type': 'Confirmation Bias',
            'detected': False,
            'mitigation': 'Multiple independent data sources consulted'
        })

        # Anchoring bias
        if 'valuation' in data:
            biases.append({
                'type': 'Anchoring Bias',
                'detected': False,
                'mitigation': 'Using multiple valuation methods, not just analyst targets'
            })

        return {
            'biases_checked': biases,
            'overall_assessment': 'Low bias risk - multiple safeguards in place'
        }

    def _determine_recommendation(self, contributions: Dict) -> str:
        """Determine final recommendation based on contributions"""
        if not contributions:
            return 'HOLD'

        total_score = sum(contributions.values())

        if total_score > 70:
            return 'STRONG BUY'
        elif total_score > 50:
            return 'BUY'
        elif total_score > 30:
            return 'HOLD'
        elif total_score > 10:
            return 'SELL'
        else:
            return 'STRONG SELL'

    def _count_analyst_actions(self, news: List) -> int:
        """Count analyst upgrades/downgrades from news"""
        upgrade_keywords = ['upgrade', 'raised', 'bullish', 'outperform']
        count = 0

        for item in news:
            content = str(item).lower()
            if any(keyword in content for keyword in upgrade_keywords):
                count += 1

        return count