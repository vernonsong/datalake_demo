# 任务: 配置上游接口URL和密钥到YAML

## 任务描述
上游接口base_url和密钥必须在yaml配置中（xxx-dev.yaml），密钥是占位符通过配置中心获取，通过心跳接口验证流程

## 完成内容

### 1. 修正配置位置
- 移除 base.yaml 中的platform配置
- 在 inter-dev.yaml 中添加platform配置

### 2. inter-dev.yaml 配置
```yaml
platform:
  metadata:
    url: http://localhost:5001/api/metadata
    api_key: ${platform.metadata.api_key}  # 占位符，从配置中心获取
  schedule:
    url: http://localhost:5001/api/schedule
    api_key: ${platform.schedule.api_key}
  integration:
    url: http://localhost:5001/api/integration
    api_key: ${platform.integration.api_key}
  lineage:
    url: http://localhost:5001/api/lineage
    api_key: ${platform.lineage.api_key}
```

### 3. 配置合并流程
- base.yaml + inter-dev.yaml
- 合并后占位符 `${platform.xxx.api_key}` 被替换为配置中心的实际密钥

### 4. 验证结果
```
平台配置正确加载:
{
  "metadata": {
    "url": "http://localhost:5001/api/metadata",
    "api_key": "metadata-secret-key"  # 占位符已替换
  },
  ...
}

心跳接口: upstream.metadata = healthy
```

## 验证状态
✅ 已通过 task-completion-validator 验证
