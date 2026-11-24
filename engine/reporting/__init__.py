"""RAGShield Reporting and Security Assessment Artifact Engine.

Provides JSON and PDF audit report generation, OWASP compliance matrices,
and regression comparison diffing between security scans.
"""

from .json_reporter import build_security_report, export_json_report
from .pdf_reporter import generate_pdf_report
from .diff import compare_scans, ScanComparisonResult, FindingDiffStatus

__all__ = [
    "build_security_report",
    "export_json_report",
    "generate_pdf_report",
    "compare_scans",
    "ScanComparisonResult",
    "FindingDiffStatus",
]
