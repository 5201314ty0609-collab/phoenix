"""
Tests for routing in the PHOENIX AIOS LangGraph framework.
"""

import unittest

from ..routing.router import (
    ConditionalRouter,
    RoutingDecision,
    RoutingRule,
    MultiTargetRouter,
)
from ..routing.strategies import (
    PriorityRouter,
    RoundRobinRouter,
    RandomRouter,
    WeightedRouter,
    StateBasedRouter,
    CompositeRouter,
)
from ..core.constants import END


class TestConditionalRouter(unittest.TestCase):
    """Tests for ConditionalRouter class."""

    def test_create_router(self):
        """Test creating a router."""
        router = ConditionalRouter()
        self.assertIsNotNone(router)

    def test_add_rule(self):
        """Test adding routing rules."""
        router = ConditionalRouter()
        router.add_rule(
            name="test",
            condition=lambda s: True,
            target="node_a",
            priority=10,
        )
        self.assertEqual(len(router.rules), 1)

    def test_remove_rule(self):
        """Test removing routing rules."""
        router = ConditionalRouter()
        router.add_rule(
            name="test",
            condition=lambda s: True,
            target="node_a",
        )
        self.assertTrue(router.remove_rule("test"))
        self.assertEqual(len(router.rules), 0)

    def test_remove_nonexistent_rule(self):
        """Test removing nonexistent rule."""
        router = ConditionalRouter()
        self.assertFalse(router.remove_rule("nonexistent"))

    def test_route_with_matching_rule(self):
        """Test routing with matching rule."""
        router = ConditionalRouter()
        router.add_rule(
            name="has_error",
            condition=lambda s: s.get("error") is not None,
            target="error_handler",
            priority=10,
        )

        state = {"error": "something went wrong"}
        decision = router.route(state, ["error_handler", "normal"], source="start")

        self.assertEqual(decision.target, "error_handler")
        self.assertIn("rule:", decision.reason)

    def test_route_with_priority(self):
        """Test routing respects priority order."""
        router = ConditionalRouter()
        router.add_rule(
            name="low_priority",
            condition=lambda s: True,
            target="node_a",
            priority=1,
        )
        router.add_rule(
            name="high_priority",
            condition=lambda s: True,
            target="node_b",
            priority=10,
        )

        state = {}
        decision = router.route(state, ["node_a", "node_b"], source="start")

        self.assertEqual(decision.target, "node_b")

    def test_route_default(self):
        """Test routing falls back to default."""
        router = ConditionalRouter(default_target=END)

        state = {}
        decision = router.route(state, ["node_a", "node_b"], source="start")

        self.assertEqual(decision.target, END)
        self.assertEqual(decision.reason, "default")

    def test_route_custom(self):
        """Test custom routing."""
        router = ConditionalRouter()
        router.add_custom_route(
            "start",
            lambda s: "custom_target",
        )

        state = {}
        decision = router.route(state, ["custom_target", "other"], source="start")

        self.assertEqual(decision.target, "custom_target")
        self.assertEqual(decision.reason, "custom_route")

    def test_routing_history(self):
        """Test routing history tracking."""
        router = ConditionalRouter()
        router.add_rule(
            name="test",
            condition=lambda s: True,
            target="node_a",
        )

        router.route({}, ["node_a"], source="s1")
        router.route({}, ["node_a"], source="s2")

        self.assertEqual(len(router.history), 2)

    def test_clear_history(self):
        """Test clearing routing history."""
        router = ConditionalRouter()
        router.add_rule(
            name="test",
            condition=lambda s: True,
            target="node_a",
        )

        router.route({}, ["node_a"], source="s1")
        router.clear_history()

        self.assertEqual(len(router.history), 0)

    def test_get_stats(self):
        """Test getting routing statistics."""
        router = ConditionalRouter()
        router.add_rule(
            name="test",
            condition=lambda s: True,
            target="node_a",
        )

        router.route({}, ["node_a"], source="s1")
        router.route({}, ["node_a"], source="s2")

        stats = router.get_stats()
        self.assertEqual(stats["total_decisions"], 2)


class TestRoutingDecision(unittest.TestCase):
    """Tests for RoutingDecision class."""

    def test_create_decision(self):
        """Test creating a routing decision."""
        decision = RoutingDecision(
            source="start",
            target="node_a",
            reason="test",
            confidence=0.9,
        )
        self.assertEqual(decision.source, "start")
        self.assertEqual(decision.target, "node_a")
        self.assertEqual(decision.reason, "test")
        self.assertEqual(decision.confidence, 0.9)

    def test_is_end(self):
        """Test checking if decision is to END."""
        decision = RoutingDecision(source="s", target=END)
        self.assertTrue(decision.is_end)

        decision = RoutingDecision(source="s", target="node")
        self.assertFalse(decision.is_end)

    def test_with_target(self):
        """Test creating decision with different target."""
        decision = RoutingDecision(source="s", target="old", reason="test")
        new_decision = decision.with_target("new")

        self.assertEqual(new_decision.target, "new")
        self.assertEqual(new_decision.reason, "test")
        self.assertEqual(decision.target, "old")  # Original unchanged


