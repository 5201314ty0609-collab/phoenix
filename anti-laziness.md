# 鲤鱼 Anti-Laziness Rules

> 借鉴 agent-skills 最佳实践，确保 鲤鱼 工作时不偷懒
> 来源: yfge/agentskill.work, liqiongyu/my-agents, EfanWang/skills-manager
> Stage: active | Enforcement: rule file (Level 4)

## 核心原则

**禁止偷懒！必须完整！不能省略！**

---

## 1. 完整性要求

### 1.1 代码完整性

**禁止**：
- ✗ 使用 `TODO`、`FIXME`、`XXX` 占位符
- ✗ 使用 `pass`、`...`、`NotImplemented` 占位
- ✗ 返回空结果或默认值而不处理
- ✗ 跳过错误处理
- ✗ 省略类型注解

**必须**：
- ✓ 实现所有函数体
- ✓ 处理所有错误情况
- ✓ 添加完整类型注解
- ✓ 编写完整文档字符串
- ✓ 实现所有边界情况

### 1.2 文档完整性

**禁止**：
- ✗ 使用占位符文档
- ✗ 省略参数说明
- ✗ 跳过返回值说明
- ✗ 忽略示例代码

**必须**：
- ✓ 完整的函数说明
- ✓ 所有参数说明
- ✓ 返回值说明
- ✓ 异常说明
- ✓ 使用示例

### 1.3 测试完整性

**禁止**：
- ✗ 只测试正常路径
- ✗ 跳过边界情况
- ✗ 忽略错误场景
- ✗ 使用 `assert True`

**必须**：
- ✓ 测试正常路径
- ✓ 测试边界情况
- ✓ 测试错误场景
- ✓ 测试并发情况
- ✓ 测试性能

---

## 2. 执行要求

### 2.1 任务执行

**禁止**：
- ✗ 跳过步骤
- ✗ 省略验证
- ✗ 忽略错误
- ✗ 提前结束

**必须**：
- ✓ 完成所有步骤
- ✓ 验证每个结果
- ✓ 处理所有错误
- ✓ 完整执行流程

### 2.2 代码审查

**禁止**：
- ✗ 只看表面
- ✗ 跳过细节
- ✗ 忽略警告
- ✗ 快速批准

**必须**：
- ✓ 深入分析
- ✓ 检查细节
- ✓ 处理警告
- ✓ 严格审查

### 2.3 问题解决

**禁止**：
- ✗ 简单绕过
- ✗ 临时修复
- ✗ 忽略根本原因
- ✗ 不完整的解决方案

**必须**：
- ✓ 找到根本原因
- ✓ 完整修复
- ✓ 验证修复
- ✓ 防止复发

---

## 3. 输出要求

### 3.1 代码输出

**禁止**：
- ✗ 未测试的代码
- ✗ 未文档化的代码
- ✗ 未类型化的代码
- ✗ 未优化的代码

**必须**：
- ✓ 完整测试
- ✓ 完整文档
- ✓ 完整类型
- ✓ 性能优化

### 3.2 文档输出

**禁止**：
- ✗ 不完整的文档
- ✗ 过时的文档
- ✗ 错误的文档
- ✗ 缺少示例

**必须**：
- ✓ 完整准确
- ✓ 及时更新
- ✓ 正确无误
- ✓ 包含示例

### 3.3 报告输出

**禁止**：
- ✗ 模糊的结论
- ✗ 缺少证据
- ✗ 不完整的分析
- ✗ 跳过细节

**必须**：
- ✓ 明确的结论
- ✓ 充分的证据
- ✓ 完整的分析
- ✓ 详细的细节

---

## 4. Observable Completion

完成工作后，必须包含执行摘要：

```
Execution Summary:
- agents: <使用的 agent 数量>
- skills: <使用的技能>
- tools: <使用的工具>
- verification: <验证方法>
- limits: <限制或阻塞>
```

**格式要求**：
- 保持轻量和事实
- 不暴露隐藏推理
- 所有字段必须存在
- 无限制时可省略 limits

---

## 5. 质量检查清单

### 5.1 代码质量

- [ ] 所有函数都有完整实现
- [ ] 所有错误都被处理
- [ ] 所有类型都已注解
- [ ] 所有文档都完整
- [ ] 所有测试都通过

### 5.2 文档质量

- [ ] 所有参数都有说明
- [ ] 所有返回值都有说明
- [ ] 所有异常都有说明
- [ ] 包含使用示例
- [ ] 文档与代码同步

### 5.3 测试质量

- [ ] 正常路径已测试
- [ ] 边界情况已测试
- [ ] 错误场景已测试
- [ ] 性能已测试
- [ ] 并发已测试

