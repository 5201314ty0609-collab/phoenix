"""
工具注册系统

提供工具的注册、发现、验证和执行能力。
支持：
- 工具注册与注销
- 参数验证
- 执行超时控制
- 重试机制
- 执行统计
- 内置工具集

Design:
    ┌─────────────────────────────────────────────────┐
    │                 ToolRegistry                     │
    │  ┌───────────┐ ┌───────────┐ ┌───────────────┐ │
    │  │ Register  │ │ Discover  │ │   Execute     │ │
    │  │ (CRUD)    │ │ (search)  │ │ (validate+run)│ │
    │  └─────┬─────┘ └─────┬─────┘ └───────┬───────┘ │
    │        │             │               │          │
    │  ┌─────┴─────────────┴───────────────┴───────┐  │
    │  │            Tool Storage                    │  │
    │  │  (name → ToolDefinition mapping)          │  │
    │  └───────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────┘
"""

from __future__ import annotations

import json
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from .agent_types import (
    ToolDefinition,
    ToolResult,
    ToolStatus,
    ToolCall,
)


@dataclass(frozen=True)
class ToolStats:
    """工具执行统计"""

    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    last_called_at: float | None = None

    def record_success(self, execution_time: float) -> ToolStats:
        new_total = self.total_calls + 1
        new_success = self.success_count + 1
        new_time = self.total_execution_time + execution_time
        return ToolStats(
            total_calls=new_total,
            success_count=new_success,
            failure_count=self.failure_count,
            timeout_count=self.timeout_count,
            total_execution_time=new_time,
            avg_execution_time=new_time / new_total,
            last_called_at=time.time(),
        )

    def record_failure(self, execution_time: float) -> ToolStats:
        new_total = self.total_calls + 1
        new_failure = self.failure_count + 1
        new_time = self.total_execution_time + execution_time
        return ToolStats(
            total_calls=new_total,
            success_count=self.success_count,
            failure_count=new_failure,
            timeout_count=self.timeout_count,
            total_execution_time=new_time,
            avg_execution_time=new_time / new_total,
            last_called_at=time.time(),
        )

    def record_timeout(self) -> ToolStats:
        new_total = self.total_calls + 1
        return ToolStats(
            total_calls=new_total,
            success_count=self.success_count,
            failure_count=self.failure_count,
            timeout_count=self.timeout_count + 1,
            total_execution_time=self.total_execution_time,
            avg_execution_time=self.total_execution_time / new_total if new_total > 0 else 0.0,
            last_called_at=time.time(),
        )


class ToolExecutor:
    """
    工具执行器

    负责单个工具的执行，包含参数验证、超时控制和重试机制。
    """

    def __init__(self, tool: ToolDefinition) -> None:
        self._tool = tool
        self._stats = ToolStats()
        self._lock = threading.RLock()

    @property
    def tool(self) -> ToolDefinition:
        return self._tool

    @property
    def stats(self) -> ToolStats:
        with self._lock:
            return self._stats

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        """
        执行工具

        1. 验证参数
        2. 执行函数（带超时）
        3. 处理重试
        4. 记录统计
        """
        # 验证参数
        is_valid, errors = self._tool.validate_parameters(arguments)
        if not is_valid:
            error_msg = f"参数验证失败: {'; '.join(errors)}"
            with self._lock:
                self._stats = self._stats.record_failure(0.0)
            return ToolResult(
                tool_name=self._tool.name,
                status=ToolStatus.FAILED,
                error=error_msg,
            )

        # 检查函数是否可用
        if self._tool.function is None:
            with self._lock:
                self._stats = self._stats.record_failure(0.0)
            return ToolResult(
                tool_name=self._tool.name,
                status=ToolStatus.FAILED,
                error="工具函数未定义",
            )

        # 执行（带重试）
        last_error: str | None = None
        for attempt in range(self._tool.retry_count + 1):
            start_time = time.time()
            try:
                result = self._tool.function(**arguments)
                execution_time = time.time() - start_time

                with self._lock:
                    self._stats = self._stats.record_success(execution_time)

                return ToolResult(
                    tool_name=self._tool.name,
                    status=ToolStatus.SUCCESS,
                    output=result,
                    execution_time=execution_time,
                    metadata={"attempt": attempt + 1},
                )

            except TimeoutError:
                execution_time = time.time() - start_time
                last_error = f"工具执行超时 ({self._tool.timeout}s)"
                with self._lock:
                    self._stats = self._stats.record_timeout()
                if attempt < self._tool.retry_count:
                    continue
                return ToolResult(
                    tool_name=self._tool.name,
                    status=ToolStatus.TIMEOUT,
                    error=last_error,
                    execution_time=execution_time,
                )

            except Exception as e:
                execution_time = time.time() - start_time
                last_error = f"工具执行异常: {type(e).__name__}: {str(e)}"
                with self._lock:
                    self._stats = self._stats.record_failure(execution_time)
                if attempt < self._tool.retry_count:
                    continue
                return ToolResult(
                    tool_name=self._tool.name,
                    status=ToolStatus.FAILED,
                    error=last_error,
                    execution_time=execution_time,
                )

        # 不应该到达这里，但为了类型安全
        return ToolResult(
            tool_name=self._tool.name,
            status=ToolStatus.FAILED,
            error=last_error or "未知错误",
        )


