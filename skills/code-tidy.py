#!/usr/bin/env python3
"""
PHOENIX Skill: Code Tidy — 代码洁癖级整理。

扫描并清理：
- 未使用的 import
- 注释掉的代码块
- 冗余注释
- 多余的空行
- 未排序的 import

Usage:
  code-tidy.py <file_or_dir>    扫描并清理
  code-tidy.py --dry-run <file> 仅扫描，不修改
"""

from pathlib import Path
from typing import List, Tuple
import os
import re
import sys


def find_unused_imports(lines: List[str], file_ext: str) -> List[Tuple[int, str]]:
    """查找未使用的 import"""
    unused = []

    if file_ext in [".py"]:
        for i, line in enumerate(lines):
            # 匹配 import x 或 from x import y
            match = re.match(r'^(?:from\s+(\S+)\s+)?import\s+(.+)$', line.strip())
            if not match:
                continue

            module = match.group(1) or ""
            imports = match.group(2)

            # 解析导入的名称
            imported_names = []
            for imp in imports.split(","):
                name = imp.strip().split(" as ")[-1].strip()
                if name:
                    imported_names.append(name)

            # 检查每个名称是否在后续代码中使用
            unused_names = []
            used_names = []

            for name in imported_names:
                used = False
                for j, later_line in enumerate(lines):
                    if j <= i:
                        continue
                    # 跳过注释和空行
                    if later_line.strip().startswith("#") or not later_line.strip():
                        continue
                    if re.search(r'\b' + re.escape(name) + r'\b', later_line):
                        used = True
                        break

                if used:
                    used_names.append(name)
                else:
                    unused_names.append(name)

            # 如果所有 import 都未使用，删掉整行
            if not used_names:
                unused.append((i, line.strip()))
            # 如果有部分未使用，需要修改这行（保留使用的）
            elif unused_names:
                # 生成新的 import 行
                if module:
                    new_line = f"from {module} import {', '.join(used_names)}"
                else:
                    new_line = f"import {', '.join(used_names)}"
                unused.append((i, new_line))

    elif file_ext in [".js", ".ts", ".tsx", ".jsx"]:
        for i, line in enumerate(lines):
            # 匹配 import { x } from 'y' 或 import x from 'y'
            match = re.match(r'^import\s+(?:{([^}]+)}|(\w+))\s+from', line.strip())
            if not match:
                continue

            names = []
            if match.group(1):
                names = [n.strip().split(" as ")[-1].strip() for n in match.group(1).split(",")]
            elif match.group(2):
                names = [match.group(2)]

            for name in names:
                if not name:
                    continue

                used = False
                for j, later_line in enumerate(lines):
                    if j <= i:
                        continue
                    if later_line.strip().startswith("//") or not later_line.strip():
                        continue
                    if re.search(r'\b' + re.escape(name) + r'\b', later_line):
                        used = True
                        break

                if not used:
                    unused.append((i, line.strip()))

    return unused


def find_commented_code(lines: List[str], file_ext: str) -> List[Tuple[int, str]]:
    """查找注释掉的代码块"""
    commented = []

    if file_ext in [".py"]:
        for i, line in enumerate(lines):
            stripped = line.strip()
            # 匹配 # 开头，但后面看起来像代码的行
            if stripped.startswith("#"):
                code_like = stripped[1:].strip()
                # 检查是否像代码（有 =, def, class, import, return, if, for 等）
                if re.match(r'^(def |class |import |from |return |if |for |while |try:|except |raise |print\(|assert )', code_like):
                    commented.append((i, line.rstrip()))
                    # 检查后续的缩进注释行（属于同一个代码块）
                    for j in range(i + 1, len(lines)):
                        next_stripped = lines[j].strip()
                        if next_stripped.startswith("#") and (next_stripped.startswith("# ") or next_stripped == "#"):
                            # 检查是否是缩进的代码
                            if lines[j].startswith("# ") or lines[j].startswith("    #"):
                                commented.append((j, lines[j].rstrip()))
                            else:
                                break
                        else:
                            break

    elif file_ext in [".js", ".ts", ".tsx", ".jsx"]:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("//"):
                code_like = stripped[2:].strip()
                if re.match(r'^(const |let |var |function |class |import |export |return |if |for |while |try |catch |throw |console\.)', code_like):
                    commented.append((i, line.rstrip()))

    return commented


