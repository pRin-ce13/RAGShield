"""Attack Registry and Dataset Loader for RAGShield.

Discovers, validates, indexes, and filters security test cases from versioned datasets.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .categories import AttackCategory, OWASPCategory, SeverityLevel
from .schema import TestCase, TestSuite


class AttackRegistry:
    """Manages the catalog of loaded, validated security test cases."""

    def __init__(self, suites_dir: Optional[Union[str, Path, List[Union[str, Path]]]] = None):
        """Initializes the registry and automatically loads all test suites.
        
        Args:
            suites_dir: Optional path or list of paths. If None, discovers datasets/test_cases.
        """
        if suites_dir is None:
            # Default to scanning datasets/test_cases recursively (v1, v2, etc.)
            base_dir = Path("datasets/test_cases")
            if base_dir.exists():
                self.suites_dirs = [base_dir]
            else:
                self.suites_dirs = [Path("datasets/test_cases/v1")]
        elif isinstance(suites_dir, (str, Path)):
            self.suites_dirs = [Path(suites_dir)]
        else:
            self.suites_dirs = [Path(p) for p in suites_dir]

        self._test_cases: Dict[str, TestCase] = {}
        self._suites: Dict[str, TestSuite] = {}
        self.load_suites()

    def load_suites(self) -> int:
        """Discovers and parses all .json test suite files in the suites directories.
        
        Returns:
            Total count of loaded test cases.
        """
        self._test_cases.clear()
        self._suites.clear()

        all_json_files: List[Path] = []
        for s_dir in self.suites_dirs:
            if s_dir.exists() and s_dir.is_dir():
                # Recursively discover all JSON files
                all_json_files.extend(s_dir.rglob("*.json"))

        for json_path in sorted(set(all_json_files)):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Skip files that are not valid test suites
                if not isinstance(data, dict) or "suite_id" not in data or "test_cases" not in data:
                    continue

                suite = TestSuite.model_validate(data)
                self._suites[suite.suite_id] = suite

                for test in suite.test_cases:
                    if test.id in self._test_cases:
                        raise ValueError(f"Duplicate test ID '{test.id}' detected in file: {json_path}")
                    self._test_cases[test.id] = test
            except Exception as e:
                # Raise if it was meant to be a test suite
                if "suite_id" in str(e) or isinstance(e, ValueError):
                    raise
                continue

        return len(self._test_cases)

    def get(self, test_id: str) -> Optional[TestCase]:
        """Retrieves a single test case by its unique ID."""
        return self._test_cases.get(test_id.strip())

    def list_all(self) -> List[TestCase]:
        """Returns all loaded test cases."""
        return list(self._test_cases.values())

    def filter_by_category(self, category: Union[str, AttackCategory]) -> List[TestCase]:
        """Filters test cases by vulnerability category."""
        cat_val = category.value if isinstance(category, AttackCategory) else str(category)
        return [t for t in self._test_cases.values() if t.category.value == cat_val]

    def filter_by_severity(self, severity: Union[str, SeverityLevel]) -> List[TestCase]:
        """Filters test cases by CVSS severity rating."""
        sev_val = severity.value if isinstance(severity, SeverityLevel) else str(severity).upper()
        return [t for t in self._test_cases.values() if t.severity.value == sev_val]

    def filter_by_owasp(self, owasp_category: Union[str, OWASPCategory]) -> List[TestCase]:
        """Filters test cases by OWASP LLM Top 10 category."""
        owasp_val = owasp_category.value if isinstance(owasp_category, OWASPCategory) else str(owasp_category)
        return [t for t in self._test_cases.values() if t.owasp_category and t.owasp_category.value == owasp_val]

    def filter_by_tag(self, tag: str) -> List[TestCase]:
        """Filters test cases matching a specific tag keyword."""
        tag_lower = tag.strip().lower()
        return [t for t in self._test_cases.values() if any(tag_lower == t_tag.lower() for t_tag in t.tags)]

    def get_summary(self) -> Dict[str, Any]:
        """Generates statistical summary of the test catalog."""
        categories: Dict[str, int] = {}
        severities: Dict[str, int] = {}
        owasp_coverage: Dict[str, int] = {}

        for t in self._test_cases.values():
            cat = t.category.value
            categories[cat] = categories.get(cat, 0) + 1

            sev = t.severity.value
            severities[sev] = severities.get(sev, 0) + 1

            if t.owasp_category:
                ow = t.owasp_category.value
                owasp_coverage[ow] = owasp_coverage.get(ow, 0) + 1

        return {
            "total_test_cases": len(self._test_cases),
            "suites_loaded": len(self._suites),
            "breakdown_by_category": categories,
            "breakdown_by_severity": severities,
            "owasp_coverage": owasp_coverage
        }