class TestRoutingRule(unittest.TestCase):
    """Tests for RoutingRule class."""

    def test_create_rule(self):
        """Test creating a routing rule."""
        rule = RoutingRule(
            name="test",
            condition=lambda s: True,
            target="node_a",
            priority=10,
        )
        self.assertEqual(rule.name, "test")
        self.assertEqual(rule.priority, 10)

    def test_evaluate_true(self):
        """Test evaluating rule that matches."""
        rule = RoutingRule(
            name="test",
            condition=lambda s: s.get("value", 0) > 0,
            target="node_a",
        )
        self.assertTrue(rule.evaluate({"value": 5}))

    def test_evaluate_false(self):
        """Test evaluating rule that doesn't match."""
        rule = RoutingRule(
            name="test",
            condition=lambda s: s.get("value", 0) > 0,
            target="node_a",
        )
        self.assertFalse(rule.evaluate({"value": -1}))

    def test_evaluate_error(self):
        """Test evaluating rule with error."""
        rule = RoutingRule(
            name="test",
            condition=lambda s: s["missing_key"] > 0,
            target="node_a",
        )
        self.assertFalse(rule.evaluate({}))


class TestMultiTargetRouter(unittest.TestCase):
    """Tests for MultiTargetRouter class."""

    def test_create_router(self):
        """Test creating multi-target router."""
        router = MultiTargetRouter()
        self.assertIsNotNone(router)

    def test_add_parallel_route(self):
        """Test adding parallel route."""
        router = MultiTargetRouter()
        router.add_parallel_route(
            name="test",
            condition=lambda s: True,
            targets=["a", "b", "c"],
        )
        self.assertEqual(len(router._parallel_rules), 1)

    def test_route_parallel(self):
        """Test parallel routing."""
        router = MultiTargetRouter()
        router.add_parallel_route(
            name="test",
            condition=lambda s: True,
            targets=["a", "b", "c"],
        )

        targets = router.route_parallel({}, ["a", "b", "c"])
        self.assertEqual(targets, ["a", "b", "c"])

    def test_route_parallel_filtered(self):
        """Test parallel routing with filtered targets."""
        router = MultiTargetRouter()
        router.add_parallel_route(
            name="test",
            condition=lambda s: True,
            targets=["a", "b", "c"],
        )

        targets = router.route_parallel({}, ["a", "b"])
        self.assertEqual(targets, ["a", "b"])

    def test_route_parallel_default(self):
        """Test parallel routing default behavior."""
        router = MultiTargetRouter()

        targets = router.route_parallel({}, ["a", "b", "c"])
        self.assertEqual(targets, ["a", "b", "c"])


class TestRoutingStrategies(unittest.TestCase):
    """Tests for routing strategy classes."""

    def test_priority_router(self):
        """Test priority-based routing."""
        router = PriorityRouter({
            "high": 100,
            "medium": 50,
            "low": 0,
        })

        target = router.select({}, ["high", "medium", "low"])
        self.assertEqual(target, "high")

    def test_priority_router_partial(self):
        """Test priority router with partial priorities."""
        router = PriorityRouter({"high": 100})

        target = router.select({}, ["high", "unknown"])
        self.assertEqual(target, "high")

    def test_round_robin_router(self):
        """Test round-robin routing."""
        router = RoundRobinRouter()

        targets = ["a", "b", "c"]
        results = [router.select({}, targets) for _ in range(6)]

        self.assertEqual(results, ["a", "b", "c", "a", "b", "c"])

    def test_round_robin_reset(self):
        """Test round-robin reset."""
        router = RoundRobinRouter()

        router.select({}, ["a", "b", "c"])
        router.select({}, ["a", "b", "c"])
        router.reset()

        target = router.select({}, ["a", "b", "c"])
        self.assertEqual(target, "a")

    def test_random_router(self):
        """Test random routing."""
        router = RandomRouter(seed=42)

        targets = ["a", "b", "c"]
        results = [router.select({}, targets) for _ in range(100)]

        # All results should be valid targets
        for result in results:
            self.assertIn(result, targets)

        # Should have some variety (not all same)
        self.assertTrue(len(set(results)) > 1)

    def test_weighted_router(self):
        """Test weighted routing."""
        router = WeightedRouter({"heavy": 100, "light": 1})

        # With such extreme weights, "heavy" should be selected most of the time
        results = [router.select({}, ["heavy", "light"]) for _ in range(100)]
        heavy_count = results.count("heavy")

        self.assertGreater(heavy_count, 80)  # Should be ~99%

    def test_state_based_router(self):
        """Test state-based routing."""
        router = StateBasedRouter()
        router.add_scorer(
            "fast",
            lambda s: 1.0 if s.get("complexity", 0) < 0.5 else 0.0,
        )
        router.add_scorer(
            "thorough",
            lambda s: 1.0 if s.get("complexity", 0) >= 0.5 else 0.0,
        )

        # Low complexity -> fast
        target = router.select({"complexity": 0.3}, ["fast", "thorough"])
        self.assertEqual(target, "fast")

        # High complexity -> thorough
        target = router.select({"complexity": 0.8}, ["fast", "thorough"])
        self.assertEqual(target, "thorough")

    def test_composite_router(self):
        """Test composite routing."""
        primary = StateBasedRouter()
        primary.add_scorer("special", lambda s: 1.0 if s.get("special") else 0.0)

        fallback = PriorityRouter({"default": 100})

        router = CompositeRouter([primary, fallback])

        # Should use primary when condition matches
        target = router.select({"special": True}, ["special", "default"])
        self.assertEqual(target, "special")

        # Should fallback when primary doesn't match well
        target = router.select({}, ["other", "default"])
        # Will use primary first (all score 0.5), then fallback
        self.assertIn(target, ["other", "default"])


if __name__ == "__main__":
    unittest.main()