def sort_imports(lines: List[str], file_ext: str) -> List[str]:
    """排序 import 语句"""
    if file_ext not in [".py"]:
        return lines

    # 找到 import 块的范围
    import_start = None
    import_end = None
    imports = []

    for i, line in enumerate(lines):
        if re.match(r'^(?:from\s+\S+\s+)?import\s+', line.strip()):
            if import_start is None:
                import_start = i
            import_end = i
            imports.append(line)
        elif import_start is not None and line.strip() and not line.strip().startswith("#"):
            break

    if not imports:
        return lines

    # 分三组：标准库 → 第三方 → 本地
    stdlib = []
    third_party = []
    local = []

    stdlib_modules = {
        "os", "sys", "re", "json", "math", "time", "datetime", "pathlib",
        "typing", "collections", "itertools", "functools", "hashlib",
        "sqlite3", "csv", "io", "tempfile", "shutil", "subprocess",
        "argparse", "logging", "unittest", "dataclasses", "abc",
        "contextlib", "copy", "uuid", "random", "string", "textwrap",
    }

    for imp in imports:
        match = re.match(r'(?:from\s+(\S+)\s+)?import\s+', imp.strip())
        if not match:
            continue

        module = match.group(1) or ""
        top_module = module.split(".")[0] if module else ""

        if top_module in stdlib_modules or not top_module:
            stdlib.append(imp)
        elif top_module.startswith(".") or top_module.startswith("_"):
            local.append(imp)
        else:
            third_party.append(imp)

    # 排序
    stdlib.sort()
    third_party.sort()
    local.sort()

    # 重建
    sorted_imports = []
    if stdlib:
        sorted_imports.extend(stdlib)
        sorted_imports.append("")
    if third_party:
        sorted_imports.extend(third_party)
        sorted_imports.append("")
    if local:
        sorted_imports.extend(local)

    # 移除末尾空行
    while sorted_imports and sorted_imports[-1] == "":
        sorted_imports.pop()

    # 安全重建
    result = []
    if import_start > 0:
        result.extend(lines[:import_start])
    result.extend(sorted_imports)
    if import_end + 1 < len(lines):
        result.extend(lines[import_end + 1:])

    return result


def remove_extra_blank_lines(lines: List[str]) -> List[str]:
    """移除多余空行（连续超过 2 个空行合并为 2 个）"""
    result = []
    blank_count = 0

    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)

    return result


def tidy_file(file_path: Path, dry_run: bool = False) -> dict:
    """整理单个文件"""
    ext = file_path.suffix
    if ext not in [".py", ".js", ".ts", ".tsx", ".jsx"]:
        return {"file": str(file_path), "skipped": True, "reason": "unsupported type"}

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"file": str(file_path), "error": str(e)}

    lines = content.split("\n")
    original_lines = len(lines)

    # 扫描问题
    unused = find_unused_imports(lines, ext)
    commented = find_commented_code(lines, ext)

    # 清理
    changes = []

    # 收集要修改/删除的行
    lines_to_remove = set()
    lines_to_modify = {}  # line_num -> new_line

    for line_num, line_text in unused:
        original_line = lines[line_num] if line_num < len(lines) else ""
        # 如果新行和原行相同，说明是整行删除
        if line_text == original_line.strip():
            lines_to_remove.add(line_num)
            changes.append(f"Removed unused import: {line_text}")
        else:
            # 部分删除，修改行
            lines_to_modify[line_num] = line_text
            changes.append(f"Cleaned import: {original_line.strip()} -> {line_text}")

    for line_num, line_text in commented:
        lines_to_remove.add(line_num)
        changes.append(f"Removed commented code: {line_text}")

    # 先修改行（从后往前）
    for line_num in sorted(lines_to_modify.keys(), reverse=True):
        if line_num < len(lines):
            lines[line_num] = lines_to_modify[line_num]

    # 再删除行（从后往前）
    for line_num in sorted(lines_to_remove, reverse=True):
        if line_num < len(lines):
            lines.pop(line_num)

    # 排序 import
    lines = sort_imports(lines, ext)

    # 移除多余空行
    lines = remove_extra_blank_lines(lines)

    # 写入
    if not dry_run and lines != content.split("\n"):
        file_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "file": str(file_path),
        "original_lines": original_lines,
        "final_lines": len(lines),
        "unused_imports": len(unused),
        "commented_code": len(commented),
        "changes": changes,
        "dry_run": dry_run,
    }


def scan_directory(dir_path: Path, dry_run: bool = False) -> List[dict]:
    """扫描目录"""
    results = []

    for file_path in sorted(dir_path.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix in [".py", ".js", ".ts", ".tsx", ".jsx"]:
            result = tidy_file(file_path, dry_run)
            results.append(result)

    return results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    dry_run = "--dry-run" in sys.argv
    target = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

    if not target:
        print("Usage: code-tidy.py <file_or_dir> [--dry-run]")
        return

    target_path = Path(target[0])

    if not target_path.exists():
        print(f"Path not found: {target_path}")
        return

    if target_path.is_file():
        result = tidy_file(target_path, dry_run)
        print_result(result)
    else:
        results = scan_directory(target_path, dry_run)
        for result in results:
            print_result(result)

        # 汇总
        total_removed = sum(r.get("unused_imports", 0) + r.get("commented_code", 0) for r in results)
        print(f"\n{'=' * 60}")
        print(f"Total: {len(results)} files scanned, {total_removed} issues found")


def print_result(result: dict):
    """打印结果"""
    if result.get("skipped"):
        return

    if result.get("error"):
        print(f"  ✗ {result['file']}: {result['error']}")
        return

    changes = result.get("changes", [])
    if not changes:
        return

    print(f"\n  📄 {result['file']}")
    print(f"     Lines: {result['original_lines']} → {result['final_lines']}")
    print(f"     Unused imports: {result['unused_imports']}")
    print(f"     Commented code: {result['commented_code']}")

    for change in changes[:5]:
        print(f"     - {change}")

    if len(changes) > 5:
        print(f"     ... and {len(changes) - 5} more changes")


if __name__ == "__main__":
    main()
