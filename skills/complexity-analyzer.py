#!/usr/bin/env python3
"""
鲤鱼 Skill: Complexity Analyzer — 代码复杂度分析。

分析代码质量指标：
- 圈复杂度（Cyclomatic Complexity）
- 函数长度
- 嵌套深度
- 参数数量
- 文件长度

Usage:
  complexity-analyzer.py <file_or_dir>             分析代码
  complexity-analyzer.py <file_or_dir> --json      JSON 输出
  complexity-analyzer.py <file_or_dir> --threshold 10  设置复杂度阈值
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import ast
import json
import re
import sys


@dataclass
class FunctionMetrics:
    """函数度量"""
    name: str
    file: str
    line_start: int
    line_end: int
    line_count: int
    cyclomatic_complexity: int
    max_nesting_depth: int
    parameter_count: int
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "line_count": self.line_count,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "max_nesting_depth": self.max_nesting_depth,
            "parameter_count": self.parameter_count,
            "issues": self.issues,
        }


@dataclass
class FileMetrics:
    """文件度量"""
    file: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    function_count: int
    class_count: int
    avg_complexity: float
    max_complexity: int
    max_function_length: int
    functions: List[FunctionMetrics] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "avg_complexity": round(self.avg_complexity, 2),
            "max_complexity": self.max_complexity,
            "max_function_length": self.max_function_length,
            "functions": [f.to_dict() for f in self.functions],
        }


# ── Python Analysis ─────────────────────────────────────────────────────────

class PythonAnalyzer(ast.NodeVisitor):
    """Python AST 分析器"""

    def __init__(self, source_lines: List[str], file_path: str):
        self.source_lines = source_lines
        self.file_path = file_path
        self.functions: List[FunctionMetrics] = []
        self.class_count = 0

    def visit_ClassDef(self, node):
        self.class_count += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, node):
        """分析单个函数"""
        # Line count
        line_start = node.lineno
        line_end = node.end_lineno or node.lineno
        line_count = line_end - line_start + 1

        # Parameter count
        args = node.args
        param_count = (
            len(args.args) + len(args.posonlyargs) +
            len(args.kwonlyargs) +
            (1 if args.vararg else 0) +
            (1 if args.kwarg else 0)
        )
        # Subtract 'self'/'cls' for methods
        if args.args and args.args[0].arg in ("self", "cls"):
            param_count -= 1

        # Cyclomatic complexity
        complexity = self._calc_complexity(node)

        # Nesting depth
        max_depth = self._calc_max_nesting(node, 0)

        # Issues
        issues = []
        if line_count > 50:
            issues.append(f"Function too long ({line_count} lines, max 50)")
        if complexity > 10:
            issues.append(f"High complexity ({complexity}, max 10)")
        if max_depth > 4:
            issues.append(f"Deep nesting ({max_depth} levels, max 4)")
        if param_count > 5:
            issues.append(f"Too many parameters ({param_count}, max 5)")

        metrics = FunctionMetrics(
            name=node.name,
            file=self.file_path,
            line_start=line_start,
            line_end=line_end,
            line_count=line_count,
            cyclomatic_complexity=complexity,
            max_nesting_depth=max_depth,
            parameter_count=param_count,
            issues=issues,
        )
        self.functions.append(metrics)

    def _calc_complexity(self, node) -> int:
        """计算圈复杂度"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.IfExp)):
                complexity += 1
            elif isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # BoolOp wraps And/Or operators
                if isinstance(child.op, ast.And):
                    complexity += len(child.values) - 1
                elif isinstance(child.op, ast.Or):
                    complexity += len(child.values) - 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1

        return complexity

    def _calc_max_nesting(self, node, current_depth: int) -> int:
        """计算最大嵌套深度"""
        max_depth = current_depth

        nesting_nodes = (
            ast.If, ast.For, ast.AsyncFor, ast.While,
            ast.With, ast.AsyncWith, ast.Try,
        )

        for child in ast.iter_child_nodes(node):
            if isinstance(child, nesting_nodes):
                child_depth = self._calc_max_nesting(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calc_max_nesting(child, current_depth)
                max_depth = max(max_depth, child_depth)

        return max_depth


def analyze_python(file_path: Path, content: str) -> Optional[FileMetrics]:
    """分析 Python 文件"""
    lines = content.split("\n")

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None

    analyzer = PythonAnalyzer(lines, str(file_path))
    analyzer.visit(tree)

    # Line statistics
    code_lines = 0
    comment_lines = 0
    blank_lines = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
        elif stripped.startswith("#"):
            comment_lines += 1
        else:
            code_lines += 1

    # Complexity stats
    complexities = [f.cyclomatic_complexity for f in analyzer.functions]
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0
    max_complexity = max(complexities) if complexities else 0
    max_func_length = max((f.line_count for f in analyzer.functions), default=0)

    return FileMetrics(
        file=str(file_path),
        total_lines=len(lines),
        code_lines=code_lines,
        comment_lines=comment_lines,
        blank_lines=blank_lines,
        function_count=len(analyzer.functions),
        class_count=analyzer.class_count,
        avg_complexity=avg_complexity,
        max_complexity=max_complexity,
        max_function_length=max_func_length,
        functions=analyzer.functions,
    )


# ── JavaScript/TypeScript Analysis ──────────────────────────────────────────

def analyze_js_ts(file_path: Path, content: str) -> Optional[FileMetrics]:
    """分析 JS/TS 文件（基于正则，非 AST）"""
    lines = content.split("\n")

    # Count lines
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    in_block_comment = False

    for line in lines:
        stripped = line.strip()
        if in_block_comment:
            comment_lines += 1
            if "*/" in stripped:
                in_block_comment = False
            continue
        if not stripped:
            blank_lines += 1
        elif stripped.startswith("//"):
            comment_lines += 1
        elif stripped.startswith("/*"):
            comment_lines += 1
            if "*/" not in stripped:
                in_block_comment = True
        else:
            code_lines += 1

    # Find functions (basic regex)
    functions: List[FunctionMetrics] = []

    func_patterns = [
        r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>|\w+\s*=>))',
        r'(?:async\s+)?(?:function\s+(\w+)|(\w+)\s*\([^)]*\)\s*\{)',
    ]

    func_starts: List[Tuple[str, int]] = []
    for i, line in enumerate(lines):
        for pattern in func_patterns:
            match = re.search(pattern, line)
            if match:
                name = match.group(1) or match.group(2) or "anonymous"
                func_starts.append((name, i))
                break

    # Analyze each function (simplified)
    for idx, (name, start_line) in enumerate(func_starts):
        # Find end of function (brace counting)
        brace_count = 0
        end_line = start_line
        found_open = False

        for j in range(start_line, len(lines)):
            for ch in lines[j]:
                if ch == "{":
                    brace_count += 1
                    found_open = True
                elif ch == "}":
                    brace_count -= 1
            if found_open and brace_count <= 0:
                end_line = j
                break

        line_count = end_line - start_line + 1

        # Count parameters
        param_match = re.search(r'\(([^)]*)\)', lines[start_line])
        param_count = 0
        if param_match:
            params = param_match.group(1).strip()
            if params:
                param_count = len([p.strip() for p in params.split(",") if p.strip()])

        # Estimate complexity (count decision points)
        complexity = 1
        max_depth = 0
        current_depth = 0

        for j in range(start_line, end_line + 1):
            line = lines[j]
            # Decision points
            complexity += len(re.findall(r'\b(if|else if|else\s*\{|case\s+|catch\s*\(|&&|\|\||\?)\b', line))
            # Nesting
            current_depth += line.count("{") - line.count("}")
            max_depth = max(max_depth, current_depth)

        issues = []
        if line_count > 50:
            issues.append(f"Function too long ({line_count} lines, max 50)")
        if complexity > 10:
            issues.append(f"High complexity ({complexity}, max 10)")
        if max_depth > 4:
            issues.append(f"Deep nesting ({max_depth} levels, max 4)")
        if param_count > 5:
            issues.append(f"Too many parameters ({param_count}, max 5)")

        functions.append(FunctionMetrics(
            name=name,
            file=str(file_path),
            line_start=start_line + 1,
            line_end=end_line + 1,
            line_count=line_count,
            cyclomatic_complexity=complexity,
            max_nesting_depth=max_depth,
            parameter_count=param_count,
            issues=issues,
        ))

    complexities = [f.cyclomatic_complexity for f in functions]
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0
    max_complexity = max(complexities) if complexities else 0
    max_func_length = max((f.line_count for f in functions), default=0)

    return FileMetrics(
        file=str(file_path),
        total_lines=len(lines),
        code_lines=code_lines,
        comment_lines=comment_lines,
        blank_lines=blank_lines,
        function_count=len(functions),
        class_count=0,
        avg_complexity=avg_complexity,
        max_complexity=max_complexity,
        max_function_length=max_func_length,
        functions=functions,
    )


