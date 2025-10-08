"""
Data Lineage Tracker
Tracks origin, timestamp, and quality of every data point in the analysis pipeline
Provides comprehensive source attribution and data freshness tracking
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
import json

logger = logging.getLogger(__name__)


class DataSource(str, Enum):
    """Enumeration of all data sources in the system"""
    YFINANCE = "yfinance"
    ALPHA_VANTAGE = "alpha_vantage"
    TAVILY_SEARCH = "tavily_search"
    TAVILY_QNA = "tavily_qna"
    TAVILY_EXTRACT = "tavily_extract"
    TAVILY_CONTEXT = "tavily_context"
    LLM_GPT4 = "llm_gpt4"
    LLM_GPT4_TURBO = "llm_gpt4_turbo"
    CALCULATED = "calculated"
    CACHED = "cached"
    FALLBACK = "fallback"
    USER_INPUT = "user_input"
    INTERNAL = "internal"


class DataFreshness(str, Enum):
    """Data freshness classification"""
    REALTIME = "realtime"  # < 5 minutes old
    FRESH = "fresh"  # < 1 hour old
    RECENT = "recent"  # < 24 hours old
    DAILY = "daily"  # < 7 days old
    WEEKLY = "weekly"  # < 30 days old
    STALE = "stale"  # > 30 days old
    UNKNOWN = "unknown"


class DataReliability(str, Enum):
    """Data reliability classification"""
    HIGH = "high"  # Official API, verified source
    MEDIUM = "medium"  # Reputable news source, calculated from reliable data
    LOW = "low"  # Web scraping, unverified source
    UNCERTAIN = "uncertain"  # LLM generated, estimated
    FALLBACK = "fallback"  # Emergency fallback data


class DataLineageMetadata(BaseModel):
    """Metadata for a single data point"""
    source: DataSource = Field(description="Primary data source")
    secondary_sources: List[DataSource] = Field(default_factory=list, description="Additional sources used")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="When data was fetched")
    data_timestamp: Optional[datetime] = Field(None, description="Timestamp of the actual data (may differ from fetch)")
    reliability: DataReliability = Field(description="Reliability score for this data")
    freshness: DataFreshness = Field(description="How fresh is this data")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score 0-1")
    transformation_applied: List[str] = Field(default_factory=list, description="Transformations applied to raw data")
    upstream_dependencies: List[str] = Field(default_factory=list, description="Field names this data depends on")
    cache_hit: bool = Field(default=False, description="Was this from cache")
    api_endpoint: Optional[str] = Field(None, description="Specific API endpoint used")
    source_url: Optional[str] = Field(None, description="URL of the source (for web data)")
    citation: Optional[str] = Field(None, description="Citation string for this source")


class DataLineageRecord(BaseModel):
    """Complete lineage record for a data field"""
    field_name: str = Field(description="Name of the data field")
    value: Any = Field(description="The actual value")
    metadata: DataLineageMetadata = Field(description="Lineage metadata")
    validation_passed: bool = Field(default=True, description="Did this pass validation")
    validation_warnings: List[str] = Field(default_factory=list, description="Any validation warnings")


class LineageSummary(BaseModel):
    """Summary of data lineage for an entire analysis"""
    total_fields: int = Field(description="Total number of data fields")
    source_breakdown: Dict[str, int] = Field(default_factory=dict, description="Count by source")
    freshness_breakdown: Dict[str, int] = Field(default_factory=dict, description="Count by freshness")
    reliability_breakdown: Dict[str, int] = Field(default_factory=dict, description="Count by reliability")
    cache_hit_rate: float = Field(description="Percentage of cached data")
    average_confidence: float = Field(description="Average confidence score")
    oldest_data_age: Optional[timedelta] = Field(None, description="Age of oldest data point")
    newest_data_age: Optional[timedelta] = Field(None, description="Age of newest data point")
    data_quality_score: float = Field(description="Overall data quality 0-100")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DataLineageTracker:
    """
    Tracks data lineage throughout the analysis pipeline
    Provides comprehensive source attribution and quality metrics
    """

    def __init__(self):
        self.records: Dict[str, DataLineageRecord] = {}
        self.agent_lineages: Dict[str, List[DataLineageRecord]] = {}

    def track(
        self,
        field_name: str,
        value: Any,
        source: DataSource,
        reliability: DataReliability,
        confidence: float = 1.0,
        secondary_sources: Optional[List[DataSource]] = None,
        data_timestamp: Optional[datetime] = None,
        transformation_applied: Optional[List[str]] = None,
        upstream_dependencies: Optional[List[str]] = None,
        cache_hit: bool = False,
        api_endpoint: Optional[str] = None,
        source_url: Optional[str] = None,
        citation: Optional[str] = None
    ) -> DataLineageRecord:
        """
        Track a single data point's lineage

        Args:
            field_name: Name of the field (e.g., "price", "pe_ratio")
            value: The actual value
            source: Primary data source
            reliability: Reliability classification
            confidence: Confidence score 0-1
            secondary_sources: Additional sources contributing to this value
            data_timestamp: When the data was actually generated (not fetched)
            transformation_applied: List of transformations (e.g., ["normalized", "smoothed"])
            upstream_dependencies: Fields this calculation depends on
            cache_hit: Whether this was from cache
            api_endpoint: Specific API endpoint
            source_url: URL for web sources
            citation: Citation string

        Returns:
            DataLineageRecord for this field
        """
        fetched_at = datetime.utcnow()

        # Calculate freshness
        if data_timestamp:
            age = fetched_at - data_timestamp
            freshness = self._calculate_freshness(age)
        else:
            freshness = DataFreshness.UNKNOWN
            data_timestamp = fetched_at

        # Create metadata
        metadata = DataLineageMetadata(
            source=source,
            secondary_sources=secondary_sources or [],
            fetched_at=fetched_at,
            data_timestamp=data_timestamp,
            reliability=reliability,
            freshness=freshness,
            confidence=confidence,
            transformation_applied=transformation_applied or [],
            upstream_dependencies=upstream_dependencies or [],
            cache_hit=cache_hit,
            api_endpoint=api_endpoint,
            source_url=source_url,
            citation=citation
        )

        # Create record
        record = DataLineageRecord(
            field_name=field_name,
            value=value,
            metadata=metadata
        )

        # Store record
        self.records[field_name] = record

        logger.debug(
            f"Tracked lineage for {field_name}: source={source}, "
            f"reliability={reliability}, freshness={freshness}"
        )

        return record

    def track_calculated(
        self,
        field_name: str,
        value: Any,
        formula: str,
        upstream_fields: List[str],
        confidence: float = 1.0
    ) -> DataLineageRecord:
        """
        Track a calculated field that depends on other fields

        Args:
            field_name: Name of calculated field
            value: Calculated value
            formula: Description of calculation (e.g., "P/E = price / EPS")
            upstream_fields: Fields used in calculation
            confidence: Confidence based on upstream data quality

        Returns:
            DataLineageRecord
        """
        # Determine reliability based on upstream fields
        upstream_reliability = self._aggregate_upstream_reliability(upstream_fields)

        return self.track(
            field_name=field_name,
            value=value,
            source=DataSource.CALCULATED,
            reliability=upstream_reliability,
            confidence=confidence,
            transformation_applied=[formula],
            upstream_dependencies=upstream_fields
        )

    def track_llm_generated(
        self,
        field_name: str,
        value: Any,
        model: str,
        prompt_context: str,
        confidence: float = 0.7,
        sources_cited: Optional[List[str]] = None
    ) -> DataLineageRecord:
        """
        Track LLM-generated content

        Args:
            field_name: Name of the field
            value: LLM output
            model: Model name (e.g., "gpt-4")
            prompt_context: Brief description of prompt
            confidence: LLM confidence
            sources_cited: Sources the LLM was given

        Returns:
            DataLineageRecord
        """
        source = DataSource.LLM_GPT4 if "gpt-4" in model.lower() else DataSource.LLM_GPT4_TURBO

        return self.track(
            field_name=field_name,
            value=value,
            source=source,
            reliability=DataReliability.UNCERTAIN,
            confidence=confidence,
            transformation_applied=[f"LLM: {model}"],
            upstream_dependencies=sources_cited or [],
            api_endpoint=model,
            citation=f"Generated by {model}"
        )

    def get_lineage(self, field_name: str) -> Optional[DataLineageRecord]:
        """Get lineage record for a specific field"""
        return self.records.get(field_name)

    def get_all_lineages(self) -> Dict[str, DataLineageRecord]:
        """Get all lineage records"""
        return self.records.copy()

    def generate_summary(self) -> LineageSummary:
        """
        Generate a summary of all tracked lineage

        Returns:
            LineageSummary with aggregate statistics
        """
        if not self.records:
            return LineageSummary(
                total_fields=0,
                cache_hit_rate=0.0,
                average_confidence=0.0,
                data_quality_score=0.0
            )

        # Count by source
        source_breakdown = {}
        for record in self.records.values():
            source = record.metadata.source.value
            source_breakdown[source] = source_breakdown.get(source, 0) + 1

        # Count by freshness
        freshness_breakdown = {}
        for record in self.records.values():
            freshness = record.metadata.freshness.value
            freshness_breakdown[freshness] = freshness_breakdown.get(freshness, 0) + 1

        # Count by reliability
        reliability_breakdown = {}
        for record in self.records.values():
            reliability = record.metadata.reliability.value
            reliability_breakdown[reliability] = reliability_breakdown.get(reliability, 0) + 1

        # Calculate cache hit rate
        cache_hits = sum(1 for r in self.records.values() if r.metadata.cache_hit)
        cache_hit_rate = (cache_hits / len(self.records)) * 100

        # Calculate average confidence
        avg_confidence = sum(r.metadata.confidence for r in self.records.values()) / len(self.records)

        # Find oldest and newest data
        now = datetime.utcnow()
        ages = [now - r.metadata.data_timestamp for r in self.records.values() if r.metadata.data_timestamp]
        oldest_age = max(ages) if ages else None
        newest_age = min(ages) if ages else None

        # Calculate overall data quality score
        quality_score = self._calculate_quality_score()

        return LineageSummary(
            total_fields=len(self.records),
            source_breakdown=source_breakdown,
            freshness_breakdown=freshness_breakdown,
            reliability_breakdown=reliability_breakdown,
            cache_hit_rate=round(cache_hit_rate, 2),
            average_confidence=round(avg_confidence, 3),
            oldest_data_age=oldest_age,
            newest_data_age=newest_age,
            data_quality_score=round(quality_score, 2)
        )

    def export_lineage_report(self) -> Dict[str, Any]:
        """
        Export complete lineage report for visualization

        Returns:
            Dictionary with complete lineage information
        """
        summary = self.generate_summary()

        # Build detailed records
        detailed_records = []
        for field_name, record in self.records.items():
            detailed_records.append({
                'field': field_name,
                'value': str(record.value)[:100] if record.value is not None else None,
                'source': record.metadata.source.value,
                'secondary_sources': [s.value for s in record.metadata.secondary_sources],
                'reliability': record.metadata.reliability.value,
                'freshness': record.metadata.freshness.value,
                'confidence': record.metadata.confidence,
                'age_seconds': (datetime.utcnow() - record.metadata.data_timestamp).total_seconds() if record.metadata.data_timestamp else None,
                'cache_hit': record.metadata.cache_hit,
                'transformations': record.metadata.transformation_applied,
                'dependencies': record.metadata.upstream_dependencies,
                'citation': record.metadata.citation,
                'validation_passed': record.validation_passed,
                'warnings': record.validation_warnings
            })

        return {
            'summary': summary.dict(),
            'records': detailed_records,
            'generated_at': datetime.utcnow().isoformat()
        }

    def get_citations(self) -> List[Dict[str, str]]:
        """
        Get all unique citations from tracked data

        Returns:
            List of citation dictionaries
        """
        citations = []
        seen_citations = set()

        for record in self.records.values():
            if record.metadata.citation and record.metadata.citation not in seen_citations:
                citations.append({
                    'source': record.metadata.source.value,
                    'citation': record.metadata.citation,
                    'reliability': record.metadata.reliability.value,
                    'url': record.metadata.source_url or "",
                    'field': record.field_name
                })
                seen_citations.add(record.metadata.citation)

        return citations

    def validate_lineage(self, field_name: str, validation_result: bool, warnings: List[str] = None):
        """
        Add validation results to a lineage record

        Args:
            field_name: Field to validate
            validation_result: True if passed validation
            warnings: List of warning messages
        """
        if field_name in self.records:
            self.records[field_name].validation_passed = validation_result
            if warnings:
                self.records[field_name].validation_warnings.extend(warnings)

    def _calculate_freshness(self, age: timedelta) -> DataFreshness:
        """Calculate freshness classification based on age"""
        minutes = age.total_seconds() / 60

        if minutes < 5:
            return DataFreshness.REALTIME
        elif minutes < 60:
            return DataFreshness.FRESH
        elif minutes < 1440:  # 24 hours
            return DataFreshness.RECENT
        elif minutes < 10080:  # 7 days
            return DataFreshness.DAILY
        elif minutes < 43200:  # 30 days
            return DataFreshness.WEEKLY
        else:
            return DataFreshness.STALE

    def _aggregate_upstream_reliability(self, upstream_fields: List[str]) -> DataReliability:
        """Determine reliability based on upstream fields"""
        if not upstream_fields:
            return DataReliability.MEDIUM

        # Get reliability of all upstream fields
        reliabilities = []
        for field in upstream_fields:
            if field in self.records:
                reliabilities.append(self.records[field].metadata.reliability)

        if not reliabilities:
            return DataReliability.MEDIUM

        # Use the lowest reliability (most conservative)
        reliability_order = [
            DataReliability.FALLBACK,
            DataReliability.UNCERTAIN,
            DataReliability.LOW,
            DataReliability.MEDIUM,
            DataReliability.HIGH
        ]

        for rel in reliability_order:
            if rel in reliabilities:
                return rel

        return DataReliability.MEDIUM

    def _calculate_quality_score(self) -> float:
        """
        Calculate overall data quality score (0-100)
        Based on reliability, freshness, confidence, and validation
        """
        if not self.records:
            return 0.0

        total_score = 0.0

        for record in self.records.values():
            # Base score from reliability (0-40 points)
            reliability_scores = {
                DataReliability.HIGH: 40,
                DataReliability.MEDIUM: 30,
                DataReliability.LOW: 20,
                DataReliability.UNCERTAIN: 10,
                DataReliability.FALLBACK: 5
            }
            score = reliability_scores.get(record.metadata.reliability, 20)

            # Add freshness score (0-30 points)
            freshness_scores = {
                DataFreshness.REALTIME: 30,
                DataFreshness.FRESH: 25,
                DataFreshness.RECENT: 20,
                DataFreshness.DAILY: 15,
                DataFreshness.WEEKLY: 10,
                DataFreshness.STALE: 5,
                DataFreshness.UNKNOWN: 10
            }
            score += freshness_scores.get(record.metadata.freshness, 10)

            # Add confidence score (0-20 points)
            score += record.metadata.confidence * 20

            # Add validation bonus (0-10 points)
            if record.validation_passed:
                score += 10
            elif record.validation_warnings:
                score += 5

            total_score += score

        # Average score
        avg_score = total_score / len(self.records)

        return min(100.0, avg_score)

    def add_agent_lineage(self, agent_name: str, records: List[DataLineageRecord]):
        """Store lineage records by agent"""
        self.agent_lineages[agent_name] = records

    def get_agent_lineage(self, agent_name: str) -> List[DataLineageRecord]:
        """Get lineage records for a specific agent"""
        return self.agent_lineages.get(agent_name, [])
