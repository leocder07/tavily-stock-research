"""
Lineage Mixin for Agents
Provides easy integration of data lineage tracking into any agent
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from services.data_lineage_tracker import (
    DataLineageTracker,
    DataSource,
    DataReliability,
    DataLineageRecord
)
from services.lineage_integration import LineageIntegration

logger = logging.getLogger(__name__)


class LineageMixin:
    """
    Mixin class that adds lineage tracking capabilities to any agent

    Usage:
        class MyAgent(BaseFinancialAgent, LineageMixin):
            def __init__(self, ...):
                super().__init__(...)
                self.init_lineage_tracking()

            async def execute(self, context):
                # Track data
                self.track_data('price', 150.0, DataSource.YFINANCE, DataReliability.HIGH)

                # Add lineage to output
                result = {'price': 150.0}
                return self.add_lineage_to_output(result)
    """

    def init_lineage_tracking(self):
        """Initialize lineage tracker for this agent"""
        self.lineage_tracker = DataLineageTracker()
        logger.debug(f"[{self.__class__.__name__}] Lineage tracking initialized")

    def track_data(
        self,
        field_name: str,
        value: Any,
        source: DataSource,
        reliability: DataReliability,
        confidence: float = 1.0,
        secondary_sources: Optional[list] = None,
        data_timestamp: Optional[datetime] = None,
        transformation: Optional[str] = None,
        upstream_fields: Optional[list] = None,
        citation: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> DataLineageRecord:
        """
        Track a data field with lineage metadata

        Args:
            field_name: Name of the field
            value: Value of the field
            source: Data source
            reliability: Reliability classification
            confidence: Confidence score 0-1
            secondary_sources: Additional sources
            data_timestamp: When the data was generated
            transformation: Description of transformations applied
            upstream_fields: Fields this depends on
            citation: Citation string
            source_url: URL of source

        Returns:
            DataLineageRecord
        """
        if not hasattr(self, 'lineage_tracker'):
            self.init_lineage_tracking()

        return self.lineage_tracker.track(
            field_name=field_name,
            value=value,
            source=source,
            reliability=reliability,
            confidence=confidence,
            secondary_sources=secondary_sources,
            data_timestamp=data_timestamp or datetime.utcnow(),
            transformation_applied=[transformation] if transformation else [],
            upstream_dependencies=upstream_fields or [],
            citation=citation,
            source_url=source_url
        )

    def track_calculated(
        self,
        field_name: str,
        value: Any,
        formula: str,
        input_fields: list,
        confidence: float = 1.0
    ) -> DataLineageRecord:
        """
        Track a calculated field

        Args:
            field_name: Name of calculated field
            value: Calculated value
            formula: Description of calculation
            input_fields: List of input field names
            confidence: Confidence score

        Returns:
            DataLineageRecord
        """
        if not hasattr(self, 'lineage_tracker'):
            self.init_lineage_tracking()

        return self.lineage_tracker.track_calculated(
            field_name=field_name,
            value=value,
            formula=formula,
            upstream_fields=input_fields,
            confidence=confidence
        )

    def track_llm_output(
        self,
        field_name: str,
        value: Any,
        model: str,
        prompt_context: str,
        confidence: float = 0.7,
        sources_cited: Optional[list] = None
    ) -> DataLineageRecord:
        """
        Track LLM-generated output

        Args:
            field_name: Name of the field
            value: LLM output
            model: Model name
            prompt_context: Brief prompt description
            confidence: Confidence score
            sources_cited: Sources provided to LLM

        Returns:
            DataLineageRecord
        """
        if not hasattr(self, 'lineage_tracker'):
            self.init_lineage_tracking()

        return self.lineage_tracker.track_llm_generated(
            field_name=field_name,
            value=value,
            model=model,
            prompt_context=prompt_context,
            confidence=confidence,
            sources_cited=sources_cited
        )

    def add_lineage_to_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add lineage summary to agent output

        Args:
            output_data: Agent's output dictionary

        Returns:
            Output data with lineage field added
        """
        if not hasattr(self, 'lineage_tracker'):
            logger.warning(f"[{self.__class__.__name__}] No lineage tracker found, skipping lineage addition")
            return output_data

        # Add lineage summary
        output_data['lineage'] = LineageIntegration.create_lineage_summary_dict(self.lineage_tracker)

        # Add detailed citations
        output_data['citations'] = self.lineage_tracker.get_citations()

        logger.info(
            f"[{self.__class__.__name__}] Added lineage: "
            f"{output_data['lineage']['data_quality']['total_fields']} fields tracked, "
            f"quality score: {output_data['lineage']['data_quality']['overall_score']:.1f}"
        )

        return output_data

    def get_lineage_summary(self) -> Dict[str, Any]:
        """
        Get lineage summary without modifying output

        Returns:
            Lineage summary dict
        """
        if not hasattr(self, 'lineage_tracker'):
            return {}

        return LineageIntegration.create_lineage_summary_dict(self.lineage_tracker)

    def export_full_lineage(self) -> Dict[str, Any]:
        """
        Export complete lineage report with all details

        Returns:
            Full lineage report
        """
        if not hasattr(self, 'lineage_tracker'):
            return {}

        return self.lineage_tracker.export_lineage_report()

    def validate_field_lineage(
        self,
        field_name: str,
        validation_passed: bool,
        warnings: Optional[list] = None
    ):
        """
        Add validation results to lineage

        Args:
            field_name: Field that was validated
            validation_passed: Whether validation passed
            warnings: List of warning messages
        """
        if not hasattr(self, 'lineage_tracker'):
            return

        self.lineage_tracker.validate_lineage(
            field_name=field_name,
            validation_result=validation_passed,
            warnings=warnings or []
        )

    def get_data_quality_score(self) -> float:
        """
        Get overall data quality score for this agent's data

        Returns:
            Quality score 0-100
        """
        if not hasattr(self, 'lineage_tracker'):
            return 0.0

        summary = self.lineage_tracker.generate_summary()
        return summary.data_quality_score

    def get_field_lineage(self, field_name: str) -> Optional[DataLineageRecord]:
        """
        Get lineage for a specific field

        Args:
            field_name: Field to get lineage for

        Returns:
            DataLineageRecord or None
        """
        if not hasattr(self, 'lineage_tracker'):
            return None

        return self.lineage_tracker.get_lineage(field_name)
