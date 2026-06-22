# PHOENIX AIOS — OpenAI AI Integration Layer

完整的 OpenAI API 集成层，提供 Chat Completions、Function Calling、Streaming 和结构化输出。

## 架构

```
PhoenixAIClient (主入口)
├── Chat Completions (对话补全)
│   ├── chat()              — 单轮对话
│   ├── chat_stream()       — 流式对话
│   ├── chat_stream_chunks() — 流式 + 回调
│   ├── chat_structured()   — 结构化输出 (JSON Schema)
│   └── continue_conversation() — 多轮对话
├── ToolRegistry (工具注册)
│   ├── register()          — 注册工具
│   ├── to_api_definitions() — 导出 API 定义
│   └── execute() / execute_all() — 执行工具调用
├── StreamHandler (流处理)
│   ├── iter_content()      — 迭代文本内容
│   ├── iter_stream()       — 迭代完整 chunk
│   └── process_stream()    — 回调模式处理
└── Conversation (会话管理)
    ├── add_user_message()  — 添加用户消息
    ├── add_assistant_message() — 添加助手消息
    ├── add_tool_result()   — 添加工具结果
    └── export/import JSON  — 持久化
```

## 快速开始

### 安装依赖

```bash
pip install openai
```

### 基本使用

```python
from aios.ai import PhoenixAIClient

# 初始化客户端
client = PhoenixAIClient(api_key="sk-...")

# 简单对话
response = client.chat("你好！")
print(response.content)

# 带系统提示
response = client.chat(
    "2+2等于多少？",
    system="你是一个数学老师，用简洁的方式回答。",
)
print(response.content)
```

### 流式输出

```python
# 方式 1: 迭代器
for chunk in client.chat_stream("讲一个故事"):
    print(chunk, end="", flush=True)

# 方式 2: 回调
def on_content(text):
    print(text, end="", flush=True)

response = client.chat_stream_chunks(
    "讲一个故事",
    on_content=on_content,
)
print(f"\n总 token: {response.usage.total_tokens}")
```

### Function Calling / 工具调用

```python
from aios.ai import PhoenixAIClient, Tool, ToolParameter, ToolRegistry

# 方式 1: 直接定义 Tool
weather_tool = Tool(
    name="get_weather",
    description="获取指定城市的天气信息",
    parameters=[
        ToolParameter(
            name="city",
            type="string",
            description="城市名称",
            required=True,
        ),
        ToolParameter(
            name="unit",
            type="string",
            description="温度单位",
            enum=["celsius", "fahrenheit"],
            default="celsius",
        ),
    ],
    handler=lambda city, unit="celsius": {"city": city, "temp": 22, "unit": unit},
)

# 方式 2: 从函数自动生成
def search_web(query: str, max_results: int = 5) -> list:
    """搜索网页。

    Args:
        query: 搜索关键词
        max_results: 最大结果数
    """
    return [{"title": f"Result for {query}", "url": "https://example.com"}]

# 注册工具
registry = ToolRegistry()
registry.register(weather_tool)
registry.register(search_web)

# 对话时使用工具
client = PhoenixAIClient(api_key="sk-...")
response = client.chat(
    "东京今天天气怎么样？",
    tools=registry,
)
print(response.content)
```

### 结构化输出

```python
# 使用 JSON Schema 约束输出格式
schema = {
    "name": "movie_list",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "movies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "year": {"type": "integer"},
                        "rating": {"type": "number"},
                    },
                    "required": ["title", "year", "rating"],
                },
            }
        },
        "required": ["movies"],
    },
}

response = client.chat_structured(
    "推荐3部经典科幻电影",
    schema=schema,
)
import json
data = json.loads(response.content)
for movie in data["movies"]:
    print(f"{movie['title']} ({movie['year']}) - {movie['rating']}")
```

### 多轮对话

```python
from aios.ai import PhoenixAIClient
from aios.ai.conversation import Conversation

client = PhoenixAIClient(api_key="sk-...")
conv = Conversation(system_prompt="你是一个友好的助手。")

# 第一轮
conv.add_user_message("你好，我叫小明。")
response = client.continue_conversation(conv.get_history())
conv.add_response(response)
print(response.content)

# 第二轮
conv.add_user_message("你还记得我叫什么吗？")
response = client.continue_conversation(conv.get_history())
conv.add_response(response)
print(response.content)

# 导出会话
json_str = conv.export_json()
# 之后可以 import_json(json_str) 恢复
```

## 内置工具

PHOENIX AIOS 提供 4 个内置工具：

| 工具 | 名称 | 功能 |
|------|------|------|
| Calculator | `calculator` | 数学表达式计算 |
| DateTime | `get_datetime` | 获取当前日期时间 |
| JSON Formatter | `format_json` | JSON 格式化和验证 |
| Text Analyzer | `analyze_text` | 文本统计分析 |

```python
from aios.ai.tools.builtin import create_default_registry

registry = create_default_registry()
# 注册到客户端使用
response = client.chat("计算 (3 + 5) * 12", tools=registry)
```

## 错误处理