# ── Main ────────────────────────────────────────────────────────────────────

def analyze_file(file_path: Path) -> Optional[FileMetrics]:
    """分析单个文件"""
    ext = file_path.suffix.lower()

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    if ext == ".py":
        return analyze_python(file_path, content)
    elif ext in [".js", ".ts", ".tsx", ".jsx"]:
        return analyze_js_ts(file_path, content)

    return None


def analyze_directory(dir_path: Path) -> List[FileMetrics]:
    """分析目录"""
    results = []

    skip_dirs = {"node_modules", ".git", "__pycache__", "venv", ".venv",
                 "dist", "build", ".next", "coverage"}

    for file_path in sorted(dir_path.rglob("*")):
        if not file_path.is_file():
            continue
        if any(skip in file_path.parts for skip in skip_dirs):
            continue
        metrics = analyze_file(file_path)
        if metrics:
            results.append(metrics)

    return results


def print_report(results: List[FileMetrics], as_json: bool = False,
                 threshold: int = 10):
    """打印复杂度报告"""
    if as_json:
        output = {
            "total_files": len(results),
            "total_functions": sum(r.function_count for r in results),
            "files": [r.to_dict() for r in results],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    if not results:
        print("No analyzable files found.")
        return

    print("Complexity Analysis Report")
    print("=" * 60)

    total_issues = 0
    all_complex_funcs: List[FunctionMetrics] = []

    for metrics in results:
        file_issues = sum(len(f.issues) for f in metrics.functions)
        total_issues += file_issues

        complex_funcs = [f for f in metrics.functions
                        if f.cyclomatic_complexity > threshold]
        all_complex_funcs.extend(complex_funcs)

        if file_issues > 0 or complex_funcs:
            print(f"\n  {metrics.file}")
            print(f"    Lines: {metrics.total_lines} ({metrics.code_lines} code)")
            print(f"    Functions: {metrics.function_count}, Classes: {metrics.class_count}")
            print(f"    Avg complexity: {metrics.avg_complexity:.1f}, Max: {metrics.max_complexity}")

            for func in metrics.functions:
                if func.issues:
                    print(f"      {func.name} (L{func.line_start}-{func.line_end})")
                    for issue in func.issues:
                        print(f"        - {issue}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Files analyzed: {len(results)}")
    print(f"  Total functions: {sum(r.function_count for r in results)}")
    print(f"  Total issues: {total_issues}")
    print(f"  Functions above threshold ({threshold}): {len(all_complex_funcs)}")

    if all_complex_funcs:
        print(f"\n  Most complex functions:")
        sorted_funcs = sorted(all_complex_funcs,
                            key=lambda f: f.cyclomatic_complexity, reverse=True)
        for func in sorted_funcs[:10]:
            print(f"    CC={func.cyclomatic_complexity:3d}  {func.file}:{func.line_start}  {func.name}()")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    args = sys.argv[1:]
    as_json = "--json" in args
    threshold = 10

    for i, arg in enumerate(args):
        if arg == "--threshold" and i + 1 < len(args):
            try:
                threshold = int(args[i + 1])
            except ValueError:
                pass

    targets = [a for a in args if not a.startswith("--")]
    # Remove threshold value if it was captured
    if "--threshold" in args:
        idx = args.index("--threshold")
        if idx + 1 < len(args):
            targets = [a for a in targets if a != args[idx + 1]]

    if not targets:
        print("Usage: complexity-analyzer.py <file_or_dir> [--json] [--threshold N]")
        return

    target = Path(targets[0])
    if not target.exists():
        print(f"Path not found: {target}")
        sys.exit(1)

    if target.is_file():
        metrics = analyze_file(target)
        results = [metrics] if metrics else []
    else:
        results = analyze_directory(target)

    print_report(results, as_json=as_json, threshold=threshold)


if __name__ == "__main__":
    main()
