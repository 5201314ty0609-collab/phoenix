"""
Tests for PHOENIX AIOS LangChain integration.
"""

import unittest
from typing import Any, Dict, List


class TestResult:
    """Test result helper."""

    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.message}"


def run_tests(test_class: type) -> List[TestResult]:
    """
    Run all tests in a test class.

    Args:
        test_class: Test class to run

    Returns:
        List of TestResult
    """
    results = []
    suite = unittest.TestLoader().loadTestsFromTestCase(test_class)

    for test in suite:
        try:
            test.debug()
            results.append(TestResult(
                name=str(test),
                passed=True,
            ))
        except AssertionError as e:
            results.append(TestResult(
                name=str(test),
                passed=False,
                message=str(e),
            ))
        except Exception as e:
            results.append(TestResult(
                name=str(test),
                passed=False,
                message=f"Error: {e}",
            ))

    return results