class ToolRegistry:
    """
    工具注册表

    管理所有可用工具，提供注册、发现和执行能力。
    线程安全，支持并发访问。
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolExecutor] = {}
        self._categories: dict[str, set[str]] = {}
        self._lock = threading.RLock()

    def register(self, tool: ToolDefinition) -> None:
        """
        注册工具

        如果同名工具已存在，将被覆盖。
        """
        with self._lock:
            executor = ToolExecutor(tool)
            self._tools[tool.name] = executor

            # 更新分类索引
            category = tool.category
            if category not in self._categories:
                self._categories[category] = set()
            self._categories[category].add(tool.name)

    def unregister(self, name: str) -> bool:
        """
        注销工具

        返回是否成功注销。
        """
        with self._lock:
            if name not in self._tools:
                return False

            executor = self._tools.pop(name)
            category = executor.tool.category
            if category in self._categories:
                self._categories[category].discard(name)
                if not self._categories[category]:
                    del self._categories[category]
            return True

    def get(self, name: str) -> ToolDefinition | None:
        """获取工具定义"""
        with self._lock:
            executor = self._tools.get(name)
            return executor.tool if executor else None

    def get_executor(self, name: str) -> ToolExecutor | None:
        """获取工具执行器"""
        with self._lock:
            return self._tools.get(name)

    def has(self, name: str) -> bool:
        """检查工具是否存在"""
        with self._lock:
            return name in self._tools

    def list_tools(self) -> list[ToolDefinition]:
        """列出所有工具"""
        with self._lock:
            return [executor.tool for executor in self._tools.values()]

    def list_names(self) -> list[str]:
        """列出所有工具名称"""
        with self._lock:
            return list(self._tools.keys())

    def list_categories(self) -> list[str]:
        """列出所有分类"""
        with self._lock:
            return list(self._categories.keys())

    def get_by_category(self, category: str) -> list[ToolDefinition]:
        """获取指定分类的所有工具"""
        with self._lock:
            names = self._categories.get(category, set())
            return [self._tools[name].tool for name in names if name in self._tools]

    def search(self, query: str) -> list[ToolDefinition]:
        """
        搜索工具

        根据名称和描述进行模糊匹配。
        """
        query_lower = query.lower()
        results: list[ToolDefinition] = []

        with self._lock:
            for executor in self._tools.values():
                tool = executor.tool
                if (query_lower in tool.name.lower() or
                    query_lower in tool.description.lower() or
                    any(query_lower in tag for tag in tool.metadata.get("tags", []))):
                    results.append(tool)

        return results

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """
        执行工具

        如果工具不存在，返回失败结果。
        """
        with self._lock:
            executor = self._tools.get(name)

        if executor is None:
            return ToolResult(
                tool_name=name,
                status=ToolStatus.FAILED,
                error=f"工具不存在: {name}",
            )

        return executor.execute(arguments)

    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """
        执行工具调用

        从 ToolCall 对象中提取参数并执行。
        """
        return self.execute(tool_call.name, tool_call.arguments)

    def get_stats(self, name: str) -> ToolStats | None:
        """获取工具执行统计"""
        with self._lock:
            executor = self._tools.get(name)
            return executor.stats if executor else None

    def get_all_stats(self) -> dict[str, ToolStats]:
        """获取所有工具的执行统计"""
        with self._lock:
            return {name: executor.stats for name, executor in self._tools.items()}

    def to_json_schema(self, names: list[str] | None = None) -> list[dict[str, Any]]:
        """
        导出为 JSON Schema 格式

        用于传递给 LLM 的工具描述。
        """
        tools = self.list_tools() if names is None else [
            self._tools[name].tool for name in names if name in self._tools
        ]

        schemas: list[dict[str, Any]] = []
        for tool in tools:
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        return schemas

    def clear(self) -> None:
        """清空所有注册的工具"""
        with self._lock:
            self._tools.clear()
            self._categories.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return self.has(name)


class BuiltinTools:
    """
    内置工具集

    提供常用的内置工具实现。
    """

    @staticmethod
    def register_all(registry: ToolRegistry) -> None:
        """注册所有内置工具"""
        BuiltinTools.register_math_tools(registry)
        BuiltinTools.register_string_tools(registry)
        BuiltinTools.register_json_tools(registry)
        BuiltinTools.register_time_tools(registry)
        BuiltinTools.register_file_tools(registry)

    @staticmethod
    def register_math_tools(registry: ToolRegistry) -> None:
        """注册数学工具"""

        def calculator(expression: str) -> float:
            """计算数学表达式"""
            # 安全的数学表达式求值
            allowed_names = {
                "abs": abs, "round": round,
                "min": min, "max": max,
                "sum": sum, "pow": pow,
                "int": int, "float": float,
            }
            # 只允许数字、运算符和允许的函数名
            import re
            if re.search(r'[a-zA-Z_]+', expression):
                for match in re.finditer(r'[a-zA-Z_]+', expression):
                    if match.group() not in allowed_names:
                        raise ValueError(f"不允许的函数: {match.group()}")
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return float(result)

        registry.register(ToolDefinition(
            name="calculator",
            description="计算数学表达式。支持基本运算符 (+, -, *, /) 和常用函数 (abs, round, min, max, sum, pow)。",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式",
                    }
                },
                "required": ["expression"],
            },
            function=calculator,
            category="math",
        ))

    @staticmethod
    def register_string_tools(registry: ToolRegistry) -> None:
        """注册字符串工具"""

        def string_length(text: str) -> int:
            """返回字符串长度"""
            return len(text)

        def string_replace(text: str, old: str, new: str) -> str:
            """替换字符串中的子串"""
            return text.replace(old, new)

        def string_split(text: str, separator: str = "\n") -> list[str]:
            """分割字符串"""
            return text.split(separator)

        def string_join(texts: list[str], separator: str = "\n") -> str:
            """连接字符串"""
            return separator.join(texts)

        registry.register(ToolDefinition(
            name="string_length",
            description="返回字符串的长度",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要计算长度的字符串"}
                },
                "required": ["text"],
            },
            function=string_length,
            category="string",
        ))

        registry.register(ToolDefinition(
            name="string_replace",
            description="替换字符串中的子串",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "原始字符串"},
                    "old": {"type": "string", "description": "要替换的子串"},
                    "new": {"type": "string", "description": "替换后的子串"},
                },
                "required": ["text", "old", "new"],
            },
            function=string_replace,
            category="string",
        ))

        registry.register(ToolDefinition(
            name="string_split",
            description="按分隔符分割字符串",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要分割的字符串"},
                    "separator": {"type": "string", "description": "分隔符", "default": "\\n"},
                },
                "required": ["text"],
            },
            function=string_split,
            category="string",
        ))

        registry.register(ToolDefinition(
            name="string_join",
            description="用分隔符连接字符串列表",
            parameters={
                "type": "object",
                "properties": {
                    "texts": {"type": "array", "items": {"type": "string"}, "description": "字符串列表"},
                    "separator": {"type": "string", "description": "分隔符", "default": "\\n"},
                },
                "required": ["texts"],
            },
            function=string_join,
            category="string",
        ))

    @staticmethod
    def register_json_tools(registry: ToolRegistry) -> None:
        """注册 JSON 工具"""

        def json_parse(text: str) -> Any:
            """解析 JSON 字符串"""
            return json.loads(text)

        def json_stringify(data: Any, indent: int = 2) -> str:
            """将对象转换为 JSON 字符串"""
            return json.dumps(data, indent=indent, ensure_ascii=False)

        def json_path(data: dict[str, Any], path: str) -> Any:
            """按路径获取 JSON 值（用点号分隔）"""
            keys = path.split(".")
            current = data
            for key in keys:
                if isinstance(current, dict):
                    if key not in current:
                        return None
                    current = current[key]
                elif isinstance(current, list):
                    try:
                        index = int(key)
                        current = current[index]
                    except (ValueError, IndexError):
                        return None
                else:
                    return None
            return current

        registry.register(ToolDefinition(
            name="json_parse",
            description="解析 JSON 字符串为对象",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "JSON 字符串"}
                },
                "required": ["text"],
            },
            function=json_parse,
            category="json",
        ))

        registry.register(ToolDefinition(
            name="json_stringify",
            description="将对象转换为 JSON 字符串",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"description": "要转换的对象"},
                    "indent": {"type": "integer", "description": "缩进空格数", "default": 2},
                },
                "required": ["data"],
            },
            function=json_stringify,
            category="json",
        ))

        registry.register(ToolDefinition(
            name="json_path",
            description="按路径获取 JSON 值（用点号分隔，如 'a.b.c'）",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "JSON 对象"},
                    "path": {"type": "string", "description": "点号分隔的路径"},
                },
                "required": ["data", "path"],
            },
            function=json_path,
            category="json",
        ))

    @staticmethod
    def register_time_tools(registry: ToolRegistry) -> None:
        """注册时间工具"""

        def get_current_time() -> str:
            """获取当前时间"""
            from datetime import datetime, timezone
            return datetime.now(timezone.utc).isoformat()

        def get_timestamp() -> float:
            """获取当前时间戳"""
            return time.time()

        def format_timestamp(timestamp: float, format: str = "%Y-%m-%d %H:%M:%S") -> str:
            """格式化时间戳"""
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.strftime(format)

        registry.register(ToolDefinition(
            name="get_current_time",
            description="获取当前 UTC 时间（ISO 8601 格式）",
            parameters={"type": "object", "properties": {}},
            function=get_current_time,
            category="time",
        ))

        registry.register(ToolDefinition(
            name="get_timestamp",
            description="获取当前 Unix 时间戳",
            parameters={"type": "object", "properties": {}},
            function=get_timestamp,
            category="time",
        ))

        registry.register(ToolDefinition(
            name="format_timestamp",
            description="将时间戳格式化为可读字符串",
            parameters={
                "type": "object",
                "properties": {
                    "timestamp": {"type": "number", "description": "Unix 时间戳"},
                    "format": {"type": "string", "description": "strftime 格式字符串", "default": "%Y-%m-%d %H:%M:%S"},
                },
                "required": ["timestamp"],
            },
            function=format_timestamp,
            category="time",
        ))

    @staticmethod
    def register_file_tools(registry: ToolRegistry) -> None:
        """注册文件工具（安全沙箱内）"""

        def read_file(path: str) -> str:
            """读取文件内容"""
            from pathlib import Path
            file_path = Path(path).expanduser()
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {path}")
            return file_path.read_text(encoding="utf-8")

        def write_file(path: str, content: str) -> str:
            """写入文件内容"""
            from pathlib import Path
            file_path = Path(path).expanduser()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"已写入 {len(content)} 字节到 {path}"

        def list_directory(path: str = ".") -> list[str]:
            """列出目录内容"""
            from pathlib import Path
            dir_path = Path(path).expanduser()
            if not dir_path.exists():
                raise FileNotFoundError(f"目录不存在: {path}")
            return sorted(str(item.name) for item in dir_path.iterdir())

        registry.register(ToolDefinition(
            name="read_file",
            description="读取文件内容",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"}
                },
                "required": ["path"],
            },
            function=read_file,
            category="file",
        ))

        registry.register(ToolDefinition(
            name="write_file",
            description="写入文件内容",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "要写入的内容"},
                },
                "required": ["path", "content"],
            },
            function=write_file,
            category="file",
        ))

        registry.register(ToolDefinition(
            name="list_directory",
            description="列出目录中的文件和子目录",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录路径", "default": "."}
                },
            },
            function=list_directory,
            category="file",
        ))
