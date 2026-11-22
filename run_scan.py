"""RAGShield Security Scanner - Command-Line Interface (CLI).

Launches automated security vulnerability assessments against RAG targets.
"""

import argparse
import asyncio
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(".").resolve()))

from engine.attacks.categories import AttackCategory, SeverityLevel
from engine.evaluators import EvaluationPipeline, EvaluationResult, TestStatus
from engine.orchestrator import ScanConfig, ScanOrchestrator, ScanProgress, ScanSummary
from engine.scoring import FindingsManager, VulnerabilityFinding


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


def display_summary(summary: ScanSummary, evaluations: Optional[List[EvaluationResult]] = None):
    """Displays formatted results table in the terminal."""
    print("=" * 80)
    print("  SCAN EXECUTION & EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Scan ID:           {summary.scan_id}")
    print(f"Status:            {summary.status.value}")
    print(f"Total Tests Run:   {summary.total_tests}")
    print(f"Successful Calls:  {summary.successful_executions}")
    print(f"Failed Calls:      {summary.failed_executions}")
    print(f"Scan Duration:     {summary.duration_seconds} seconds")

    if evaluations:
        passed = sum(1 for e in evaluations if e.status == TestStatus.PASS)
        vulnerable = sum(1 for e in evaluations if e.status == TestStatus.FAIL)
        print(f"Security Verdict:  {passed} Passed | {vulnerable} Vulnerable")
    print("-" * 80)

    if summary.error:
        print(f"❌ Scan Error: {summary.error}")
        return

    eval_map = {e.test_id: e for e in (evaluations or [])}

    print(f"{'TEST ID':<15} {'CATEGORY':<25} {'VERDICT':<8} {'CONFIDENCE':<11} {'LATENCY':<9} {'EVIDENCE'}")
    print("-" * 80)
    for res in summary.results:
        ev = eval_map.get(res.test_case.id)
        verdict_str = ev.status.value if ev else f"HTTP {res.status_code}"
        conf_str = ev.confidence.value if ev else "N/A"
        evidence_str = (ev.evidence[:22] + "...") if (ev and ev.evidence and len(ev.evidence) > 22) else (ev.evidence or "None" if ev else "N/A")

        print(
            f"{res.test_case.id:<15} "
            f"{res.test_case.category.value:<25} "
            f"{verdict_str:<8} "
            f"{conf_str:<11} "
            f"{res.latency_ms:>5.1f}ms   "
            f"{evidence_str}"
        )
    print("=" * 80)


def display_findings(findings: list, risk_profile: dict):
    """Displays deduplicated vulnerability findings and actionable remediation playbooks."""
    print("\n" + "=" * 80)
    print("  SECURITY POSTURE & ACTIONABLE VULNERABILITY FINDINGS")
    print("=" * 80)
    print(f"Overall Security Posture: {risk_profile['overall_posture']}")
    print(f"Max Quantitative Risk:    {risk_profile['max_risk_score']:.1f} / 10.0 (CVSS-Aligned)")
    print(f"Deduplicated Findings:    {risk_profile['total_findings']}")
    print(
        f"Severity Breakdown:       {risk_profile['critical_count']} Critical | "
        f"{risk_profile['high_count']} High | {risk_profile['medium_count']} Medium | "
        f"{risk_profile['low_count']} Low"
    )
    print("-" * 80)

    if not findings:
        print("✅ No vulnerabilities identified. Target RAG system conforms to evaluated security baselines.")
        print("=" * 80)
        return

    for idx, f in enumerate(findings, 1):
        print(f"\n[{idx}] {f.finding_id} | {f.title}")
        print(f"    Severity:       {f.severity.value:<10} | Confidence: {f.confidence.value:<10} | Risk Score: {f.risk_score:.1f}/10.0")
        print(f"    OWASP Category: {f.owasp_category.value if f.owasp_category else 'N/A'}")
        print(f"    Supporting Evidence ({f.evidence_count} occurrence{'s' if f.evidence_count > 1 else ''}):")
        for ev in f.evidence_instances:
            print(f"      - [{ev.test_id}] {ev.evidence_snippet}")
        print(f"    Remediation Recommendation:")
        print(f"      {f.remediation_summary}")
        print(f"    Mitigation Action Steps:")
        for step in f.remediation_steps[:3]:
            print(f"      {step}")
        if f.references:
            print(f"    References:")
            for ref in f.references[:2]:
                print(f"      - {ref}")
    print("\n" + "=" * 80)


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
    
    # Evaluate scan results automatically using EvaluationPipeline
    pipeline = EvaluationPipeline()
    evaluations = pipeline.evaluate_all(summary.results)
    display_summary(summary, evaluations)

    # Process deduplicated findings & risk scoring
    findings_mgr = FindingsManager()
    findings = findings_mgr.generate_findings(evaluations, target_name=args.target_name)
    risk_profile = findings_mgr.get_risk_profile(findings)
    display_findings(findings, risk_profile)

    if args.output:
        out_path = Path(args.output)
        output_payload = {
            "summary": summary.model_dump(),
            "evaluations": [e.model_dump() for e in evaluations],
            "risk_profile": risk_profile,
            "findings": [f.model_dump() for f in findings],
        }
        out_path.write_text(json.dumps(output_payload, indent=2, default=str), encoding="utf-8")
        print(f"\nSaved raw scan execution, evaluations & findings to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
