"""
Tests for chain module.
"""

import unittest
from typing import Any, Dict

from ..chains import (
    Chain,
    ChainStep,
    LCELChain,
    LCELStep,
    SequentialChain,
    ParallelChain,
    ConditionalChain,
    Condition,
)
from ..core import ExecutionResult


class TestChainStep(unittest.TestCase):
    """Test ChainStep."""

    def test_execute_success(self):
        """Test successful execution."""
        step = ChainStep(
            name="test",
            function=lambda ctx: ctx["input"] * 2,
        )
        result = step.execute({"input": 5})
        self.assertEqual(result.status.value, "completed")
        self.assertEqual(result.data, 10)

    def test_execute_error(self):
        """Test execution with error."""
        step = ChainStep(
            name="test",
            function=lambda ctx: 1 / 0,
        )
        result = step.execute({"input": 5})
        self.assertEqual(result.status.value, "failed")
        self.assertIn("division by zero", result.error)


class TestChain(unittest.TestCase):
    """Test Chain."""

    def test_add_step(self):
        """Test adding steps."""
        chain = Chain("test")
        step = ChainStep(name="step1", function=lambda ctx: ctx["input"])
        chain.add_step(step)
        self.assertEqual(len(chain.steps), 1)

    def test_remove_step(self):
        """Test removing steps."""
        chain = Chain("test")
        step = ChainStep(name="step1", function=lambda ctx: ctx["input"])
        chain.add_step(step)
        self.assertTrue(chain.remove_step("step1"))
        self.assertEqual(len(chain.steps), 0)

    def test_invoke(self):
        """Test chain execution."""
        chain = Chain("test")
        chain.add_step(ChainStep(
            name="double",
            function=lambda ctx: ctx["input"] * 2,
        ))
        result = chain.invoke({"input": 5})
        self.assertTrue(result.success)
        self.assertEqual(result.data, 10)


class TestLCELChain(unittest.TestCase):
    """Test LCELChain."""

    def test_pipe_operator(self):
        """Test pipe operator."""
        chain = (
            LCELChain("test")
            | LCELStep("double", lambda x: x * 2)
            | LCELStep("add_one", lambda x: x + 1)
        )
        result = chain.invoke(5)
        self.assertTrue(result.success)
        self.assertEqual(result.data, 11)

    def test_pipe_callable(self):
        """Test pipe with callable."""
        chain = (
            LCELChain("test")
            | (lambda x: x * 2)
            | (lambda x: x + 1)
        )
        result = chain.invoke(5)
        self.assertTrue(result.success)
        self.assertEqual(result.data, 11)


class TestSequentialChain(unittest.TestCase):
    """Test SequentialChain."""

    def test_sequential_execution(self):
        """Test sequential execution."""
        chain = SequentialChain("test")
        chain.add_step(ChainStep(
            name="double",
            function=lambda ctx: ctx["input"] * 2,
        ))
        chain.add_step(ChainStep(
            name="add_one",
            function=lambda ctx: ctx["double"] + 1,
        ))
        result = chain.invoke({"input": 5})
        self.assertTrue(result.success)
        self.assertEqual(result.data, 11)

    def test_add_transform(self):
        """Test add_transform."""
        chain = SequentialChain("test")
        chain.add_transform("double", lambda x: x * 2)
        chain.add_transform("add_one", lambda x: x + 1)
        result = chain.invoke({"input": 5})
        self.assertTrue(result.success)


class TestParallelChain(unittest.TestCase):
    """Test ParallelChain."""

    def test_parallel_execution(self):
        """Test parallel execution."""
        chain = ParallelChain("test")
        chain.add_step(ChainStep(
            name="double",
            function=lambda ctx: ctx["input"] * 2,
        ))
        chain.add_step(ChainStep(
            name="triple",
            function=lambda ctx: ctx["input"] * 3,
        ))
        result = chain.invoke({"input": 5})
        self.assertTrue(result.success)
        self.assertIn("double", result.data)
        self.assertIn("triple", result.data)
        self.assertEqual(result.data["double"], 10)
        self.assertEqual(result.data["triple"], 15)


class TestConditionalChain(unittest.TestCase):
    """Test ConditionalChain."""

    def test_conditional_execution(self):
        """Test conditional execution."""
        chain = ConditionalChain("test")

        chain.add_condition(Condition(
            name="is_positive",
            predicate=lambda ctx: ctx["input"] > 0,
            chain=SequentialChain("positive").add_step(
                ChainStep(name="double", function=lambda ctx: ctx["input"] * 2)
            ),
            priority=10,
        ))

        chain.add_condition(Condition(
            name="is_negative",
            predicate=lambda ctx: ctx["input"] < 0,
            chain=SequentialChain("negative").add_step(
                ChainStep(name="negate", function=lambda ctx: -ctx["input"])
            ),
            priority=5,
        ))

        result = chain.invoke({"input": 5})
        self.assertTrue(result.success)
        self.assertEqual(result.data, 10)

    def test_default_chain(self):
        """Test default chain."""
        chain = ConditionalChain("test")

        default = SequentialChain("default")
        default.add_step(ChainStep(
            name="zero",
            function=lambda ctx: 0,
        ))
        chain.set_default(default)

        result = chain.invoke({"input": 0})
        self.assertTrue(result.success)
        self.assertEqual(result.data, 0)


if __name__ == "__main__":
    unittest.main()
