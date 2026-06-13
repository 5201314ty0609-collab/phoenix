# 🐦‍🔥 PHOENIX

**Self-Evolving Agent Harness · 自进化 AI Agent 编排系统**

PHOENIX 是一个独立运行的 AI Agent 控制台——融合 MUNDO 的编排模式与 NexSandglass 的记忆架构。实时监控、自动学习、自我进化。

---

## 快速开始

```bash
# 1. 创建你的身份
python3 user_manager.py setup

# 2. 启动控制台
python3 server.py

# 3. 打开浏览器
open http://127.0.0.1:8765
```

**零依赖。** Python 3.9+ stdlib only。

---

## 核心模块

| 模块 | 功能 | 测试 |
|------|------|------|
| `nexsandglass.py` | 四层记忆引擎——沙粒写入·偏移率·决策检测·灵魂蒸馏 | 53 ✓ |
| `tool-guard.py` | 工具循环防护——三种检测器·四级决策链 | 33 ✓ |
| `skill-registry.py` | 技能依赖管理——62技能拓扑验证·冲突检测 | 14 ✓ |
| `policy-engine.py` | 策略引擎——15规则·7链·优先级仲裁 | — |
| `timeline.py` | 执行时间线——SQLite+FTS5·回放·导出 | — |
| `event-bus/bus.py` | 事件总线——25事件类型·发布订阅·桥接 | — |
| `server.py` | HTTP API 服务器——8端点·SSE实时推送 | 13 ✓ |
| `user_manager.py` | 用户层级——创始人·合伙人·使用者·自动升级 | — |

---

## 用户层级

| 层级 | 权限 | 升级条件 |
|------|------|---------|
| 👑 创始人 | 全权限，不可降级 | holyty + PHOENIX |
| ⭐ 合伙人 | 完整功能，画像可见 | ≥10 条对话沙粒 |
| 🌱 使用者 | 基础功能，学习期 | 注册默认 |

注册新用户：`python3 user_manager.py register <用户名> user`

积累 ≥10 条对话沙粒后**自动升级**为合伙人。

---

## 架构

```
L4 灵魂蒸馏 ──→ persona.md (沟通风格·决策模式·核心价值观)
L3 决策检测 ──→ decisions.jsonl (双语CN/EN选择模式匹配)
L2 偏移率   ──→ drift.json → 7-Sense趋势预测
L1 沙粒写入 ──→ sand.txt + sand.db (纯文本+SQLite+FTS5)
```

---

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/status` | GET | 系统综合状态 + 7-Sense |
| `/api/modules` | GET | 模块清单与统计 |
| `/api/timeline` | GET | 执行时间线查询 |
| `/api/persona` | GET | NexSandglass 用户画像 |
| `/api/tool-guard` | GET | 工具防护状态 |
| `/api/skills` | GET | 技能生态统计 |
| `/api/users` | GET | 用户层级列表 |
| `/api/stream` | GET | SSE 实时事件流 |
| `/api/persona/rebuild` | POST | 强制重建画像 |
| `/api/tool-guard/reset` | POST | 重置工具防护 |
| `/api/drift/recalc` | POST | 重算 30 天偏移 |

---

## 来源

PHOENIX 融合了两个开源项目的架构精华：

- [MUNDO Agent v2.0.9](https://github.com/LiHongwei-cn/lihongwei-cn) — Agent 编排模式（事件总线·策略引擎·工具防护·技能注册）
- [NexSandglass V2.9.3](https://github.com/lovevin1314-tech/NexSandglass-Agent-DedicatedMemory) — 记忆架构（偏移率·决策粒子·灵魂蒸馏·四层引擎）

**每项吸收都做了改进**——双语支持、SQLite双写、完整测试、frozen dataclass、上下文管理器——比原版更好。

---

## 创始人

- **holyty** — 架构设计与方向
- **PHOENIX** — 自进化引擎核心

MIT License
