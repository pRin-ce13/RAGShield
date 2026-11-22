"""RAGShield Security Scanner - Command-Line Interface (CLI).

Launches automated security vulnerability assessments against RAG targets.
"""

import argparse
import asyncio
import json
from pathlib import Path
import sys
from typing import Optional

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(".").resolve()))

from engine.attacks.categories import AttackCategory, SeverityLevel
from engine.orchestrator import ScanConfig, ScanOrchestrator, ScanProgress, ScanSummary


def print_banner():
    banner = """
================================================================================
  🛡️  RAGShield -- Automated RAG Security Assessment Scanner
================================================================================
"""
    print(banner)


def progress_reporter(progress: ScanProgress):
    """Outputs real-time scan progress to the console."""
    bar_width = 30
    filled = int(bar_width * (progress.percentage / 100))
    bar = "█" * filled + "░" * (bar_width - filled)
    print(
        f"\r[{bar}] {progress.percentage:5.1f}% | "
        f"Completed: {progress.completed_tests}/{progress.total_tests} | "
        f"Current: {progress.current_test_id:<15}",
        end="",
        flush=True
    )


async def execute_scan(args) -> ScanSummary:
    """Configures and runs the scan orchestrator."""
    categories = None
    if args.category:
        categories = [AttackCategory(args.category)]

    severities = None
    if args.severity:
        severities = [SeverityLevel(args.severity.upper())]

    config = ScanConfig(
        target_name=args.target_name,
        target_url=args.url,
        api_key=args.api_key,
        allow_local=True,
        categories=categories,
        severities=severities,
        max_concurrency=args.concurrency,
        timeout_seconds=args.timeout
    )

    orchestrator = ScanOrchestrator(config=config)
    
    print(f"Target URL:        {config.target_url}")
    print(f"Target Name:       {config.target_name}")
    print(f"Max Concurrency:   {config.max_concurrency}")
    print(f"Filter Category:   {args.category or 'All Categories'}")
    print(f"Filter Severity:   {args.severity or 'All Severities'}")
    print("-" * 80)
    print("Initiating pre-flight verification and test execution...\n")

    summary = await orchestrator.run_scan(on_progress=progress_reporter)
    print("\n")  # Newline after progress bar
    return summary


def display_summary(summary: ScanSummary):
    """Displays formatted results table in the terminal."""
    print("=" * 80)
    print("  SCAN EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Scan ID:           {summary.scan_id}")
    print(f"Status:            {summary.status.value}")
    print(f"Total Tests Run:   {summary.total_tests}")
    print(f"Successful Calls:  {summary.successful_executions}")
    print(f"Failed Calls:      {summary.failed_executions}")
    print(f"Scan Duration:     {summary.duration_seconds} seconds")
    print("-" * 80)

    if summary.error:
        print(f"❌ Scan Error: {summary.error}")
        return

    print(f"{'TEST ID':<15} {'CATEGORY':<28} {'STATUS':<8} {'LATENCY':<10} {'SOURCES'}")
    print("-" * 80)
    for res in summary.results:
        status_str = f"HTTP {res.status_code}"
        sources_str = ", ".join(res.sources) if res.sources else "None cited"
        print(
            f"{res.test_case.id:<15} "
            f"{res.test_case.category.value:<28} "
            f"{status_str:<8} "
            f"{res.latency_ms:>6.1f}ms   "
            f"{sources_str}"
        )
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="RAGShield Security Assessment Scanner")
    parser.add_argument("--url", default="http://127.0.0.1:8001", help="Target RAG API base URL")
    parser.add_argument("--target-name", default="Demo RAG Target", help="Name identifier for target")
    parser.add_argument("--api-key", default="demo_synthetic_insecure_key_for_testing", help="Target API key")
    parser.add_argument("--category", choices=[c.value for c in AttackCategory], help="Filter by vulnerability category")
    parser.add_argument("--severity", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"], help="Filter by CVSS severity")
    parser.add_argument("--concurrency", type=int, default=3, help="Max simultaneous requests")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds")
    parser.add_argument("--output", help="Optional JSON file path to save raw execution results")

    args = parser.parse_args()
    print_banner()

    summary = asyncio.run(execute_scan(args))
    display_summary(summary)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
        print(f"\nSaved raw scan execution results to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
