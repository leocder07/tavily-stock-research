"""
Export Service - Generate PDF, CSV, and JSON exports of analysis results

This service handles export functionality for stock analysis reports:
1. JSON export - Full structured data
2. CSV export - Spreadsheet-compatible format
3. PDF export - Professional investment report with charts
"""

import csv
import json
import io
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting analysis results in various formats."""

    def __init__(self):
        self.supported_formats = ['json', 'csv', 'pdf']

    async def export_to_json(self, analysis_data: Dict[str, Any]) -> str:
        """
        Export analysis data to JSON format.

        Args:
            analysis_data: Complete analysis results

        Returns:
            JSON string with formatted data
        """
        try:
            # Structure the export data
            export_data = {
                'metadata': {
                    'analysis_id': analysis_data.get('analysis_id', 'N/A'),
                    'symbol': analysis_data.get('symbol', 'N/A'),
                    'generated_at': datetime.utcnow().isoformat(),
                    'format_version': '1.0'
                },
                'executive_summary': analysis_data.get('executive_summary', {}),
                'recommendation': analysis_data.get('recommendation', {}),
                'analyses': {
                    'valuation': analysis_data.get('valuation_analysis', {}),
                    'macro_economics': analysis_data.get('macro_analysis', {}),
                    'insider_activity': analysis_data.get('insider_analysis', {}),
                    'fundamental': analysis_data.get('fundamental_analysis', {}),
                    'technical': analysis_data.get('technical_analysis', {}),
                    'sentiment': analysis_data.get('sentiment_analysis', {}),
                    'risk': analysis_data.get('risk_analysis', {}),
                    'peer_comparison': analysis_data.get('peer_analysis', {})
                },
                'market_data': analysis_data.get('market_data', {}),
                'citations': analysis_data.get('citations', [])
            }

            # Convert to formatted JSON
            json_output = json.dumps(export_data, indent=2, default=str)

            logger.info(f"Successfully exported analysis to JSON format")
            return json_output

        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise

    async def export_to_csv(self, analysis_data: Dict[str, Any]) -> str:
        """
        Export analysis data to CSV format.

        Args:
            analysis_data: Complete analysis results

        Returns:
            CSV string with tabular data
        """
        try:
            output = io.StringIO()
            writer = csv.writer(output)

            # Header section
            writer.writerow(['Stock Analysis Report'])
            writer.writerow(['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')])
            writer.writerow(['Symbol:', analysis_data.get('symbol', 'N/A')])
            writer.writerow(['Analysis ID:', analysis_data.get('analysis_id', 'N/A')])
            writer.writerow([])

            # Executive Summary
            writer.writerow(['=== EXECUTIVE SUMMARY ==='])
            exec_summary = analysis_data.get('executive_summary', {})
            if exec_summary:
                writer.writerow(['Recommendation:', exec_summary.get('recommendation', 'N/A')])
                writer.writerow(['Confidence Score:', exec_summary.get('confidence_score', 'N/A')])
                writer.writerow(['Investment Thesis:', exec_summary.get('investment_thesis', 'N/A')])
            writer.writerow([])

            # Valuation Analysis
            valuation = analysis_data.get('valuation_analysis', {})
            if valuation:
                writer.writerow(['=== VALUATION ANALYSIS ==='])
                writer.writerow(['Intrinsic Value (DCF):', valuation.get('recommended_fair_value', 'N/A')])
                writer.writerow(['Current Price:', valuation.get('current_price', 'N/A')])
                writer.writerow(['Margin of Safety (%):', valuation.get('margin_of_safety', 'N/A')])
                writer.writerow(['Recommendation:', valuation.get('investment_recommendation', 'N/A')])

                scenarios = valuation.get('valuation_methods', {}).get('scenarios', {})
                if scenarios:
                    writer.writerow(['Bull Case Value:', scenarios.get('bull_case', {}).get('intrinsic_value', 'N/A')])
                    writer.writerow(['Base Case Value:', scenarios.get('base_case', {}).get('intrinsic_value', 'N/A')])
                    writer.writerow(['Bear Case Value:', scenarios.get('bear_case', {}).get('intrinsic_value', 'N/A')])
                writer.writerow([])

            # Macro Economics
            macro = analysis_data.get('macro_analysis', {})
            if macro:
                writer.writerow(['=== MACROECONOMIC ENVIRONMENT ==='])
                writer.writerow(['Macro Rating:', macro.get('macro_environment_rating', 'N/A')])

                fed = macro.get('key_macro_factors', {}).get('fed_policy', {})
                writer.writerow(['Fed Funds Rate:', fed.get('current_fed_rate', 'N/A')])
                writer.writerow(['Policy Stance:', fed.get('policy_stance', 'N/A')])

                gdp = macro.get('key_macro_factors', {}).get('gdp_growth', {})
                writer.writerow(['GDP Growth:', gdp.get('current_gdp_growth', 'N/A')])

                inflation = macro.get('key_macro_factors', {}).get('inflation', {})
                writer.writerow(['CPI Inflation:', inflation.get('current_cpi', 'N/A')])
                writer.writerow([])

            # Insider Activity & Smart Money
            insider = analysis_data.get('insider_analysis', {})
            if insider:
                writer.writerow(['=== SMART MONEY & INSIDER ACTIVITY ==='])
                writer.writerow(['Smart Money Sentiment:', insider.get('smart_money_sentiment', 'N/A')])
                writer.writerow(['Smart Money Score:', insider.get('smart_money_analysis', {}).get('smart_money_score', 'N/A')])

                insider_act = insider.get('insider_activity', {})
                writer.writerow(['Insider Sentiment:', insider_act.get('insider_sentiment', 'N/A')])

                inst = insider.get('institutional_ownership', {})
                writer.writerow(['Institutional Ownership (%):', inst.get('institutional_ownership_pct', 'N/A')])
                writer.writerow(['Ownership Trend:', inst.get('ownership_trend', 'N/A')])

                analyst = insider.get('analyst_ratings', {})
                writer.writerow(['Analyst Rating:', analyst.get('analyst_rating', 'N/A')])
                writer.writerow(['Price Target:', analyst.get('consensus_price_target', 'N/A')])
                writer.writerow(['Upside to Target (%):', analyst.get('upside_to_target', 'N/A')])
                writer.writerow([])

            # Fundamental Analysis
            fundamental = analysis_data.get('fundamental_analysis', {})
            if fundamental:
                writer.writerow(['=== FUNDAMENTAL ANALYSIS ==='])
                metrics = fundamental.get('financial_metrics', {})
                if metrics:
                    writer.writerow(['Revenue:', metrics.get('revenue', 'N/A')])
                    writer.writerow(['Net Income:', metrics.get('net_income', 'N/A')])
                    writer.writerow(['EPS:', metrics.get('eps', 'N/A')])
                    writer.writerow(['P/E Ratio:', metrics.get('pe_ratio', 'N/A')])
                    writer.writerow(['ROE (%):', metrics.get('roe', 'N/A')])
                writer.writerow([])

            # Technical Analysis
            technical = analysis_data.get('technical_analysis', {})
            if technical:
                writer.writerow(['=== TECHNICAL ANALYSIS ==='])
                signals = technical.get('trading_signals', {})
                if signals:
                    writer.writerow(['Overall Signal:', signals.get('overall', 'N/A')])
                    writer.writerow(['Trend:', signals.get('trend', 'N/A')])
                    writer.writerow(['Momentum:', signals.get('momentum', 'N/A')])
                writer.writerow([])

            # Risk Assessment
            risk = analysis_data.get('risk_analysis', {})
            if risk:
                writer.writerow(['=== RISK ASSESSMENT ==='])
                writer.writerow(['Overall Risk Level:', risk.get('overall_risk_level', 'N/A')])
                writer.writerow(['Volatility:', risk.get('volatility', 'N/A')])
                writer.writerow(['Beta:', risk.get('beta', 'N/A')])
                writer.writerow([])

            # Citations
            citations = analysis_data.get('citations', [])
            if citations:
                writer.writerow(['=== DATA SOURCES & CITATIONS ==='])
                writer.writerow(['#', 'Title', 'URL', 'Agent', 'Relevance Score'])
                for idx, citation in enumerate(citations[:20], 1):  # Limit to 20
                    writer.writerow([
                        idx,
                        citation.get('title', 'N/A'),
                        citation.get('url', 'N/A'),
                        citation.get('agent_id', 'N/A'),
                        citation.get('relevance_score', 'N/A')
                    ])

            csv_output = output.getvalue()
            output.close()

            logger.info(f"Successfully exported analysis to CSV format")
            return csv_output

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise

    async def export_to_pdf(self, analysis_data: Dict[str, Any]) -> bytes:
        """
        Export analysis data to PDF format.

        Args:
            analysis_data: Complete analysis results

        Returns:
            PDF bytes

        Note: This is a simplified implementation using reportlab.
        For production, consider using more advanced PDF libraries like WeasyPrint.
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.platypus import Image as RLImage

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)

            # Container for PDF elements
            elements = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=1  # Center
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#5E72E4'),
                spaceAfter=12,
                spaceBefore=12
            )

            # Title Page
            symbol = analysis_data.get('symbol', 'N/A')
            elements.append(Paragraph(f"Stock Analysis Report: {symbol}", title_style))
            elements.append(Spacer(1, 12))

            # Metadata
            metadata_data = [
                ['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')],
                ['Analysis ID:', analysis_data.get('analysis_id', 'N/A')],
                ['Symbol:', symbol]
            ]
            metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
            metadata_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(metadata_table)
            elements.append(Spacer(1, 24))

            # Executive Summary
            elements.append(Paragraph("Executive Summary", heading_style))
            exec_summary = analysis_data.get('executive_summary', {})
            if exec_summary:
                summary_data = [
                    ['Recommendation:', exec_summary.get('recommendation', 'N/A')],
                    ['Confidence Score:', f"{exec_summary.get('confidence_score', 0)}%"],
                    ['Investment Thesis:', exec_summary.get('investment_thesis', 'N/A')[:200] + '...']
                ]
                summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
                summary_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(summary_table)
            elements.append(Spacer(1, 20))

            # Valuation Analysis
            valuation = analysis_data.get('valuation_analysis', {})
            if valuation:
                elements.append(Paragraph("Valuation Analysis (DCF Model)", heading_style))
                val_data = [
                    ['Metric', 'Value'],
                    ['Intrinsic Value (DCF)', f"${valuation.get('recommended_fair_value', 'N/A')}"],
                    ['Current Price', f"${valuation.get('current_price', 'N/A')}"],
                    ['Margin of Safety', f"{valuation.get('margin_of_safety', 'N/A')}%"],
                    ['Recommendation', valuation.get('investment_recommendation', 'N/A')]
                ]

                scenarios = valuation.get('valuation_methods', {}).get('scenarios', {})
                if scenarios:
                    val_data.extend([
                        ['Bull Case', f"${scenarios.get('bull_case', {}).get('intrinsic_value', 'N/A')}"],
                        ['Base Case', f"${scenarios.get('base_case', {}).get('intrinsic_value', 'N/A')}"],
                        ['Bear Case', f"${scenarios.get('bear_case', {}).get('intrinsic_value', 'N/A')}"]
                    ])

                val_table = Table(val_data, colWidths=[3*inch, 3*inch])
                val_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5E72E4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                elements.append(val_table)
                elements.append(Spacer(1, 20))

            # Macro Economics
            macro = analysis_data.get('macro_analysis', {})
            if macro:
                elements.append(Paragraph("Macroeconomic Environment", heading_style))
                macro_insights = macro.get('key_insights', [])
                for insight in macro_insights[:5]:
                    elements.append(Paragraph(f"• {insight}", styles['Normal']))
                elements.append(Spacer(1, 20))

            # Smart Money & Insider Activity
            insider = analysis_data.get('insider_analysis', {})
            if insider:
                elements.append(Paragraph("Smart Money & Insider Activity", heading_style))
                insider_data = [
                    ['Metric', 'Value'],
                    ['Smart Money Sentiment', insider.get('smart_money_sentiment', 'N/A')],
                    ['Smart Money Score', f"{insider.get('smart_money_analysis', {}).get('smart_money_score', 'N/A')}/10"],
                    ['Analyst Rating', insider.get('analyst_ratings', {}).get('analyst_rating', 'N/A')],
                    ['Price Target', f"${insider.get('analyst_ratings', {}).get('consensus_price_target', 'N/A')}"]
                ]
                insider_table = Table(insider_data, colWidths=[3*inch, 3*inch])
                insider_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5E72E4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                elements.append(insider_table)
                elements.append(Spacer(1, 20))

            # Citations (first 10)
            citations = analysis_data.get('citations', [])
            if citations:
                elements.append(Paragraph("Data Sources & Citations", heading_style))
                for idx, citation in enumerate(citations[:10], 1):
                    citation_text = f"{idx}. {citation.get('title', 'N/A')} ({citation.get('agent_id', 'N/A')})"
                    elements.append(Paragraph(citation_text, styles['Normal']))
                    elements.append(Paragraph(f"   <font size=8>{citation.get('url', 'N/A')}</font>", styles['Normal']))
                    elements.append(Spacer(1, 6))

            # Footer
            elements.append(Spacer(1, 30))
            footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
            elements.append(Paragraph("Generated by Multi-Agent Stock Research System | Powered by Tavily + LangGraph", footer_style))

            # Build PDF
            doc.build(elements)

            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"Successfully exported analysis to PDF format")
            return pdf_bytes

        except ImportError as e:
            logger.error(f"ReportLab not installed: {e}")
            raise ImportError("Please install reportlab: pip install reportlab")
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            raise


# Singleton instance
export_service = ExportService()
