"""
Tests for the PHOENIX AIOS LangGraph framework.
"""

import unittest
from .test_state import TestAgentState, TestStateReducer
from .test_graph import TestStateGraph, TestCompiledGraph
from .test_router import TestConditionalRouter, TestRoutingStrategies
from .test_checkpoint import TestCheckpointManager
from .test_parallel import TestParallelExecutor, TestSend


def suite() -> unittest.TestSuite:
    """Create test suite.

    Returns:
        Test suite with all tests.
    """
    suite = unittest.TestSuite()

    # State tests
    suite.addTest(unittest.makeSuite(TestAgentState))
    suite.addTest(unittest.makeSuite(TestStateReducer))

    # Graph tests
    suite.addTest(unittest.makeSuite(TestStateGraph))
    suite.addTest(unittest.makeSuite(TestCompiledGraph))

    # Router tests
    suite.addTest(unittest.makeSuite(TestConditionalRouter))
    suite.addTest(unittest.makeSuite(TestRoutingStrategies))

    # Checkpoint tests
    suite.addTest(unittest.makeSuite(TestCheckpointManager))

    # Parallel tests
    suite.addTest(unittest.makeSuite(TestParallelExecutor))
    suite.addTest(unittest.makeSuite(TestSend))

    return suite


if __name__ == "__main__":
    unittest.main(defaultTest="suite")
