"""
Base Sentiment Source
Abstract base class for all sentiment data sources
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class SentimentData(BaseModel):
    """Normalized sentiment data structure"""

    source: str = Field(description="Source name (twitter, reddit, news, tavily)")
    symbol: str = Field(description="Stock symbol")
    sentiment_score: float = Field(description="Normalized score -1.0 to 1.0", ge=-1, le=1)
    sentiment_label: str = Field(description="bullish/neutral/bearish")
    confidence: float = Field(description="Confidence 0-1", ge=0, le=1)
    volume: int = Field(description="Number of mentions/posts/articles", ge=0)
    timeframe: str = Field(description="Time range (24h, 7d, etc.)")

    # Sentiment breakdown
    positive_count: int = Field(default=0, ge=0)
    neutral_count: int = Field(default=0, ge=0)
    negative_count: int = Field(default=0, ge=0)

    # Key insights
    top_topics: List[str] = Field(default_factory=list, description="Top discussed topics")
    bull_arguments: List[str] = Field(default_factory=list, description="Bullish arguments")
    bear_arguments: List[str] = Field(default_factory=list, description="Bearish arguments")

    # Metadata
    sample_posts: List[Dict[str, Any]] = Field(default_factory=list, description="Sample posts/articles")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseSentimentSource(ABC):
    """Abstract base class for sentiment data sources"""

    def __init__(self, source_name: str, api_key: Optional[str] = None):
        """
        Initialize sentiment source

        Args:
            source_name: Name of the source (twitter, reddit, etc.)
            api_key: API key for the service (if required)
        """
        self.source_name = source_name
        self.api_key = api_key
        self.logger = logging.getLogger(f"sentiment.{source_name}")

    @abstractmethod
    async def fetch_sentiment(self, symbol: str, timeframe: str = "24h") -> Optional[SentimentData]:
        """
        Fetch sentiment data for a stock symbol

        Args:
            symbol: Stock symbol (e.g., AAPL)
            timeframe: Time range (24h, 7d, 30d)

        Returns:
            SentimentData object or None if fetch fails
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the data source is available and configured

        Returns:
            True if available, False otherwise
        """
        pass

    def normalize_score(self, raw_score: float, min_val: float, max_val: float) -> float:
        """
        Normalize a score to -1.0 to 1.0 range

        Args:
            raw_score: Raw score from the API
            min_val: Minimum possible value
            max_val: Maximum possible value

        Returns:
            Normalized score between -1.0 and 1.0
        """
        if max_val == min_val:
            return 0.0

        # Normalize to 0-1 first
        normalized = (raw_score - min_val) / (max_val - min_val)

        # Scale to -1 to 1
        return (normalized * 2) - 1

    def classify_sentiment(self, score: float) -> str:
        """
        Classify sentiment score into label

        Args:
            score: Sentiment score -1.0 to 1.0

        Returns:
            'bullish', 'neutral', or 'bearish'
        """
        if score > 0.15:
            return "bullish"
        elif score < -0.15:
            return "bearish"
        else:
            return "neutral"

    def calculate_confidence(self, volume: int, min_volume: int = 10) -> float:
        """
        Calculate confidence based on data volume

        Args:
            volume: Number of data points
            min_volume: Minimum volume for high confidence

        Returns:
            Confidence score 0-1
        """
        if volume >= min_volume * 10:
            return 1.0
        elif volume >= min_volume * 5:
            return 0.9
        elif volume >= min_volume:
            return 0.7
        elif volume >= min_volume / 2:
            return 0.5
        else:
            return 0.3
