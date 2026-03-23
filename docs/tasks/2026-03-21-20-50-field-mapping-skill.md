# 任务: 字段映射技能

## 任务描述
在业务技能下编写字段映射技能，包含skill.md、映射脚本、CSV模板

## 完成内容

### 1. 创建技能文件
- `skills/business-skill/field-mapping/SKILL.md` - 技能说明
- `skills/business-skill/field-mapping/单号.csv` - 字段映射表模板
- `skills/business-skill/field-mapping/mapping_script.py` - 映射脚本

### 2. 工作流程
- 从元数据服务查询源表和目标表字段结构
- 保存映射关系到CSV文件
- 运行mapping_script.py生成DDL

### 3. 验证结果
通过模拟对话验证：
- 元数据服务-获取数据库列表 ✓
- 元数据服务-获取表列表 ✓
- 字段映射-需求识别 ✓

## 验证状态
✅ 已通过 task-completion-validator 验证
