#!/usr/bin/env python3
"""
鲤鱼 Skill: Doc Gen — 文档生成工具。

自动生成/更新文档：
- 函数 docstring
- 文件级 README
- API 文档片段

Usage:
  doc-gen.py docstrings <file>        为函数添加 docstring
  doc-gen.py docstrings <file> --check  仅检查缺少的 docstring
  doc-gen.py readme <dir>              生成目录的 README
  doc-gen.py api <file>                生成 API 文档片段
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import ast
import json
import re
import sys


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    line: int
    end_line: int
    is_async: bool
    is_method: bool
    params: List[str]
    return_annotation: str
    docstring: Optional[str]
    decorators: List[str]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "line": self.line,
            "end_line": self.end_line,
            "is_async": self.is_async,
            "is_method": self.is_method,
            "params": self.params,
            "return_annotation": self.return_annotation,
            "has_docstring": self.docstring is not None,
            "decorators": self.decorators,
        }


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    line: int
    end_line: int
    docstring: Optional[str]
    methods: List[FunctionInfo]
    base_classes: List[str]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "line": self.line,
            "end_line": self.end_line,
            "has_docstring": self.docstring is not None,
            "methods": [m.to_dict() for m in self.methods],
            "base_classes": self.base_classes,
        }


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    lines: int
    docstring: Optional[str]
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[str]

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "lines": self.lines,
            "has_module_docstring": self.docstring is not None,
            "functions": [f.to_dict() for f in self.functions],
            "classes": [c.to_dict() for c in self.classes],
            "imports": self.imports,
        }


# ── Python Analysis ─────────────────────────────────────────────────────────

class PythonDocAnalyzer(ast.NodeVisitor):
    """Python 文档分析器"""

    def __init__(self, source: str):
        self.source = source
        self.source_lines = source.split("\n")
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.imports: List[str] = []
        self.module_docstring: Optional[str] = None

    def analyze(self) -> FileInfo:
        """分析文件"""
        try:
            tree = ast.parse(self.source)
        except SyntaxError:
            return FileInfo(
                path="", lines=len(self.source_lines),
                docstring=None, functions=[], classes=[], imports=[],
            )

        # Module docstring
        if (tree.body and isinstance(tree.body[0], ast.Expr) and
                isinstance(tree.body[0].value, (ast.Str, ast.Constant))):
            node = tree.body[0].value
            self.module_docstring = node.s if isinstance(node, ast.Str) else str(node.value)

        self.visit(tree)

        return FileInfo(
            path="",
            lines=len(self.source_lines),
            docstring=self.module_docstring,
            functions=self.functions,
            classes=self.classes,
            imports=self.imports,
        )

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.imports.append(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._process_function(node, is_method=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._process_function(node, is_async=True, is_method=False)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        methods = []
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(ast.dump(base))

        # Collect methods
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_function(child, is_async=isinstance(child, ast.AsyncFunctionDef), is_method=True)
                methods.append(method_info)

        docstring = ast.get_docstring(node)

        self.classes.append(ClassInfo(
            name=node.name,
            line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=docstring,
            methods=methods,
            base_classes=base_classes,
        ))

        # Don't generic_visit since we already processed children
        for child in ast.iter_child_nodes(node):
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.visit(child)

    def _process_function(self, node, is_async: bool = False, is_method: bool = False):
        info = self._extract_function(node, is_async, is_method)
        self.functions.append(info)

    def _extract_function(self, node, is_async: bool = False, is_method: bool = False) -> FunctionInfo:
        """提取函数信息"""
        # Parameters
        params = []
        args = node.args
        for arg in args.args:
            if arg.arg in ("self", "cls"):
                continue
            annotation = ""
            if arg.annotation:
                annotation = ast.dump(arg.annotation)
            params.append(f"{arg.arg}{annotation}")

        if args.vararg:
            params.append(f"*{args.vararg.arg}")
        if args.kwarg:
            params.append(f"**{args.kwarg.arg}")

        # Return annotation
        return_annotation = ""
        if node.returns:
            try:
                return_annotation = ast.unparse(node.returns)
            except Exception:
                return_annotation = ast.dump(node.returns)

        # Decorators
        decorators = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except Exception:
                decorators.append(ast.dump(dec))

        # Docstring
        docstring = ast.get_docstring(node)

        return FunctionInfo(
            name=node.name,
            line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            is_async=is_async,
            is_method=is_method,
            params=params,
            return_annotation=return_annotation,
            docstring=docstring,
            decorators=decorators,
        )


# ── Docstring Generator ─────────────────────────────────────────────────────

def generate_docstring(func: FunctionInfo, indent: str = "    ") -> str:
    """生成 docstring"""
    lines = []

    # Summary line
    name_words = func.name.replace("_", " ").strip()
    lines.append(f'{indent}"""')
    lines.append(f"{indent}{name_words.capitalize()}.")

    # Parameters
    if func.params:
        lines.append(f"{indent}")
        lines.append(f"{indent}Args:")
        for param in func.params:
            param_name = param.split(":")[0].strip().lstrip("*")
            lines.append(f"{indent}    {param_name}: Description.")

    # Returns
    if func.return_annotation and func.return_annotation != "None":
        lines.append(f"{indent}")
        lines.append(f"{indent}Returns:")
        lines.append(f"{indent}    Description of return value.")

    lines.append(f'{indent}"""')

    return "\n".join(lines)


