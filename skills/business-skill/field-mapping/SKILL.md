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

#### 步骤2：使用batch_process工具批量处理

**关键**：使用系统提供的`batch_process`工具，它会为每个单号创建独立的子会话，避免上下文累积。

调用示例：

```python
batch_process(
    items='<解析Excel得到的JSON数组字符串>',
    instruction_template='处理单号{单号}的字段映射，源库为{源库}，源表为{源表}，目标库为{目标库}，目标表为{目标表}',
    batch_size=5
)
```

**重要说明**：
- `items`: 将解析Excel得到的data数组转为JSON字符串
- `instruction_template`: 处理指令模板，使用花括号引用Excel列名
- `batch_size`: 每批处理数量，默认5个（超过会分批）

#### 步骤3：解读批量处理结果

`batch_process`工具会返回详细的处理结果：

```json
{
  "success": true,
  "status": "completed",
  "total": 3,
  "success_count": 2,
  "fail_count": 1,
  "results": [
    {
      "index": 1,
      "item": {"单号": "ORDER001", ...},
      "status": "success",
      "response": "..."
    },
    ...
  ]
}
```

根据结果向用户展示汇总信息。

---

## 批量处理优势

1. **独立上下文**：每个单号在独立的子会话中处理，互不干扰
2. **避免累积**：不会因为处理大量单号导致上下文爆炸
3. **通用能力**：`batch_process`工具可用于任何需要批量处理的场景
4. **自动分批**：超过batch_size会自动分批处理
5. **详细结果**：返回每个项目的处理状态和结果

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
