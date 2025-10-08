"""
Lineage Visualization Formatter
Converts lineage data into frontend-friendly formats for visualization
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.data_lineage_tracker import (
    DataLineageTracker,
    DataSource,
    DataReliability,
    DataFreshness
)

logger = logging.getLogger(__name__)


class LineageVisualizer:
    """
    Formats lineage data for frontend visualization
    Supports multiple visualization types: timeline, sankey, network graph
    """

    @staticmethod
    def create_timeline_view(tracker: DataLineageTracker) -> Dict[str, Any]:
        """
        Create timeline visualization showing data freshness

        Returns:
            {
                'timeline': [
                    {
                        'timestamp': '2025-10-07T12:00:00Z',
                        'fields': ['price', 'volume'],
                        'source': 'yfinance',
                        'freshness': 'realtime'
                    },
                    ...
                ],
                'time_range': {
                    'start': '2025-10-07T10:00:00Z',
                    'end': '2025-10-07T12:00:00Z'
                }
            }
        """
        records = tracker.get_all_lineages()

        # Group by timestamp
        timeline_groups = {}
        for field_name, record in records.items():
            timestamp = record.metadata.data_timestamp.isoformat()

            if timestamp not in timeline_groups:
                timeline_groups[timestamp] = {
                    'timestamp': timestamp,
                    'fields': [],
                    'sources': set(),
                    'freshness': record.metadata.freshness.value
                }

            timeline_groups[timestamp]['fields'].append(field_name)
            timeline_groups[timestamp]['sources'].add(record.metadata.source.value)

        # Convert to list and sort
        timeline = []
        for item in timeline_groups.values():
            item['sources'] = list(item['sources'])
            item['field_count'] = len(item['fields'])
            timeline.append(item)

        timeline.sort(key=lambda x: x['timestamp'])

        # Calculate time range
        if timeline:
            time_range = {
                'start': timeline[0]['timestamp'],
                'end': timeline[-1]['timestamp']
            }
        else:
            time_range = {}

        return {
            'timeline': timeline,
            'time_range': time_range
        }

    @staticmethod
    def create_source_flow_diagram(tracker: DataLineageTracker) -> Dict[str, Any]:
        """
        Create Sankey diagram data showing data flow from sources to final fields

        Returns:
            {
                'nodes': [
                    {'id': 'yfinance', 'name': 'Yahoo Finance', 'type': 'source'},
                    {'id': 'price', 'name': 'Price', 'type': 'field'},
                    ...
                ],
                'links': [
                    {'source': 'yfinance', 'target': 'price', 'value': 1, 'reliability': 'high'},
                    ...
                ]
            }
        """
        nodes = []
        links = []
        node_ids = set()

        records = tracker.get_all_lineages()

        # Create source nodes
        sources = set()
        for record in records.values():
            sources.add(record.metadata.source.value)

        for source in sources:
            if source not in node_ids:
                nodes.append({
                    'id': source,
                    'name': LineageVisualizer._format_source_name(source),
                    'type': 'source',
                    'category': 'data_source'
                })
                node_ids.add(source)

        # Create field nodes and links
        for field_name, record in records.items():
            # Add field node
            if field_name not in node_ids:
                nodes.append({
                    'id': field_name,
                    'name': LineageVisualizer._format_field_name(field_name),
                    'type': 'field',
                    'category': 'data_field',
                    'reliability': record.metadata.reliability.value,
                    'freshness': record.metadata.freshness.value
                })
                node_ids.add(field_name)

            # Add link from source to field
            links.append({
                'source': record.metadata.source.value,
                'target': field_name,
                'value': 1,
                'reliability': record.metadata.reliability.value,
                'confidence': record.metadata.confidence
            })

            # Add links for upstream dependencies
            for upstream in record.metadata.upstream_dependencies:
                if upstream in node_ids:
                    links.append({
                        'source': upstream,
                        'target': field_name,
                        'value': 1,
                        'type': 'dependency',
                        'reliability': record.metadata.reliability.value
                    })

        return {
            'nodes': nodes,
            'links': links,
            'metadata': {
                'total_sources': len(sources),
                'total_fields': len(records),
                'total_dependencies': sum(len(r.metadata.upstream_dependencies) for r in records.values())
            }
        }

    @staticmethod
    def create_quality_dashboard(tracker: DataLineageTracker) -> Dict[str, Any]:
        """
        Create dashboard data for data quality visualization

        Returns:
            {
                'overview': {
                    'total_fields': 45,
                    'quality_score': 87.5,
                    'high_quality_pct': 75.0,
                    'fresh_data_pct': 90.0
                },
                'by_source': [
                    {
                        'source': 'yfinance',
                        'count': 30,
                        'avg_confidence': 0.95,
                        'reliability': 'high'
                    },
                    ...
                ],
                'freshness_gauge': {
                    'realtime': 20,
                    'fresh': 15,
                    'recent': 8,
                    'stale': 2
                },
                'reliability_breakdown': {
                    'high': 35,
                    'medium': 8,
                    'low': 2
                }
            }
        """
        summary = tracker.generate_summary()
        records = tracker.get_all_lineages()

        # Calculate percentages
        high_quality_count = sum(
            1 for r in records.values()
            if r.metadata.reliability in [DataReliability.HIGH, DataReliability.MEDIUM]
        )
        high_quality_pct = (high_quality_count / len(records) * 100) if records else 0

        fresh_count = sum(
            1 for r in records.values()
            if r.metadata.freshness in [DataFreshness.REALTIME, DataFreshness.FRESH, DataFreshness.RECENT]
        )
        fresh_data_pct = (fresh_count / len(records) * 100) if records else 0

        # By source analysis
        by_source = {}
        for record in records.values():
            source = record.metadata.source.value
            if source not in by_source:
                by_source[source] = {
                    'source': source,
                    'count': 0,
                    'confidences': [],
                    'reliabilities': []
                }

            by_source[source]['count'] += 1
            by_source[source]['confidences'].append(record.metadata.confidence)
            by_source[source]['reliabilities'].append(record.metadata.reliability.value)

        # Calculate averages
        by_source_list = []
        for source_data in by_source.values():
            avg_confidence = sum(source_data['confidences']) / len(source_data['confidences'])
            # Most common reliability
            most_common_reliability = max(set(source_data['reliabilities']), key=source_data['reliabilities'].count)

            by_source_list.append({
                'source': source_data['source'],
                'display_name': LineageVisualizer._format_source_name(source_data['source']),
                'count': source_data['count'],
                'avg_confidence': round(avg_confidence, 3),
                'reliability': most_common_reliability
            })

        # Sort by count
        by_source_list.sort(key=lambda x: x['count'], reverse=True)

        return {
            'overview': {
                'total_fields': summary.total_fields,
                'quality_score': summary.data_quality_score,
                'high_quality_pct': round(high_quality_pct, 1),
                'fresh_data_pct': round(fresh_data_pct, 1),
                'avg_confidence': summary.average_confidence,
                'cache_hit_rate': summary.cache_hit_rate
            },
            'by_source': by_source_list,
            'freshness_gauge': summary.freshness_breakdown,
            'reliability_breakdown': summary.reliability_breakdown,
            'timestamp': summary.timestamp.isoformat()
        }

    @staticmethod
    def create_field_detail_view(
        tracker: DataLineageTracker,
        field_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create detailed view for a specific field's lineage

        Returns:
            {
                'field': 'pe_ratio',
                'value': 25.3,
                'source': {
                    'primary': 'calculated',
                    'secondary': ['price', 'eps'],
                    'reliability': 'high'
                },
                'timeline': {
                    'fetched_at': '2025-10-07T12:00:00Z',
                    'data_timestamp': '2025-10-07T11:58:00Z',
                    'age_minutes': 2
                },
                'transformations': ['P/E = price / EPS'],
                'dependencies': [
                    {
                        'field': 'price',
                        'value': 150.0,
                        'source': 'yfinance'
                    },
                    ...
                ],
                'quality': {
                    'confidence': 0.95,
                    'reliability': 'high',
                    'freshness': 'realtime',
                    'validation_passed': true
                },
                'citation': 'Calculated from Yahoo Finance data'
            }
        """
        record = tracker.get_lineage(field_name)
        if not record:
            return None

        # Calculate age
        age = datetime.utcnow() - record.metadata.data_timestamp
        age_minutes = age.total_seconds() / 60

        # Get dependency details
        dependencies = []
        for dep_field in record.metadata.upstream_dependencies:
            dep_record = tracker.get_lineage(dep_field)
            if dep_record:
                dependencies.append({
                    'field': dep_field,
                    'value': str(dep_record.value)[:50] if dep_record.value is not None else None,
                    'source': dep_record.metadata.source.value,
                    'reliability': dep_record.metadata.reliability.value
                })

        return {
            'field': field_name,
            'value': record.value,
            'source': {
                'primary': record.metadata.source.value,
                'primary_display': LineageVisualizer._format_source_name(record.metadata.source.value),
                'secondary': [s.value for s in record.metadata.secondary_sources],
                'reliability': record.metadata.reliability.value,
                'cache_hit': record.metadata.cache_hit
            },
            'timeline': {
                'fetched_at': record.metadata.fetched_at.isoformat(),
                'data_timestamp': record.metadata.data_timestamp.isoformat(),
                'age_seconds': age.total_seconds(),
                'age_minutes': round(age_minutes, 1),
                'age_human': LineageVisualizer._format_age(age)
            },
            'transformations': record.metadata.transformation_applied,
            'dependencies': dependencies,
            'quality': {
                'confidence': record.metadata.confidence,
                'reliability': record.metadata.reliability.value,
                'freshness': record.metadata.freshness.value,
                'validation_passed': record.validation_passed,
                'warnings': record.validation_warnings
            },
            'citation': record.metadata.citation,
            'source_url': record.metadata.source_url
        }

    @staticmethod
    def _format_source_name(source: str) -> str:
        """Format source name for display"""
        name_map = {
            'yfinance': 'Yahoo Finance',
            'alpha_vantage': 'Alpha Vantage',
            'tavily_search': 'Tavily Search',
            'tavily_qna': 'Tavily Q&A',
            'tavily_extract': 'Tavily Extract',
            'tavily_context': 'Tavily Context',
            'llm_gpt4': 'GPT-4',
            'llm_gpt4_turbo': 'GPT-4 Turbo',
            'calculated': 'Calculated',
            'cached': 'Cache',
            'fallback': 'Fallback',
            'user_input': 'User Input',
            'internal': 'Internal'
        }
        return name_map.get(source, source.replace('_', ' ').title())

    @staticmethod
    def _format_field_name(field: str) -> str:
        """Format field name for display"""
        return field.replace('_', ' ').title()

    @staticmethod
    def _format_age(age: timedelta) -> str:
        """Format age as human-readable string"""
        seconds = age.total_seconds()

        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)} minutes ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)} hours ago"
        else:
            return f"{int(seconds / 86400)} days ago"


def create_lineage_visualization_suite(tracker: DataLineageTracker) -> Dict[str, Any]:
    """
    Create complete visualization suite for frontend

    Returns:
        {
            'timeline': {...},
            'flow_diagram': {...},
            'quality_dashboard': {...},
            'metadata': {...}
        }
    """
    visualizer = LineageVisualizer()

    return {
        'timeline': visualizer.create_timeline_view(tracker),
        'flow_diagram': visualizer.create_source_flow_diagram(tracker),
        'quality_dashboard': visualizer.create_quality_dashboard(tracker),
        'metadata': {
            'generated_at': datetime.utcnow().isoformat(),
            'total_fields': len(tracker.get_all_lineages())
        }
    }