所有错误都映射到 PHOENIX 的错误层次结构：

```python
from aios.ai import (
    PhoenixAIClient,
    AIError,
    AuthenticationError,
    RateLimitError,
    ConnectionError,
    TimeoutError,
    ValidationError,
    ToolExecutionError,
)

client = PhoenixAIClient(api_key="sk-...")

try:
    response = client.chat("Hello!")
except AuthenticationError:
    print("API key 无效")
except RateLimitError as e:
    print(f"请求过多，{e.retry_after}秒后重试")
except ConnectionError:
    print("网络连接失败")
except TimeoutError:
    print("请求超时")
except ValidationError as e:
    print(f"参数错误: {e}")
except AIError as e:
    print(f"AI 错误: {e}")
```

### 错误类型层次

```
AIError (基类)
├── AuthenticationError    (401)
├── PermissionError        (403)
├── RateLimitError         (429)
├── ConnectionError
├── TimeoutError
├── ValidationError        (400)
├── NotFoundError          (404)
├── UnprocessableError     (422)
├── ServerError            (500)
├── OverloadedError        (529)
├── ToolExecutionError
├── ToolNotFoundError
└── ContentFilterError
```

## 配置

### ChatConfig

```python
from aios.ai.types import ChatConfig

config = ChatConfig(
    model="gpt-4o",           # 模型 ID
    temperature=0.7,          # 采样温度 (0-2)
    top_p=0.9,                # 核采样参数
    max_tokens=1000,          # 最大生成 token
    frequency_penalty=0.5,    # 频率惩罚 (-2 到 2)
    presence_penalty=0.3,     # 存在惩罚 (-2 到 2)
    seed=42,                  # 确定性种子
    timeout=60.0,             # 请求超时（秒）
    max_retries=3,            # 最大重试次数
)

client = PhoenixAIClient(config=config)
```

### ToolChoiceConfig

```python
from aios.ai.types import ToolChoiceConfig, ToolChoiceMode

# 自动选择（默认）
response = client.chat("...", tools=registry, tool_choice=ToolChoiceConfig())

# 强制使用特定工具
response = client.chat(
    "...",
    tools=registry,
    tool_choice=ToolChoiceConfig(tool_name="get_weather"),
)

# 禁止使用工具
response = client.chat(
    "...",
    tools=registry,
    tool_choice=ToolChoiceConfig(mode=ToolChoiceMode.NONE),
)
```

## 自定义工具

### 从函数创建

```python
from aios.ai.tools.base import ToolFromCallable

def my_tool(query: str, limit: int = 10) -> list:
    """搜索数据库。

    Args:
        query: 搜索关键词
        limit: 返回结果数量上限
    """
    return []

tool = ToolFromCallable.from_function(my_tool)
```

### 手动定义

```python
from aios.ai.tools import Tool, ToolParameter

tool = Tool(
    name="send_email",
    description="发送电子邮件",
    parameters=[
        ToolParameter(name="to", type="string", description="收件人", required=True),
        ToolParameter(name="subject", type="string", description="主题", required=True),
        ToolParameter(name="body", type="string", description="正文", required=True),
    ],
    handler=lambda to, subject, body: {"status": "sent", "to": to},
)
```

## 运行测试

```bash
# 运行所有测试
python -m pytest aios/ai/tests/ -v

# 运行特定测试文件
python -m pytest aios/ai/tests/test_types.py -v
python -m pytest aios/ai/tests/test_tools.py -v
python -m pytest aios/ai/tests/test_streaming.py -v
python -m pytest aios/ai/tests/test_conversation.py -v
python -m pytest aios/ai/tests/test_errors.py -v
python -m pytest aios/ai/tests/test_builtin_tools.py -v
```

## 文件结构

```
aios/ai/
├── __init__.py           # 包入口，导出所有公共 API
├── client.py             # PhoenixAIClient 主客户端
├── types.py              # 不可变数据类型定义
├── errors.py             # 错误层次和映射
├── conversation.py       # 多轮会话管理
├── README.md             # 本文档
├── tools/
│   ├── __init__.py       # 工具包入口
│   ├── base.py           # Tool, ToolParameter, ToolRegistry
│   └── builtin.py        # 内置工具（计算器、日期等）
├── streaming/
│   ├── __init__.py       # 流处理包入口
│   └── handler.py        # StreamHandler, StreamCollector
└── tests/
    ├── __init__.py
    ├── test_types.py      # 类型测试
    ├── test_tools.py      # 工具测试
    ├── test_streaming.py  # 流处理测试
    ├── test_conversation.py # 会话测试
    ├── test_errors.py     # 错误测试
    └── test_builtin_tools.py # 内置工具测试
```

## 设计原则

1. **不可变性** — 所有数据类型使用 `frozen=True`，修改创建新实例
2. **类型安全** — 完整的类型注解，使用 `dataclass` 和 `Enum`
3. **错误映射** — OpenAI SDK 异常自动映射到 PHOENIX 错误层次
4. **关注点分离** — 工具、流处理、会话管理各自独立
5. **可测试性** — 所有组件可独立测试，无需真实 API 调用
