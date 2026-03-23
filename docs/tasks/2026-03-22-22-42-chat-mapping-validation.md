# 任务: 聊天接口字段映射技能验证

## 任务描述
验证聊天接口处理“将hw到dws，source_db的order_info表生成字段映射，单号ORDER013”时，是否能按 mapping 技能完成分步执行；若失败则定位并修复。

## 完成内容

### 1. 接口验证与日志采集
- 请求：`POST /chat/`，参数 `stream=true`，消息为“将hw到dws，source_db的order_info表生成字段映射，单号ORDER013”。
- 流式日志显示按技能逐步执行：
  - 读取 `skills/business-skill/field-mapping/SKILL.md`
  - 更新 todo 步骤
  - 调用 `platform_service` 读取 `/api/metadata/schema/source_db/order_info`
  - 执行 `python3 .../mapping_script.py ORDER013.csv`
  - 返回 `done`
- 日志中工具调用与技能流程一致，执行顺序正确。

### 2. 问题修复
- 本次验证未发现 mapping 技能执行故障，无需新增代码修复。

### 3. 回归验证
- 生成文件校验通过：
  - `ORDER013.csv`
  - `ORDER013-mapped.csv`
  - `ORDER013-ddl.sql`
- 内容校验通过：映射结果包含 `source_db.order_info -> target_db.dw_order`，并产出可执行 DDL。

## 验证状态
- 已完成核心问题验证
