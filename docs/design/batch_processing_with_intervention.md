# 批量处理用户介入方案设计

## 问题场景

在批量处理多个单号时，可能遇到以下需要用户介入的情况：

1. **数据问题**：源表不存在、字段缺失等
2. **权限问题**：无法访问某些资源
3. **配置不明确**：需要用户选择或确认
4. **输出汇总**：需要查看所有单号的详细处理结果

## 解决方案

### 方案对比

| 方案 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| **方案1：两阶段处理** | 简单直接 | 需要两次处理 | 少量需要介入的情况 |
| **方案2：增强版工具** | 一次处理，自动识别 | 实现复杂 | 大量批量处理场景 |
| **方案3：混合模式** | 灵活性高 | 需要Agent智能判断 | 复杂业务场景 |

### 推荐方案：增强版批量处理工具

## 架构设计

```
用户上传Excel
    ↓
解析Excel获取任务列表
    ↓
调用 batch_process_with_intervention
    ↓
自动批量处理（独立子会话）
    ├─ 成功的项目 → 收集输出文件
    ├─ 失败的项目 → 标记需要介入
    └─ 有问题的项目 → 自动识别需要介入
    ↓
返回结果（包含needs_intervention列表）
    ↓
Agent检查needs_intervention
    ├─ 为空 → 展示汇总报告，完成
    └─ 不为空 → 在主会话中逐个处理需要介入的项目
```

## 核心功能

### 1. 自动识别需要介入的项目

通过关键词检测响应内容：
- "需要确认"
- "请确认"
- "不存在"
- "找不到"
- "权限不足"
- "无法访问"
- "请选择"
- "请提供"
- "缺少"
- "不明确"
- "冲突"

### 2. 收集详细输出

- **完整响应**：保留每个项目的完整响应内容
- **生成文件**：自动收集生成的文件（CSV、DDL等）
- **文件归档**：将所有文件复制到统一目录

### 3. 生成汇总报告

自动生成包含以下内容的汇总报告：
- 每个项目的处理状态
- 生成的文件列表
- 需要介入的项目标记
- 错误信息

## 使用示例

### Agent工作流程

```python
# 步骤1: 解析Excel
result = execute_command("python3 skills/common-tools/excel_parser.py uploaded_file.xlsx")
data = json.loads(result)

# 步骤2: 调用增强版批量处理工具
batch_result = batch_process_with_intervention(
    items=json.dumps(data['data']),
    instruction_template='处理单号{单号}的字段映射，源库为{源库}，源表为{源表}',
    batch_size=5,
    collect_outputs=True,
    output_dir='batch_outputs'
)

# 步骤3: 检查是否有需要介入的项目
if batch_result['intervention_count'] > 0:
    print(f"⚠️  有 {batch_result['intervention_count']} 个项目需要用户介入")
    
    # 展示需要介入的项目
    for item in batch_result['needs_intervention']:
        order_id = item['item']['单号']
        print(f"\n单号: {order_id}")
        print(f"问题: {item.get('error') or item['response_summary']}")
        
        # 在主会话中处理（可以与用户交互）
        # 这里Agent会自动与用户对话，获取必要信息
        user_input = ask_user(f"请为单号 {order_id} 提供必要信息")
        
        # 重新处理该单号
        retry_result = process_single_order(order_id, user_input)

# 步骤4: 展示汇总报告
print(batch_result['summary_report'])
```

### 返回结果示例

```json
{
  "success": true,
  "status": "completed",
  "total": 5,
  "processed": 5,
  "success_count": 3,
  "fail_count": 1,
  "intervention_count": 2,
  "results": [
    {
      "index": 1,
      "item": {"单号": "ORDER001", ...},
      "status": "success",
      "response_summary": "字段映射完成...",
      "full_response": "...",
      "generated_files": [
        "batch_outputs/ORDER001-mapped.csv",
        "batch_outputs/ORDER001-ddl.sql"
      ],
      "needs_intervention": false
    },
    {
      "index": 2,
      "item": {"单号": "ORDER002", ...},
      "status": "completed",
      "response_summary": "源表不存在，需要确认...",
      "full_response": "...",
      "generated_files": [],
      "needs_intervention": true
    },
    ...
  ],
  "needs_intervention": [
    {
      "index": 2,
      "item": {"单号": "ORDER002", ...},
      "status": "completed",
      "response_summary": "源表不存在，需要确认...",
      "needs_intervention": true
    },
    {
      "index": 4,
      "item": {"单号": "ORDER004", ...},
      "status": "failed",
      "error": "权限不足",
      "needs_intervention": true
    }
  ],
  "summary_report": "============================================================\n批量处理汇总报告\n...",
  "message": "批量处理完成！总计 5 个，成功 3 个，失败 1 个，需要介入 2 个"
}
```

