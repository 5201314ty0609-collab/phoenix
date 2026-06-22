#!/usr/bin/env python3
"""
PHOENIX Skill: Security Audit — 代码安全扫描。

扫描代码中的安全问题：
- 硬编码密钥/密码
- SQL 注入风险
- XSS 漏洞
- 路径遍历
- 不安全的随机数
- 调试残留

Usage:
  security-audit.py <file_or_dir>           扫描代码
  security-audit.py <file_or_dir> --json    JSON 输出
  security-audit.py <file_or_dir> --strict  严格模式（包含低风险）
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import json
import re
import sys


@dataclass
class SecurityIssue:
    """安全问题"""
    file: str
    line: int
    severity: str       # critical / high / medium / low
    category: str       # secret / sqli / xss / path_traversal / crypto / debug
    description: str
    code_snippet: str = ""
    suggestion: str = ""

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
        }


# ── Detection Patterns ──────────────────────────────────────────────────────

SECRET_PATTERNS = [
    (r'(?:api[_-]?key|apikey)\s*[=:]\s*["\'][A-Za-z0-9+/=_\-]{16,}["\']',
     "Possible hardcoded API key", "critical", "Use environment variables"),
    (r'(?:secret|password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}["\']',
     "Possible hardcoded password/secret", "critical", "Use secret manager or env vars"),
    (r'(?:token)\s*[=:]\s*["\'][A-Za-z0-9+/=_\-]{16,}["\']',
     "Possible hardcoded token", "critical", "Use environment variables"),
    (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
     "Embedded private key", "critical", "Never embed keys in source code"),
    (r'(?:aws_access_key_id|aws_secret_access_key)\s*[=:]\s*["\'][A-Z0-9]{16,}["\']',
     "AWS credentials", "critical", "Use IAM roles or env vars"),
    (r'(?:mongodb|postgres|mysql|redis)://[^\s"\']+:([^@\s"\'#]+)@',
     "Database connection string with password", "critical", "Use env vars for connection strings"),
]

SQLI_PATTERNS = [
    (r'(?:f["\'].*SELECT.*{.*}|f["\'].*INSERT.*{.*}|f["\'].*UPDATE.*{.*}|f["\'].*DELETE.*{.*})',
     "f-string in SQL query — potential injection", "high", "Use parameterized queries"),
    (r'(?:execute|cursor\.execute)\s*\(\s*["\'].*%s',
     "String formatting in SQL execute", "high", "Use parameterized queries"),
    (r'(?:execute|cursor\.execute)\s*\(\s*f["\']',
     "f-string in SQL execute", "high", "Use parameterized queries"),
    (r'(?:execute|cursor\.execute)\s*\(\s*["\'].*\.format\(',
     ".format() in SQL execute", "high", "Use parameterized queries"),
    (r'(?:execute|query)\s*\(\s*["\'].*\+\s*\w+',
     "String concatenation in SQL query", "high", "Use parameterized queries"),
]

XSS_PATTERNS = [
    (r'innerHTML\s*=', "Direct innerHTML assignment", "medium", "Use textContent or sanitize"),
    (r'dangerouslySetInnerHTML', "React dangerouslySetInnerHTML", "medium", "Sanitize HTML first"),
    (r'document\.write\s*\(', "document.write usage", "medium", "Use DOM manipulation instead"),
    (r'\.html\s*\(\s*[^)]*\$', "jQuery .html() with variable", "medium", "Use .text() or sanitize"),
    (r'v-html\s*=', "Vue v-html directive", "medium", "Use v-text or sanitize"),
]

CRYPTO_PATTERNS = [
    (r'\bmd5\s*\(', "MD5 usage — cryptographically broken", "medium", "Use SHA-256 or better"),
    (r'\bsha1\s*\(', "SHA-1 usage — deprecated", "low", "Use SHA-256 or better"),
    (r'random\.random\s*\(\)', "Insecure random number generator", "medium", "Use secrets module for crypto"),
    (r'Math\.random\s*\(\)', "Insecure random number generator", "medium", "Use crypto.getRandomValues()"),
]

DEBUG_PATTERNS = [
    (r'\bconsole\.(log|debug|info|warn|error)\s*\(', "Debug console statement", "low", "Remove before production"),
    (r'\bprint\s*\(["\']DEBUG', "Debug print statement", "low", "Remove before production"),
    (r'\bpdb\.(set_trace|pm)\s*\(\)', "Debugger breakpoint", "high", "Remove debugger call"),
    (r'\bdebugger\b', "JavaScript debugger statement", "high", "Remove debugger statement"),
    (r'\bbreakpoint\s*\(\)', "Python breakpoint()", "high", "Remove breakpoint call"),
]

PATH_TRAVERSAL_PATTERNS = [
    (r'open\s*\(\s*[^)]*\+', "Dynamic file path with concatenation", "medium", "Validate and sanitize path"),
    (r'os\.path\.join\s*\([^)]*request', "User input in file path", "medium", "Validate path is within allowed directory"),
    (r'Path\s*\([^)]*request', "User input in Path constructor", "medium", "Validate path boundaries"),
]

INSECURE_NETWORK_PATTERNS = [
    (r'verify\s*=\s*False', "SSL verification disabled", "high", "Always verify SSL certificates"),
    (r'verify_ssl\s*=\s*False', "SSL verification disabled", "high", "Always verify SSL certificates"),
    (r'REQUESTS_CA_BUNDLE\s*=\s*""', "Empty CA bundle", "high", "Use proper CA certificates"),
]


# ── Scanner ─────────────────────────────────────────────────────────────────

class SecurityScanner:
    """代码安全扫描器"""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.issues: List[SecurityIssue] = []

    def scan_file(self, file_path: Path) -> List[SecurityIssue]:
        """扫描单个文件"""
        ext = file_path.suffix.lower()
        if ext not in [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs",
                       ".java", ".rb", ".php", ".env", ".yml", ".yaml", ".toml"]:
            return []

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        lines = content.split("\n")
        issues = []
        rel_path = str(file_path)

        # Skip test files for some checks
        is_test = "test" in file_path.name.lower() or "spec" in file_path.name.lower()

        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()

            # Skip comments
            if stripped.startswith("#") or stripped.startswith("//"):
                continue

            # Secret patterns (always check)
            for pattern, desc, severity, suggestion in SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        file=rel_path, line=line_num, severity=severity,
                        category="secret", description=desc,
                        code_snippet=stripped[:120], suggestion=suggestion,
                    ))

            # SQL injection (skip test files)
            if not is_test:
                for pattern, desc, severity, suggestion in SQLI_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(SecurityIssue(
                            file=rel_path, line=line_num, severity=severity,
                            category="sqli", description=desc,
                            code_snippet=stripped[:120], suggestion=suggestion,
                        ))

            # XSS
            for pattern, desc, severity, suggestion in XSS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        file=rel_path, line=line_num, severity=severity,
                        category="xss", description=desc,
                        code_snippet=stripped[:120], suggestion=suggestion,
                    ))

            # Path traversal
            if not is_test:
                for pattern, desc, severity, suggestion in PATH_TRAVERSAL_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(SecurityIssue(
                            file=rel_path, line=line_num, severity=severity,
                            category="path_traversal", description=desc,
                            code_snippet=stripped[:120], suggestion=suggestion,
                        ))

            # Insecure network
            for pattern, desc, severity, suggestion in INSECURE_NETWORK_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        file=rel_path, line=line_num, severity=severity,
                        category="network", description=desc,
                        code_snippet=stripped[:120], suggestion=suggestion,
                    ))

            # Crypto (strict mode only for low severity)
            for pattern, desc, severity, suggestion in CRYPTO_PATTERNS:
                if severity == "low" and not self.strict:
                    continue
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        file=rel_path, line=line_num, severity=severity,
                        category="crypto", description=desc,
                        code_snippet=stripped[:120], suggestion=suggestion,
                    ))

            # Debug remnants (high severity only unless strict)
            for pattern, desc, severity, suggestion in DEBUG_PATTERNS:
                if severity == "low" and not self.strict:
                    continue
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        file=rel_path, line=line_num, severity=severity,
                        category="debug", description=desc,
                        code_snippet=stripped[:120], suggestion=suggestion,
                    ))

        return issues

    def scan_directory(self, dir_path: Path) -> List[SecurityIssue]:
        """扫描目录"""
        all_issues = []

        skip_dirs = {"node_modules", ".git", "__pycache__", "venv", ".venv",
                     "dist", "build", ".next", "coverage", ".pytest_cache"}

        for file_path in sorted(dir_path.rglob("*")):
            if not file_path.is_file():
                continue
            # Skip directories we don't want to scan
            if any(skip in file_path.parts for skip in skip_dirs):
                continue
            issues = self.scan_file(file_path)
            all_issues.extend(issues)

        return all_issues


# ── Output ──────────────────────────────────────────────────────────────────

def print_report(issues: List[SecurityIssue], as_json: bool = False):
    """打印安全报告"""
    if as_json:
        output = {
            "total": len(issues),
            "by_severity": {},
            "by_category": {},
            "issues": [i.to_dict() for i in issues],
        }
        for sev in ["critical", "high", "medium", "low"]:
            count = sum(1 for i in issues if i.severity == sev)
            if count > 0:
                output["by_severity"][sev] = count
        for cat in set(i.category for i in issues):
            output["by_category"][cat] = sum(1 for i in issues if i.category == cat)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    if not issues:
        print("No security issues found.")
        return

    # Group by severity
    critical = [i for i in issues if i.severity == "critical"]
    high = [i for i in issues if i.severity == "high"]
    medium = [i for i in issues if i.severity == "medium"]
    low = [i for i in issues if i.severity == "low"]

    print("Security Audit Report")
    print("=" * 60)
    print(f"Total issues: {len(issues)}")
    if critical:
        print(f"  CRITICAL: {len(critical)}")
    if high:
        print(f"  HIGH:     {len(high)}")
    if medium:
        print(f"  MEDIUM:   {len(medium)}")
    if low:
        print(f"  LOW:      {len(low)}")
    print()

    for severity, label, icon in [
        ("critical", "CRITICAL", "!!!"),
        ("high", "HIGH", "!!"),
        ("medium", "MEDIUM", "!"),
        ("low", "LOW", "."),
    ]:
        group = [i for i in issues if i.severity == severity]
        if not group:
            continue

        print(f"[{label}] ({len(group)} issues)")
        print("-" * 40)
        for issue in group:
            print(f"  {icon} {issue.file}:{issue.line}")
            print(f"    {issue.description}")
            if issue.code_snippet:
                print(f"    Code: {issue.code_snippet[:80]}")
            if issue.suggestion:
                print(f"    Fix: {issue.suggestion}")
            print()

    # Exit code based on severity
    has_critical_or_high = bool(critical or high)
    if has_critical_or_high:
        print("RESULT: CRITICAL/HIGH issues found — fix before deploying")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    args = sys.argv[1:]
    as_json = "--json" in args
    strict = "--strict" in args
    targets = [a for a in args if not a.startswith("--")]

    if not targets:
        print("Usage: security-audit.py <file_or_dir> [--json] [--strict]")
        return

    scanner = SecurityScanner(strict=strict)
    target = Path(targets[0])

    if not target.exists():
        print(f"Path not found: {target}")
        sys.exit(1)

    if target.is_file():
        issues = scanner.scan_file(target)
    else:
        issues = scanner.scan_directory(target)

    print_report(issues, as_json=as_json)

    if any(i.severity in ("critical", "high") for i in issues):
        sys.exit(1)


if __name__ == "__main__":
    main()
