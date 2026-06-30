#!/usr/bin/env python3
"""
鲤鱼 Rule Migrator & Manager 测试脚本
"""

import sys
import time
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rule_migrator import RuleAnalyzer, RuleMigrator, MigrationValidator
from rule_manager import RuleManager


def test_rule_analyzer_edge_cases():
    """测试 RuleAnalyzer 边界情况"""
    print("=== RuleAnalyzer Edge Cases ===")
    results = []

    # Test 1: Non-existent file
    metadata = RuleAnalyzer.analyze_rule(Path('/tmp/nonexistent.md'))
    results.append(("Non-existent file", metadata == {}))

    # Test 2: Empty file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write('')
        f.flush()
        metadata = RuleAnalyzer.analyze_rule(Path(f.name))
        results.append(("Empty file returns metadata", isinstance(metadata, dict)))
        Path(f.name).unlink()

    # Test 3: File with all metadata
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Rule

> Stage: validated | Enforcement: Level 4
> Version: 2.0.0
> Created: 2026-01-01
> Updated: 2026-06-01

## Metadata

- **Rule ID**: test-rule
- **Category**: testing
- **Priority**: 8
- **Layer**: liyu
- **Languages**: python, typescript

## Trigger

When testing code

## Domains

testing, quality
""")
        f.flush()
        metadata = RuleAnalyzer.analyze_rule(Path(f.name))
        results.append(("Full metadata extraction", metadata.get('stage') == 'validated'))
        results.append(("Enforcement level", metadata.get('enforcement_level') == 4))
        results.append(("Domains extraction", 'testing' in metadata.get('domains', [])))
        Path(f.name).unlink()

    # Test 4: determine_category
    metadata = {'domains': ['security'], 'title': 'Security Rule', 'content': ''}
    category = RuleAnalyzer.determine_category(metadata)
    results.append(("Category from domain", category == 'security'))

    metadata = {'domains': [], 'title': 'Testing Guide', 'content': ''}
    category = RuleAnalyzer.determine_category(metadata)
    results.append(("Category from title", category == 'testing'))

    # Test 5: determine_layer
    layer = RuleAnalyzer.determine_layer(Path('/Users/.claude/rules/liyu/test.md'))
    results.append(("Phoenix layer", layer == 'liyu'))

    layer = RuleAnalyzer.determine_layer(Path('/Users/.claude/rules/common/test.md'))
    results.append(("Common layer", layer == 'common'))

    layer = RuleAnalyzer.determine_layer(Path('/Users/.claude/rules/zh/test.md'))
    results.append(("Translation layer", layer == 'translation'))

    # Test 6: determine_priority
    metadata = {'stage': 'hardened', 'enforcement_level': 6, 'layer': 'liyu'}
    priority = RuleAnalyzer.determine_priority(metadata)
    results.append(("Priority hardened", priority == 10))

    metadata = {'stage': 'draft', 'enforcement_level': 1, 'layer': 'common'}
    priority = RuleAnalyzer.determine_priority(metadata)
    results.append(("Priority draft", priority == 5))

    # Test 7: determine_languages
    metadata = {'file_path': '/Users/.claude/rules/typescript/test.md'}
    languages = RuleAnalyzer.determine_languages(metadata)
    results.append(("Language from path", languages == ['typescript']))

    metadata = {'file_path': '/Users/.claude/rules/liyu/test.md'}
    languages = RuleAnalyzer.determine_languages(metadata)
    results.append(("Language all", languages == ['all']))

    # Print results
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")

    return all(r[1] for r in results)


def test_rule_manager_edge_cases():
    """测试 RuleManager 边界情况"""
    print("\n=== RuleManager Edge Cases ===")
    results = []

    manager = RuleManager()

    # Test 1: Get non-existent rule
    rule = manager.get_rule('nonexistent-rule')
    results.append(("Get non-existent rule", rule is None))

    # Test 2: List rules with filters
    rules = manager.list_rules(category='testing')
    results.append(("List by category", isinstance(rules, list)))

    rules = manager.list_rules(layer='liyu')
    results.append(("List by layer", isinstance(rules, list)))

    # Test 3: Get stats
    stats = manager.get_stats()
    results.append(("Stats has total", 'total' in stats))
    results.append(("Stats has by_category", 'by_category' in stats))
    results.append(("Stats has by_layer", 'by_layer' in stats))
    results.append(("Stats has by_stage", 'by_stage' in stats))

    # Test 4: Update non-existent rule
    result = manager.update_rule('nonexistent-rule', name='test')
    results.append(("Update non-existent rule returns False", result is False))

    # Test 5: Deprecate non-existent rule
    result = manager.deprecate_rule('nonexistent-rule')
    results.append(("Deprecate non-existent rule returns False", result is False))

    # Test 6: Delete non-existent rule
    result = manager.delete_rule('nonexistent-rule')
    results.append(("Delete non-existent rule returns False", result is False))

    # Test 7: Promote non-existent rule
    result = manager.promote_rule('nonexistent-rule', 'active')
    results.append(("Promote non-existent rule returns False", result is False))

    # Print results
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")

    return all(r[1] for r in results)


def test_rule_manager_lifecycle():
    """测试 RuleManager 生命周期"""
    print("\n=== RuleManager Lifecycle Tests ===")
    results = []

    manager = RuleManager()

    # Test 1: Create rule
    result = manager.create_rule(
        rule_id='test-lifecycle-rule',
        category='testing',
        name='Test Lifecycle Rule',
        layer='liyu',
        priority=7
    )
    results.append(("Create rule", result is True))

    # Test 2: Get created rule
    rule = manager.get_rule('test-lifecycle-rule')
    results.append(("Get created rule", rule is not None))
    if rule:
        results.append(("Rule name matches", rule.get('name') == 'Test Lifecycle Rule'))
        results.append(("Rule category matches", rule.get('category') == 'testing'))
        results.append(("Rule layer matches", rule.get('layer') == 'liyu'))
        results.append(("Rule priority matches", rule.get('priority') == 7))
        results.append(("Rule stage is draft", rule.get('stage') == 'draft'))

    # Test 3: Update rule
    result = manager.update_rule('test-lifecycle-rule', name='Updated Name', priority=8)
    results.append(("Update rule", result is True))
    rule = manager.get_rule('test-lifecycle-rule')
    if rule:
        results.append(("Updated name matches", rule.get('name') == 'Updated Name'))
        results.append(("Updated priority matches", rule.get('priority') == 8))

    # Test 4: Promote rule
    result = manager.promote_rule('test-lifecycle-rule', 'active')
    results.append(("Promote to active", result is True))
    rule = manager.get_rule('test-lifecycle-rule')
    if rule:
        results.append(("Stage is active", rule.get('stage') == 'active'))

    # Test 5: Invalid promotion
    result = manager.promote_rule('test-lifecycle-rule', 'hardened')
    results.append(("Invalid promotion rejected", result is False))

    # Test 6: Deprecate rule
    result = manager.deprecate_rule('test-lifecycle-rule', 'Testing deprecation')
    results.append(("Deprecate rule", result is True))
    rule = manager.get_rule('test-lifecycle-rule')
    if rule:
        results.append(("Status is deprecated", rule.get('status') == 'deprecated'))

    # Test 7: Delete rule
    result = manager.delete_rule('test-lifecycle-rule', force=True)
    results.append(("Delete rule", result is True))
    rule = manager.get_rule('test-lifecycle-rule')
    results.append(("Rule deleted", rule is None))

    # Print results
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")

    return all(r[1] for r in results)


def test_performance():
    """测试性能"""
    print("\n=== Performance Tests ===")
    results = []

    # Test 1: Rule scanning performance
    migrator = RuleMigrator()
    start = time.time()
    rules = migrator.scan_rules()
    elapsed = time.time() - start
    results.append(("Rule scanning < 2s", elapsed < 2.0))
    print(f"  Scanned {len(rules)} rules in {elapsed:.3f}s")

    # Test 2: Stats performance
    manager = RuleManager()
    start = time.time()
    for _ in range(100):
        manager.get_stats()
    elapsed = time.time() - start
    results.append(("Stats 100x < 1s", elapsed < 1.0))
    print(f"  100 stats queries in {elapsed:.3f}s")

    # Test 3: List performance
    start = time.time()
    for _ in range(100):
        manager.list_rules()
    elapsed = time.time() - start
    results.append(("List 100x < 1s", elapsed < 1.0))
    print(f"  100 list queries in {elapsed:.3f}s")

    # Print results
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")

    return all(r[1] for r in results)


def main():
    """运行所有测试"""
    print("=" * 72)
    print("  鲤鱼 Rule Migrator & Manager - Comprehensive Test Suite")
    print("=" * 72)
    print()

    test_results = []

    # Run all tests
    test_results.append(("RuleAnalyzer Edge Cases", test_rule_analyzer_edge_cases()))
    test_results.append(("RuleManager Edge Cases", test_rule_manager_edge_cases()))
    test_results.append(("RuleManager Lifecycle", test_rule_manager_lifecycle()))
    test_results.append(("Performance Tests", test_performance()))

    # Print summary
    print("\n" + "=" * 72)
    print("  Test Summary")
    print("=" * 72)
    print()

    passed = sum(1 for _, p in test_results if p)
    total = len(test_results)

    for name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"  Total: {passed}/{total} test suites passed")

    if passed == total:
        print("\n  All tests PASSED!")
        return 0
    else:
        print("\n  Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
