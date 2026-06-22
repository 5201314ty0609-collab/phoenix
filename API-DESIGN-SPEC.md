# PHOENIX AIOS API 设计规范

## 核心原则

1. **RESTful 风格** - 资源导向、HTTP 方法语义
2. **统一响应格式** - 一致的信封结构
3. **版本控制** - URL 路径版本 `/api/v1/`
4. **错误处理** - 标准错误码和消息
5. **文档优先** - OpenAPI 3.0 规范

## 统一响应格式

### 成功响应
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数无效",
    "details": [...]
  }
}
```

## 资源设计

### Agent 资源

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/agents` | GET | 获取 Agent 列表 |
| `/api/v1/agents` | POST | 创建 Agent |
| `/api/v1/agents/{id}` | GET | 获取单个 Agent |
| `/api/v1/agents/{id}` | PUT | 更新 Agent |
| `/api/v1/agents/{id}` | DELETE | 删除 Agent |
| `/api/v1/agents/{id}/heartbeat` | POST | Agent 心跳 |

### Task 资源

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/tasks` | GET | 获取任务列表 |
| `/api/v1/tasks` | POST | 创建任务 |
| `/api/v1/tasks/{id}` | GET | 获取单个任务 |
| `/api/v1/tasks/{id}` | PUT | 更新任务 |
| `/api/v1/tasks/{id}/status` | PATCH | 更新任务状态 |
| `/api/v1/tasks/{id}/cancel` | POST | 取消任务 |

### Memory 资源

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/memories` | GET | 获取记忆列表 |
| `/api/v1/memories` | POST | 创建记忆 |
| `/api/v1/memories/{id}` | GET | 获取单个记忆 |
| `/api/v1/memories/{id}` | PUT | 更新记忆 |
| `/api/v1/memories/{id}` | DELETE | 删除记忆 |
| `/api/v1/memories/search` | POST | 搜索记忆 |

## 错误码定义

| 错误码 | HTTP 状态码 | 描述 |
|--------|------------|------|
| VALIDATION_ERROR | 400 | 请求参数无效 |
| UNAUTHORIZED | 401 | 未认证 |
| FORBIDDEN | 403 | 无权限 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| RATE_LIMITED | 429 | 请求过多 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

## 认证方案

### JWT Bearer Token
```
Authorization: Bearer <token>
```

### API Key
```
X-API-Key: <api-key>
```

## 分页参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| limit | int | 20 | 每页数量 |
| sort | string | created_at | 排序字段 |
| order | string | desc | 排序方向 |

## 过滤参数

```
GET /api/v1/agents?status=active&type=core
GET /api/v1/tasks?status=running&priority=high
GET /api/v1/memories?type=semantic&importance=0.8
```

## 版本控制

- URL 路径版本：`/api/v1/`, `/api/v2/`
- 向后兼容：新版本保持旧版本功能
- 废弃通知：响应头 `Sunset: <date>`

## 文档

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