def add_docstrings_to_file(file_path: Path, check_only: bool = False) -> Dict:
    """为文件中的函数添加 docstring"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"file": str(file_path), "error": str(e)}

    if not file_path.suffix == ".py":
        return {"file": str(file_path), "skipped": True, "reason": "Not a Python file"}

    analyzer = PythonDocAnalyzer(content)
    info = analyzer.analyze()
    info.path = str(file_path)

    missing = []
    for func in info.functions:
        if func.docstring is None and not func.name.startswith("_"):
            missing.append(func)
    for cls in info.classes:
        if cls.docstring is None:
            missing.append(cls)
        for method in cls.methods:
            if method.docstring is None and not method.name.startswith("_"):
                missing.append(method)

    if check_only or not missing:
        return {
            "file": str(file_path),
            "total_functions": len(info.functions) + sum(len(c.methods) for c in info.classes),
            "missing_docstrings": len(missing),
            "missing": [m.name for m in missing],
        }

    # Add docstrings (from bottom to top to preserve line numbers)
    lines = content.split("\n")
    insertions = []

    for item in sorted(missing, key=lambda x: x.line, reverse=True):
        if isinstance(item, FunctionInfo):
            # Find the line after the def statement (after the colon)
            def_line = lines[item.line - 1]
            # Determine indent
            indent = ""
            for ch in def_line:
                if ch in (" ", "\t"):
                    indent += ch
                else:
                    break

            # Find insertion point (after def line, before first statement)
            insert_idx = item.line  # 0-indexed, line after def
            docstring = generate_docstring(item, indent=indent)
            insertions.append((insert_idx, docstring, item.name))

    for idx, docstring, name in insertions:
        lines.insert(idx, docstring)

    new_content = "\n".join(lines)
    file_path.write_text(new_content, encoding="utf-8")

    return {
        "file": str(file_path),
        "added_docstrings": len(insertions),
        "functions_updated": [name for _, _, name in insertions],
    }


# ── Directory README Generator ──────────────────────────────────────────────

def generate_readme(dir_path: Path) -> str:
    """生成目录 README"""
    py_files = sorted(dir_path.glob("*.py"))
    js_files = sorted(dir_path.glob("*.js")) + sorted(dir_path.glob("*.ts"))

    lines = []
    lines.append(f"# {dir_path.name}")
    lines.append("")

    # Analyze Python files
    all_functions = []
    all_classes = []

    for f in py_files:
        if f.name.startswith("_") or f.name.startswith("test"):
            continue
        try:
            content = f.read_text(encoding="utf-8")
            analyzer = PythonDocAnalyzer(content)
            info = analyzer.analyze()
            info.path = str(f)

            if info.functions:
                lines.append(f"## {f.name}")
                if info.module_docstring:
                    lines.append(f"\n{info.module_docstring.split(chr(10))[0]}")
                lines.append("")

                for func in info.functions:
                    if not func.name.startswith("_"):
                        desc = func.docstring.split("\n")[0] if func.docstring else "No description"
                        lines.append(f"- `{func.name}()` — {desc}")
                lines.append("")
        except Exception:
            pass

    if not lines[-1].strip():
        lines.pop()

    return "\n".join(lines)


# ── API Doc Generator ───────────────────────────────────────────────────────

def generate_api_doc(file_path: Path) -> str:
    """生成 API 文档片段"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return f"Error reading {file_path}"

    analyzer = PythonDocAnalyzer(content)
    info = analyzer.analyze()
    info.path = str(file_path)

    lines = []
    lines.append(f"# API: {file_path.stem}")
    lines.append("")

    if info.module_docstring:
        lines.append(info.module_docstring)
        lines.append("")

    # Classes
    for cls in info.classes:
        lines.append(f"## class `{cls.name}`")
        if cls.base_classes:
            lines.append(f"Extends: {', '.join(cls.base_classes)}")
        lines.append("")
        if cls.docstring:
            lines.append(cls.docstring)
            lines.append("")

        for method in cls.methods:
            if method.name.startswith("_"):
                continue
            sig = ", ".join(method.params)
            ret = f" -> {method.return_annotation}" if method.return_annotation else ""
            prefix = "async " if method.is_async else ""
            lines.append(f"### `{prefix}{method.name}({sig}){ret}`")
            lines.append("")
            if method.docstring:
                lines.append(method.docstring)
            lines.append("")

    # Module-level functions
    for func in info.functions:
        if func.name.startswith("_"):
            continue
        sig = ", ".join(func.params)
        ret = f" -> {func.return_annotation}" if func.return_annotation else ""
        prefix = "async " if func.is_async else ""
        lines.append(f"## `{prefix}{func.name}({sig}){ret}`")
        lines.append("")
        if func.docstring:
            lines.append(func.docstring)
        lines.append("")

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "docstrings":
        if len(sys.argv) < 3:
            print("Usage: doc-gen.py docstrings <file> [--check]")
            return

        check_only = "--check" in sys.argv
        target = Path([a for a in sys.argv[2:] if not a.startswith("--")][0])

        if not target.exists():
            print(f"Path not found: {target}")
            sys.exit(1)

        if target.is_file():
            result = add_docstrings_to_file(target, check_only=check_only)
            if result.get("skipped"):
                print(f"Skipped: {result['reason']}")
            elif check_only:
                print(f"{result['file']}: {result['missing_docstrings']} missing docstrings")
                for name in result.get("missing", []):
                    print(f"  - {name}")
            else:
                print(f"{result['file']}: added {result.get('added_docstrings', 0)} docstrings")
                for name in result.get("functions_updated", []):
                    print(f"  + {name}")
        else:
            total_added = 0
            total_missing = 0
            for f in sorted(target.rglob("*.py")):
                if "__pycache__" in str(f):
                    continue
                result = add_docstrings_to_file(f, check_only=check_only)
                if result.get("skipped"):
                    continue
                if check_only:
                    total_missing += result.get("missing_docstrings", 0)
                    if result.get("missing"):
                        print(f"{f.name}: {result['missing_docstrings']} missing")
                else:
                    added = result.get("added_docstrings", 0)
                    total_added += added
                    if added:
                        print(f"{f.name}: added {added}")

            if check_only:
                print(f"\nTotal missing: {total_missing}")
            else:
                print(f"\nTotal added: {total_added}")

    elif cmd == "readme":
        if len(sys.argv) < 3:
            print("Usage: doc-gen.py readme <dir>")
            return

        target = Path(sys.argv[2])
        if not target.is_dir():
            print(f"Not a directory: {target}")
            sys.exit(1)

        readme = generate_readme(target)
        print(readme)

    elif cmd == "api":
        if len(sys.argv) < 3:
            print("Usage: doc-gen.py api <file>")
            return

        target = Path(sys.argv[2])
        if not target.exists():
            print(f"Path not found: {target}")
            sys.exit(1)

        doc = generate_api_doc(target)
        print(doc)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
