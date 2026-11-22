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

    def __init__(self, suites_dir: Union[str, Path] = "datasets/test_cases/v1"):
        """Initializes the registry and automatically loads all test suites from the specified directory.
        
        Args:
            suites_dir: Path to the directory containing JSON test suites.
        """
        self.suites_dir = Path(suites_dir)
        self._test_cases: Dict[str, TestCase] = {}
        self._suites: Dict[str, TestSuite] = {}
        self.load_suites()

    def load_suites(self) -> int:
        """Discovers and parses all .json test suite files in the suites directory.
        
        Returns:
            Total count of loaded test cases.
        """
        self._test_cases.clear()
        self._suites.clear()

        if not self.suites_dir.exists() or not self.suites_dir.is_dir():
            raise FileNotFoundError(f"Test suites directory not found: {self.suites_dir}")

        for json_path in sorted(self.suites_dir.glob("*.json")):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            suite = TestSuite.model_validate(data)
            self._suites[suite.suite_id] = suite

            for test in suite.test_cases:
                if test.id in self._test_cases:
                    raise ValueError(f"Duplicate test ID '{test.id}' detected in file: {json_path}")
                self._test_cases[test.id] = test

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
