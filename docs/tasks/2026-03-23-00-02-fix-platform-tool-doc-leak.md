# 2026-03-23-00-02-fix-platform-tool-doc-leak.md

## 问题
`platform_service` 工具的 docstring 内包含具体端点与示例，导致智能体即使未按要求阅读接口文档，也可能“照抄示例”调用成功，并在验证场景中误通过。

## 修复目标
- 移除工具层的具体端点示例，避免“知识泄露式提示”。
- 强制“先读文档再调用工具”成为可验证约束，而非口头约束。

## 变更内容
1. `platform_service` 新增必填参数 `doc_path` 与 `doc_excerpt`，并在工具执行时校验：
   - `doc_path` 必须指向对应平台的接口文档目录。
   - `doc_excerpt` 必须包含并匹配文档中的 `DOC_GUARD:` 行。
2. 为 `skills/platform-skill/**` 下的平台接口文档增加 `DOC_GUARD:` 标记，并更新示例调用补齐 `doc_path/doc_excerpt`。
3. 升级 `scripts/task_completion_validator.py`：改用流式对话收集 `file_read/tool_call` 事件，并对 `platform_service` 增加校验：
   - 必须携带 `doc_path/doc_excerpt`。
   - 调用前必须出现读取该 `doc_path` 的 `file_read` 事件。

## 验证方式
- 运行单测：`pytest tests/`
- 运行验证器：`python scripts/task_completion_validator.py`

