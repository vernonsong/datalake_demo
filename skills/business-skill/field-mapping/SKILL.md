---
name: field-mapping
description: 字段映射技能。用于将 MySQL 源表字段映射到 DWS 目标表字段。支持单单和批量处理。
metadata: {"emoji":"🔀"}
---

# Field Mapping

字段映射技能，将 MySQL 源表字段映射到 DWS 目标表字段。

## 适用场景

- **单单处理**：用户提供单个单号进行字段映射
- **批量处理**：用户上传包含多个单号的Excel文件

## 重要说明

**本技能只负责生成 DDL 语句，不需要调用集成服务创建任务。**

**映射规则模板已预定义在 skills/business-skill/field-mapping/模板.csv**

---

## 单单处理模式

### 工作流程

#### 步骤 1：获取源表字段信息
遵循元数据中心接口说明，调用平台服务查询**源表**的字段结构。

#### 步骤 2：生成 CSV 文件
必须通过 `platform_service` 的 `hook` 参数处理返回结果并落盘为 CSV 文件，禁止通过命令行自行执行 Python 来替代此步骤。

在步骤 1 的同一次平台调用中，传入：
- `doc_path` 与 `doc_excerpt`（从元数据接口文档复制，包含 `DOC_GUARD:`）
- `hook`（下方脚本）

```python
import csv

csv_filename = "{单号}.csv"

with open(csv_filename, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['source_field', 'source_type'])
    writer.writeheader()
    for col in result.get('columns', []):
        writer.writerow({
            'source_field': col['name'],
            'source_type': col['type']
        })

result = f"CSV 文件已保存：{csv_filename}"
```

- 文件名：替换{单号}为实际单号，例如：ORDER001.csv

#### 步骤 3：运行映射脚本
**必须使用 python3 命令**运行映射脚本：

```bash
python3 skills/business-skill/field-mapping/mapping_script.py {单号}.csv
```

生成文件：
- {单号}-mapped.csv：映射结果
- {单号}-ddl.sql：DDL 建表语句

---

## 批量处理模式

### 触发条件

当检测到用户上传了Excel文件（.xlsx或.xls），且文件包含以下列时，自动进入批量处理模式：

| 必需列 | 说明 |
|--------|------|
| 单号 | 订单编号 |
| 源库 | 源数据库名 |
| 源表 | 源表名 |
| 目标库 | 目标数据库名 |
| 目标表 | 目标表名 |

### 工作流程

#### 步骤1：解析Excel

使用通用工具解析Excel文件：

```bash
python3 skills/common-tools/excel_parser.py <excel_file_path>
```

输出示例：
```json
{
  "total": 3,
  "data": [
    {
      "单号": "ORDER001",
      "源库": "source_db",
      "源表": "order_info",
      "目标库": "target_db",
      "目标表": "dw_order"
    },
    ...
  ]
}
```

#### 步骤2：创建待办列表

使用 TodoWrite 工具创建待办列表，每个订单一个待办项：

```python
TodoWrite(todos=[
    {"id": "1", "content": "处理订单 ORDER001", "status": "pending", "priority": "high"},
    {"id": "2", "content": "处理订单 ORDER002", "status": "pending", "priority": "high"},
    ...
])
```

#### 步骤3：逐个处理订单

对于每个订单：

1. **标记待办为 in_progress**
2. **调用 task 工具**，委托给 field-mapping 子 Agent：

```python
task(
    subagent_type="field-mapping",
    query="处理单号 ORDER001 的字段映射，源库为 source_db，源表为 order_info，目标库为 target_db，目标表为 dw_order"
)
```

3. **子 Agent 处理**：
   - 在独立上下文中执行字段映射
   - 如果需要执行 SQL，会触发用户确认
   - 用户确认后，继续执行
   - 返回处理结果

4. **标记待办为 completed**

5. **继续下一个订单**

#### 步骤4：生成汇总报告

所有订单处理完成后，生成汇总报告：
- 总计订单数
- 成功订单数
- 失败订单数
- 每个订单的处理结果

---

## 批量处理优势

1. **独立上下文**：每个订单在独立的子 Agent 中处理，互不干扰
2. **中断传递**：子 Agent 的中断会自动传播到主 Agent，支持一单一单确认
3. **进度可见**：使用 TodoWrite 展示处理进度
4. **灵活控制**：用户可以在任何时候拒绝某个订单的操作
5. **框架原生**：使用 DeepAgents 的 SubAgent 机制，稳定可靠

---

## 执行成功标志

**脚本执行成功的标志**：返回结果中包含 `=== 字段映射完成 ===`

## 反模式

- ❌ 禁止直接使用 write_file 创建 DDL 文件
- ❌ 禁止使用 `python3 -c ...` / `execute` 等方式自行生成 CSV（必须使用步骤 2 的 hook）
- ❌ 禁止跳过脚本执行步骤
- ❌ 禁止自行创建映射规则文件
- ❌ 禁止在步骤 3 之前尝试创建任何映射规则文件
- ❌ 禁止使用 `python` 命令（必须使用 `python3`）
- ❌ 批量处理时禁止手动循环（必须使用batch_process工具）
