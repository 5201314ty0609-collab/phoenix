#!/usr/bin/env python3
"""
PHOENIX Skill: Verify Completion — 完成前强制验证。

在声称工作完成前运行验证检查：
- 代码是否能正常运行（语法检查）
- 是否有明显的错误
- 文件是否完整

Usage:
  verify-completion.py <file_or_dir>    验证文件
  verify-completion.py --strict <file>  严格模式
"""

from pathlib import Path
from typing import List, Tuple
import ast
import re
import sys


def check_python_syntax(file_path: Path) -> List[str]:
    """检查 Python 语法"""
    errors = []

    try:
        content = file_path.read_text(encoding="utf-8")
        ast.parse(content)
    except SyntaxError as e:
        errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
    except Exception as e:
        errors.append(f"Parse error: {str(e)}")

    return errors


def check_javascript_syntax(file_path: Path) -> List[str]:
    """检查 JavaScript/TypeScript 语法（基础检查）"""
    errors = []

    try:
        content = file_path.read_text(encoding="utf-8")

        # 检查括号匹配
        brackets = {"(": ")", "[": "]", "{": "}"}
        stack = []

        for i, char in enumerate(content):
            if char in brackets:
                stack.append((char, i))
            elif char in brackets.values():
                if not stack:
                    line_num = content[:i].count("\n") + 1
                    errors.append(f"Unmatched closing bracket '{char}' at line {line_num}")
                    break
                expected = brackets[stack[-1][0]]
                if char != expected:
                    line_num = content[:i].count("\n") + 1
                    errors.append(f"Mismatched bracket: expected '{expected}', got '{char}' at line {line_num}")
                    break
                stack.pop()

        if stack and not errors:
            line_num = content[:stack[-1][1]].count("\n") + 1
            errors.append(f"Unclosed bracket '{stack[-1][0]}' at line {line_num}")

        # 检查明显的语法问题
        if re.search(r'\bfunction\s+\w+\s*\([^)]*$', content, re.MULTILINE):
            errors.append("Possible unclosed function declaration")

    except Exception as e:
        errors.append(f"Read error: {str(e)}")

    return errors


def check_common_issues(file_path: Path, strict: bool = False) -> List[str]:
    """检查常见问题"""
    issues = []

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # 检查 TODO/FIXME/HACK
        for i, line in enumerate(lines):
            if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', line):
                if strict:
                    issues.append(f"Line {i + 1}: Contains {re.search(r'(TODO|FIXME|HACK|XXX)', line).group(1)}")

        # 检查 console.log / print 语句（生产代码中应该移除）
        if strict:
            for i, line in enumerate(lines):
                if re.search(r'\bconsole\.(log|debug|info)\b', line):
                    issues.append(f"Line {i + 1}: Debug statement (console.log)")
                if re.search(r'\bprint\s*\(', line) and not line.strip().startswith("#"):
                    # 排除测试文件
                    if "test" not in file_path.name.lower():
                        issues.append(f"Line {i + 1}: Debug statement (print)")

        # 检查空文件
        if not content.strip():
            issues.append("File is empty")

        # 检查尾随空格（严格模式）
        if strict:
            trailing = [i + 1 for i, line in enumerate(lines) if line != line.rstrip()]
            if trailing:
                issues.append(f"Trailing whitespace on lines: {trailing[:5]}")

    except Exception as e:
        issues.append(f"Read error: {str(e)}")

    return issues


def verify_file(file_path: Path, strict: bool = False) -> dict:
    """验证单个文件"""
    ext = file_path.suffix

    # 语法检查
    syntax_errors = []
    if ext == ".py":
        syntax_errors = check_python_syntax(file_path)
    elif ext in [".js", ".ts", ".tsx", ".jsx"]:
        syntax_errors = check_javascript_syntax(file_path)

    # 通用检查
    common_issues = check_common_issues(file_path, strict)

    all_issues = syntax_errors + common_issues

    return {
        "file": str(file_path),
        "valid": len(syntax_errors) == 0,
        "syntax_errors": syntax_errors,
        "common_issues": common_issues,
        "total_issues": len(all_issues),
    }


def verify_directory(dir_path: Path, strict: bool = False) -> List[dict]:
    """验证目录"""
    results = []

    for file_path in sorted(dir_path.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix in [".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".md"]:
            result = verify_file(file_path, strict)
            results.append(result)

    return results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    strict = "--strict" in sys.argv
    target = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

    if not target:
        print("Usage: verify-completion.py <file_or_dir> [--strict]")
        return

    target_path = Path(target[0])

    if not target_path.exists():
        print(f"Path not found: {target_path}")
        return

    if target_path.is_file():
        result = verify_file(target_path, strict)
        print_result(result)
    else:
        results = verify_directory(target_path, strict)

        valid_count = sum(1 for r in results if r["valid"])
        invalid_count = len(results) - valid_count

        for result in results:
            if not result["valid"] or result["common_issues"]:
                print_result(result)

        print(f"\n{'=' * 60}")
        print(f"Total: {len(results)} files verified")
        print(f"Valid: {valid_count}")
        if invalid_count > 0:
            print(f"Invalid: {invalid_count}")
            sys.exit(1)
        else:
            print("All files passed verification! ✓")


def print_result(result: dict):
    """打印结果"""
    status = "✓" if result["valid"] else "✗"
    print(f"\n  {status} {result['file']}")

    for error in result["syntax_errors"]:
        print(f"    ERROR: {error}")

    for issue in result["common_issues"]:
        print(f"    WARN: {issue}")


if __name__ == "__main__":
    main()
