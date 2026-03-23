# 任务: 心跳接口调用上游接口

## 任务描述
在心跳接口中增加调用任意一上游接口，测试保证链路是通的

## 完成内容

### 1. 更新路由
- 文件: `app/routers/__init__.py`
- 修改: 心跳接口依赖注入MetadataClient，调用上游元数据服务

### 2. 更新Schema
- 文件: `app/schemas/__init__.py`
- 修改: HealthResponse添加upstream字段

### 3. 测试验证
- Mock服务运行在 localhost:5001
- FastAPI服务运行在 localhost:8000
- 验证结果: 上游状态 healthy

### 4. 验证结果
```json
{
    "status": "healthy",
    "timestamp": "2026-03-21T19:17:35.827197",
    "service": "datalake-platform",
    "upstream": {
        "metadata": "healthy"
    }
}
```

## 验证状态
✅ 已通过 task-completion-validator 验证
