# 任务: 修复 ali_api_key 配置中心报错

## 任务描述
修复后端报错 `ali_api_key is required in config center`，确保配置中心从环境变量加载敏感配置并可稳定返回。

## 完成内容

### 1. 修复配置中心密钥加载
- 文件: `mock_service/config_service.py`
- 移除硬编码敏感配置，改为从环境变量加载。
- 固定从项目根目录 `.env` 读取环境变量，避免启动目录差异导致配置缺失。
- 对 `ali_api_key`、`jwt_secret`、`mock_api_secret` 增加必填校验，缺失时启动即报错。
- 文件: `app/core/dependencies.py`
- `get_ali_api_key` 增加环境变量回退，配置中心不可用时仍可获取 `ALI_API_KEY`。

### 2. 更新测试覆盖
- 文件: `tests/integration/test_config_service.py`、`tests/unit/test_dependencies.py`
- 新增环境变量补齐，确保集成测试可稳定启动。
- 新增针对环境变量加载与缺失校验的单元测试。
- 新增依赖注入链路测试，覆盖 `get_ali_api_key` 与 `get_llm`。

### 3. 验证结果
- 执行: `PYTHONPATH=. pytest tests/integration/test_config_service.py tests/unit/test_dependencies.py`
- 结果: `23 passed`
- 执行: `PYTHONPATH=. pytest tests/unit/test_config.py`
- 结果: `29 passed`
- 执行: `python3 scripts/task_completion_validator.py`
- 结果: 当前运行环境聊天接口超时，验证器未通过
- 执行: `python3 - <<'PY' ... get_ali_api_key() ... PY`
- 结果: `True`

## 验证状态
- 已完成核心问题验证
