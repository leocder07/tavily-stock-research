"""
Expert AI Agents - Self-Sufficient Financial Analysis
Uses GPT-4 as financial experts with local calculations
No external API dependencies beyond OpenAI LLM
"""

from .expert_fundamental_agent import ExpertFundamentalAgent
from .expert_technical_agent import ExpertTechnicalAgent
from .expert_risk_agent import ExpertRiskAgent
from .expert_synthesis_agent import ExpertSynthesisAgent

__all__ = [
    'ExpertFundamentalAgent',
    'ExpertTechnicalAgent',
    'ExpertRiskAgent',
    'ExpertSynthesisAgent'
]