## 汇总报告示例

```
============================================================
批量处理汇总报告
============================================================

✅ ORDER001 - success
   📄 生成文件:
      - batch_outputs/ORDER001-mapped.csv
      - batch_outputs/ORDER001-ddl.sql

❌ ORDER002 - completed
   ⚠️  需要用户介入
   
✅ ORDER003 - success
   📄 生成文件:
      - batch_outputs/ORDER003-mapped.csv
      - batch_outputs/ORDER003-ddl.sql

❌ ORDER004 - failed
   ⚠️  需要用户介入
   ❌ 错误: 权限不足

✅ ORDER005 - success
   📄 生成文件:
      - batch_outputs/ORDER005-mapped.csv
      - batch_outputs/ORDER005-ddl.sql

============================================================
```

## Agent处理流程

### 完整流程

```
1. 用户上传Excel
   ↓
2. Agent解析Excel
   ↓
3. Agent调用batch_process_with_intervention
   ↓
4. 工具自动处理所有项目（独立子会话）
   ↓
5. 工具返回结果（包含needs_intervention列表）
   ↓
6. Agent检查intervention_count
   ├─ = 0 → 展示汇总报告，完成
   └─ > 0 → 进入介入处理流程
       ↓
7. Agent展示需要介入的项目列表
   ↓
8. Agent逐个处理需要介入的项目
   ├─ 在主会话中处理（可以与用户交互）
   ├─ 获取用户输入
   └─ 重新处理该项目
   ↓
9. 更新汇总报告
   ↓
10. 完成
```

### Agent对话示例

```
Agent: 我看到您上传了包含5个单号的Excel文件。
       现在开始批量处理...

Agent: [调用batch_process_with_intervention]
       
       批量处理完成！
       - 总计: 5个单号
       - 成功: 3个
       - 失败: 1个
       - 需要介入: 2个

Agent: ⚠️  有2个单号需要您的介入：

       1. ORDER002
          问题: 源表 user_info_v2 不存在
          可能的原因: 表名错误或表已被删除
          
       2. ORDER004
          问题: 权限不足，无法访问源库 sensitive_db
          
       是否需要我帮您处理这些问题？

User: 是的，ORDER002的表名应该是user_info，ORDER004需要申请权限

Agent: 好的，我来处理：
       
       1. 重新处理ORDER002，使用正确的表名user_info...
          ✅ ORDER002处理完成
          
       2. ORDER004需要申请权限，这个需要您联系管理员处理
       
       最终结果：
       - 成功: 4个
       - 需要人工处理: 1个（ORDER004权限问题）
       
       所有生成的文件已保存到 batch_outputs/ 目录
       汇总报告: batch_outputs/summary_report.txt
```

## 技术实现要点

### 1. 独立子会话

每个项目使用独立的`thread_id`，确保上下文隔离：
```python
sub_thread_id = f"batch_{uuid.uuid4().hex[:8]}"
result = agent.invoke(
    {"messages": [{"role": "user", "content": instruction}]},
    config={"configurable": {"thread_id": sub_thread_id}}
)
```

### 2. 关键词检测

通过关键词列表检测是否需要用户介入：
```python
intervention_keywords = [
    "需要确认", "请确认", "不存在", "找不到",
    "权限不足", "无法访问", "请选择", "请提供",
    "缺少", "不明确", "冲突"
]
```

### 3. 文件收集

自动收集生成的文件并归档：
```python
possible_files = [
    f"{order_id}.csv",
    f"{order_id}-mapped.csv",
    f"{order_id}-ddl.sql"
]

for filename in possible_files:
    if os.path.exists(filename):
        shutil.copy2(filename, output_dir)
```

### 4. 汇总报告生成

生成结构化的汇总报告：
```python
report_lines = []
for result in results:
    status_icon = "✅" if result['status'] == "success" else "❌"
    report_lines.append(f"{status_icon} {order_id} - {status}")
    if result.get('needs_intervention'):
        report_lines.append(f"   ⚠️  需要用户介入")
```

## 优势总结

1. **自动识别**：无需人工判断，自动识别需要介入的项目
2. **详细输出**：保留完整响应和生成的文件
3. **统一归档**：所有输出文件集中管理
4. **汇总报告**：一目了然的处理结果
5. **灵活处理**：支持在主会话中重新处理需要介入的项目
6. **上下文隔离**：批量处理不影响主会话上下文

## 后续优化

1. **可配置关键词**：允许用户自定义需要介入的关键词
2. **重试机制**：自动重试失败的项目
3. **并行处理**：对独立项目进行并行处理
4. **进度通知**：实时推送处理进度
5. **结果导出**：支持导出Excel格式的汇总报告
