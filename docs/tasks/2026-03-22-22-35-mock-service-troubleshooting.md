# 任务: mock服务返回异常排查与修复

## 任务描述
排查并修复 mock 服务无法返回正确结果的问题，确保 token、鉴权与业务接口返回稳定。

## 完成内容

### 1. 问题复现与定位
- 复现到 `http://localhost:5001/health` 返回 `mock_service`，`/api/config/ali_api_key` 返回固定 `"Mock service response"`。
- 定位到 5001 端口运行的是旧入口 `mock_service/mock_server.py`，该入口只实现了极简 GET/POST，未实现 `/api/config/*`、`/api/token`、鉴权与业务接口。
- 根因是旧入口与新入口并存，误启动旧入口会导致“mock服务无法返回正确结果”。

### 2. 修复实现
- 文件: `mock_service/mock_server.py`
- 将旧入口改为兼容入口，直接委托 `mock_service.api_server.run_api_server`。
- 保留原命令 `python3 -m mock_service.mock_server` 可用，避免再次误启动错误实现。
- 文件: `tests/unit/test_mock_server_entry.py`
- 新增回归测试，验证 `run_server()` 委托到 `run_api_server()`。

### 3. 验证结果
- 执行 `python3 -m mock_service.mock_server` 后，确认：
  - `/health` 返回 `mock_api_server`
  - `/api/config/ali_api_key` 正常返回 key/value
  - `/api/token` 正常返回 token
  - 使用 token 访问 `/api/metadata/databases` 返回 200 且有 `databases`
- 执行: `PYTHONPATH=. pytest tests/unit/test_mock_server_entry.py tests/unit/test_dependencies.py tests/integration/test_config_service.py`
- 结果: `24 passed`

## 验证状态
- 已完成核心问题验证