---

## 6. 常见偷懒模式

### 6.1 代码偷懒

**模式 1：占位符实现**
```python
# ✗ 错误
def process(data):
    # TODO: 实现处理逻辑
    pass

# ✓ 正确
def process(data):
    """处理数据并返回结果"""
    if not data:
        raise ValueError("数据不能为空")
    
    result = []
    for item in data:
        processed = transform(item)
        result.append(processed)
    
    return result
```

**模式 2：跳过错误处理**
```python
# ✗ 错误
def fetch(url):
    return requests.get(url)

# ✓ 正确
def fetch(url):
    """获取 URL 内容"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logger.error(f"获取失败: {url}, 错误: {e}")
        raise
```

**模式 3：省略类型注解**
```python
# ✗ 错误
def process(data):
    return data

# ✓ 正确
def process(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """处理数据"""
    return data
```

### 6.2 文档偷懒

**模式 1：占位符文档**
```python
# ✗ 错误
def process(data):
    """处理数据"""
    pass

# ✓ 正确
def process(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """处理数据并返回结果
    
    Args:
        data: 输入数据列表
        
    Returns:
        处理后的数据列表
        
    Raises:
        ValueError: 数据格式错误
        
    Examples:
        >>> process([{"key": "value"}])
        [{"key": "value", "processed": True}]
    """
    pass
```

**模式 2：跳过参数说明**
```python
# ✗ 错误
def connect(host, port):
    """连接到服务器"""
    pass

# ✓ 正确
def connect(host: str, port: int) -> Connection:
    """连接到服务器
    
    Args:
        host: 服务器地址
        port: 服务器端口
        
    Returns:
        连接对象
    """
    pass
```

### 6.3 测试偷懒

**模式 1：只测试正常路径**
```python
# ✗ 错误
def test_process():
    result = process([1, 2, 3])
    assert result == [1, 2, 3]

# ✓ 正确
def test_process_normal():
    result = process([1, 2, 3])
    assert result == [1, 2, 3]

def test_process_empty():
    result = process([])
    assert result == []

def test_process_invalid():
    with pytest.raises(ValueError):
        process(None)

def test_process_large():
    data = list(range(10000))
    result = process(data)
    assert len(result) == 10000
```

**模式 2：使用 `assert True`**
```python
# ✗ 错误
def test_something():
    assert True

# ✓ 正确
def test_something():
    result = my_function()
    assert result == expected_value
    assert result.property == expected_property
```

---

## 7. 执行检查

### 7.1 任务开始前

- [ ] 理解完整需求
- [ ] 识别所有边界情况
- [ ] 规划完整实现
- [ ] 准备测试用例

### 7.2 任务执行中

- [ ] 完成所有步骤
- [ ] 验证每个结果
- [ ] 处理所有错误
- [ ] 记录所有决策

### 7.3 任务完成后

- [ ] 运行所有测试
- [ ] 验证完整性
- [ ] 更新文档
- [ ] 生成执行摘要

---

## 8. 违规处理

### 8.1 检测到偷懒

**立即停止**：
1. 识别偷懒模式
2. 分析根本原因
3. 重新执行任务
4. 确保完整性

### 8.2 预防措施

**代码审查**：
- 检查所有函数实现
- 验证所有错误处理
- 确认所有类型注解
- 审查所有文档

**测试验证**：
- 运行完整测试套件
- 检查覆盖率
- 验证边界情况
- 测试错误场景

---

## 9. 最佳实践

### 9.1 代码实践

1. **完整实现**：不要使用占位符
2. **错误处理**：处理所有可能的错误
3. **类型注解**：所有函数都有类型
4. **文档完整**：所有公共 API 都有文档

### 9.2 测试实践

1. **全面覆盖**：测试所有路径
2. **边界测试**：测试边界情况
3. **错误测试**：测试错误场景
4. **性能测试**：测试性能要求

### 9.3 文档实践

1. **完整准确**：文档与代码同步
2. **示例丰富**：包含使用示例
3. **更新及时**：代码变更时更新文档
4. **易于理解**：清晰简洁

---

## 10. 总结

**核心原则**：
- 完整性：不要省略任何东西
- 准确性：确保所有内容正确
- 一致性：保持风格统一
- 可验证：所有内容都可验证

**记住**：
> **宁可多做，不要少做**
> **宁可复杂，不要简单**
> **宁可完整，不要省略**
> **宁可准确，不要模糊**

---

*这些规则借鉴了 GitHub 上最佳的 agent-skills 实践*
*确保 鲤鱼 工作时不会偷懒*
