---
name: field-mapping
description: 字段映射技能。用于将 MySQL 源表字段映射到 DWS 目标表字段。
metadata: {"emoji":"🔀"}
---

# Field Mapping

字段映射技能，将 MySQL 源表字段映射到 DWS 目标表字段。

## 适用场景

当用户需要做数据入湖或数据同步时，需要将源表字段映射到目标表字段。

## 重要说明

**本技能只负责生成 DDL 语句，不需要调用集成服务创建任务。**

**映射规则模板已预定义在 skills/business-skill/field-mapping/模板.csv**

## 工作流程

### 步骤 1：获取源表字段信息
遵循元数据中心接口说明，调用平台服务查询**源表**的字段结构。

### 步骤 2：生成 CSV 文件
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

### 步骤 3：运行映射脚本生成目标 CSV 文件
**必须使用 python3 命令**运行映射脚本，不需要创建任何映射规则文件：

```bash
python3 skills/business-skill/field-mapping/mapping_script.py {单号}.csv
```

**注意**：
- 必须使用 `python3` 命令，不要使用 `python`（可能不存在）
- 脚本会自动读取预定义的映射规则模板
- 脚本会自动读取{单号}.csv 文件（包含源表字段信息）
- 脚本会自动生成目标 CSV 文件和 DDL 文件

生成文件：
- {单号}-mapped.csv：映射结果（包含 source_field, source_type, target_type 等）
- {单号}-ddl.sql：DDL 建表语句

## 执行成功标志

**脚本执行成功的标志**：返回结果中包含 `=== 字段映射完成 ===`

## 反模式

- ❌ 禁止直接使用 write_file 创建 DDL 文件
- ❌ 禁止使用 `python3 -c ...` / `execute` 等方式自行生成 CSV（必须使用步骤 2 的 hook）
- ❌ 禁止跳过脚本执行步骤
- ❌ 禁止自行创建映射规则文件
- ❌ 禁止在步骤 3 之前尝试创建任何映射规则文件
- ❌ 禁止使用 `python` 命令（必须使用 `python3`）
